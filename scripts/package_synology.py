"""Build a Synology DSM 7 package (.spk) for Peach on x86-64.

The package bundles a relocatable CPython (python-build-standalone), Linux x86-64 wheels taken
from the locked dependency set (uv.lock) and the Peach sources. Everything is assembled with
tarfile, so it works on Windows. No FFmpeg binaries are bundled.

  uv run --no-sync python scripts/package_synology.py --dry-run
  uv run --no-sync python scripts/package_synology.py
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tarfile
import tomllib
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKELETON = ROOT / "scripts" / "synology"
BUILD_DIR = ROOT / "build" / "synology"

PACKAGE_ID = "PeachZhTW"
PYTHON_MINOR = "3.14"
#: python-build-standalone release and asset (install_only_stripped, baseline x86-64 CPU).
PBS_RELEASE = "20261110"
PBS_ASSET = "cpython-3.14.10+20261110-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz"
PBS_SHA256 = "c2ff2e97422f5d3896a16e0317fd212ba977bbf2688d93a6f7a03d817506bd30"
PBS_SIZE = 36875876
PBS_URL = ("https://github.com/astral-sh/python-build-standalone/releases/download/"
           f"{PBS_RELEASE}/{PBS_ASSET.replace('+', '%2B')}")
#: Highest manylinux glibc tag a wheel may require; the real floor is measured from the ELF files.
MAX_WHEEL_GLIBC = (2, 28)
UV_PLATFORM = "x86_64-manylinux_2_28"
#: Platform names whose family is x86_64 in Synology pkgscripts-ng, plus the family name itself.
ARCH_VALUES = (
    "x86_64 apollolake avoton braswell broadwell broadwellnk broadwellnkv2 broadwellntbap bromolow "
    "cedarview coffeelake denverton epyc7002 geminilake geminilakenk grantley kvmx64 purley r1000 "
    "r1000nk skylaked v1000 v1000nk"
)
#: Fixed timestamp so the same inputs give the same archive.
PACKAGE_MTIME = int(os.environ.get("SOURCE_DATE_EPOCH", "1767225600"))
ICON_SIZES = (16, 24, 32, 48, 64, 72, 256)
WINDOWS_SUFFIXES = (".exe", ".dll", ".pyd", ".bat", ".cmd", ".ps1", ".lnk")
SCRIPT_NAMES = ("start-stop-status", "preinst", "postinst", "preuninst", "postuninst",
                "preupgrade", "postupgrade")
#: Parts of the CPython install the service never uses: Tcl/Tk, IDLE, pip (it ships Windows launchers),
#: tests, headers and the extra console scripts.
PRUNE_PREFIXES = (
    "python/lib/libtcl", "python/lib/tcl", "python/lib/tk", "python/lib/itcl", "python/lib/thread",
    "python/lib/tdbc", "python/include/", "python/bin/idle", "python/bin/pip", "python/bin/pydoc",
    "python/bin/python3-config", "python/bin/python3.14-config",
    f"python/lib/python{PYTHON_MINOR}/idlelib", f"python/lib/python{PYTHON_MINOR}/tkinter",
    f"python/lib/python{PYTHON_MINOR}/turtledemo", f"python/lib/python{PYTHON_MINOR}/test/",
    f"python/lib/python{PYTHON_MINOR}/ensurepip", f"python/lib/python{PYTHON_MINOR}/site-packages/pip",
    f"python/lib/python{PYTHON_MINOR}/lib-dynload/_tkinter",
)

ELF_MACHINE_X86_64 = 62
_GLIBC = re.compile(rb"GLIBC_(\d+)\.(\d+)(?:\.\d+)?\x00")
_GLIBCXX = re.compile(rb"GLIBCXX_3\.4\.(\d+)\x00")


@dataclass(frozen=True)
class Download:
    name: str
    url: str
    size: int
    sha256: str


@dataclass
class ElfReport:
    glibc: tuple[int, int] = (0, 0)
    glibcxx: int = 0
    count: int = 0
    wrong_machine: list[str] = field(default_factory=list)

    def add(self, name: str, data: bytes) -> None:
        self.count += 1
        if len(data) < 20 or data[4] != 2 or int.from_bytes(data[18:20], "little") != ELF_MACHINE_X86_64:
            self.wrong_machine.append(name)
        for match in _GLIBC.finditer(data):
            self.glibc = max(self.glibc, (int(match.group(1)), int(match.group(2))))
        for match in _GLIBCXX.finditer(data):
            self.glibcxx = max(self.glibcxx, int(match.group(1)))


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


# --------------------------------------------------------------------------- wheel selection

def _glibc_of(platform_tag: str) -> tuple[int, int] | None:
    if not platform_tag.endswith("_x86_64"):
        return None
    legacy = {"manylinux1": (2, 5), "manylinux2010": (2, 12), "manylinux2014": (2, 17)}
    head = platform_tag[: -len("_x86_64")]
    if head in legacy:
        return legacy[head]
    match = re.fullmatch(r"manylinux_(\d+)_(\d+)", head)
    return (int(match.group(1)), int(match.group(2))) if match else None


def wheel_rank(filename: str, max_glibc: tuple[int, int] = MAX_WHEEL_GLIBC) -> tuple | None:
    """Sort key of a wheel usable on CPython 3.14 / Linux x86-64 (glibc), or None when unusable."""
    parts = filename[: -len(".whl")].split("-")
    if len(parts) < 5:
        return None
    python_tags, abi_tags, platform_tags = (set(part.split(".")) for part in parts[-3:])
    minor = int(PYTHON_MINOR.split(".")[1])
    exact = f"cp3{minor}" in python_tags and f"cp3{minor}" in abi_tags
    stable = "abi3" in abi_tags and any(
        (m := re.fullmatch(r"cp3(\d+)", tag)) and int(m.group(1)) <= minor for tag in python_tags)
    pure = "none" in abi_tags and "any" in platform_tags and bool(python_tags & {"py3", "py2"})
    if pure:
        return (3, (0, 0))
    # py3-none-manylinux wheels carry a native helper without a Python ABI (for example watchdog).
    generic = "none" in abi_tags and "py3" in python_tags
    if not (exact or stable or generic):
        return None
    floors = [g for tag in platform_tags if (g := _glibc_of(tag)) is not None]
    if not floors or min(floors) > max_glibc:
        return None
    return (0 if exact else 1 if stable else 2, min(floors))


def pick_wheel(candidates: list[dict], max_glibc: tuple[int, int] = MAX_WHEEL_GLIBC) -> dict | None:
    ranked = []
    for entry in candidates:
        name = entry["url"].rsplit("/", 1)[1]
        rank = wheel_rank(urllib.parse.unquote(name), max_glibc)
        if rank is not None:
            ranked.append((rank, name, entry))
    return min(ranked, key=lambda item: (item[0], item[1]))[2] if ranked else None


def locked_wheels(lock_path: Path, wanted: dict[str, str]) -> tuple[list[Download], list[str]]:
    """Choose one wheel per wanted package from uv.lock; return downloads and unresolved names."""
    lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    packages = {normalize(item["name"]): item for item in lock["package"]}
    downloads, missing = [], []
    for name, version in sorted(wanted.items()):
        package = packages.get(name)
        if package is None or package.get("version") != version:
            missing.append(f"{name}=={version} (not in uv.lock)")
            continue
        entry = pick_wheel(package.get("wheels", []))
        if entry is None:
            missing.append(f"{name}=={version} (no compatible wheel)")
            continue
        filename = urllib.parse.unquote(entry["url"].rsplit("/", 1)[1])
        downloads.append(Download(filename, entry["url"], int(entry.get("size", 0)),
                                  entry["hash"].removeprefix("sha256:")))
    return downloads, missing


def resolve_requirements(extras: list[str], work: Path) -> dict[str, str]:
    """Ask uv which locked packages apply to Linux x86-64 (markers and extras evaluated)."""
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("uv was not found on PATH")
    command = [uv, "export", "--locked", "--no-dev", "--no-emit-project", "--format", "requirements-txt"]
    for extra in extras:
        command += ["--extra", extra]
    exported = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
    requirements = work / "requirements.txt"
    requirements.write_text(exported.stdout, encoding="utf-8")
    dry = subprocess.run(
        [uv, "pip", "install", "--dry-run", "--no-deps", "--require-hashes", "--python-platform", UV_PLATFORM,
         "--python-version", PYTHON_MINOR, "--only-binary", ":all:", "--target", str(work / "dry-target"),
         "-r", str(requirements)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
    if dry.returncode:
        raise SystemExit("uv could not resolve wheels for the target platform:\n" + dry.stderr[-2000:])
    found = {}
    for line in (dry.stdout + dry.stderr).splitlines():
        match = re.match(r"\s*\+\s+(\S+)==(\S+)\s*$", line)
        if match:
            found[normalize(match.group(1))] = match.group(2)
    return found


# --------------------------------------------------------------------------- download

def fetch(item: Download, cache: Path) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / item.name
    if target.is_file() and sha256_of(target) == item.sha256:
        return target
    partial = target.with_suffix(target.suffix + ".part")
    digest = hashlib.sha256()
    request = urllib.request.Request(item.url, headers={"User-Agent": "peach-package-synology"})
    with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as handle:
        for block in iter(lambda: response.read(1 << 20), b""):
            digest.update(block)
            handle.write(block)
    if digest.hexdigest() != item.sha256:
        partial.unlink(missing_ok=True)
        raise SystemExit(f"checksum mismatch for {item.name}")
    partial.replace(target)
    return target


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


# --------------------------------------------------------------------------- tar writing

class Packer:
    """Writes tar members with fixed owner, time and explicit modes; collects ELF facts."""

    def __init__(self, tar: tarfile.TarFile, elf: ElfReport | None = None) -> None:
        self.tar = tar
        self.elf = elf
        self.dirs: set[str] = set()
        self.names: set[str] = set()

    def _parents(self, name: str) -> None:
        parent = ""
        for part in name.split("/")[:-1]:
            parent = f"{parent}/{part}" if parent else part
            if parent not in self.dirs:
                self.dirs.add(parent)
                info = tarfile.TarInfo(parent)
                info.type, info.mode, info.mtime = tarfile.DIRTYPE, 0o755, PACKAGE_MTIME
                self.tar.addfile(info)

    def file(self, name: str, data: bytes, mode: int) -> None:
        if name in self.names:
            return
        self.names.add(name)
        self._parents(name)
        info = tarfile.TarInfo(name)
        info.size, info.mode, info.mtime = len(data), mode, PACKAGE_MTIME
        self.tar.addfile(info, io.BytesIO(data))
        if self.elf is not None and data[:4] == b"\x7fELF":
            self.elf.add(name, data)

    def link(self, name: str, target: str, *, hard: bool = False) -> None:
        if name in self.names:
            return
        self.names.add(name)
        self._parents(name)
        info = tarfile.TarInfo(name)
        info.type = tarfile.LNKTYPE if hard else tarfile.SYMTYPE
        info.linkname, info.mode, info.mtime = target, 0o777, PACKAGE_MTIME
        self.tar.addfile(info)

    def copy_member(self, member: tarfile.TarInfo, source: tarfile.TarFile, name: str) -> None:
        if member.isdir():
            self._parents(name + "/x")
            return
        if member.issym() or member.islnk():
            self.link(name, member.linkname, hard=member.islnk())
        elif member.isfile():
            handle = source.extractfile(member)
            mode = member.mode & 0o777 | 0o444
            self.file(name, handle.read() if handle else b"", mode | 0o111 if wheel_mode(name) == 0o755 else mode)


def safe_name(name: str) -> str:
    cleaned = name.replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    if not cleaned or cleaned.startswith("/") or ".." in cleaned.split("/"):
        raise ValueError(f"unsafe archive path: {name!r}")
    return cleaned


def add_python(packer: Packer, archive: Path) -> None:
    with tarfile.open(archive, "r:gz") as source:
        for member in source:
            name = safe_name(member.name)
            if not name.startswith("python/") and name != "python":
                raise ValueError(f"unexpected path in Python archive: {name}")
            if name.startswith(PRUNE_PREFIXES) or name.lower().endswith(WINDOWS_SUFFIXES):
                continue
            packer.copy_member(member, source, name)


def wheel_mode(name: str) -> int:
    return 0o755 if re.search(r"\.so(\.|$)", name.rsplit("/", 1)[-1]) else 0o644


def add_wheel(packer: Packer, wheel: Path, site: str) -> None:
    with zipfile.ZipFile(wheel) as archive:
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            name = safe_name(entry.filename)
            if "__pycache__/" in name or name.endswith(".pyc"):
                continue
            head, _, rest = name.partition("/")
            if head.endswith(".data"):
                scheme, _, rest = rest.partition("/")
                if scheme not in {"purelib", "platlib"}:
                    continue
                name = rest
            packer.file(f"{site}/{name}", archive.read(entry), wheel_mode(name))


def add_peach(packer: Packer, root: Path, site: str) -> None:
    spec = importlib.util.spec_from_file_location("peach_bundle_resources", root / "src/peach/bundle_resources.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = root / "src" / "peach"
    for path in sorted(source.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            packer.file(f"{site}/peach/{path.relative_to(source).as_posix()}", path.read_bytes(), 0o644)
    resources = f"{site}/peach/_resources"
    for src, target in module.data_files(root):
        if src.is_dir():
            for path in sorted(src.rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts:
                    packer.file(f"{resources}/{target}/{path.relative_to(src).as_posix()}", path.read_bytes(), 0o644)
        else:
            packer.file(f"{resources}/{target}/{src.name}", src.read_bytes(), 0o644)


def make_icons(ico: Path) -> dict[int, bytes]:
    from PIL import Image
    with Image.open(ico) as image:
        image.size = max(image.info.get("sizes", {image.size}))
        base = image.convert("RGBA")
    icons = {}
    for size in ICON_SIZES:
        buffer = io.BytesIO()
        base.resize((size, size), Image.LANCZOS).save(buffer, "PNG")
        icons[size] = buffer.getvalue()
    return icons


def build_package_tgz(output: Path, *, python_archive: Path, wheels: list[Path], root: Path,
                      skeleton: Path, icons: dict[int, bytes]) -> ElfReport:
    """Write package.tgz (the program files DSM extracts into the package target)."""
    elf = ElfReport()
    site = f"python/lib/python{PYTHON_MINOR}/site-packages"
    with output.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=PACKAGE_MTIME, compresslevel=9) as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT) as tar:
            packer = Packer(tar, elf)
            add_python(packer, python_archive)
            for wheel in wheels:
                add_wheel(packer, wheel, site)
            add_peach(packer, root, site)
            packer.file("bin/provision.py", (skeleton / "provision.py").read_bytes(), 0o755)
            packer.file("ui/config", normalized_text(skeleton / "ui" / "config"), 0o644)
            for size, data in sorted(icons.items()):
                packer.file(f"ui/images/icon_{size}.png", data, 0o644)
    return elf


def normalized_text(path: Path) -> bytes:
    data = path.read_bytes()
    if b"\r" in data:
        raise ValueError(f"CRLF line endings in {path}")
    return data


# --------------------------------------------------------------------------- SPK assembly

def render_info(template: Path, *, version: str, revision: int, checksum: str, extract_kb: int) -> bytes:
    text = template.read_text(encoding="utf-8")
    if "\r" in text:
        raise ValueError("INFO.template must use LF line endings")
    values = {"@VERSION@": f"{version}-{revision:04d}", "@ARCH@": ARCH_VALUES,
              "@CHECKSUM@": checksum, "@EXTRACTSIZE@": str(extract_kb)}
    for key, value in values.items():
        text = text.replace(key, value)
    return text.encode("utf-8")


def md5_of(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def assemble_spk(output: Path, *, package_tgz: Path, skeleton: Path, version: str, revision: int,
                 min_glibc: tuple[int, int], icons: dict[int, bytes], extract_kb: int, license_file: Path) -> None:
    info = render_info(skeleton / "INFO.template", version=version, revision=revision,
                       checksum=md5_of(package_tgz), extract_kb=extract_kb)
    with tarfile.open(output, "w", format=tarfile.GNU_FORMAT) as tar:
        packer = Packer(tar)

        def put(name: str, data: bytes, mode: int) -> None:
            packer.file(name, data, mode)

        put("INFO", info, 0o644)
        put("package.tgz", package_tgz.read_bytes(), 0o644)
        for name in SCRIPT_NAMES:
            text = normalized_text(skeleton / "scripts" / name).decode("utf-8")
            text = text.replace("@MIN_GLIBC@", f"{min_glibc[0]}.{min_glibc[1]}")
            put(f"scripts/{name}", text.encode("utf-8"), 0o755)
        put("conf/privilege", normalized_text(skeleton / "conf" / "privilege"), 0o644)
        for path in sorted((skeleton / "WIZARD_UIFILES").iterdir()):
            put(f"WIZARD_UIFILES/{path.name}", normalized_text(path), 0o644)
        put("PACKAGE_ICON.PNG", icons[72], 0o644)
        put("PACKAGE_ICON_256.PNG", icons[256], 0o644)
        put("LICENSE", license_file.read_bytes(), 0o644)


# --------------------------------------------------------------------------- static verification

def verify_spk(spk: Path, *, personal: tuple[str, ...] = ()) -> tuple[list[str], dict]:
    """Inspect a finished .spk; returns problems and a few facts."""
    problems: list[str] = []
    facts: dict = {}
    required = {"INFO", "package.tgz", "LICENSE", "PACKAGE_ICON.PNG", "PACKAGE_ICON_256.PNG", "conf/privilege",
                *(f"scripts/{name}" for name in SCRIPT_NAMES)}
    with tarfile.open(spk, "r") as outer:
        members = {m.name: m for m in outer.getmembers()}
        for name in sorted(required - set(members)):
            problems.append(f"missing {name}")
        if not any(n.startswith("WIZARD_UIFILES/install_uifile") for n in members):
            problems.append("missing wizard files")
        for name, member in members.items():
            if member.uid or member.gid or member.uname or member.gname:
                problems.append(f"owner is not 0:0 for {name}")
            if name.startswith("scripts/"):
                data = outer.extractfile(member).read()
                if not data.startswith(b"#!/bin/sh\n"):
                    problems.append(f"bad shebang in {name}")
                if b"\r" in data:
                    problems.append(f"CRLF in {name}")
                if member.mode & 0o777 != 0o755:
                    problems.append(f"{name} is not mode 0755")
                if b"@MIN_GLIBC@" in data:
                    problems.append(f"unrendered placeholder in {name}")
        info = outer.extractfile(members["INFO"]).read().decode("utf-8") if "INFO" in members else ""
        fields = dict(re.findall(r'^(\w+)="(.*)"$', info, re.M))
        facts["info"] = fields
        for key in ("package", "version", "arch", "os_min_ver", "maintainer", "checksum"):
            if not fields.get(key):
                problems.append(f"INFO lacks {key}")
        if fields.get("os_min_ver") != "7.2-64561":
            problems.append("os_min_ver is not 7.2-64561")
        if "arm" in fields.get("arch", "") or "aarch" in fields.get("arch", ""):
            problems.append("arch includes an ARM value")
        if "package.tgz" in members:
            payload = outer.extractfile(members["package.tgz"])
            data = payload.read()
            if fields.get("checksum") and hashlib.md5(data, usedforsecurity=False).hexdigest() != fields["checksum"]:
                problems.append("INFO checksum does not match package.tgz")
            problems += _verify_payload(data, facts, personal)
        for name in members:
            if name.startswith("conf/") and name.endswith("privilege"):
                privilege = json.loads(outer.extractfile(members[name]).read())
                if privilege.get("defaults", {}).get("run-as") != "package":
                    problems.append("privilege is not run-as package")
        for name in members:
            if name.startswith("WIZARD_UIFILES/"):
                try:
                    json.loads(outer.extractfile(members[name]).read())
                except ValueError:
                    problems.append(f"{name} is not valid JSON")
    return problems, facts


def _verify_payload(data: bytes, facts: dict, personal: tuple[str, ...]) -> list[str]:
    problems: list[str] = []
    elf = ElfReport()
    total = 0
    tops: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as inner:
        for member in inner:
            name = member.name
            if member.uid or member.gid:
                problems.append(f"owner is not 0:0 for {name}")
            if name.startswith("/") or ".." in name.split("/"):
                problems.append(f"unsafe path {name}")
            if name.lower().endswith(WINDOWS_SUFFIXES):
                problems.append(f"Windows-only file {name}")
            if name.startswith("python/lib/python") and "/site-packages/" in name:
                tops.add(name.split("/site-packages/", 1)[1].split("/", 1)[0])
            if not member.isfile():
                if member.issym():
                    target = posixpath.normpath(posixpath.join(posixpath.dirname(name), member.linkname))
                    if member.linkname.startswith("/") or target.startswith(".."):
                        problems.append(f"symlink escapes the package: {name}")
                continue
            total += member.size
            content = inner.extractfile(member).read()
            if content[:4] == b"\x7fELF":
                elf.add(name, content)
                if not member.mode & 0o100 and ".so" not in name.rsplit("/", 1)[-1]:
                    problems.append(f"ELF file is not executable: {name}")
            elif any(token.encode() in content for token in personal if token):
                problems.append(f"personal path found in {name}")
            if name.startswith("bin/") and not member.mode & 0o100:
                problems.append(f"{name} is not executable")
    problems += [f"ELF is not x86-64: {n}" for n in elf.wrong_machine]
    facts.update(elf_files=elf.count, glibc=elf.glibc, glibcxx=elf.glibcxx, size=total,
                 top_packages=sorted(t for t in tops if not t.endswith((".dist-info", ".libs")) and t != "__pycache__"))
    return problems


# --------------------------------------------------------------------------- entry point

def print_listing(items: list[Download]) -> None:
    total = sum(item.size for item in items)
    print(f"Files to download ({len(items)}, {total / 1048576:.1f} MiB):")
    for item in items:
        print(f"  {item.name}  {item.size} bytes  sha256={item.sha256[:12]}...  {item.url}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=BUILD_DIR)
    parser.add_argument("--revision", type=int, default=1, help="package build number (default 1)")
    parser.add_argument("--without-vision", action="store_true", help="leave out OpenCV and NumPy (face features)")
    parser.add_argument("--dry-run", action="store_true", help="resolve and list downloads, then stop")
    args = parser.parse_args(argv)

    sys.path.insert(0, str(ROOT / "src"))
    from peach import __version__
    out = args.output_dir
    cache = out / "cache"
    work = out / "work"
    work.mkdir(parents=True, exist_ok=True)

    wanted = resolve_requirements([] if args.without_vision else ["vision"], work)
    wheels, missing = locked_wheels(ROOT / "uv.lock", wanted)
    if missing:
        print("No usable wheel for:", file=sys.stderr)
        for line in missing:
            print(f"  {line}", file=sys.stderr)
        return 2
    python = Download(PBS_ASSET, PBS_URL, PBS_SIZE, PBS_SHA256)
    print_listing([python, *wheels])
    if args.dry_run:
        return 0

    python_path = fetch(python, cache)
    wheel_paths = [fetch(item, cache / "wheels") for item in wheels]
    icons = make_icons(ROOT / "resources" / "peach.ico")
    package_tgz = work / "package.tgz"
    elf = build_package_tgz(package_tgz, python_archive=python_path, wheels=wheel_paths, root=ROOT,
                            skeleton=SKELETON, icons=icons)
    print(f"ELF files: {elf.count}; highest glibc symbol: {elf.glibc[0]}.{elf.glibc[1]}; "
          f"highest GLIBCXX: 3.4.{elf.glibcxx}")
    if elf.wrong_machine:
        print("Non x86-64 ELF files:", *elf.wrong_machine, sep="\n  ", file=sys.stderr)
        return 3
    min_glibc = max(elf.glibc, (2, 17))
    with tarfile.open(package_tgz, "r:gz") as inner:
        extract_kb = sum(m.size for m in inner if m.isfile()) // 1024
    spk = out / f"Peach-{__version__}-x86_64.spk"
    assemble_spk(spk, package_tgz=package_tgz, skeleton=SKELETON, version=__version__, revision=args.revision,
                 min_glibc=min_glibc, icons=icons, extract_kb=extract_kb, license_file=ROOT / "LICENSE")
    problems, facts = verify_spk(spk, personal=(str(Path.home()), Path.home().name))
    print(f"Top-level packages: {', '.join(facts['top_packages'])}")
    print(f"Unpacked size: {facts['size'] / 1048576:.1f} MiB")
    if problems:
        print("Verification problems:", file=sys.stderr)
        for line in problems:
            print(f"  {line}", file=sys.stderr)
        return 4
    print(f"SPK: {spk}")
    print(f"Size: {spk.stat().st_size} bytes  SHA-256: {sha256_of(spk)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
