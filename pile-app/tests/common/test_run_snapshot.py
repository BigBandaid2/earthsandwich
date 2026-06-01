"""Tests for `RunSnapshot` — the atomicity primitive for self-healing scrapes.

What's covered:
  - Lifecycle: take → commit (success path); take → rollback (failure path).
  - Rollback restores the TSV to its pre-snapshot content.
  - Rollback removes only media files added since the snapshot — files that
    existed before the scrape (regardless of whether they were overwritten
    during the run) stay where they are.
  - First-time-scrape case: pre-scrape TSV doesn't exist. Rollback removes
    the partial TSV the run created.
  - Leftover-snapshot detection: `.exists()` returns True after a `.take()`
    that wasn't followed by commit or rollback.
  - Best-effort cleanup: OSError on a media-file deletion doesn't abort the
    whole rollback.
"""

import csv
from pathlib import Path
from unittest.mock import patch

import pytest

from common.pile import TSV_COLUMNS, RunSnapshot


def _write_tsv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TSV_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _row(shortcode: str, timestamp: str = "2026-01-01T00:00:00+0000") -> dict:
    return {
        "id": "1", "instagram_id": f"pk-{shortcode}", "shortcode": shortcode,
        "tag_verbatim": "", "lat_verbatim": "", "lng_verbatim": "",
        "media_url": f"pile/media/instagram/acct_{shortcode}.jpg",
        "caption": "", "timestamp": timestamp,
        "location": "", "lat": "", "lng": "", "region": "", "reasoning": "",
        "deleted_upstream": "", "deleted_upstream_at": "",
    }


@pytest.fixture
def sandbox(tmp_path):
    """Per-test pile-shaped sandbox: an empty media_dir, no TSV yet."""
    media_dir = tmp_path / "pile" / "media" / "instagram"
    media_dir.mkdir(parents=True)
    tsv_path = tmp_path / "posts.acct.local.tsv"
    return tsv_path, media_dir, "acct"


class TestLifecycleSuccess:
    """take → commit: the .snapshot file gets cleaned up; pile is whatever
    the scrape made it."""

    def test_commit_removes_snapshot_file(self, sandbox):
        tsv_path, media_dir, target = sandbox
        _write_tsv(tsv_path, [_row("SC1")])

        snap = RunSnapshot(str(tsv_path), str(media_dir), target)
        snap.take()
        assert snap.exists()

        snap.commit()
        assert not snap.exists()
        assert tsv_path.exists()  # the live TSV stays put

    def test_commit_is_idempotent_when_no_snapshot_file_exists(self, sandbox):
        """commit() on an already-committed (or never-taken) snapshot is fine."""
        tsv_path, media_dir, target = sandbox
        snap = RunSnapshot(str(tsv_path), str(media_dir), target)
        snap.commit()  # must not raise

    def test_exists_is_false_before_take(self, sandbox):
        tsv_path, media_dir, target = sandbox
        _write_tsv(tsv_path, [_row("SC1")])
        snap = RunSnapshot(str(tsv_path), str(media_dir), target)
        assert snap.exists() is False


class TestRollbackTSV:
    """Rollback restores the TSV to its pre-snapshot state."""

    def test_rollback_restores_tsv_content(self, sandbox):
        tsv_path, media_dir, target = sandbox
        original = [_row("SC1"), _row("SC2")]
        _write_tsv(tsv_path, original)

        snap = RunSnapshot(str(tsv_path), str(media_dir), target)
        snap.take()

        # Scrape simulates progress: live TSV gets a 3rd row.
        appended = original + [_row("SC3")]
        _write_tsv(tsv_path, appended)
        with tsv_path.open(encoding="utf-8") as f:
            assert sum(1 for _ in f) == 4  # header + 3 rows

        snap.rollback()

        with tsv_path.open(encoding="utf-8") as f:
            assert sum(1 for _ in f) == 3  # header + 2 original rows
        with tsv_path.open(encoding="utf-8") as f:
            shortcodes = [r["shortcode"] for r in csv.DictReader(f, delimiter="\t")]
        assert shortcodes == ["SC1", "SC2"]

    def test_rollback_removes_partial_tsv_when_none_existed_pre_scrape(self, sandbox):
        """First-time scrape: there was no TSV before; rollback should leave
        no TSV behind (the scrape's partial work is discarded)."""
        tsv_path, media_dir, target = sandbox
        assert not tsv_path.exists()

        snap = RunSnapshot(str(tsv_path), str(media_dir), target)
        snap.take()

        # Scrape creates the TSV with one row...
        _write_tsv(tsv_path, [_row("SC1")])
        assert tsv_path.exists()

        # ...then fails.
        snap.rollback()

        assert not tsv_path.exists()


class TestRollbackMediaFiles:
    """Rollback deletes only the media files added since the snapshot."""

    def test_rollback_deletes_files_added_since_snapshot(self, sandbox):
        tsv_path, media_dir, target = sandbox
        # Pre-scrape: 2 files on disk.
        (media_dir / f"{target}_SC_old1.jpg").write_bytes(b"older")
        (media_dir / f"{target}_SC_old2.jpg").write_bytes(b"older")
        _write_tsv(tsv_path, [_row("SC_old1"), _row("SC_old2")])

        snap = RunSnapshot(str(tsv_path), str(media_dir), target)
        snap.take()

        # Scrape downloads 2 new files for new shortcodes...
        (media_dir / f"{target}_SC_new1.jpg").write_bytes(b"new")
        (media_dir / f"{target}_SC_new2.jpg").write_bytes(b"new")

        # ...then fails.
        summary = snap.rollback()

        assert summary["files_deleted"] == 2
        # Old files survive
        assert (media_dir / f"{target}_SC_old1.jpg").exists()
        assert (media_dir / f"{target}_SC_old2.jpg").exists()
        # New files gone
        assert not (media_dir / f"{target}_SC_new1.jpg").exists()
        assert not (media_dir / f"{target}_SC_new2.jpg").exists()

    def test_rollback_keeps_overwritten_files(self, sandbox):
        """A file that EXISTED pre-scrape AND was overwritten during the run
        stays put (the same shortcode → same CDN bytes → content equivalent).

        This is exactly the 2026-05-29 incident's first-144-files case: those
        files were overwritten in place and were still good. The bug was the
        sweep deleting the OTHER 179, not the overwrites.
        """
        tsv_path, media_dir, target = sandbox
        path = media_dir / f"{target}_SC1.jpg"
        path.write_bytes(b"original")
        _write_tsv(tsv_path, [_row("SC1")])

        snap = RunSnapshot(str(tsv_path), str(media_dir), target)
        snap.take()

        # Scrape "re-downloads" the same shortcode, overwriting.
        path.write_bytes(b"overwritten")

        summary = snap.rollback()

        # File stays (was in the snapshot)
        assert path.exists()
        assert summary["files_deleted"] == 0

    def test_rollback_ignores_other_targets_files(self, sandbox):
        """Cross-target safety: rollback for `acct` MUST NOT touch any file
        whose name doesn't start with `acct_`."""
        tsv_path, media_dir, target = sandbox
        (media_dir / "othertarget_SC1.jpg").write_bytes(b"other target's file")

        snap = RunSnapshot(str(tsv_path), str(media_dir), target)
        snap.take()

        # New file for OUR target arrives during the "scrape"
        (media_dir / f"{target}_SC1.jpg").write_bytes(b"ours")

        summary = snap.rollback()

        assert summary["files_deleted"] == 1
        assert not (media_dir / f"{target}_SC1.jpg").exists()
        # Other target's file survives untouched
        assert (media_dir / "othertarget_SC1.jpg").exists()


class TestLeftoverSnapshotDetection:
    """A `.snapshot` left over from a previously-killed run is the trigger
    for self-healing recovery at the next scrape's start."""

    def test_exists_returns_true_after_take_without_commit_or_rollback(self, sandbox):
        tsv_path, media_dir, target = sandbox
        _write_tsv(tsv_path, [_row("SC1")])

        snap = RunSnapshot(str(tsv_path), str(media_dir), target)
        snap.take()

        # Simulate the process being killed before commit/rollback. Build a
        # FRESH instance — that's what the next scrape's start would see.
        fresh = RunSnapshot(str(tsv_path), str(media_dir), target)
        assert fresh.exists()


class TestBestEffortCleanup:
    """The rollback path must not raise on OS errors — we're already
    handling a failure and must not compound it."""

    def test_rollback_continues_when_a_media_delete_fails(self, sandbox):
        tsv_path, media_dir, target = sandbox
        _write_tsv(tsv_path, [])

        snap = RunSnapshot(str(tsv_path), str(media_dir), target)
        snap.take()

        # Two new files; one will raise OSError on remove
        (media_dir / f"{target}_SC_new1.jpg").write_bytes(b"new")
        (media_dir / f"{target}_SC_new2.jpg").write_bytes(b"new")

        real_remove = __import__("os").remove
        deleted_paths: list[str] = []

        def flaky_remove(path):
            if "SC_new1" in str(path):
                raise OSError("simulated permission denied")
            deleted_paths.append(str(path))
            real_remove(path)

        with patch("common.pile.os.remove", side_effect=flaky_remove):
            summary = snap.rollback()

        # The successful deletion still happened; the failed one was skipped.
        assert summary["files_deleted"] == 1
        assert not (media_dir / f"{target}_SC_new2.jpg").exists()
        # The one that errored is still on disk
        assert (media_dir / f"{target}_SC_new1.jpg").exists()
