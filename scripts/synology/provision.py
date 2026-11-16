"""First-install provisioning for the Synology package.

Runs once from postinst with the bundled interpreter. It writes the Peach settings file for a
fresh data root (media directory, access password) through the same onboarding code the web
setup uses. An existing settings file is never touched, so upgrades and reinstalls keep their data.
Environment: PEACH_DATA_ROOT, PEACH_SYNOLOGY_MEDIA, PEACH_SYNOLOGY_PORT, PEACH_SYNOLOGY_PASSWORD.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from peach import access, onboarding


def main() -> int:
    data_root = Path(os.environ["PEACH_DATA_ROOT"])
    media = os.environ.get("PEACH_SYNOLOGY_MEDIA", "").strip()
    password = os.environ.pop("PEACH_SYNOLOGY_PASSWORD", "")
    try:
        port = int(os.environ["PEACH_SYNOLOGY_PORT"])
    except (KeyError, ValueError):
        print("provision: invalid port", file=sys.stderr)
        return 2
    if not 1024 <= port <= 65535 or not media.startswith("/") or ".." in media.split("/"):
        print("provision: invalid media path or port", file=sys.stderr)
        return 2
    try:
        access.validate_password(password, password)
    except ValueError as error:
        print(f"provision: password rejected: {error}", file=sys.stderr)
        return 2
    config, broken = onboarding.resolve_config(data_root)
    if broken is not None:
        print(f"provision: existing settings file is unreadable: {broken}", file=sys.stderr)
        return 3
    if config.path.exists():
        print(f"provision: settings already exist at {config.path}, left unchanged")
        return 0
    answers = onboarding.Answers(
        data_root=data_root, media_dirs=(Path(media),), host="0.0.0.0", port=port,
        mdns_name=config.server.mdns_name, media_sources=None)
    applied = onboarding.apply(config, answers, windows=False, access_password=password)
    print(f"provision: wrote {applied.settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
