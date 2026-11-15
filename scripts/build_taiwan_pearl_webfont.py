"""Slice the Taiwan Pearl TTF into unicode-range woff2 segments for the web UI.

Run it in a throwaway environment (fonttools and brotli are not project dependencies):

    uv run --no-project --with fonttools --with brotli python scripts/build_taiwan_pearl_webfont.py \
        --font <TaiwanPearl-Regular.ttf> --license <SIL_Open_Font_License_1.1.txt> \
        --out web/vendor/taiwan-pearl/2.125

The font is licensed under SIL OFL 1.1 with the Reserved Font Name "TaiwanPearl". A subset is a
Modified Version, so every user-facing name record is rewritten to FAMILY and the copyright and
license notices (name IDs 0, 13 and 14) are kept. The output directory is deterministic for a given
input font and fonttools version; content-hashed file names let `/vendor/` stay immutable.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import io
import shutil
import sys
from pathlib import Path


# fontTools and brotli are build-time tools run through `uv run --no-project --with`, not project
# dependencies, so they are loaded by name instead of declared imports.
subset = importlib.import_module("fontTools.subset")
TTFont = importlib.import_module("fontTools.ttLib").TTFont

FAMILY = "Peach Round TC"
POSTSCRIPT = "PeachRoundTC-Regular"
COMMON_CHUNK = 300
SECONDARY_CHUNK = 1100
REST_CHUNK = 2500
HANGUL = (0xAC00, 0xD7FF)
HANGUL_CHUNK = 3800
# Everything outside the ideograph blocks and Hangul syllables shares one segment: Latin, punctuation,
# Bopomofo, kana and symbols.
IDEOGRAPH_BLOCKS = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF), (0x20000, 0x323AF), (0x2F800, 0x2FA1F))


def is_ideograph(code: int) -> bool:
    return any(low <= code <= high for low, high in IDEOGRAPH_BLOCKS)


def big5_range(first_lead: int, last_lead: int, last_code: int | None = None) -> list[int]:
    """Code points of the Big5 rows first_lead..last_lead, in Big5 order (stroke order)."""
    found: list[int] = []
    for lead in range(first_lead, last_lead + 1):
        for trail in [*range(0x40, 0x7F), *range(0xA1, 0xFF)]:
            if last_code is not None and (lead << 8 | trail) > last_code:
                return found
            try:
                char = bytes([lead, trail]).decode("big5")
            except UnicodeDecodeError:
                continue
            if len(char) == 1 and is_ideograph(ord(char)):
                found.append(ord(char))
    return found


def chunks(values: list[int], size: int) -> list[list[int]]:
    count = max(1, round(len(values) / size))
    step = -(-len(values) // count)
    return [values[start:start + step] for start in range(0, len(values), step)]


def css_ranges(codes: list[int]) -> str:
    codes = sorted(set(codes))
    parts: list[str] = []
    start = previous = codes[0]
    for code in [*codes[1:], None]:
        if code is not None and code == previous + 1:
            previous = code
            continue
        parts.append(f"U+{start:X}" if start == previous else f"U+{start:X}-{previous:X}")
        if code is not None:
            start = previous = code
    return ",".join(parts)


def rename(font: TTFont) -> None:
    names = font["name"]
    for name_id in (16, 17, 18, 20, 21, 22):
        names.removeNames(nameID=name_id)
    texts = {1: FAMILY, 3: f"{POSTSCRIPT};{FAMILY} subset", 4: f"{FAMILY} Regular", 6: POSTSCRIPT}
    for record in list(names.names):
        if record.nameID in texts:
            names.setName(texts[record.nameID], record.nameID, record.platformID, record.platEncID, record.langID)


def subset_font(source: Path, codes: list[int]) -> bytes:
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    options.name_languages = ["*"]
    options.name_legacy = True
    options.hinting = False
    options.notdef_outline = True
    options.glyph_names = False
    options.recalc_timestamp = False
    options.drop_tables += ["FFTM"]
    font = TTFont(source, recalcTimestamp=False)
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=codes)
    subsetter.subset(font)
    rename(font)
    out = io.BytesIO()
    font.flavor = "woff2"
    font.save(out)
    return out.getvalue()


def license_text(font: TTFont, license_file: Path) -> str:
    notice = next((str(r) for r in font["name"].names if r.nameID == 13 and r.platformID == 1), "")
    head = notice.split("This Font Software", 1)[0].strip()
    body = license_file.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    return f"{head}\n\n{body}\n" if head else f"{body}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--font", required=True, type=Path, help="TaiwanPearl-Regular.ttf")
    parser.add_argument("--license", required=True, type=Path, help="SIL OFL 1.1 text shipped with the font")
    parser.add_argument("--out", required=True, type=Path, help="output directory, e.g. web/vendor/taiwan-pearl/2.125")
    args = parser.parse_args()

    source = TTFont(args.font, recalcTimestamp=False, lazy=True)
    version = str(source["name"].getDebugName(5) or "").strip()
    cmap = set(source.getBestCmap())
    hangul = sorted(code for code in cmap if HANGUL[0] <= code <= HANGUL[1])
    base = sorted(code for code in cmap if not is_ideograph(code) and code not in set(hangul))
    common = [code for code in big5_range(0xA4, 0xC6, 0xC67E) if code in cmap]
    secondary = [code for code in big5_range(0xC9, 0xF9) if code in cmap and code not in set(common)]
    used = set(base) | set(common) | set(secondary)
    rest = sorted(code for code in cmap if is_ideograph(code) and code not in used)

    segments: list[tuple[str, list[int]]] = [("base", base)]
    segments += [(f"hangul-{n:02d}", part) for n, part in enumerate(chunks(hangul, HANGUL_CHUNK), 1)]
    segments += [(f"common-{n:02d}", part) for n, part in enumerate(chunks(common, COMMON_CHUNK), 1)]
    segments += [(f"secondary-{n:02d}", part) for n, part in enumerate(chunks(secondary, SECONDARY_CHUNK), 1)]
    segments += [(f"rest-{n:02d}", part) for n, part in enumerate(chunks(rest, REST_CHUNK), 1)]

    if args.out.exists():
        shutil.rmtree(args.out)
    (args.out / "files").mkdir(parents=True)
    css = [f"/* Taiwan Pearl {version}, SIL OFL 1.1; subset renamed to \"{FAMILY}\" (Reserved Font Name). */"]
    report: list[dict] = []
    for name, codes in segments:
        data = subset_font(args.font, codes)
        digest = hashlib.sha256(data).hexdigest()
        file_name = f"taiwan-pearl-{name}-{digest[:10]}.woff2"
        (args.out / "files" / file_name).write_bytes(data)
        css.append(
            f"/* {name} */\n@font-face {{\n  font-family: '{FAMILY}';\n  font-style: normal;\n"
            f"  font-display: swap;\n  font-weight: 400;\n"
            f"  src: url(./files/{file_name}) format('woff2');\n  unicode-range: {css_ranges(codes)};\n}}")
        report.append({"name": name, "file": file_name, "characters": len(codes), "bytes": len(data), "sha256": digest})
        print(f"{name}: {len(codes)} characters, {len(data)} bytes", file=sys.stderr)
    (args.out / "index.css").write_text("\n\n".join(css) + "\n", encoding="utf-8", newline="\n")
    (args.out / "LICENSE").write_text(license_text(source, args.license), encoding="utf-8", newline="\n")
    (args.out / "segments.tsv").write_text(
        "".join(f"{r['name']}\t{r['file']}\t{r['characters']}\t{r['bytes']}\t{r['sha256'].upper()}\n" for r in report),
        encoding="utf-8", newline="\n")
    print(f"total: {sum(r['bytes'] for r in report)} bytes in {len(report)} segments", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
