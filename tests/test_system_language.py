"""运行 Peach 的电脑的系统语言：只报有译文的语言，给前端「自动」选界面语言兜底。"""
from __future__ import annotations

import unittest
from unittest import mock

from peach import system_language as module


class SystemLanguageTests(unittest.TestCase):
    def setUp(self):
        module.system_language.cache_clear()
        self.addCleanup(module.system_language.cache_clear)

    def test_language_tags_map_to_the_interface_languages_that_have_translations(self):
        cases = {"zh_CN": "zh-CN", "zh-TW": "zh-TW", "en_US.UTF-8": "en", "EN": "en",
                 "ja_JP": None, "": None, None: None}
        for tag, expected in cases.items():
            with self.subTest(tag=tag):
                self.assertEqual(module.interface_language(tag), expected)

    def test_chinese_tags_split_by_script_first_and_region_second(self):
        # 与 frontend/test/i18n.test.ts 的「中文标签按文字子标签优先、地区其次分流」用同一组案例。
        cases = {
            "zh-TW": "zh-TW", "zh_TW.UTF-8": "zh-TW", "zh-Hant": "zh-TW", "zh-Hant-CN": "zh-TW",
            "zh-HK": "zh-TW", "zh-MO": "zh-TW", "zh_HK@euro": "zh-TW", "ZH-tw": "zh-TW",
            "zh": "zh-CN", "zh-CN": "zh-CN", "zh_CN.UTF-8": "zh-CN", "zh-Hans": "zh-CN",
            "zh-Hans-TW": "zh-CN", "zh-SG": "zh-CN", "zh-MY": "zh-CN",
            "zhx": None, "ja-TW": None, "de_DE.UTF-8": None,
        }
        for tag, expected in cases.items():
            with self.subTest(tag=tag):
                self.assertEqual(module.interface_language(tag), expected)

    def test_the_first_supported_system_language_wins(self):
        with mock.patch.object(module, "_candidates", return_value=iter(["ja_JP", "zh_TW", "en_US"])):
            self.assertEqual(module.system_language(), "zh-TW")

    def test_a_system_without_a_supported_language_reports_nothing(self):
        with mock.patch.object(module, "_candidates", return_value=iter(["ja_JP", "de_DE"])):
            self.assertIsNone(module.system_language())

    def test_environment_locales_are_read_and_the_c_locale_is_ignored(self):
        environment = {"LC_ALL": "C", "LANGUAGE": "fr:en_GB", "LANG": "zh_CN.UTF-8"}
        with mock.patch.object(module.sys, "platform", "linux"), mock.patch.dict(module.os.environ, environment, clear=True), \
                mock.patch.object(module.locale, "getlocale", return_value=(None, None)):
            self.assertEqual(list(module._candidates()), ["fr", "en_GB", "zh_CN.UTF-8"])
            self.assertEqual(module.system_language(), "en")


class RequestLanguageTests(unittest.TestCase):
    """服务端直接出的页面：与前端「自动」一样先看浏览器的语言偏好，再看系统。"""

    def test_the_highest_weighted_language_with_a_translation_wins(self):
        from peach.interface_text import request_language
        with mock.patch.object(module, "system_language", return_value="zh-CN"):
            self.assertEqual(request_language("ja-JP,en-US;q=0.9,zh-CN;q=0.8"), "en")
            self.assertEqual(request_language("en;q=0.5, zh-TW;q=0.7"), "zh-TW")
            self.assertEqual(request_language("zh-Hant-HK,en;q=0.5"), "zh-TW")
            self.assertEqual(request_language("zh-CN,zh-TW;q=0.5"), "zh-CN")
            self.assertEqual(request_language("en;q=0, de"), "zh-CN")
            self.assertEqual(request_language(None), "zh-CN")
        with mock.patch.object(module, "system_language", return_value=None):
            self.assertEqual(request_language("ja"), "en")


if __name__ == "__main__":
    unittest.main()
