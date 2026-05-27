"""Unit tests for `_resort_tsv_and_rename_media` — the post-streaming step
that restores canonical row order and cleans up orphan media files.

Covers:
  - Orphan sweep: target-prefixed files not referenced by any TSV row get
    deleted; other-target files and referenced files are preserved.
  - Sort + re-id: rows are written back in timestamp-ASC order with
    sequential ids.
  - Two-pass rename: id swaps survive without colliding (file A→B's old
    id while file B→A's old id).
"""

import csv
import os
from pathlib import Path

import pytest

import load_posts_tsv
from load_posts_tsv import _resort_tsv_and_rename_media, TSV_COLUMNS


def _write_tsv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TSV_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _read_tsv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _media_url(media_dir: Path, target: str, local_id: int, ext: str = "jpg") -> str:
    """Build a media_url relative to PROJECT_ROOT in posix format, like the
    real `process_media` would produce."""
    abs_path = media_dir / f"{target}_{local_id}.{ext}"
    rel = os.path.relpath(abs_path, load_posts_tsv.PROJECT_ROOT)
    return rel.replace(os.sep, "/")


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Point PROJECT_ROOT at a tmp directory so we don't touch the real repo
    layout. Yields (tsv_path, media_dir, target_name)."""
    monkeypatch.setattr(load_posts_tsv, "PROJECT_ROOT", str(tmp_path))
    media_dir = tmp_path / "public" / "media"
    media_dir.mkdir(parents=True)
    tsv_path = tmp_path / "posts.test.local.tsv"
    return tsv_path, media_dir, "testacct"


def _row(local_id: int, timestamp: str, media_url: str, shortcode: str = "") -> dict:
    return {
        "id": str(local_id),
        "instagram_id": f"pk{local_id}",
        "shortcode": shortcode or f"SC{local_id}",
        "media_url": media_url,
        "caption": "",
        "timestamp": timestamp,
        "location": "",
        "lat": "",
        "lng": "",
        "region": "",
        "reasoning": "",
    }


class TestOrphanSweep:
    def test_orphan_target_file_is_deleted(self, sandbox):
        """A `<target>_*` file in media_dir not referenced by any TSV row
        is treated as a leftover from a prior scrape and removed."""
        tsv_path, media_dir, target = sandbox
        # Referenced file (will be kept).
        (media_dir / f"{target}_1.jpg").write_bytes(b"keep")
        # Orphan: matches prefix but not referenced — different extension.
        (media_dir / f"{target}_1.mp4").write_bytes(b"orphan")

        rows = [_row(1, "2026-01-01T00:00:00+0000", _media_url(media_dir, target, 1, "jpg"))]
        _write_tsv(tsv_path, rows)

        _resort_tsv_and_rename_media(str(tsv_path), target, str(media_dir))

        assert (media_dir / f"{target}_1.jpg").exists()
        assert not (media_dir / f"{target}_1.mp4").exists()

    def test_other_target_files_are_not_touched(self, sandbox):
        """Cross-target safety: a `<other>_*` file must not be deleted even
        if it has no TSV row to back it (it belongs to a different scrape)."""
        tsv_path, media_dir, target = sandbox
        (media_dir / f"{target}_1.jpg").write_bytes(b"ours")
        (media_dir / "otheraccount_1.jpg").write_bytes(b"not ours")

        rows = [_row(1, "2026-01-01T00:00:00+0000", _media_url(media_dir, target, 1, "jpg"))]
        _write_tsv(tsv_path, rows)

        _resort_tsv_and_rename_media(str(tsv_path), target, str(media_dir))

        assert (media_dir / "otheraccount_1.jpg").exists()

    def test_sweep_handles_files_with_no_dot_prefix(self, sandbox):
        """`<target>_<anything>` matches even without a typical extension —
        e.g. partial downloads, .tmp leftovers. As long as it's the target's
        prefix and not referenced, sweep it."""
        tsv_path, media_dir, target = sandbox
        (media_dir / f"{target}_1.jpg").write_bytes(b"keep")
        (media_dir / f"{target}_99.jpg.rename-tmp").write_bytes(b"stale tmp")

        rows = [_row(1, "2026-01-01T00:00:00+0000", _media_url(media_dir, target, 1, "jpg"))]
        _write_tsv(tsv_path, rows)

        _resort_tsv_and_rename_media(str(tsv_path), target, str(media_dir))

        assert (media_dir / f"{target}_1.jpg").exists()
        assert not (media_dir / f"{target}_99.jpg.rename-tmp").exists()

    def test_no_sweep_when_media_dir_missing(self, sandbox, tmp_path):
        """If media_dir doesn't exist (edge case from a corrupted setup),
        the function returns cleanly without raising."""
        tsv_path, _media_dir, target = sandbox
        rows = [_row(1, "2026-01-01T00:00:00+0000", "")]
        _write_tsv(tsv_path, rows)

        bogus = str(tmp_path / "nonexistent")
        _resort_tsv_and_rename_media(str(tsv_path), target, bogus)  # must not raise

    def test_relative_media_dir_path_does_not_misclassify_referenced_files(
        self, sandbox, monkeypatch
    ):
        """Regression: a relative `media_dir` argument used to make every
        on-disk file get classified as orphan (because the `referenced`
        set had absolute paths from PROJECT_ROOT but the scan produced
        relative paths). The fix normalizes both sides via os.path.abspath
        before comparing. This test reproduces the original failure.
        """
        tsv_path, media_dir, target = sandbox
        keep = media_dir / f"{target}_1.jpg"
        orphan = media_dir / f"{target}_2.mp4"
        keep.write_bytes(b"keep")
        orphan.write_bytes(b"orphan")

        rows = [_row(1, "2026-01-01T00:00:00+0000", _media_url(media_dir, target, 1))]
        _write_tsv(tsv_path, rows)

        # Pass media_dir as a RELATIVE path (the buggy case). Make sure the
        # process CWD is the sandbox root so the relative path resolves the
        # same way PROJECT_ROOT does.
        monkeypatch.chdir(str(media_dir.parent.parent))
        rel_media_dir = os.path.relpath(str(media_dir))

        _resort_tsv_and_rename_media(str(tsv_path), target, rel_media_dir)

        assert keep.exists(), "referenced file was wrongly swept under relative media_dir"
        assert not orphan.exists(), "orphan was not swept under relative media_dir"


class TestSortAndReid:
    def test_rows_sorted_by_timestamp_ascending(self, sandbox):
        """A TSV in pagination order gets re-sorted to oldest-first."""
        tsv_path, media_dir, target = sandbox
        # File names match the original streaming-order ids
        (media_dir / f"{target}_1.jpg").write_bytes(b"a")
        (media_dir / f"{target}_2.jpg").write_bytes(b"b")
        (media_dir / f"{target}_3.jpg").write_bytes(b"c")

        # Streaming order (id 1 = newest, id 3 = oldest)
        rows = [
            _row(1, "2026-03-15T00:00:00+0000", _media_url(media_dir, target, 1)),
            _row(2, "2026-02-15T00:00:00+0000", _media_url(media_dir, target, 2)),
            _row(3, "2026-01-15T00:00:00+0000", _media_url(media_dir, target, 3)),
        ]
        _write_tsv(tsv_path, rows)

        _resort_tsv_and_rename_media(str(tsv_path), target, str(media_dir))

        result = _read_tsv(tsv_path)
        # After re-sort, oldest is row 1, newest is row 3
        assert [r["timestamp"] for r in result] == [
            "2026-01-15T00:00:00+0000",
            "2026-02-15T00:00:00+0000",
            "2026-03-15T00:00:00+0000",
        ]
        assert [r["id"] for r in result] == ["1", "2", "3"]

    def test_rename_handles_full_id_swap(self, sandbox):
        """All ids change in a full reversal — every media file must be
        renamed without colliding. Two-pass `.rename-tmp` makes this safe."""
        tsv_path, media_dir, target = sandbox
        (media_dir / f"{target}_1.jpg").write_bytes(b"newest-content")
        (media_dir / f"{target}_2.jpg").write_bytes(b"middle-content")
        (media_dir / f"{target}_3.jpg").write_bytes(b"oldest-content")

        rows = [
            _row(1, "2026-03-15T00:00:00+0000", _media_url(media_dir, target, 1)),
            _row(2, "2026-02-15T00:00:00+0000", _media_url(media_dir, target, 2)),
            _row(3, "2026-01-15T00:00:00+0000", _media_url(media_dir, target, 3)),
        ]
        _write_tsv(tsv_path, rows)

        _resort_tsv_and_rename_media(str(tsv_path), target, str(media_dir))

        # After re-sort: id 1 = oldest (was id 3), id 3 = newest (was id 1)
        assert (media_dir / f"{target}_1.jpg").read_bytes() == b"oldest-content"
        assert (media_dir / f"{target}_2.jpg").read_bytes() == b"middle-content"
        assert (media_dir / f"{target}_3.jpg").read_bytes() == b"newest-content"

        # No `.rename-tmp` files should be left behind
        leftovers = [f.name for f in media_dir.iterdir() if ".rename-tmp" in f.name]
        assert leftovers == []

    def test_missing_media_file_does_not_crash(self, sandbox):
        """If a row's media_url points to a file that doesn't exist (download
        failed earlier), the id is still updated but no rename happens."""
        tsv_path, media_dir, target = sandbox
        # Only one of two files actually on disk
        (media_dir / f"{target}_2.jpg").write_bytes(b"only this exists")

        rows = [
            _row(1, "2026-02-15T00:00:00+0000", _media_url(media_dir, target, 1)),  # file missing
            _row(2, "2026-01-15T00:00:00+0000", _media_url(media_dir, target, 2)),
        ]
        _write_tsv(tsv_path, rows)

        _resort_tsv_and_rename_media(str(tsv_path), target, str(media_dir))

        result = _read_tsv(tsv_path)
        # Re-sorted: id 1 = oldest (was id 2 — file was on disk and was renamed to _1.jpg)
        #            id 2 = newest (was id 1 — file was missing, no rename happened)
        assert [r["id"] for r in result] == ["1", "2"]
        assert (media_dir / f"{target}_1.jpg").read_bytes() == b"only this exists"
