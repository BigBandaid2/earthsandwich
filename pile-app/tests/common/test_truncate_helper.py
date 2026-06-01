"""Unit tests for `truncate_tsv_to_timestamp` (the `--newer-than` CLI helper).

Covers:
  - Rows with timestamp > cutoff are removed; rows <= cutoff are kept.
  - Rows AT the cutoff timestamp are kept (inclusive boundary on the keep side).
  - Returns the number of rows removed.
  - Idempotent when no rows match (returns 0, file unchanged).
  - Idempotent when file doesn't exist (returns 0).
  - Survives ISO format variations in the TSV (`+0000` vs `+00:00`) because
    comparison is numeric on the parsed Unix timestamp.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

import pytest

from common.pile import TSV_COLUMNS, truncate_tsv_to_timestamp


def _write_tsv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TSV_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _read_tsv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _row(local_id: int, timestamp: str) -> dict:
    return {
        "id": str(local_id),
        "instagram_id": f"pk{local_id}",
        "shortcode": f"SC{local_id}",
        "media_url": "",
        "caption": "",
        "timestamp": timestamp,
        "location": "",
    }


def _ts(iso: str) -> int:
    """Parse an ISO timestamp the same way the CLI/pipeline does (UTC for naive)."""
    s = iso.strip().replace(" ", "T")
    if s.endswith("+00"):
        s += ":00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


class TestTruncateTsvToTimestamp:
    def test_removes_rows_strictly_newer_than_cutoff(self, tmp_path):
        path = tmp_path / "posts.tsv"
        _write_tsv(path, [
            _row(1, "2024-01-01T00:00:00+0000"),
            _row(2, "2024-06-15T12:00:00+0000"),
            _row(3, "2025-01-01T00:00:00+0000"),
            _row(4, "2025-06-15T12:00:00+0000"),
        ])
        cutoff = _ts("2024-12-31T23:59:59+0000")

        removed = truncate_tsv_to_timestamp(str(path), cutoff)

        assert removed == 2
        kept = _read_tsv(path)
        assert [r["id"] for r in kept] == ["1", "2"]

    def test_row_at_exactly_cutoff_is_kept(self, tmp_path):
        """The cutoff boundary is inclusive on the keep side — the symmetry
        with the streaming filter (`if ts <= since_ts: break`) is what makes
        a re-run with the same --newer-than value a true idempotent no-op."""
        path = tmp_path / "posts.tsv"
        _write_tsv(path, [
            _row(1, "2024-02-20T02:27:16+0000"),
            _row(2, "2024-02-20T02:27:17+0000"),
        ])
        cutoff = _ts("2024-02-20T02:27:16+0000")

        removed = truncate_tsv_to_timestamp(str(path), cutoff)

        assert removed == 1
        assert [r["id"] for r in _read_tsv(path)] == ["1"]

    def test_no_rows_match_returns_zero(self, tmp_path):
        path = tmp_path / "posts.tsv"
        _write_tsv(path, [
            _row(1, "2020-01-01T00:00:00+0000"),
            _row(2, "2021-01-01T00:00:00+0000"),
        ])
        cutoff = _ts("2030-01-01T00:00:00+0000")

        removed = truncate_tsv_to_timestamp(str(path), cutoff)

        assert removed == 0
        assert len(_read_tsv(path)) == 2

    def test_missing_file_returns_zero(self, tmp_path):
        path = tmp_path / "does-not-exist.tsv"
        cutoff = _ts("2024-12-31T00:00:00+0000")

        removed = truncate_tsv_to_timestamp(str(path), cutoff)

        assert removed == 0
        assert not path.exists()

    def test_handles_iso_format_variations_in_tsv(self, tmp_path):
        """The TSV might in theory carry `+00:00`-style offsets, or other
        ISO variations — numeric comparison on parsed Unix timestamps must
        normalize them correctly."""
        path = tmp_path / "posts.tsv"
        _write_tsv(path, [
            _row(1, "2024-01-01T00:00:00+0000"),
            _row(2, "2024-06-15T12:00:00+00:00"),  # colon-separated offset
            _row(3, "2025-01-01T00:00:00+0000"),
        ])
        cutoff = _ts("2024-12-31T23:59:59+0000")

        removed = truncate_tsv_to_timestamp(str(path), cutoff)

        assert removed == 1
        assert [r["id"] for r in _read_tsv(path)] == ["1", "2"]

    def test_rows_with_missing_timestamp_are_dropped(self, tmp_path):
        """Defensive: a row with no timestamp can't be evaluated against the
        cutoff. The function treats such rows as undecidable and drops them
        rather than silently keeping them on the wrong side."""
        path = tmp_path / "posts.tsv"
        _write_tsv(path, [
            _row(1, "2024-01-01T00:00:00+0000"),
            _row(2, ""),  # malformed
            _row(3, "2024-06-15T12:00:00+0000"),
        ])
        cutoff = _ts("2025-01-01T00:00:00+0000")

        removed = truncate_tsv_to_timestamp(str(path), cutoff)

        assert removed == 1
        assert [r["id"] for r in _read_tsv(path)] == ["1", "3"]
