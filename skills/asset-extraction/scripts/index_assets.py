from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

SCHEMA_VERSION = 1
CHUNK_SIZE = 1024 * 1024

DEFAULT_ASSET_EXTENSIONS = frozenset(
    {
        ".aac",
        ".avif",
        ".blend",
        ".bmp",
        ".dae",
        ".fbx",
        ".flac",
        ".gif",
        ".glb",
        ".gltf",
        ".heic",
        ".heif",
        ".ico",
        ".jpeg",
        ".jpg",
        ".m4a",
        ".mkv",
        ".mov",
        ".mp3",
        ".mp4",
        ".obj",
        ".ogg",
        ".ply",
        ".png",
        ".stl",
        ".svg",
        ".tif",
        ".tiff",
        ".usdz",
        ".wav",
        ".webm",
        ".webp",
    }
)

DEFAULT_EXCLUDED_DIRECTORIES = frozenset(
    {
        ".cache",
        ".git",
        ".gradle",
        ".mypy_cache",
        ".next",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "target",
        "vendor",
    }
)

MIME_OVERRIDES = {
    ".avif": "image/avif",
    ".glb": "model/gltf-binary",
    ".gltf": "model/gltf+json",
    ".heic": "image/heic",
    ".heif": "image/heif",
    ".m4a": "audio/mp4",
    ".obj": "model/obj",
    ".stl": "model/stl",
    ".usdz": "model/vnd.usdz+zip",
}

KIND_EXTENSIONS = {
    "image": frozenset(
        {
            ".avif",
            ".bmp",
            ".gif",
            ".heic",
            ".heif",
            ".ico",
            ".jpeg",
            ".jpg",
            ".png",
            ".svg",
            ".tif",
            ".tiff",
            ".webp",
        }
    ),
    "audio": frozenset({".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav"}),
    "video": frozenset({".mkv", ".mov", ".mp4", ".webm"}),
    "model": frozenset(
        {".blend", ".dae", ".fbx", ".glb", ".gltf", ".obj", ".ply", ".stl", ".usdz"}
    ),
}


@dataclass(frozen=True)
class FileInfo:
    path: Path
    relative_path: str
    size: int
    mtime_ns: int


def normalize_extensions(values: list[str] | None) -> frozenset[str]:
    raw_values = values if values else sorted(DEFAULT_ASSET_EXTENSIONS)
    normalized = {value if value.startswith(".") else f".{value}" for value in raw_values}
    return frozenset(value.casefold() for value in normalized if value != ".")


def normalize_names(values: list[str] | None) -> frozenset[str]:
    return frozenset(value.strip().casefold() for value in values or [] if value.strip())


def collect_files(
    root: Path,
    *,
    include_all: bool,
    extensions: frozenset[str],
    excluded_directories: frozenset[str],
    output: Path,
) -> list[FileInfo]:
    files: list[FileInfo] = []
    for directory, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_directory = Path(directory)
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name.casefold() not in excluded_directories
            and not (current_directory / name).is_symlink()
        )
        for name in sorted(filenames):
            path = current_directory / name
            if path.is_symlink() or not path.is_file() or path.resolve() == output:
                continue
            if not include_all and path.suffix.casefold() not in extensions:
                continue
            stat = path.stat()
            files.append(
                FileInfo(
                    path=path,
                    relative_path=path.relative_to(root).as_posix(),
                    size=stat.st_size,
                    mtime_ns=stat.st_mtime_ns,
                )
            )
    return files


def inventory_fingerprint(files: list[FileInfo]) -> str:
    digest = hashlib.sha256()
    for file_info in files:
        digest.update(
            f"{file_info.relative_path}\0{file_info.size}\0{file_info.mtime_ns}\n".encode()
        )
    return digest.hexdigest()


def hash_file(file_info: FileInfo) -> str:
    before = file_info.path.stat()
    digest = hashlib.sha256()
    with file_info.path.open("rb") as stream:
        while chunk := stream.read(CHUNK_SIZE):
            digest.update(chunk)
    after = file_info.path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError(f"input changed while hashing: {file_info.relative_path}")
    return digest.hexdigest()


def mime_type_for(path: Path) -> str:
    suffix = path.suffix.casefold()
    return (
        MIME_OVERRIDES.get(suffix)
        or mimetypes.guess_type(path.name)[0]
        or "application/octet-stream"
    )


def kind_for(path: Path) -> str:
    suffix = path.suffix.casefold()
    for kind, extensions in KIND_EXTENSIONS.items():
        if suffix in extensions:
            return kind
    return "other"


def rank_score(relative_path: str, keywords: frozenset[str]) -> int:
    lowered = relative_path.casefold()
    return sum(lowered.count(keyword) for keyword in keywords)


def read_manifest(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
    if not path.is_file() or path.is_symlink():
        return None
    try:
        with path.open(encoding="utf-8") as stream:
            header = json.loads(stream.readline())
            if not isinstance(header, dict) or header.get("record_type") != "manifest":
                return None
            entries = [json.loads(line) for line in stream if line.strip()]
    except (OSError, json.JSONDecodeError):
        return None
    if not all(
        isinstance(entry, dict) and entry.get("record_type") == "asset" for entry in entries
    ):
        return None
    return header, entries


def write_manifest(path: Path, header: dict[str, Any], entries: list[dict[str, Any]]) -> None:
    if path.is_symlink():
        raise ValueError(f"refusing to write through symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: str | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_path = stream.name
            stream.write(json.dumps(header, ensure_ascii=False, sort_keys=True) + "\n")
            for entry in entries:
                stream.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path:
            Path(temporary_path).unlink(missing_ok=True)


def index_assets(
    root: Path,
    output: Path,
    *,
    include_all: bool = False,
    extensions: list[str] | None = None,
    keywords: list[str] | None = None,
    excluded_directories: list[str] | None = None,
    max_shortlist: int = 20,
    reuse: bool = False,
) -> dict[str, Any]:
    root = root.expanduser().resolve()
    output = output.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"asset root is not a directory: {root}")
    if max_shortlist < 1:
        raise ValueError("max_shortlist must be at least 1")

    extension_set = normalize_extensions(extensions)
    excluded_set = DEFAULT_EXCLUDED_DIRECTORIES | normalize_names(excluded_directories)
    keyword_set = normalize_names(keywords)
    files = collect_files(
        root,
        include_all=include_all,
        extensions=extension_set,
        excluded_directories=excluded_set,
        output=output,
    )
    fingerprint = inventory_fingerprint(files)
    config = {
        "excluded_directories": sorted(excluded_set),
        "extensions": sorted(extension_set),
        "include_all": include_all,
        "keywords": sorted(keyword_set),
        "max_shortlist": max_shortlist,
    }

    cached = read_manifest(output) if reuse else None
    if cached:
        cached_header, cached_entries = cached
        if (
            cached_header.get("root") == str(root)
            and cached_header.get("inventory_fingerprint") == fingerprint
            and cached_header.get("config") == config
        ):
            return {"header": cached_header, "entries": cached_entries, "reused": True}

    seen: dict[str, str] = {}
    entries: list[dict[str, Any]] = []
    for file_info in files:
        digest = hash_file(file_info)
        duplicate_of = seen.get(digest)
        if duplicate_of is None:
            seen[digest] = file_info.relative_path
        entry = {
            "record_type": "asset",
            "path": file_info.relative_path,
            "size": file_info.size,
            "sha256": digest,
            "mime_type": mime_type_for(file_info.path),
            "kind": kind_for(file_info.path),
            "extension": file_info.path.suffix.casefold(),
            "rank_score": rank_score(file_info.relative_path, keyword_set),
            "duplicate_of": duplicate_of,
        }
        entries.append(entry)

    unique_entries = [entry for entry in entries if entry["duplicate_of"] is None]
    shortlist = sorted(
        unique_entries,
        key=lambda entry: (-int(entry["rank_score"]), -int(entry["size"]), str(entry["path"])),
    )[:max_shortlist]
    header = {
        "record_type": "manifest",
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inventory_fingerprint": fingerprint,
        "config": config,
        "total_candidates": len(entries),
        "unique_candidates": len(unique_entries),
        "duplicate_files": len(entries) - len(unique_entries),
        "shortlist": [
            {"path": entry["path"], "rank_score": entry["rank_score"]} for entry in shortlist
        ],
    }
    return {"header": header, "entries": entries, "reused": False}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="directory to inventory")
    parser.add_argument("--output", type=Path, required=True, help="JSONL manifest path")
    parser.add_argument(
        "--extension",
        action="append",
        dest="extensions",
        help="extension to include; repeat for multiple extensions",
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="include all regular files instead of the default asset extensions",
    )
    parser.add_argument(
        "--keyword",
        action="append",
        default=[],
        help="case-insensitive path keyword used for shortlist ranking",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="additional directory name to exclude; repeat as needed",
    )
    parser.add_argument("--max-shortlist", type=int, default=20)
    parser.add_argument("--reuse", action="store_true", help="reuse an unchanged existing manifest")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = index_assets(
            args.root,
            args.output,
            include_all=args.include_all,
            extensions=args.extensions,
            keywords=args.keyword,
            excluded_directories=args.exclude_dir,
            max_shortlist=args.max_shortlist,
            reuse=args.reuse,
        )
        if not result["reused"]:
            write_manifest(args.output.expanduser().resolve(), result["header"], result["entries"])
        header = result["header"]
        print(
            json.dumps(
                {
                    "output": str(args.output.expanduser().resolve()),
                    "reused": result["reused"],
                    "total_candidates": header["total_candidates"],
                    "unique_candidates": header["unique_candidates"],
                    "duplicate_files": header["duplicate_files"],
                    "shortlist": header["shortlist"],
                },
                ensure_ascii=False,
            )
        )
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(f"asset index failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
