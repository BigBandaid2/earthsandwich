"""Pile directory scanning: data-file table-validation + media cataloguing (T057, FR-182).

Data files are validated as tables (tsv/csv/json) with row × column counts;
files that don't parse as a table are rejected with a reason and cannot be
selected. Media directories are catalogued (count, type breakdown, total bytes),
never enumerated for per-file selection.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

#: Extensions catalogued as media rather than validated as tables.
MEDIA_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".mp4", ".mov", ".avi", ".mkv", ".wav", ".mp3"}
_DATA_EXTS = {".tsv": "\t", ".csv": ",", ".txt": None}


@dataclass
class FileScan:
    name: str
    valid: bool
    fmt: str | None = None        # tsv | csv | json
    rows: int = 0
    cols: int = 0
    reason: str = ""              # why rejected, when not valid


def _scan_delimited(path: Path, delimiter: str | None) -> FileScan:
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            sample = fh.read(8192)
            fh.seek(0)
            if delimiter is None:                          # .txt — sniff
                try:
                    delimiter = csv.Sniffer().sniff(sample, delimiters="\t,;|").delimiter
                except csv.Error:
                    return FileScan(path.name, False, reason="not a table — no delimiter detected")
            reader = csv.reader(fh, delimiter=delimiter)
            header = next(reader, None)
            if not header or len(header) < 1:
                return FileScan(path.name, False, reason="not a table — empty or headerless")
            cols = len(header)
            if cols < 2 and delimiter not in (",", "\t"):
                return FileScan(path.name, False, reason="not a table — single column")
            rows = sum(1 for _ in reader)
    except OSError as exc:
        return FileScan(path.name, False, reason=f"unreadable: {exc}")
    fmt = {"\t": "tsv", ",": "csv"}.get(delimiter, "csv")
    return FileScan(path.name, True, fmt=fmt, rows=rows, cols=cols)


def _scan_json(path: Path) -> FileScan:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError) as exc:
        return FileScan(path.name, False, reason=f"not valid JSON: {exc}")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        cols = len({k for record in data if isinstance(record, dict) for k in record})
        return FileScan(path.name, True, fmt="json", rows=len(data), cols=cols)
    if isinstance(data, dict):
        return FileScan(path.name, True, fmt="json", rows=1, cols=len(data))
    return FileScan(path.name, False, reason="not a table — JSON is not an array of objects")


def scan_data_file(path: str | Path) -> FileScan:
    """Validate one file as a table; report format + row×col, or a reject reason."""
    path = Path(path)
    if not path.is_file():
        return FileScan(path.name, False, reason="file not found")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _scan_json(path)
    if suffix in _DATA_EXTS:
        return _scan_delimited(path, _DATA_EXTS[suffix])
    if suffix in MEDIA_EXTS:
        return FileScan(path.name, False, reason=f"media file ({suffix}) — use a media directory")
    return _scan_delimited(path, None)                     # unknown ext — try to sniff


def scan_data_directory(directory: str | Path) -> list[FileScan]:
    """Scan every file in a data directory, sorted; dotfiles excluded."""
    directory = Path(directory)
    if not directory.is_dir():
        return []
    return [scan_data_file(entry) for entry in sorted(directory.iterdir())
            if entry.is_file() and not entry.name.startswith(".")]


def catalogue_media_directory(directory: str | Path) -> dict:
    """Summarize a media directory: count, type breakdown, total bytes (FR-182)."""
    directory = Path(directory)
    types: dict[str, int] = {}
    count = 0
    total = 0
    if directory.is_dir():
        for entry in directory.rglob("*"):
            if entry.is_file() and not entry.name.startswith("."):
                ext = entry.suffix.lower().lstrip(".") or "(none)"
                types[ext] = types.get(ext, 0) + 1
                count += 1
                try:
                    total += entry.stat().st_size
                except OSError:
                    pass
    return {"count": count, "types": dict(sorted(types.items())), "bytes": total}
