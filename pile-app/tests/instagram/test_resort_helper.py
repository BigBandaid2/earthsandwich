"""Unit tests for `resort_tsv_and_sweep_media` (the post-streaming step
that restores canonical row order and cleans up orphan media files), plus
`prune_scrape_logs` and `extract_city_heuristic`.

Covers:
  - Orphan sweep: target-prefixed files not referenced by any TSV row get
    deleted; other-target files and referenced files are preserved.
  - Sort + re-id: rows are written back in timestamp-ASC order with
    sequential ids. Media filenames stay put (T225 — they're now keyed
    on shortcode, not id, so id changes never trigger a rename).
  - Log pruning retention policy.
  - City-heuristic edge cases for the no-inference fallback.
"""

import csv
import os
import time
from pathlib import Path

import pytest

import common.pile
from common.pile import TSV_COLUMNS, resort_tsv_and_sweep_media
from common.run_logging import prune_scrape_logs
from instagram.inferred_location import extract_city_heuristic


def _write_tsv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TSV_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _read_tsv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _media_url(media_dir: Path, target: str, local_id: int, ext: str = "jpg") -> str:
    """Build a media_url relative to APP_ROOT in posix format, like the
    real `process_media` would produce."""
    abs_path = media_dir / f"{target}_{local_id}.{ext}"
    rel = os.path.relpath(abs_path, str(common.pile.APP_ROOT))
    return rel.replace(os.sep, "/")


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Point APP_ROOT at a tmp directory so we don't touch the real repo
    layout. Yields (tsv_path, media_dir, target_name)."""
    monkeypatch.setattr(common.pile, "APP_ROOT", str(tmp_path))
    media_dir = tmp_path / "pile" / "media" / "instagram"
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
        (media_dir / f"{target}_1.jpg").write_bytes(b"keep")
        (media_dir / f"{target}_1.mp4").write_bytes(b"orphan")

        rows = [_row(1, "2026-01-01T00:00:00+0000", _media_url(media_dir, target, 1, "jpg"))]
        _write_tsv(tsv_path, rows)

        resort_tsv_and_sweep_media(str(tsv_path), target, str(media_dir))

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

        resort_tsv_and_sweep_media(str(tsv_path), target, str(media_dir))

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

        resort_tsv_and_sweep_media(str(tsv_path), target, str(media_dir))

        assert (media_dir / f"{target}_1.jpg").exists()
        assert not (media_dir / f"{target}_99.jpg.rename-tmp").exists()

    def test_no_sweep_when_media_dir_missing(self, sandbox, tmp_path):
        """If media_dir doesn't exist (edge case from a corrupted setup),
        the function returns cleanly without raising."""
        tsv_path, _media_dir, target = sandbox
        rows = [_row(1, "2026-01-01T00:00:00+0000", "")]
        _write_tsv(tsv_path, rows)

        bogus = str(tmp_path / "nonexistent")
        resort_tsv_and_sweep_media(str(tsv_path), target, bogus)

    def test_relative_media_dir_path_does_not_misclassify_referenced_files(
        self, sandbox, monkeypatch
    ):
        """Regression: a relative `media_dir` argument used to make every
        on-disk file get classified as orphan (because the `referenced`
        set had absolute paths from APP_ROOT but the scan produced
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

        # CWD = the sandbox's APP_ROOT so the relative path resolves the
        # same way the sandbox APP_ROOT does.
        monkeypatch.chdir(str(media_dir.parent.parent.parent))
        rel_media_dir = os.path.relpath(str(media_dir))

        resort_tsv_and_sweep_media(str(tsv_path), target, rel_media_dir)

        assert keep.exists(), "referenced file was wrongly swept under relative media_dir"
        assert not orphan.exists(), "orphan was not swept under relative media_dir"


class TestSortAndReid:
    def test_rows_sorted_by_timestamp_ascending(self, sandbox):
        """A TSV in pagination order gets re-sorted to oldest-first."""
        tsv_path, media_dir, target = sandbox
        (media_dir / f"{target}_1.jpg").write_bytes(b"a")
        (media_dir / f"{target}_2.jpg").write_bytes(b"b")
        (media_dir / f"{target}_3.jpg").write_bytes(b"c")

        rows = [
            _row(1, "2026-03-15T00:00:00+0000", _media_url(media_dir, target, 1)),
            _row(2, "2026-02-15T00:00:00+0000", _media_url(media_dir, target, 2)),
            _row(3, "2026-01-15T00:00:00+0000", _media_url(media_dir, target, 3)),
        ]
        _write_tsv(tsv_path, rows)

        resort_tsv_and_sweep_media(str(tsv_path), target, str(media_dir))

        result = _read_tsv(tsv_path)
        assert [r["timestamp"] for r in result] == [
            "2026-01-15T00:00:00+0000",
            "2026-02-15T00:00:00+0000",
            "2026-03-15T00:00:00+0000",
        ]
        assert [r["id"] for r in result] == ["1", "2", "3"]

    def test_id_swap_does_not_rename_media_files(self, sandbox):
        """Post-T225 the on-disk media filename is keyed on `shortcode` (not
        `<id>`), so the canonical sort+reid pass MUST NOT rename any media
        file even when every row's id changes. Files stay where the original
        download_media call placed them; only the in-TSV `id` column moves."""
        tsv_path, media_dir, target = sandbox
        # Files named with shortcode (e.g., SC1, SC2, SC3 from _row's default).
        (media_dir / f"{target}_SC1.jpg").write_bytes(b"newest-content")
        (media_dir / f"{target}_SC2.jpg").write_bytes(b"middle-content")
        (media_dir / f"{target}_SC3.jpg").write_bytes(b"oldest-content")

        rows = [
            _row(1, "2026-03-15T00:00:00+0000", _media_url(media_dir, target, "SC1")),
            _row(2, "2026-02-15T00:00:00+0000", _media_url(media_dir, target, "SC2")),
            _row(3, "2026-01-15T00:00:00+0000", _media_url(media_dir, target, "SC3")),
        ]
        _write_tsv(tsv_path, rows)

        resort_tsv_and_sweep_media(str(tsv_path), target, str(media_dir))

        # Files stay PUT — content unchanged at the original filenames.
        assert (media_dir / f"{target}_SC1.jpg").read_bytes() == b"newest-content"
        assert (media_dir / f"{target}_SC2.jpg").read_bytes() == b"middle-content"
        assert (media_dir / f"{target}_SC3.jpg").read_bytes() == b"oldest-content"

        # No `.rename-tmp` leftovers (the rename pass is gone entirely).
        leftovers = [f.name for f in media_dir.iterdir() if ".rename-tmp" in f.name]
        assert leftovers == []

        # In-TSV ids re-numbered to match the timestamp-ASC order.
        result = _read_tsv(tsv_path)
        assert [r["timestamp"] for r in result] == [
            "2026-01-15T00:00:00+0000",
            "2026-02-15T00:00:00+0000",
            "2026-03-15T00:00:00+0000",
        ]
        assert [r["id"] for r in result] == ["1", "2", "3"]
        # And the shortcode→media_url linkage in each row is preserved
        # exactly (no row's media_url got rewritten).
        assert result[0]["media_url"].endswith("_SC3.jpg")
        assert result[2]["media_url"].endswith("_SC1.jpg")

    def test_missing_media_file_does_not_crash(self, sandbox):
        """If a row's media_url points to a file that doesn't exist (download
        failed earlier), the resort+sweep pass still completes cleanly."""
        tsv_path, media_dir, target = sandbox
        (media_dir / f"{target}_SC2.jpg").write_bytes(b"only this exists")

        rows = [
            _row(1, "2026-02-15T00:00:00+0000", _media_url(media_dir, target, "SC1")),
            _row(2, "2026-01-15T00:00:00+0000", _media_url(media_dir, target, "SC2")),
        ]
        _write_tsv(tsv_path, rows)

        resort_tsv_and_sweep_media(str(tsv_path), target, str(media_dir))

        result = _read_tsv(tsv_path)
        assert [r["id"] for r in result] == ["1", "2"]
        # The on-disk file that did exist is still there, untouched.
        assert (media_dir / f"{target}_SC2.jpg").read_bytes() == b"only this exists"


class TestSweepOrphansFlag:
    """The `sweep_orphans` kwarg is the post-2026-05-29 guard against the
    "interrupted scrape mis-classifies older posts' media as orphans"
    failure mode. Sort + reid always runs (always safe); the sweep only
    runs when the scrape completed cleanly.
    """

    def test_sweep_orphans_false_preserves_unreferenced_files(self, sandbox):
        """The regression test for the 2026-05-29 incident: an interrupted
        scrape's TSV contains only the rows that got re-pulled. The on-disk
        media files for older, un-re-pulled posts look like orphans relative
        to that partial TSV. With sweep_orphans=False, they MUST stay."""
        tsv_path, media_dir, target = sandbox

        # Simulate the post-incident state: 2 rows in the partial TSV,
        # 5 files on disk (the missing 3 represent un-re-pulled older posts
        # whose media files should NOT be swept).
        for sc in ("SC_old1", "SC_old2", "SC_old3"):
            (media_dir / f"{target}_{sc}.jpg").write_bytes(b"older post - must not be swept")
        (media_dir / f"{target}_SC_new1.jpg").write_bytes(b"newly re-pulled")
        (media_dir / f"{target}_SC_new2.jpg").write_bytes(b"newly re-pulled")

        rows = [
            _row(1, "2026-03-01T00:00:00+0000", _media_url(media_dir, target, "SC_new1"), shortcode="SC_new1"),
            _row(2, "2026-03-02T00:00:00+0000", _media_url(media_dir, target, "SC_new2"), shortcode="SC_new2"),
        ]
        _write_tsv(tsv_path, rows)

        resort_tsv_and_sweep_media(str(tsv_path), target, str(media_dir), sweep_orphans=False)

        # All 5 files survive — the 3 "older" ones are preserved despite
        # not being in the TSV.
        survivors = sorted(p.name for p in media_dir.iterdir())
        assert f"{target}_SC_old1.jpg" in survivors
        assert f"{target}_SC_old2.jpg" in survivors
        assert f"{target}_SC_old3.jpg" in survivors
        assert f"{target}_SC_new1.jpg" in survivors
        assert f"{target}_SC_new2.jpg" in survivors

    def test_sweep_orphans_false_still_sorts_and_reids_rows(self, sandbox):
        """The sweep guard MUST NOT block the sort + reid step — partial
        scrapes still benefit from canonical row ordering."""
        tsv_path, media_dir, target = sandbox
        (media_dir / f"{target}_SC1.jpg").write_bytes(b"a")
        (media_dir / f"{target}_SC2.jpg").write_bytes(b"b")

        rows = [
            _row(1, "2026-03-15T00:00:00+0000", _media_url(media_dir, target, "SC1"), shortcode="SC1"),
            _row(2, "2026-02-15T00:00:00+0000", _media_url(media_dir, target, "SC2"), shortcode="SC2"),
        ]
        _write_tsv(tsv_path, rows)

        resort_tsv_and_sweep_media(str(tsv_path), target, str(media_dir), sweep_orphans=False)

        result = _read_tsv(tsv_path)
        # Sort + reid still happened — even though the run was interrupted.
        assert [r["timestamp"] for r in result] == [
            "2026-02-15T00:00:00+0000",
            "2026-03-15T00:00:00+0000",
        ]
        assert [r["id"] for r in result] == ["1", "2"]

    def test_sweep_orphans_true_still_works_for_clean_runs(self, sandbox):
        """The default behavior must be unchanged — clean scrapes get their
        orphan files swept as before."""
        tsv_path, media_dir, target = sandbox
        (media_dir / f"{target}_SC1.jpg").write_bytes(b"keep")
        (media_dir / f"{target}_orphan.mp4").write_bytes(b"orphan")

        rows = [_row(1, "2026-01-01T00:00:00+0000", _media_url(media_dir, target, "SC1"), shortcode="SC1")]
        _write_tsv(tsv_path, rows)

        # Explicit default — clean run, sweep allowed
        resort_tsv_and_sweep_media(str(tsv_path), target, str(media_dir), sweep_orphans=True)

        assert (media_dir / f"{target}_SC1.jpg").exists()
        assert not (media_dir / f"{target}_orphan.mp4").exists()


class TestPruneScrapeLogs:
    def _make_log(self, log_dir: Path, name: str, age_offset: int) -> Path:
        """Create a log file with mtime = now + age_offset (negative for older)."""
        path = log_dir / name
        path.write_text("...")
        ts = time.time() + age_offset
        os.utime(path, (ts, ts))
        return path

    def test_no_logs_no_op(self, tmp_path):
        """Empty directory: function returns without error."""
        prune_scrape_logs("anyone", str(tmp_path))

    def test_fewer_than_keep_no_op(self, tmp_path):
        """3 logs with keep=5: nothing deleted (under the threshold)."""
        for i in range(3):
            self._make_log(tmp_path, f"scrape-foo-2026010{i}.log", age_offset=-i)
        prune_scrape_logs("foo", str(tmp_path), keep=5)
        assert sorted(p.name for p in tmp_path.iterdir()) == [
            "scrape-foo-20260100.log",
            "scrape-foo-20260101.log",
            "scrape-foo-20260102.log",
        ]

    def test_more_than_keep_deletes_oldest(self, tmp_path):
        """6 logs with keep=5: deletes 2 oldest, keeps 4 newest (current run's
        log will bring total to 5 again)."""
        for i in range(6):
            self._make_log(tmp_path, f"scrape-foo-day{i}.log", age_offset=-(5 - i) * 86400)
        prune_scrape_logs("foo", str(tmp_path), keep=5)
        remaining = sorted(p.name for p in tmp_path.iterdir())
        assert remaining == ["scrape-foo-day2.log", "scrape-foo-day3.log",
                              "scrape-foo-day4.log", "scrape-foo-day5.log"]

    def test_only_touches_matching_target(self, tmp_path):
        """A scrape for target 'foo' must not delete 'bar's logs even if
        bar has many old ones."""
        for i in range(6):
            self._make_log(tmp_path, f"scrape-foo-{i}.log", age_offset=-i * 100)
            self._make_log(tmp_path, f"scrape-bar-{i}.log", age_offset=-i * 100)
        prune_scrape_logs("foo", str(tmp_path), keep=5)
        remaining = sorted(p.name for p in tmp_path.iterdir())
        bar_logs = [n for n in remaining if "bar" in n]
        foo_logs = [n for n in remaining if "foo" in n]
        assert len(bar_logs) == 6
        assert len(foo_logs) == 4

    def test_target_prefix_boundary(self, tmp_path):
        """'foo' must not match 'foobar' — the trailing `-` after the target
        name in `scrape-<target>-*` enforces the boundary."""
        self._make_log(tmp_path, "scrape-foo-1.log", age_offset=-1)
        for i in range(6):
            self._make_log(tmp_path, f"scrape-foobar-{i}.log", age_offset=-(i + 10))
        prune_scrape_logs("foo", str(tmp_path), keep=5)
        foobar_logs = [p.name for p in tmp_path.iterdir() if p.name.startswith("scrape-foobar-")]
        assert len(foobar_logs) == 6

    def test_keeps_newest_4_by_mtime(self, tmp_path):
        """With keep=5 and 10 logs of varying ages, the 4 newest by mtime
        survive (the current run's log brings total to 5)."""
        names = [f"scrape-foo-{i}.log" for i in range(10)]
        for i, name in enumerate(names):
            self._make_log(tmp_path, name, age_offset=-(9 - i) * 60)
        prune_scrape_logs("foo", str(tmp_path), keep=5)
        remaining = sorted(p.name for p in tmp_path.iterdir())
        assert remaining == ["scrape-foo-6.log", "scrape-foo-7.log",
                              "scrape-foo-8.log", "scrape-foo-9.log"]


class TestExtractCityHeuristic:
    """The city-extraction heuristic used by the no-inference fallback path
    to copy the prior post's CITY (not its venue) into a blank-location row.
    """

    def test_three_segment_canonical_venue_city_country(self):
        assert extract_city_heuristic("Sistine Chapel, Vatican City, Italy") == "Vatican City"

    def test_three_segment_neighborhood_city_country(self):
        assert extract_city_heuristic("Chiado, Lisbon, Portugal") == "Lisbon"

    def test_four_segments_drops_first_keeps_third(self):
        """Four-segment 'Venue, Neighborhood, City, Country' → 'City'."""
        assert extract_city_heuristic("Hudson River, New York Harbor, New York, USA") == "New York"

    def test_two_segments_city_country_returns_city(self):
        assert extract_city_heuristic("Lisbon, Portugal") == "Lisbon"

    def test_single_segment_returns_as_is(self):
        """Bare strings (no commas) come back unchanged — sometimes geo-tags
        are just 'Costco' or a place name. Better than blanking."""
        assert extract_city_heuristic("Costco") == "Costco"

    def test_empty_string_returns_empty(self):
        assert extract_city_heuristic("") == ""

    def test_whitespace_only_returns_empty(self):
        assert extract_city_heuristic("   ") == ""

    def test_strips_whitespace_around_segments(self):
        assert extract_city_heuristic("Pike Place Market,  Seattle , United States") == "Seattle"

    def test_us_city_state_country_resolves_to_state_documented_limitation(self):
        """Known limitation: 'Seattle, Washington, USA' resolves to 'Washington'
        because the heuristic can't distinguish 'City, State, Country' from
        'Venue, City, Country'. Documented in the helper's docstring; the
        fallback is still a general-area marker, just at state level."""
        assert extract_city_heuristic("Seattle, Washington, USA") == "Washington"
