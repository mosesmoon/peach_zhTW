"""AVWikiDB 的作品页：社区来源，只读 `__NEXT_DATA__` 里的 `pageProps.movie`（ADR-0205）。

`/work/<番号>/` 是 Next.js 页，一次请求给全。站方自述作品资料来自 FANZA 官方 API（MGS 一侧另行匯入），
所以标题、厂牌、系列、导演、类别、片长都是 DMM／MGS 的原文，与 r18.dev、DMM、MGStage 同源，只有一类
是它独有的：官方没有署名的作品，站方按包装印字、同作别号与人工比对认出来的演员（`actorUnknown`）。
同源的标量字段在有码链上只补空，不当第二家印证（`metadata_policy.independent_sources`）；站方认出的
演员单独不自动落库（`metadata_auto_apply._without_unbacked_identification`）。

不采用的字段：站方改写的 `summary`、`reviewSummary`；样片网址；`/mgsimg/` 站内图片路径（robots.txt 对
AI 相关爬虫明确禁止）。`cover_urls` 留空：图本体是 DMM／MGS 的图，封面层另有来源，转载地址放进来会被
封面互证误算成第二个图源。演员不带编号：编号只在「恰好一位对得上」时由补女优资料后继绑定（ADR-0067）。

日期是 UTC 的 ISO 时间，换成日本时间再取日。MGS 一侧的有码作品（Prestige 的 `ABW-358`）给的是配信开始日，
标题还带商店附注，所以标题留空、日期记进 `extra['delivery_date']`，与 `metadata_amane` 对 Prestige 的做法一致。
"""
from __future__ import annotations

import urllib.parse
from datetime import datetime, timedelta, timezone

from .. import avwikidb
from ..metadata import identifies_code
from ..metadata_routes import classify
from .base import FailureReason, Page, Session, SiteConfig, SiteRecord, SiteSource, SourceFailure, challenge_page

#: 个人营运的单点站，主机间隔与补女优资料后继一致，用 3 秒；不带 Cookie，拒绝访问由 Cloudflare 按出口判。
AVWIKIDB = SiteConfig(name="avwikidb", label="AVWikiDB", provider="avwikidb-work",
                      base_url="https://avwikidb.com", domains=("avwikidb.com",), stage="community",
                      interval=3.0)

UNRECOGNISED_CODE = "errors.avwikidb.unrecognized"
#: 标量字段（标题、发行日）可信的 `floor`：DMM 数字版与素人版。MGS 版的有码作品不在此列。
OFFICIAL_FLOORS = frozenset({"videoa", "videoc"})
_JST = timezone(timedelta(hours=9))


def _name(value: object, key: str) -> str:
    """`maker[0].maker.name` 这一类两层嵌套里的名字；缺任何一层是空串。"""
    first = value[0] if isinstance(value, list) and value else None
    inner = first.get(key) if isinstance(first, dict) else None
    return str(inner.get("name") or "").strip() if isinstance(inner, dict) else ""


def _names(value: object, key: str) -> tuple[str, ...]:
    rows = value if isinstance(value, list) else []
    found = (_name([row], key) for row in rows)
    return tuple(dict.fromkeys(name for name in found if name))


def _jst_date(value: object) -> str:
    """`2021-02-18T01:00:54.000Z` → `2021-02-18`；读不出是空串。"""
    try:
        moment = datetime.fromisoformat(str(value or "").strip().replace("Z", "+00:00"))
    except ValueError:
        return ""
    return moment.astimezone(_JST).date().isoformat() if moment.tzinfo else ""


def _minutes(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0 else None


class AVWikiDBSource(SiteSource):
    DEFAULT = AVWIKIDB

    def fetch(self, code: str, *, session: Session) -> Page:
        return session.get(f"{self.config.base_url}/work/{urllib.parse.quote(code.upper(), safe='-')}/",
                           config=self.config)

    def parse(self, page: Page, code: str) -> SiteRecord:
        text = page.text
        movie = avwikidb.work_movie(text)
        if movie is None:
            reason = FailureReason.CLOUDFLARE_CHALLENGE if challenge_page(text) else FailureReason.PARSE_ERROR
            raise SourceFailure(reason, UNRECOGNISED_CODE)
        if movie.get("_needsDisambiguation"):
            raise SourceFailure(FailureReason.PARSE_ERROR, "errors.avwikidb.ambiguous")
        content_id = str(movie.get("fanzaContentId") or "").strip()
        writings = [str(movie.get(key) or "").strip()
                    for key in ("mgsProductCode", "adultVideoAlias", "adultVideoId")]
        shown = next((writing for writing in writings if writing), "")
        if not shown or not any(identifies_code(code, {"id": writing, "content_id": content_id})
                                for writing in writings if writing):
            raise SourceFailure(FailureReason.NOT_FOUND, "errors.avwikidb.notFound")
        floor = str(movie.get("floor") or "").strip()
        # 问的是不带数字前缀的写法（`LUXU-688`，靠本机证据才认得是素人）时，站上读回的 `259LUXU-688` 认得出。
        official = floor in OFFICIAL_FLOORS or "amateur" in (classify(code), classify(shown))
        published = _jst_date(movie.get("dateOfPublication"))
        cast = movie.get("actor") if isinstance(movie.get("actor"), list) else []
        performers = tuple({"japanese_name": name} for name in dict.fromkeys(
            str((row.get("actor") or {}).get("name") or "").strip()
            for row in cast if isinstance(row, dict) and isinstance(row.get("actor"), dict)) if name)
        extra: dict = {"floor": floor, "actor_unknown": bool(movie.get("actorUnknown"))}
        if content_id:
            extra["content_id"] = content_id
        if published and not official:
            extra["delivery_date"] = published
        return SiteRecord(
            source=self.config.name, provenance=self.config.provider, code=shown,
            source_url=f"{self.config.base_url}/work/{urllib.parse.quote(shown.upper(), safe='-')}/",
            title=str(movie.get("title") or "").strip() if official else "",
            performers=performers,
            studio=_name(movie.get("maker"), "maker"), label=_name(movie.get("label"), "label"),
            series=_name(movie.get("series"), "series"), director=_name(movie.get("director"), "director"),
            release_date=published if official else "", runtime=_minutes(movie.get("durationMin")),
            tags=_names(movie.get("genre"), "genre"), extra=extra)
