"""Synology SPK 封装脚本的打包逻辑：用很小的假输入树验证，不下载任何东西。"""
from __future__ import annotations

import gzip
import importlib.util
import io
import json
import re
import shutil
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    spec = importlib.util.spec_from_file_location("package_synology_builder", ROOT / "scripts" / "package_synology.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fake_elf(glibc: str = "GLIBC_2.17", machine: int = 62) -> bytes:
    header = bytearray(64)
    header[:4] = b"\x7fELF"
    header[4] = 2
    header[18:20] = machine.to_bytes(2, "little")
    return bytes(header) + b"\x00" + glibc.encode() + b"\x00GLIBCXX_3.4.19\x00"


def tar_bytes(entries) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for name, kind, payload, mode in entries:
            info = tarfile.TarInfo(name)
            info.mode = mode
            if kind == "dir":
                info.type = tarfile.DIRTYPE
                tar.addfile(info)
            elif kind == "link":
                info.type = tarfile.SYMTYPE
                info.linkname = payload
                tar.addfile(info)
            else:
                info.size = len(payload)
                tar.addfile(info, io.BytesIO(payload))
    return buffer.getvalue()


class WheelSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_builder()

    def rank(self, name):
        return self.builder.wheel_rank(name)

    def test_linux_x86_64_wheels_are_accepted_and_foreign_ones_are_not(self):
        self.assertIsNotNone(self.rank("a-1-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.whl"))
        self.assertIsNotNone(self.rank("a-1-cp310-abi3-manylinux_2_17_x86_64.whl"))
        self.assertIsNotNone(self.rank("a-1-py3-none-manylinux2014_x86_64.whl"))
        self.assertIsNotNone(self.rank("a-1-py3-none-any.whl"))
        for name in ("a-1-cp314-cp314-manylinux2014_aarch64.whl", "a-1-cp314-cp314-musllinux_1_2_x86_64.whl",
                     "a-1-cp314-cp314-win_amd64.whl", "a-1-cp314-cp314-macosx_11_0_arm64.whl",
                     "a-1-cp314-cp314t-manylinux_2_28_x86_64.whl", "a-1-cp315-cp315-manylinux_2_28_x86_64.whl",
                     "a-1-cp313-cp313-manylinux_2_28_x86_64.whl", "a-1-cp314-cp314-manylinux_2_34_x86_64.whl"):
            self.assertIsNone(self.rank(name), name)

    def test_the_most_specific_and_most_compatible_wheel_wins(self):
        entries = [{"url": f"https://example.test/{name}"} for name in (
            "a-1-py3-none-any.whl", "a-1-cp310-abi3-manylinux_2_17_x86_64.whl",
            "a-1-cp314-cp314-manylinux_2_28_x86_64.whl", "a-1-cp314-cp314-manylinux_2_17_x86_64.whl")]
        chosen = self.builder.pick_wheel(entries)
        self.assertTrue(chosen["url"].endswith("a-1-cp314-cp314-manylinux_2_17_x86_64.whl"))

    def test_locked_wheels_reports_missing_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "uv.lock"
            lock.write_text(
                '[[package]]\nname = "demo"\nversion = "1.0"\n'
                'wheels = [{ url = "https://example.test/demo-1.0-py3-none-any.whl", hash = "sha256:' + "a" * 64 + '", size = 7 }]\n'
                '[[package]]\nname = "native"\nversion = "2.0"\n'
                'wheels = [{ url = "https://example.test/native-2.0-cp314-cp314-win_amd64.whl", hash = "sha256:' + "b" * 64 + '", size = 9 }]\n',
                encoding="utf-8")
            downloads, missing = self.builder.locked_wheels(lock, {"demo": "1.0", "native": "2.0", "absent": "3"})
        self.assertEqual([item.name for item in downloads], ["demo-1.0-py3-none-any.whl"])
        self.assertEqual(downloads[0].sha256, "a" * 64)
        self.assertEqual(len(missing), 2)


class PackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_builder()

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name)
        self.root = self.fake_project(self.work / "project")
        self.python = self.work / "python.tar.gz"
        self.python.write_bytes(gzip.compress(tar_bytes([
            ("python", "dir", b"", 0o755),
            ("python/bin", "dir", b"", 0o755),
            ("python/bin/python3.14", "file", fake_elf(), 0o755),
            ("python/bin/python3", "link", "python3.14", 0o777),
            ("python/bin/pip3", "file", b"#!/bin/sh\n", 0o755),
            ("python/lib/python3.14/site-packages", "dir", b"", 0o755),
            ("python/lib/python3.14/site-packages/pip/_vendor/t64.exe", "file", b"MZ", 0o644),
            ("python/lib/python3.14/venv/scripts/Activate.ps1", "file", b"x", 0o644),
        ])))
        self.wheel = self.work / "demo-1.0-cp314-cp314-manylinux_2_17_x86_64.whl"
        with zipfile.ZipFile(self.wheel, "w") as archive:
            archive.writestr("demo/__init__.py", "VALUE = 1\n")
            archive.writestr("demo/native.cpython-314-x86_64-linux-gnu.so", fake_elf("GLIBC_2.27"))
            archive.writestr("demo/__pycache__/x.pyc", b"junk")
            archive.writestr("demo-1.0.data/scripts/demo", "#!python\n")
            archive.writestr("demo-1.0.data/purelib/extra.py", "X = 1\n")
        self.icons = {size: b"\x89PNG" + bytes([size % 256]) for size in self.builder.ICON_SIZES}
        self.tgz = self.work / "package.tgz"
        self.elf = self.builder.build_package_tgz(
            self.tgz, python_archive=self.python, wheels=[self.wheel], root=self.root,
            skeleton=self.builder.SKELETON, icons=self.icons)
        self.spk = self.work / "Peach-test.spk"
        self.builder.assemble_spk(
            self.spk, package_tgz=self.tgz, skeleton=self.builder.SKELETON, version="9.9.9", revision=3,
            min_glibc=self.elf.glibc, icons=self.icons, extract_kb=1, license_file=self.root / "LICENSE")

    def fake_project(self, root: Path) -> Path:
        (root / "src" / "peach").mkdir(parents=True)
        shutil.copy(ROOT / "src" / "peach" / "bundle_resources.py", root / "src" / "peach" / "bundle_resources.py")
        (root / "src" / "peach" / "__init__.py").write_text('__version__ = "9.9.9"\n', encoding="utf-8")
        (root / "src" / "peach" / "__pycache__").mkdir()
        (root / "src" / "peach" / "__pycache__" / "x.pyc").write_bytes(b"junk")
        for directory in ("web", "migrations", "resources/seed", "tools/amane-bridge"):
            (root / directory).mkdir(parents=True)
        (root / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
        (root / "migrations" / "001.sql").write_text("select 1;", encoding="utf-8")
        for pack in ("entities.json", "metadata.json"):
            (root / "resources" / "seed" / pack).write_text("{}", encoding="utf-8")
        for name in ("bridge.py", "pyproject.toml", "uv.lock"):
            (root / "tools" / "amane-bridge" / name).write_text("x", encoding="utf-8")
        (root / "LICENSE").write_text("license text", encoding="utf-8")
        return root

    def payload(self):
        with tarfile.open(self.tgz, "r:gz") as tar:
            return {m.name: m for m in tar.getmembers()}

    def test_payload_layout_modes_and_owners(self):
        members = self.payload()
        self.assertEqual(members["python/bin/python3"].issym(), True)
        self.assertEqual(members["python/bin/python3"].linkname, "python3.14")
        self.assertEqual(members["python/bin/python3.14"].mode, 0o755)
        site = "python/lib/python3.14/site-packages"
        self.assertEqual(members[f"{site}/demo/native.cpython-314-x86_64-linux-gnu.so"].mode, 0o755)
        self.assertEqual(members[f"{site}/demo/__init__.py"].mode, 0o644)
        self.assertIn(f"{site}/extra.py", members)
        self.assertIn(f"{site}/peach/__init__.py", members)
        self.assertIn(f"{site}/peach/_resources/web/index.html", members)
        self.assertIn(f"{site}/peach/_resources/migrations/001.sql", members)
        self.assertIn(f"{site}/peach/_resources/resources/seed/entities.json", members)
        self.assertIn(f"{site}/peach/_resources/resources/seed/metadata.json", members)
        self.assertIn(f"{site}/peach/_resources/tools/amane-bridge/bridge.py", members)
        self.assertEqual(members["bin/provision.py"].mode, 0o755)
        self.assertIn("ui/config", members)
        for size in self.builder.ICON_SIZES:
            self.assertIn(f"ui/images/icon_{size}.png", members)
        for name, member in members.items():
            self.assertEqual((member.uid, member.gid, member.uname, member.gname), (0, 0, "", ""), name)

    def test_junk_and_windows_files_are_left_out(self):
        names = set(self.payload())
        self.assertFalse([n for n in names if "__pycache__" in n or n.endswith(".pyc")])
        self.assertFalse([n for n in names if n.lower().endswith(self.builder.WINDOWS_SUFFIXES)])
        self.assertNotIn("python/bin/pip3", names)
        self.assertFalse([n for n in names if n.endswith("/demo-1.0.data/scripts/demo") or "/scripts/demo" in n])

    def test_elf_facts_come_from_the_files(self):
        self.assertEqual(self.elf.glibc, (2, 27))
        self.assertEqual(self.elf.glibcxx, 19)
        self.assertEqual(self.elf.wrong_machine, [])
        report = self.builder.ElfReport()
        report.add("arm.so", fake_elf(machine=183))
        self.assertEqual(report.wrong_machine, ["arm.so"])

    def test_spk_structure_scripts_and_info(self):
        problems, facts = self.builder.verify_spk(self.spk)
        self.assertEqual(problems, [])
        info = facts["info"]
        self.assertEqual(info["version"], "9.9.9-0003")
        self.assertEqual(info["package"], "PeachZhTW")
        self.assertEqual(info["os_min_ver"], "7.2-64561")
        self.assertIn("x86_64", info["arch"].split())
        self.assertFalse({"armv7", "armv8", "aarch64", "alpine", "rtd1296"} & set(info["arch"].split()))
        with tarfile.open(self.spk) as tar:
            names = tar.getnames()
            for name in ("INFO", "package.tgz", "LICENSE", "PACKAGE_ICON.PNG", "PACKAGE_ICON_256.PNG", "conf/privilege",
                         "WIZARD_UIFILES/install_uifile", "WIZARD_UIFILES/install_uifile_cht",
                         "WIZARD_UIFILES/install_uifile_chs", *(f"scripts/{n}" for n in self.builder.SCRIPT_NAMES)):
                self.assertIn(name, names)
            preinst = tar.extractfile("scripts/preinst").read().decode()
            self.assertIn('MIN_GLIBC="2.27"', preinst)
            for name in self.builder.SCRIPT_NAMES:
                member = tar.getmember(f"scripts/{name}")
                data = tar.extractfile(member).read()
                self.assertEqual(member.mode, 0o755, name)
                self.assertTrue(data.startswith(b"#!/bin/sh\n"), name)
                self.assertNotIn(b"\r", data, name)

    def test_verification_flags_a_broken_package(self):
        broken = self.work / "broken.spk"
        with tarfile.open(self.spk) as source, tarfile.open(broken, "w") as target:
            for member in source.getmembers():
                if member.name == "scripts/postinst":
                    continue
                data = source.extractfile(member) if member.isfile() else None
                target.addfile(member, data)
        problems, _facts = self.builder.verify_spk(broken)
        self.assertIn("missing scripts/postinst", problems)

    def test_verification_flags_a_missing_seed_pack(self):
        names = set(self.payload())
        self.assertEqual(self.builder._verify_seed_packs(names), [])
        names.discard("python/lib/python3.14/site-packages/peach/_resources/resources/seed/metadata.json")
        self.assertEqual(self.builder._verify_seed_packs(names),
                         ["missing seed pack resources/seed/metadata.json"])

    def test_crlf_skeleton_files_are_rejected(self):
        crlf = self.work / "crlf"
        crlf.write_bytes(b"#!/bin/sh\r\nexit 0\r\n")
        with self.assertRaises(ValueError):
            self.builder.normalized_text(crlf)

    def test_archive_paths_cannot_escape(self):
        for name in ("../evil", "/abs/path", "a/../../b"):
            with self.assertRaises(ValueError):
                self.builder.safe_name(name)


class SkeletonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skeleton = ROOT / "scripts" / "synology"
        cls.builder = load_builder()

    def test_wizard_files_are_valid_json_with_the_same_keys(self):
        keys = {}
        for name in ("install_uifile", "install_uifile_cht", "install_uifile_chs"):
            # `normalized_text` 遇到 CRLF 抛 `ValueError`，与打包时同一道门。
            steps = json.loads(self.builder.normalized_text(self.skeleton / "WIZARD_UIFILES" / name))
            keys[name] = [sub["key"] for step in steps for item in step["items"] for sub in item.get("subitems", [])]
        self.assertEqual(keys["install_uifile"], ["wizard_media_path", "wizard_port", "wizard_access_password",
                                                   "wizard_ffmpeg_dir"])
        self.assertEqual(keys["install_uifile_cht"], keys["install_uifile"])
        self.assertEqual(keys["install_uifile_chs"], keys["install_uifile"])

    def test_port_pattern_accepts_exactly_the_unprivileged_range(self):
        steps = json.loads((self.skeleton / "WIZARD_UIFILES" / "install_uifile").read_text(encoding="utf-8"))
        pattern = next(sub["validator"]["regex"]["expr"] for step in steps for item in step["items"]
                       for sub in item.get("subitems", []) if sub["key"] == "wizard_port")
        compiled = re.compile(pattern.strip("/"))
        for port in range(0, 70000):
            self.assertEqual(bool(compiled.fullmatch(str(port))), 1024 <= port <= 65535, port)

    def test_privilege_runs_as_the_package_user(self):
        privilege = json.loads((self.skeleton / "conf" / "privilege").read_text(encoding="utf-8"))
        self.assertEqual(privilege["defaults"]["run-as"], "package")
        self.assertEqual(privilege["username"], "PeachZhTW")

    def test_scripts_use_lf_posix_shell_and_no_personal_paths(self):
        for path in sorted((self.skeleton / "scripts").iterdir()):
            self.assertTrue(self.builder.normalized_text(path).startswith(b"#!/bin/sh\n"), path.name)
        leaks = [f"{path.name}: {token!r}" for path in self.skeleton.rglob("*") if path.is_file()
                 for token in (b"C:\\", b"/Users/", b"/home/") if token in path.read_bytes()]
        self.assertEqual(leaks, [])

    def test_info_template_has_the_required_fields(self):
        text = self.builder.normalized_text(self.skeleton / "INFO.template").decode("utf-8")
        fields = dict(re.findall(r'(?m)^(\w+)="(.*)"$', text))
        missing = [field for field in ("package", "version", "arch", "os_min_ver", "maintainer", "displayname_cht",
                                       "description_cht", "dsmuidir", "dsmappname", "checksum") if field not in fields]
        self.assertEqual(missing, [])
        self.assertEqual(fields["os_min_ver"], "7.2-64561")

    def test_ui_config_is_valid_json(self):
        config = json.loads((self.skeleton / "ui" / "config").read_text(encoding="utf-8"))
        self.assertEqual(config[".url"]["SYNO.SDS.PeachZhTW.Application"]["port"], "8900")


if __name__ == "__main__":
    unittest.main()
