"""zh-TW 语言资源由 `scripts/build_zh_tw_locales.py` 从 zh-CN 产生：键、占位、字形与覆写都与源文对得上。"""
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_zh_tw_locales as builder  # noqa: E402


jobs = builder.jobs


class ZhTwLocaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.terms = builder.Terms(builder.load_json(builder.TERMS))

    def test_the_committed_files_match_a_fresh_build(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_zh_tw_locales.py"), "--check"],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_every_zh_cn_namespace_has_a_zh_tw_file_with_the_same_keys_in_the_same_order(self):
        for name, source, target in jobs():
            with self.subTest(name):
                self.assertTrue(target.exists(), target)
                self.assertEqual(list(builder.flatten(builder.load_json(target))),
                                 list(builder.flatten(builder.load_json(source))))

    def test_placeholders_and_nested_references_match_the_source_exactly(self):
        for name, source, target in jobs():
            with self.subTest(name):
                zh_cn, zh_tw = (builder.flatten(builder.load_json(path)) for path in (source, target))
                mismatched = [key for key in zh_cn
                              if sorted(builder.PLACEHOLDER.findall(zh_cn[key]))
                              != sorted(builder.PLACEHOLDER.findall(zh_tw[key]))]
                self.assertEqual(mismatched, [])

    def test_no_simplified_characters_remain_outside_the_allow_list(self):
        for name, _source, target in jobs():
            with self.subTest(name):
                left = {key: builder.simplified_leftovers(text, self.terms.allow)
                        for key, text in builder.flatten(builder.load_json(target)).items()}
                self.assertEqual({key: found for key, found in left.items() if found}, {})

    def test_every_override_key_exists_in_the_source(self):
        for name, source, _target in jobs():
            with self.subTest(name):
                path = builder.OVERRIDES / f"{name}.json"
                self.assertTrue(path.exists(), path)
                overrides = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(sorted(set(overrides) - set(builder.flatten(builder.load_json(source)))), [])

    def test_a_stale_override_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(builder, "OVERRIDES", Path(folder)):
            (Path(folder) / "probe.json").write_text(json.dumps({"gone": "文字"}, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(builder.BuildError):
                builder.load_overrides("probe", {"kept": "文字"})

    def test_protected_fragments_survive_conversion_unchanged(self):
        text = "访问 `演员:` 与 https://example.com/文 {{count, number}} $t(shared.ok) <b>默认</b> C:\\data\\a.json"
        converted = builder.convert_text(text, self.terms)
        for fragment in ("`演员:`", "https://example.com/", "{{count, number}}", "$t(shared.ok)",
                         "<b>", "</b>", "C:\\data\\a.json"):
            self.assertIn(fragment, converted)
        self.assertNotIn("訪問", converted)

    def test_term_rules_do_not_rewrite_their_own_results(self):
        for source, expected in (("埠", "連接埠"), ("进程", "處理程序"),
                                 ("端口", "連接埠"), ("应用程序", "應用程式"), ("刮削", "擷取"),
                                 ("采集", "抓取"), ("抽帧", "擷取影格"), ("采集刮削", "抓取擷取")):
            with self.subTest(source):
                self.assertEqual(builder.convert_text(source, self.terms), expected)

    def test_a_changed_source_text_gives_a_review_warning_but_does_not_fail(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(builder, "OVERRIDES", Path(folder)):
            (Path(folder) / "probe.json").write_text(
                json.dumps({"k": {"text": "覆寫", "source": "舊原文"}}, ensure_ascii=False), encoding="utf-8")
            final, warnings = builder.load_overrides("probe", {"k": "新原文"})
        self.assertEqual(final, {"k": "覆寫"})
        self.assertEqual(len(warnings), 1)

    def test_an_override_with_different_placeholders_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(builder, "OVERRIDES", Path(folder)):
            (Path(folder) / "probe.json").write_text(json.dumps({"k": "沒有占位"}, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(builder.BuildError):
                builder.load_overrides("probe", {"k": "共 {{count}} 個"})


if __name__ == "__main__":
    unittest.main()
