from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BUNDLE_PATH = ROOT / "streamlit_cloud_bundle.zip"
MANIFEST_PATH = ROOT / "streamlit_cloud_bundle.manifest.json"

REQUIRED_MEMBERS = [
    "cache/components_search.sqlite",
    "cache/components_prepared_v5.parquet",
    "cache/components_prepared_v5_meta.json",
    "cache/mlcc_lcsc_dimension_cache.json",
    "cache/pdc_findchips_cache.json",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(paths: list[Path]) -> dict:
    entries = []
    for path in paths:
        stat = path.stat()
        entries.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "sha256": sha256_file(path),
            }
        )
    return {"members": entries}


def load_manifest(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_manifest(path: Path, manifest: dict) -> None:
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def add_file_to_zip(archive: zipfile.ZipFile, source_path: Path) -> None:
    rel_name = source_path.relative_to(ROOT).as_posix()
    stat = source_path.stat()
    info = zipfile.ZipInfo(rel_name)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.date_time = tuple(
        __import__("datetime").datetime.fromtimestamp(stat.st_mtime).timetuple()[:6]
    )
    info.external_attr = 0o644 << 16
    with source_path.open("rb") as handle:
        archive.writestr(info, handle.read(), compresslevel=6)


def resolve_member_paths(extra_members: list[str] | None = None) -> list[Path]:
    member_paths = [ROOT / rel for rel in REQUIRED_MEMBERS]
    for rel in extra_members or []:
        candidate = ROOT / rel
        if candidate not in member_paths:
            member_paths.append(candidate)
    missing = [path for path in member_paths if not path.exists()]
    if missing:
        missing_text = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"bundle source files are missing:\n{missing_text}")
    return member_paths


def build_bundle(output_path: Path, member_paths: list[Path]) -> tuple[bool, dict]:
    manifest = build_manifest(member_paths)
    previous_manifest = load_manifest(MANIFEST_PATH)
    if output_path.exists() and previous_manifest == manifest:
        return False, manifest

    temp_path = output_path.with_suffix(output_path.suffix + ".part")
    if temp_path.exists():
        temp_path.unlink()

    with zipfile.ZipFile(temp_path, "w") as archive:
        for source_path in sorted(member_paths, key=lambda item: item.relative_to(ROOT).as_posix()):
            add_file_to_zip(archive, source_path)

    os.replace(temp_path, output_path)
    write_manifest(MANIFEST_PATH, manifest)
    return True, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Streamlit Community Cloud data bundle.")
    parser.add_argument(
        "--output",
        default=str(BUNDLE_PATH),
        help="Output zip path. Defaults to streamlit_cloud_bundle.zip in the repo root.",
    )
    parser.add_argument(
        "--extra-member",
        action="append",
        default=[],
        help="Additional relative file to include in the bundle.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (ROOT / output_path).resolve()

    member_paths = resolve_member_paths(extra_members=args.extra_member)
    rebuilt, manifest = build_bundle(output_path, member_paths)

    total_size = sum(entry["size"] for entry in manifest["members"])
    action = "rebuilt" if rebuilt else "unchanged"
    print(f"[bundle] {action}: {output_path}")
    print(f"[bundle] members: {len(manifest['members'])}, source bytes: {total_size}")
    for entry in manifest["members"]:
        print(f"  - {entry['path']} ({entry['size']} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
