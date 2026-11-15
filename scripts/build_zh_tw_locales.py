"""由 zh-CN 语言资源产生 zh-TW：OpenCC `s2twp` → 术语与常用词后处理 → 逐键覆写。

zh-TW 不手改：上游每天改 zh-CN，所以 `resources/locales/zh-TW/*.json` 与 `scripts/locales/zh-TW/dev.json`
都是本脚本的产物。审校者只编辑 `scripts/zh_tw/overrides/<命名空间>.json`（点号路径键 → 最终字串，
或 `{"text": ..., "source": ...}`，`source` 记录覆写所依据的 zh-CN 源文）和 `scripts/zh_tw/terms.json`。

用法：
  python scripts/build_zh_tw_locales.py          写出全部 zh-TW 文件
  python scripts/build_zh_tw_locales.py --check  不写文件，产物与现有文件逐字节不同时以 1 退出
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import opencc

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "resources" / "locales" / "zh-CN"
TARGET_DIR = ROOT / "resources" / "locales" / "zh-TW"
DEV_SOURCE = ROOT / "scripts" / "locales" / "zh-CN" / "dev.json"
DEV_TARGET = ROOT / "scripts" / "locales" / "zh-TW" / "dev.json"
TERMS = ROOT / "scripts" / "zh_tw" / "terms.json"
OVERRIDES = ROOT / "scripts" / "zh_tw" / "overrides"
DEV_NAME = "dev"

HAN = re.compile("[" + chr(0x3400) + "-" + chr(0x9FFF) + "]")
#: 不可变片段：转换前换成占位记号，转换后还原。
PROTECTED_SPANS = re.compile("|".join([
    r"\{\{[^{}]*\}\}",                         # i18next 占位
    r"\$t\([^()]*\)",                          # 嵌套翻译
    r"</?[A-Za-z][A-Za-z0-9-]*(?:\s+[A-Za-z][\w:-]*(?:=(?:\"[^\"]*\"|'[^']*'|[^\s<>\"']+))?)*\s*/?>",  # HTML 标签与属性
    r"https?://[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+",  # URL
    r"`[^`]*`",                                # 反引号程序片段
    r"[A-Za-z]:\\[A-Za-z0-9_.\\/\-]*",         # Windows 路径
    r"(?<![\w/.])(?:~?/[A-Za-z0-9_.\-]+)+/?",  # POSIX 路径
    r"[A-Za-z0-9_\-]+(?:\.[A-Za-z0-9_\-]+)*\.[A-Za-z][A-Za-z0-9]{0,7}\b",  # 带副档名的文件名
]))
PLACEHOLDER = re.compile(r"\{\{[^{}]*\}\}|\$t\([^()]*\)")
MARK_OPEN, MARK_CLOSE = chr(0xE000), chr(0xE001)
MARK = re.compile(MARK_OPEN + r"(\d+)" + MARK_CLOSE)

S2TWP = opencc.OpenCC("s2twp")
S2T = opencc.OpenCC("s2t")
T2S = opencc.OpenCC("t2s")


class BuildError(Exception):
    """产物不合格：键结构、占位、简体残留或覆写有问题。"""


def flatten(tree: dict, prefix: str = "") -> dict[str, str]:
    flat: dict[str, str] = {}
    for key, value in tree.items():
        if isinstance(value, dict):
            flat.update(flatten(value, f"{prefix}{key}."))
        else:
            flat[prefix + key] = value
    return flat


def map_leaves(tree: dict, convert, prefix: str = "") -> dict:
    """保持键与顺序，只替换叶节点字串；`convert(路径, 值)`。"""
    out: dict = {}
    for key, value in tree.items():
        out[key] = (map_leaves(value, convert, f"{prefix}{key}.") if isinstance(value, dict)
                    else convert(prefix + key, value))
    return out


class Terms:
    """术语后处理：glossary 与 phrases 合成一次最长优先的单遍替换，改写结果不会被再次改写。"""

    def __init__(self, data: dict):
        rules = {**data.get("phrases", {}), **data.get("glossary", {})}
        explicit = {item for item in data.get("protected", []) if not item.startswith("_")}
        # 改写结果若含有某条规则的键（例如「外掛」→「外掛程式」），转换后的文字里本来就有的结果
        # 会被再改一次，所以这样的结果自动当成受保护词。
        auto = {value for value in rules.values() if any(key in value for key in rules)}
        self.protected = explicit | auto
        self.rules = {key: value for key, value in rules.items() if key != value}
        entries = {**self.rules, **{word: word for word in self.protected}}
        ordered = sorted(entries, key=lambda word: (-len(word), word))
        self.entries = entries
        self.pattern = re.compile("|".join(re.escape(word) for word in ordered)) if ordered else None
        # 受保护词是核定的写法，其中的「里」「后」「采」等不算简体残留。
        self.allow = [item for item in data.get("allow_simplified", []) if not item.startswith("_")] + sorted(self.protected)

    def apply(self, text: str) -> str:
        if self.pattern is None:
            return text
        return self.pattern.sub(lambda match: self.entries[match.group(0)], text)


def convert_text(text: str, terms: Terms, post: bool = True) -> str:
    """一条源文的转换：保护不可变片段 → OpenCC → 术语后处理 → 还原，并断言占位集合不变。"""
    spans: list[str] = []

    def hide(match: re.Match) -> str:
        spans.append(match.group(0))
        return f"{MARK_OPEN}{len(spans) - 1}{MARK_CLOSE}"

    converted = S2TWP.convert(PROTECTED_SPANS.sub(hide, text))
    if post:
        converted = terms.apply(converted)
    result = MARK.sub(lambda match: spans[int(match.group(1))], converted)
    check_placeholders(text, result)
    return result


def check_placeholders(source: str, target: str, where: str = "") -> None:
    if sorted(PLACEHOLDER.findall(source)) != sorted(PLACEHOLDER.findall(target)):
        raise BuildError(f"placeholder mismatch{where}: {source!r} -> {target!r}")


def simplified_leftovers(text: str, allow: list[str]) -> list[str]:
    """文字里仍是简体的字：s2t 会改写、而 t2s 不认得它是繁体的字；`allow_simplified` 里的词先剔除。"""
    for word in sorted(allow, key=len, reverse=True):
        text = text.replace(word, "")
    found = []
    text = PROTECTED_SPANS.sub("", text)  # 反引号等受保护片段原样保留，不检查
    for char in dict.fromkeys(HAN.findall(text)):
        if S2T.convert(char) != char and T2S.convert(char) == char:
            found.append(char)
    return found


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(tree: dict) -> bytes:
    return (json.dumps(tree, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def load_overrides(name: str, source: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """逐键覆写：返回 {键: 最终字串} 与「源文已变」的警告。覆写键不在源文、占位不一致都报错。"""
    path = OVERRIDES / f"{name}.json"
    raw = load_json(path) if path.exists() else {}
    final, warnings = {}, []
    for key, entry in raw.items():
        if key not in source:
            raise BuildError(f"stale override {name}:{key} (key is gone from zh-CN)")
        text, recorded = (entry, None) if isinstance(entry, str) else (entry["text"], entry.get("source"))
        check_placeholders(source[key], text, f" in override {name}:{key}")
        if recorded is not None and recorded != source[key]:
            warnings.append(f"override needs review {name}:{key}: zh-CN source changed")
        final[key] = text
    return final, warnings


def build_one(name: str, source_tree: dict, terms: Terms) -> tuple[dict, dict, list[str]]:
    """返回 (zh-TW 树, 统计, 警告)。"""
    source = flatten(source_tree)
    overrides, warnings = load_overrides(name, source)
    stats = {"strings": len(source), "rewritten": 0, "overridden": len(overrides)}

    def convert(path: str, value: str) -> str:
        if path in overrides:
            return overrides[path]
        plain = convert_text(value, terms, post=False)
        result = convert_text(value, terms)
        stats["rewritten"] += plain != result
        return result

    target = map_leaves(source_tree, convert)
    flat = flatten(target)
    if list(flat) != list(source):
        raise BuildError(f"{name}: key structure differs from zh-CN")
    problems = []
    for key, text in flat.items():
        left = simplified_leftovers(text, terms.allow)
        if left:
            problems.append(f"{name}:{key}: simplified characters {''.join(left)} in {text[:60]!r}")
    if problems:
        raise BuildError("\n".join(problems))
    return target, stats, warnings


def jobs() -> list[tuple[str, Path, Path]]:
    found = [(path.stem, path, TARGET_DIR / path.name) for path in sorted(SOURCE_DIR.glob("*.json"))]
    return found + [(DEV_NAME, DEV_SOURCE, DEV_TARGET)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build zh-TW locale files from zh-CN.")
    parser.add_argument("--check", action="store_true",
                        help="do not write; exit 1 if the zh-TW files differ from a fresh build")
    args = parser.parse_args(argv)
    terms = Terms(load_json(TERMS))
    stale, failed = [], False
    for name, source_path, target_path in jobs():
        try:
            tree, stats, warnings = build_one(name, load_json(source_path), terms)
        except BuildError as error:
            print(f"error: {error}", file=sys.stderr)
            failed = True
            continue
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
        body = dump(tree)
        print(f"{name}: {stats['strings']} strings, {stats['rewritten']} rewritten by terms, "
              f"{stats['overridden']} overridden")
        if args.check:
            if not target_path.exists() or target_path.read_bytes() != body:
                stale.append(target_path.relative_to(ROOT).as_posix())
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(body)
    if stale:
        print("error: out of date, run scripts/build_zh_tw_locales.py: " + ", ".join(stale), file=sys.stderr)
    return 1 if failed or stale else 0


if __name__ == "__main__":
    sys.exit(main())
