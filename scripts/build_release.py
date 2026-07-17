#!/usr/bin/env python3
"""Build the GitHub manual-install archive."""

from __future__ import annotations

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "custom_components" / "sharp_cocoro_air"
DIST = ROOT / "dist"
ARCHIVE = DIST / "sharp_cocoro_air.zip"


def main() -> None:
    if not (COMPONENT / "manifest.json").is_file():
        raise SystemExit("Integration manifest is missing")

    DIST.mkdir(exist_ok=True)
    if ARCHIVE.exists():
        ARCHIVE.unlink()

    with ZipFile(ARCHIVE, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sorted(COMPONENT.rglob("*")):
            if not source.is_file() or "__pycache__" in source.parts:
                continue
            relative = source.relative_to(ROOT)
            archive.write(source, relative.as_posix())

    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    print(f"{ARCHIVE.relative_to(ROOT)} sha256={digest}")


if __name__ == "__main__":
    main()
