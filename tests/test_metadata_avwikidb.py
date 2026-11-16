"""AVWikiDB 作品页来源（ADR-0205）：解析、失败分档、来源登记、限流与冷却，以及落库规则。"""
import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

from peach import avwikidb, library_processing, performer_alias_followup, performer_profile_followup, scraping_access
from peach.http import HttpResponse
from peach.jav_cover_fetch import HostLimitedTransport
from peach.library_processing import PROVIDER_NAMES, SOURCE_INTERVALS, SOURCE_LABELS, SOURCE_LIMITER
from peach.metadata_auto_apply import _without_unbacked_identification, metadata_auto_apply_candidate
from peach.metadata_policy import (CHAIN_COMMUNITY, CHAIN_OFFICIAL, IDENTIFYING_SOURCES, REPUBLISHING_SOURCES,
                                   SOURCE_SPECS, chain_rank, independent_sources, source_tier)
from peach.repository import LedgerDatabase
from peach.scraping_access import FIRST_BLOCKED_PAUSE, SourcePaused, SourceTransport, cooldown_state
from peach.sources import PERMANENT_REASONS, SITE_SOURCES, FailureReason, Page, Session, SourceFailure
from peach.sources.avwikidb import AVWIKIDB, AVWikiDBSource
from peach.sources.replay import Cassette, minimize
from support.ledger import fresh_ledger

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "source-replay" / "avwikidb"
CHALLENGE = (b"<!DOCTYPE html><html><head><title>Just a moment...</title></head>"
             b"<body><script>window._cf_chl_opt={}</script></body></html>")


def recorded(code: str) -> Page:
    cassette = Cassette.load(FIXTURES / f"{code}.json")
    row = cassette.interactions[0]
    return Page(row["url"], row["response"]["text"].encode("utf-8"))


def work_page(movie: dict) -> Page:
    data = json.dumps({"props": {"pageProps": {"movie": movie}}}, ensure_ascii=False)
    return Page("https://avwikidb.com/work/X/",
                f'<html><script id="__NEXT_DATA__" type="application/json">{data}</script></html>'.encode())


def parse(page: Page, code: str):
    return AVWikiDBSource().parse(page, code)


class ParseRecordedSampleTests(unittest.TestCase):
    """四个录制样本（2026-11-16 联网取得，已裁成解析读的那几个键）。"""

    def test_a_censored_fanza_work_fills_every_scalar_runtime_and_tags(self):
        record = parse(recorded("SSIS-001"), "SSIS-001")
        self.assertEqual((record.code, record.release_date, record.runtime, record.studio, record.label,
                          record.series, record.director),
                         ("SSIS-001", "2021-02-18", 147.0, "エスワン ナンバーワンスタイル", "S1 NO.1 STYLE", "", "苺原"))
        self.assertTrue(record.title.startswith("一ヶ月間の禁欲の果てに"))
        self.assertEqual([row["japanese_name"] for row in record.performers], ["葵つかさ", "乙白さやか"])
        self.assertIn("FANZA独占配信", record.tags)
        self.assertEqual(record.extra, {"floor": "videoa", "actor_unknown": False, "content_id": "ssis00001"})

    def test_an_amateur_work_keeps_the_site_identified_cast_flagged(self):
        record = parse(recorded("259LUXU-1000"), "259LUXU-1000")
        self.assertEqual((record.code, record.title, record.release_date, record.runtime, record.series),
                         ("259LUXU-1000", "ラグジュTV 982", "2018-08-06", 74.0, "ラグジュTV"))
        self.assertEqual([row["japanese_name"] for row in record.performers], ["早見奈緒"])
        self.assertIs(record.extra["actor_unknown"], True)
        self.assertEqual(record.extra["floor"], "mgs")

    def test_a_mgs_censored_work_leaves_title_and_date_empty_and_records_the_delivery_date(self):
        """ABW-358：MGS 的标题带商店附注、日期是配信日，不当发行日候选（比照 Prestige 的 `delivery_date`）。"""
        record = parse(recorded("ABW-358"), "ABW-358")
        self.assertEqual((record.title, record.release_date, record.runtime, record.series, record.studio),
                         ("", "", 210.0, "絶対セイキョウイク", "プレステージ"))
        self.assertEqual(record.extra["delivery_date"], "2023-05-23")
        self.assertEqual([row["japanese_name"] for row in record.performers], ["涼森れむ"])

    def test_the_missing_work_replays_as_not_found(self):
        from peach.sources.replay import ReplayTransport, outcome_of
        cassette = Cassette.load(FIXTURES / "SSIS-9998.json")
        outcome, payload, failure = outcome_of("avwikidb", "SSIS-9998", ReplayTransport(cassette))
        self.assertEqual((outcome, payload, failure["reason"]), ("not_found", None, "not_found"))


class ParseTests(unittest.TestCase):
    def test_a_sparse_work_gives_empty_fields_not_invented_ones(self):
        record = parse(work_page({"adultVideoId": "SSIS-001", "floor": "videoa"}), "SSIS-001")
        self.assertEqual((record.title, record.studio, record.label, record.series, record.director,
                          record.release_date, record.runtime, record.performers, record.tags),
                         ("", "", "", "", "", "", None, (), ()))

    def test_nameless_actors_are_skipped_and_men_are_never_read(self):
        record = parse(work_page({
            "adultVideoId": "SSIS-001", "floor": "videoa",
            "actor": [{"actor": {"name": "葵つかさ", "fanzaAvActressId": 1}}, {"actor": {"name": " "}},
                      {"actor": {"name": "葵つかさ"}}, "junk"],
            "histrion": [{"histrion": {"name": "平田司"}}]}), "SSIS-001")
        self.assertEqual(record.performers, ({"japanese_name": "葵つかさ"},))

    def test_published_time_is_converted_to_japan_time_before_taking_the_date(self):
        record = parse(work_page({"adultVideoId": "SSIS-001", "floor": "videoa",
                                  "dateOfPublication": "2021-02-17T16:00:00.000Z"}), "SSIS-001")
        self.assertEqual(record.release_date, "2021-02-18")
        record = parse(work_page({"adultVideoId": "SSIS-001", "floor": "videoa",
                                  "dateOfPublication": "garbage"}), "SSIS-001")
        self.assertEqual(record.release_date, "")

    def test_payload_never_carries_site_authored_text_samples_images_ids_or_covers(self):
        page = work_page({
            "adultVideoId": "SSIS-001", "floor": "videoa", "title": "T",
            "summary": "站方改写的摘要", "reviewSummary": "站方改写的评论摘要", "reviewAverage": 4.3,
            "sampleVideoBestUrl": "https://cc3001.dmm.co.jp/litevideo/x.mp4",
            "mgsImageUrl": "/mgsimg/images/a.jpg", "mgsSampleImages": ["/mgsimg/images/b.jpg"],
            "amateurProfile": {"reportedName": "仮名", "age": 26},
            "actor": [{"actor": {"name": "葵つかさ", "fanzaAvActressId": 1006229, "nameEn": "Tsukasa Aoi"}}]})
        payload = parse(page, "SSIS-001").payload()
        text = json.dumps(payload, ensure_ascii=False)
        for forbidden in ("摘要", "mgsimg", "litevideo", "仮名", "reviewAverage"):
            self.assertNotIn(forbidden, text)
        self.assertEqual((payload["cover_urls"], payload["cover_url"]), ([], ""))
        self.assertEqual(payload["actresses"], [{"japanese_name": "葵つかさ"}], "不带 external_id，编号交给 ADR-0067 的绑定")

    def test_identity_accepts_the_three_writings_the_site_uses_and_rejects_another_code(self):
        amateur = {"adultVideoId": "LUXU-1000", "adultVideoAlias": "259LUXU-1000", "mgsProductCode": "259LUXU-1000",
                   "floor": "mgs"}
        self.assertEqual(parse(work_page(amateur), "259LUXU-1000").code, "259LUXU-1000")
        by_content = {"adultVideoId": "SSIS-001", "fanzaContentId": "ssis00001", "floor": "videoa"}
        self.assertEqual(parse(work_page(by_content), "SSIS-001").code, "SSIS-001")
        with self.assertRaises(SourceFailure) as caught:
            parse(work_page(by_content), "SSIS-002")
        self.assertEqual((caught.exception.reason, caught.exception.code), (FailureReason.NOT_FOUND,
                                                                             "errors.avwikidb.notFound"))

    def test_an_amateur_code_on_a_mgs_floor_still_gets_title_and_date(self):
        record = parse(work_page({"adultVideoId": "LUXU-1000", "mgsProductCode": "259LUXU-1000", "floor": "mgs",
                                  "title": "ラグジュTV 982", "dateOfPublication": "2018-08-06T00:00:00.000Z"}),
                       "259LUXU-1000")
        self.assertEqual((record.title, record.release_date), ("ラグジュTV 982", "2018-08-06"))
        self.assertNotIn("delivery_date", record.extra)


class AmateurByEvidenceTests(unittest.TestCase):
    def test_a_code_asked_without_its_numeric_prefix_is_recognised_from_the_site_writing(self):
        record = parse(work_page({"adultVideoId": "LUXU-688", "mgsProductCode": "259LUXU-688", "floor": "mgs",
                                  "title": "ラグジュTV 688", "dateOfPublication": "2017-11-26T00:00:00.000Z"}),
                       "LUXU-688")
        self.assertEqual((record.title, record.release_date), ("ラグジュTV 688", "2017-11-26"))


class FailureTests(unittest.TestCase):
    def failure(self, page, code="SSIS-001"):
        with self.assertRaises(SourceFailure) as caught:
            parse(page, code)
        return caught.exception

    def test_a_challenge_page_is_a_cloudflare_challenge_not_a_layout_change(self):
        failure = self.failure(Page("https://avwikidb.com/work/SSIS-001/", CHALLENGE))
        self.assertEqual((failure.reason, failure.code, failure.cooldown_action),
                         (FailureReason.CLOUDFLARE_CHALLENGE, "errors.avwikidb.unrecognized", "blocked"))

    def test_a_page_without_the_data_block_is_a_permanent_parse_error(self):
        failure = self.failure(Page("https://avwikidb.com/work/SSIS-001/", b"<html><title>AVWikiDB</title></html>"))
        self.assertEqual((failure.reason, failure.cooldown_action), (FailureReason.PARSE_ERROR, ""))
        self.assertIn(failure.reason, PERMANENT_REASONS)
        no_movie = Page("https://avwikidb.com/work/SSIS-001/",
                        b'<script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{}}}</script>')
        self.assertEqual(self.failure(no_movie).reason, FailureReason.PARSE_ERROR)

    def test_an_ambiguous_work_is_not_guessed(self):
        failure = self.failure(work_page({"adultVideoId": "SSIS-001", "_needsDisambiguation": True}))
        self.assertEqual((failure.reason, failure.code), (FailureReason.PARSE_ERROR, "errors.avwikidb.ambiguous"))

    def test_the_locale_resources_carry_the_three_messages(self):
        from peach import interface_text
        for code in ("unrecognized", "notFound", "ambiguous"):
            self.assertTrue(interface_text.text(f"server:errors.avwikidb.{code}"))


class CompactingTests(unittest.TestCase):
    def test_compacting_keeps_the_parse_result_and_drops_the_rest(self):
        movie = {"adultVideoId": "SSIS-001", "floor": "videoa", "title": "T", "summary": "摘要",
                 "dateOfPublication": "2021-02-17T16:00:00.000Z", "durationMin": 147,
                 "actor": [{"actor": {"name": "葵つかさ", "nameInKana": "あおい", "height": 160}}],
                 "maker": [{"maker": {"name": "M", "fanzaMakerId": 3}}], "similarSection": ["x"] * 50}
        page = work_page(movie)
        small = Page(page.url, avwikidb.compact_work_page(page.text).encode("utf-8"))
        self.assertEqual(parse(small, "SSIS-001"), parse(page, "SSIS-001"))
        for dropped in ("摘要", "あおい", "similarSection", "fanzaMakerId"):
            self.assertNotIn(dropped, small.text)

    def test_other_pages_pass_through_unchanged(self):
        for html in ("<html>404</html>", CHALLENGE.decode()):
            self.assertEqual(avwikidb.compact_work_page(html), html)
        self.assertEqual(minimize("<html>404</html>"), "<html>404</html>")


class RegistrationTests(unittest.TestCase):
    def test_the_source_is_registered_in_every_table_the_chain_reads(self):
        self.assertIs(SITE_SOURCES["avwikidb"], AVWikiDBSource)
        self.assertEqual((SOURCE_SPECS["avwikidb"].kind, SOURCE_LABELS["avwikidb"], PROVIDER_NAMES["avwikidb"]),
                         ("community", AVWIKIDB.label, AVWIKIDB.provider))
        self.assertEqual(scraping_access.source_for("https://avwikidb.com/work/SSIS-001/"), "avwikidb")
        entry = scraping_access.SOURCES["avwikidb"]
        self.assertEqual((entry["label"], entry["domains"], bool(entry.get("cookie"))),
                         (AVWIKIDB.label, AVWIKIDB.domains, False))
        self.assertEqual((AVWIKIDB.interval, SOURCE_INTERVALS["avwikidb.com"], AVWIKIDB.stage, AVWIKIDB.cookie),
                         (3.0, 3.0, "community", False))

    def test_the_source_is_community_tier_after_javdb_and_never_outranks_an_official_one(self):
        self.assertEqual(source_tier("avwikidb"), CHAIN_COMMUNITY)
        for field in ("title", "performers", "studio", "series", "release_date", "tags"):
            with self.subTest(field=field):
                self.assertLess(chain_rank(field, "javdb"), chain_rank(field, "avwikidb"))
                self.assertLess(chain_rank(field, "dmm"), chain_rank(field, "avwikidb"))
                self.assertLess(chain_rank(field, "avwikidb"), chain_rank(field, "javbus"))
        self.assertGreater(source_tier("avwikidb"), CHAIN_OFFICIAL)
        self.assertEqual(REPUBLISHING_SOURCES, {"avwikidb"})
        self.assertNotIn("avwikidb", IDENTIFYING_SOURCES)


class RateLimitAndCooldownTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_the_work_pages_and_the_follow_ups_wait_on_the_same_limiter(self):
        """作品页（`LibraryMetadataProvider.transport`）与补女优资料、补头像后继共一份限速器：合计每 3 秒一页。"""
        provider = library_processing.LibraryMetadataProvider(self.root / "secrets")
        self.assertIs(provider.transport.limiter, SOURCE_LIMITER)
        contract = SimpleNamespace(candidate_root=self.root / "candidates", follow_secrets_root=self.root / "secrets")
        pages = performer_profile_followup.avwikidb_pages(contract)
        self.assertIs(pages.limiter, SOURCE_LIMITER)
        self.assertIsNot(pages.limiter, performer_alias_followup._LIMITER)
        self.assertEqual(SOURCE_LIMITER._intervals["avwikidb.com"], 3.0)

    def test_a_challenge_served_with_200_pauses_the_site_and_the_follow_up_pages_see_the_same_record(self):
        calls = []

        def fake(request, timeout, limit):
            calls.append(request.url)
            return HttpResponse(200, {}, CHALLENGE, request.url)

        raw = SourceTransport(self.root)
        raw.transports["avwikidb"] = fake
        session = Session(HostLimitedTransport(raw, 0.0))
        with self.assertRaises(SourceFailure) as caught:
            SITE_SOURCES["avwikidb"]().query("SSIS-001", session=session)
        self.assertEqual(caught.exception.reason, FailureReason.CLOUDFLARE_CHALLENGE)
        until, blocks = cooldown_state(self.root, "avwikidb")
        self.assertEqual((round(until - time.time()), blocks), (FIRST_BLOCKED_PAUSE, 1))
        with self.assertRaises(SourcePaused):
            SITE_SOURCES["avwikidb"]().query("SSIS-002", session=session)
        self.assertEqual(len(calls), 1, "冷却期内第二部片不发请求")
        # 同一份冷却记录：补女优资料后继的取页器（同一个凭据根）也停下。
        contract = SimpleNamespace(candidate_root=self.root / "candidates", follow_secrets_root=self.root)
        pages = performer_profile_followup.avwikidb_pages(contract)
        with self.assertRaises(performer_alias_followup.Blocked):
            pages.get("https://avwikidb.com/actor/1/")


class CoverMissMemoryTests(unittest.TestCase):
    def test_joining_the_chain_does_not_void_a_recorded_no_cover_answer(self):
        """AVWikiDB 不给封面：接上它之前记下的「封面没有」不作废，不为此重问一遍封面来源（含 javdb 的配额）。"""
        from unittest.mock import Mock
        from peach.library_processing import _MissCache, _RemoteSession
        from peach.metadata_routes import COVERLESS_SOURCES, route_for_code
        self.assertEqual(COVERLESS_SOURCES, ("avwikidb",))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "misses.json"
            before = sorted(name for name in SOURCE_SPECS if name != "avwikidb")
            old = _MissCache(path, now=lambda: 1000.0, sites=before)
            old.record("cover", "SSIS-001")
            fresh = _MissCache(path, now=lambda: 2000.0)
            self.assertIn("avwikidb", route_for_code("SSIS-001"))
            session = _RemoteSession(SimpleNamespace(), None, fresh, retrying=False)
            session._provider = Mock()
            row = {"id": 1, "name": "SSIS-001.mp4", "path": "B:\a.mp4"}
            issue = Mock()
            self.assertEqual(session._cover(row, "SSIS-001", root, update=lambda **_: None, issue=issue), 0)
            session._provider.cover.assert_not_called()


class IndependentSourcesTests(unittest.TestCase):
    def test_a_republisher_never_counts_as_a_second_independent_source(self):
        dmm, javbus, wiki = {"source": "dmm"}, {"source": "javbus"}, {"source": "avwikidb"}
        self.assertEqual(independent_sources("title", [dmm, wiki]), 1)
        self.assertEqual(independent_sources("studio", [javbus, wiki]), 1)
        self.assertEqual(independent_sources("title", [wiki]), 1, "只有它一家时仍算一家，不为零")
        self.assertEqual(independent_sources("title", [dmm, javbus]), 2)

    def test_its_identification_of_the_cast_is_its_own_judgement(self):
        identified = {"source": "avwikidb", "site_identified": True}
        wiki = {"source": "av_neme"}
        self.assertEqual(independent_sources("performers", [wiki, identified]), 2)
        self.assertEqual(independent_sources("performers", [wiki, {"source": "avwikidb"}]), 1)
        self.assertEqual(independent_sources("title", [wiki, identified]), 1)


def cast(source, *names, identified=False):
    return {"source": source, "value": [{"name": name} for name in names],
            "display_value": "、".join(names), **({"site_identified": True} if identified else {})}


class UnbackedIdentificationTests(unittest.TestCase):
    def test_a_site_identified_cast_alone_is_not_evidence(self):
        lone = cast("avwikidb", "早見奈緒", identified=True)
        self.assertEqual(_without_unbacked_identification("performers", [lone]), [])

    def test_with_no_name_wiki_heard_the_whole_cast_field_is_withheld_for_review(self):
        """MGStage 的素人名义若照旧自动补空，站方认出的艺名就再也进不了复核。"""
        lone, official = cast("avwikidb", "早見奈緒", identified=True), cast("mgstage", "まいな")
        self.assertEqual(_without_unbacked_identification("performers", [official, lone]), [])

    def test_it_counts_once_another_identifying_source_names_the_same_people(self):
        lone, wiki = cast("avwikidb", "早見奈緒", "別人", identified=True), cast("av_neme", "別人", "早見奈緒")
        self.assertEqual(_without_unbacked_identification("performers", [wiki, lone]), [wiki, lone])
        other = cast("sougouwiki", "別の誰か")
        official = cast("mgstage", "まいな")
        self.assertEqual(_without_unbacked_identification("performers", [official, other, lone]), [official, other],
                         "认人 Wiki 给了别的人：听 Wiki，站方那份单独丢掉")

    def test_an_official_cast_from_the_same_site_and_other_fields_are_untouched(self):
        credited = cast("avwikidb", "葵つかさ")
        self.assertEqual(_without_unbacked_identification("performers", [credited]), [credited])
        title = {**cast("avwikidb", "x", identified=True), "display_value": "T"}
        self.assertEqual(_without_unbacked_identification("title", [title]), [title])

    def test_a_mgstage_name_is_not_a_backer(self):
        """MGStage 给的是素人名义，不是认人来源。"""
        lone, nominal = cast("avwikidb", "まいな", identified=True), cast("mgstage", "まいな")
        self.assertEqual(_without_unbacked_identification("performers", [nominal, lone]), [])


class AutoApplyTests(unittest.TestCase):
    """用真账本核 `metadata_auto_apply_candidate`：单独的站方认人不落库，同源转载不算第二家印证。"""

    CODE = "259LUXU-1000"

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.database = LedgerDatabase(fresh_ledger(self.root))
        with self.database.write_transaction() as connection:
            connection.execute("INSERT INTO asset(id,location,path,name,code,medium) VALUES(1,?,?,?,?,'video')",
                               ("local", "B:\\a.mp4", f"{self.CODE}.mp4", self.CODE))

    def group(self, field, *answers):
        """`answers` 是 (来源, 快照 dict)；经 `_merge_candidates` 生成候选，与采集同一条路。"""
        groups = {}
        row = dict(id=1, name=f"{self.CODE}.mp4", path="B:\\a.mp4", size=8)
        for source, document in answers:
            library_processing._merge_candidates(groups, row, self.CODE, source, {"id": self.CODE, **document},
                                                 self.root / f"{source}.json", {}, database=self.database)
        group = groups[f"asset:1:{field}"]
        return {**group, "candidates": json.loads(group["candidates_json"])}

    def apply(self, group):
        with self.database.read_connection() as connection:
            return metadata_auto_apply_candidate(connection, group)

    def test_a_site_identified_cast_alone_stays_a_candidate_for_manual_review(self):
        group = self.group("performers", ("avwikidb", {"actresses": [{"japanese_name": "早見奈緒"}],
                                                       "actor_unknown": True}))
        self.assertTrue(group["candidates"][0]["site_identified"])
        self.assertIsNone(self.apply(group))

    def test_an_amateur_nominal_name_does_not_land_over_an_unbacked_identification(self):
        """真实素人链上永远有 MGStage 的素人名义：它不能把站方认出的艺名挤出复核。"""
        group = self.group("performers", ("mgstage", {"actresses": [{"japanese_name": "まいな"}]}),
                           ("avwikidb", {"actresses": [{"japanese_name": "早見奈緒"}], "actor_unknown": True}))
        self.assertEqual({c["source"] for c in group["candidates"]}, {"mgstage", "avwikidb"})
        self.assertIsNone(self.apply(group))
        without = self.group("performers", ("mgstage", {"actresses": [{"japanese_name": "まいな"}]}))
        self.assertEqual(self.apply(without)["source"], "mgstage", "没有站方认人时 MGStage 照旧补空")

    def test_the_batch_script_flags_the_same_candidates(self):
        """`scrape_codes` 自己摊候选，标记要与采集任务同一个，否则那条路上单独的认人会直接落库。"""
        from collections import defaultdict
        from test_scripts import load_script
        script = load_script("scrape_codes")
        for unknown, expected in ((True, True), (False, False)):
            health = defaultdict(lambda: defaultdict(int))
            found = script._candidates_from(
                {"id": self.CODE, "actresses": [{"japanese_name": "早見奈緒"}], "title": "T", "actor_unknown": unknown},
                query=self.CODE, source="avwikidb", profile="chain", snapshot=self.root / "s.json",
                genre_decisions={}, health=health, unmapped_genres={}, code=self.CODE)
            self.assertEqual(bool(found["performers"].get("site_identified")), expected)
            self.assertNotIn("site_identified", found["title"])

    def test_it_lands_with_two_agreeing_sources_once_a_name_wiki_agrees(self):
        people = [{"japanese_name": "早見奈緒"}]
        group = self.group("performers", ("av_neme", {"actresses": people}),
                           ("avwikidb", {"actresses": people, "actor_unknown": True}))
        chosen = self.apply(group)
        self.assertEqual((chosen["source"], chosen["agreed_sources"]), ("av_neme", 2))

    def test_it_does_not_override_a_disagreeing_name_wiki(self):
        group = self.group("performers", ("sougouwiki", {"actresses": [{"japanese_name": "別の人"}]}),
                           ("avwikidb", {"actresses": [{"japanese_name": "早見奈緒"}], "actor_unknown": True}))
        chosen = self.apply(group)
        self.assertEqual((chosen["source"], chosen["agreed_sources"]), ("sougouwiki", 1))

    def test_an_officially_credited_cast_from_it_fills_an_empty_field_like_any_single_community_source(self):
        group = self.group("performers", ("avwikidb", {"actresses": [{"japanese_name": "早見奈緒"}],
                                                       "actor_unknown": False}))
        chosen = self.apply(group)
        self.assertEqual((chosen["source"], chosen["agreed_sources"]), ("avwikidb", 1))

    def test_scalar_agreement_with_an_official_source_counts_as_one(self):
        official = ("dmm", {"title": "ラグジュTV 982"})
        mirror = ("avwikidb", {"title": "ラグジュTV 982"})
        chosen = self.apply(self.group("title", official, mirror))
        self.assertEqual(chosen["agreed_sources"], 1)
        independent = ("avbase", {"title": "ラグジュTV 982"})
        self.assertEqual(self.apply(self.group("title", official, independent))["agreed_sources"], 2)

    def test_it_alone_fills_an_empty_scalar_but_never_replaces_a_value(self):
        group = self.group("title", ("avwikidb", {"title": "ラグジュTV 982"}))
        self.assertEqual(self.apply(group)["source"], "avwikidb")
        replacing = {**group, "current_value": "既存の題"}
        self.assertIsNone(self.apply(replacing), "社区来源只补空，不改已有值（ADR-0033）")


if __name__ == "__main__":
    unittest.main()
