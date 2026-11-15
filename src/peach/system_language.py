"""运行 Peach 的电脑的系统界面语言（ADR-0156）。

界面语言选「自动」时，前端先看浏览器的语言偏好；浏览器里没有可用的语言，才用这里报的系统语言兜底。
只认有译文的语言：中文按文字子标签与地区分成简体和繁体（规则见 `interface_language`），英文算英文，其余报 None，由前端落到英文。
"""
from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
import locale
import os
import sys


def interface_language(tag: object) -> str | None:
    """一个语言标签（zh_TW.UTF-8、en-US、zh-Hant…）对应哪种界面语言（ADR-0201）。

    先去掉 `.编码`、`@修饰`，`_` 当 `-`，不分大小写。主语言不是 zh 的只认 en。
    中文里文字子标签优先于地区：含 Hant 给 zh-TW、含 Hans 给 zh-CN；都没有时 TW、HK、MO 给 zh-TW，其余（含只写 zh）给 zh-CN。
    与前端 `matchInterfaceLanguage` 逐项一致，两边的测试用同一组案例。
    """
    if not isinstance(tag, str):
        return None
    parts = tag.strip().lower().split(".")[0].split("@")[0].replace("_", "-").split("-")
    if parts[0] == "en":
        return "en"
    if parts[0] != "zh":
        return None
    subtags = parts[1:]
    if "hant" in subtags:
        return "zh-TW"
    if "hans" in subtags:
        return "zh-CN"
    return "zh-TW" if {"tw", "hk", "mo"} & set(subtags) else "zh-CN"


def _candidates() -> Iterator[str]:
    if sys.platform == "win32":
        # Windows 的显示语言；区域格式（GetUserDefaultLCID）可能和界面语言不同，以显示语言为准。
        try:
            import ctypes
            name = locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage())
        except (AttributeError, OSError):
            name = None
        if name:
            yield name
    for key in ("LC_ALL", "LC_MESSAGES", "LANGUAGE", "LANG"):
        value = os.environ.get(key, "")
        if value and value not in ("C", "POSIX"):
            yield from value.split(":")
    try:
        name = locale.getlocale()[0]
    except ValueError:
        name = None
    if name:
        yield name


@lru_cache(maxsize=1)
def system_language() -> str | None:
    """系统语言里第一个有译文的；系统语言在进程活着时不会变，算一次就够。"""
    for tag in _candidates():
        match = interface_language(tag)
        if match:
            return match
    return None
