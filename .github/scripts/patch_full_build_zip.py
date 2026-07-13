#!/usr/bin/env python3
"""Patch the downloaded full build zip before it is embedded/republished.

The first Android release uses a historical FENtastic build zip as the seed.
Some files inside that zip are not in this repository, so fixes that affect
APK startup must be applied to the downloaded zip during the APK workflow.
"""

from __future__ import annotations

import argparse
import os
import re
import zipfile
from pathlib import Path


TEXT_SUFFIXES = (
    ".xml",
    ".py",
    ".txt",
    ".json",
    ".properties",
)

OVERLAY_DIRS = (
    (
        Path("addons/service.subtitles.kodipovilai"),
        "addons/service.subtitles.kodipovilai/",
    ),
    (
        Path("wizard/source/plugin.program.kodipovilwizard"),
        "addons/plugin.program.kodipovilwizard/",
    ),
)

# Files produced by the packaging/release pipeline must be preserved from the
# seed zip. The source tree version of pool.py intentionally contains only the
# __POOL_SECRET__ placeholder; build-edition zips may already contain the
# injected value from tools/build_ai_subtitles_packages.py.
PRESERVE_FROM_SEED = {
    "addons/service.subtitles.kodipovilai/resources/lib/pool.py",
}


def patch_text(name: str, data: bytes, apk_version: str) -> tuple[bytes, bool]:
    if not name.lower().endswith(TEXT_SUFFIXES):
        return data, False
    text = data.decode("utf-8", "replace")
    original = text

    if name == "addons/plugin.program.kodipovilwizard/uservar.py":
        text = re.sub(
            r"^APK_RELEASE_VERSION = .*$",
            "APK_RELEASE_VERSION = {0!r}".format(apk_version),
            text,
            flags=re.M,
        )

    # Historical skin files in the seed build zip contain a few visibility
    # conditions missing the closing ')' in Art(...). Kodi logs these as
    # "unmatched parentheses in string.isempty(...)" on startup.
    text = text.replace(
        "!String.IsEmpty(Player.Art(clearlogo)</visible>",
        "!String.IsEmpty(Player.Art(clearlogo))</visible>",
    )
    text = text.replace(
        "String.IsEmpty(Player.Art(clearlogo)</visible>",
        "String.IsEmpty(Player.Art(clearlogo))</visible>",
    )
    text = text.replace(
        "!String.IsEmpty(ListItem.Art(clearlogo)\">",
        "!String.IsEmpty(ListItem.Art(clearlogo))\">",
    )
    text = text.replace(
        "String.IsEmpty(ListItem.Art(clearlogo)\">",
        "String.IsEmpty(ListItem.Art(clearlogo))\">",
    )

    if text == original:
        return data, False
    return text.encode("utf-8"), True


def should_skip_overlay(path: Path) -> bool:
    parts = set(path.parts)
    return (
        "__pycache__" in parts
        or path.name.endswith((".pyc", ".pyo"))
        or path.name == ".DS_Store"
    )


def overlay_files(repo_root: Path) -> dict[str, bytes]:
    overlays: dict[str, bytes] = {}
    for source_rel, zip_prefix in OVERLAY_DIRS:
        source_dir = repo_root / source_rel
        if not source_dir.is_dir():
            raise SystemExit("overlay source missing: {0}".format(source_dir))
        for path in sorted(source_dir.rglob("*")):
            if path.is_dir() or should_skip_overlay(path):
                continue
            rel = path.relative_to(source_dir).as_posix()
            name = zip_prefix + rel
            if name in PRESERVE_FROM_SEED:
                continue
            overlays[name] = path.read_bytes()
    return overlays


def patch_zip(zip_path: Path, apk_version: str, repo_root: Path) -> None:
    tmp_path = zip_path.with_suffix(".patched.zip")
    patched_names: list[str] = []
    overlays = overlay_files(repo_root)
    overlay_prefixes = tuple(prefix for _source, prefix in OVERLAY_DIRS)
    written_names: set[str] = set()

    with zipfile.ZipFile(zip_path, "r") as src, zipfile.ZipFile(
        tmp_path, "w", zipfile.ZIP_DEFLATED
    ) as dst:
        for info in src.infolist():
            # Replace these addons from the current repository instead of
            # carrying the historical copies from the seed zip, except for
            # pipeline-generated files that must preserve packaged secrets.
            if (info.filename.startswith(overlay_prefixes)
                    and info.filename not in PRESERVE_FROM_SEED):
                continue
            data = src.read(info.filename)
            data, patched = patch_text(info.filename, data, apk_version)
            if patched:
                patched_names.append(info.filename)
            dst.writestr(info, data)
            written_names.add(info.filename)

        for name, data in overlays.items():
            data, patched = patch_text(name, data, apk_version)
            dst.writestr(name, data)
            written_names.add(name)
            patched_names.append(name + (" (overlay+patch)" if patched else " (overlay)"))

    required = {
        "addons/plugin.program.kodipovilwizard/uservar.py",
        "addons/service.subtitles.kodipovilai/service.py",
        "addons/service.subtitles.kodipovilai/resources/settings.xml",
    }
    missing = sorted(required - written_names)
    if missing:
        tmp_path.unlink(missing_ok=True)
        raise SystemExit("patched build zip is missing required files: " + ", ".join(missing))

    tmp_path.replace(zip_path)
    print("Patched build zip files:")
    for name in patched_names:
        print("  " + name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("apk_version")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(os.environ.get("GITHUB_WORKSPACE", ".")),
        help="Repository root whose current service/wizard addons should overlay the seed zip.",
    )
    args = parser.parse_args()
    patch_zip(args.zip_path, args.apk_version, args.repo_root)


if __name__ == "__main__":
    main()
