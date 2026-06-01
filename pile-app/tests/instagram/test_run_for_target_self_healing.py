"""Integration tests for `run_for_target`'s self-healing failure paths.

Mocks `iter_new_media`, `resolve_target_user_id`, `canonicalize_tagged_location`,
and `download_media` so the full pipeline executes end-to-end without network
or LLM dependencies. Asserts:

  - On mid-stream `FetchInterruptedError`: snapshot rollback restores the
    pre-scrape TSV + deletes new media files; `scrape-failures.jsonl`
    appends a structured record with `failure_type="fetch_interrupted"`.
  - On mid-stream `InferenceHardBlockError`: same rollback semantics;
    `failure_type="inference_hard_block"`; operator_hint mentions
    `ANTHROPIC_API_KEY`.
  - On generic unexpected exception: same rollback semantics;
    `failure_type="unexpected_error"`; record includes a traceback.
  - On clean completion: the snapshot file is committed (deleted) and no
    failure record is written.
  - On detection of a leftover `.snapshot` from a previously-killed run:
    auto-rollback happens at the start of the next scrape, logged via a
    `leftover_snapshot_recovered` failure record.
"""

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import common.pile
import instagram.pipeline
from common.anti_throttle import RATE_PRESETS
from common.inference import InferenceHardBlockError
from common.pile import TSV_COLUMNS
from instagram.pipeline import FetchInterruptedError, run_for_target


# The aggressive preset has zero delays, so tests run fast without
# touching `jittered_sleep` directly. media_delay=(0,0) makes the
# per-post sleep a no-op.
AGGRESSIVE_RATE = RATE_PRESETS["aggressive"]


def _existing_row(shortcode: str, timestamp: str, local_id: int = 1) -> dict:
    return {
        "id": str(local_id), "instagram_id": f"pk-{shortcode}", "shortcode": shortcode,
        "tag_verbatim": "Old Tag", "lat_verbatim": "10", "lng_verbatim": "20",
        "media_url": f"pile/media/instagram/acct_{shortcode}.jpg",
        "caption": "old", "timestamp": timestamp,
        "location": "Old Place", "lat": "10", "lng": "20", "region": "ABC",
        "reasoning": "", "deleted_upstream": "", "deleted_upstream_at": "",
    }


def _make_media(shortcode, pk, taken_at, tagged_name="Place", tagged_lat=1.0, tagged_lng=2.0):
    """instagrapi-shaped fake Media with a populated Location (tagged path)."""
    location = SimpleNamespace(name=tagged_name, lat=tagged_lat, lng=tagged_lng)
    return SimpleNamespace(
        pk=pk, code=shortcode, caption_text="cap",
        taken_at=taken_at, media_type=1,
        thumbnail_url=f"https://cdn.example/{shortcode}.jpg",
        video_url="", resources=None, location=location,
    )


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Pre-populated sandbox: 2 existing rows, 2 existing media files,
    APP_ROOT pointed at tmp_path so `normalize_media_url_for_tsv` produces
    sensible relative paths for the new row."""
    monkeypatch.setattr(common.pile, "APP_ROOT", tmp_path)

    pile_dir = tmp_path / "pile"
    media_dir = pile_dir / "media" / "instagram"
    log_dir = tmp_path / "logs"
    pile_dir.mkdir(parents=True)
    media_dir.mkdir(parents=True)
    log_dir.mkdir(parents=True)

    target = "acct"
    output_path = pile_dir / f"posts.{target}.local.tsv"

    pre_rows = [
        _existing_row("SC_existing1", "2024-01-01T00:00:00+0000", local_id=1),
        _existing_row("SC_existing2", "2024-01-02T00:00:00+0000", local_id=2),
    ]
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TSV_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(pre_rows)

    for row in pre_rows:
        (media_dir / f"{target}_{row['shortcode']}.jpg").write_bytes(b"old media")

    return {
        "tmp_path": tmp_path,
        "target": target,
        "output_path": output_path,
        "output_template": str(output_path),
        "media_dir": str(media_dir),
        "log_dir": str(log_dir),
        "pre_rows": pre_rows,
        "pre_files": sorted(f.name for f in media_dir.iterdir()),
    }


def _read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _read_failure_records(log_dir: str) -> list[dict]:
    path = Path(log_dir) / "scrape-failures.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _mock_download_media(media_url, target, shortcode, media_type, dir_):
    """Stand-in for download_media that actually writes a file so the
    rollback's media-cleanup pass has something to find + delete."""
    path = os.path.join(dir_, f"{target}_{shortcode}.jpg")
    with open(path, "wb") as f:
        f.write(b"new media")
    return path


def _patch_pipeline_collaborators(monkeypatch, *, iter_factory, canonicalize=None):
    """Wire up the standard mocks for the Instagram pipeline's collaborators."""
    monkeypatch.setattr(instagram.pipeline, "iter_new_media", iter_factory)
    monkeypatch.setattr(instagram.pipeline, "download_media", _mock_download_media)
    monkeypatch.setattr(instagram.pipeline, "resolve_target_user_id", lambda cl, t: (12345, 4))
    if canonicalize is None:
        canonicalize = MagicMock(return_value=("Canonical", "1.0", "2.0", "XYZ", ""))
    monkeypatch.setattr(instagram.pipeline, "canonicalize_tagged_location", canonicalize)


# ---------------------------------------------------------------------------
# Test 1 — Mid-stream FetchInterruptedError → rollback + failure record
# ---------------------------------------------------------------------------

def test_fetch_interrupted_mid_stream_rolls_back_pile(sandbox, monkeypatch):
    """A FetchInterruptedError raised mid-iteration triggers snapshot rollback —
    pre-scrape TSV restored, new media files deleted, scrape-failures.jsonl
    gets a fetch_interrupted record."""

    def iter_factory(*args, **kwargs):
        yield _make_media("SC_new1", 1001, datetime(2024, 1, 3, tzinfo=timezone.utc))
        yield _make_media("SC_new2", 1002, datetime(2024, 1, 4, tzinfo=timezone.utc))
        raise FetchInterruptedError("page 2 hard-blocked: simulated DNS failure")

    _patch_pipeline_collaborators(monkeypatch, iter_factory=iter_factory)

    run_for_target(
        cl=MagicMock(),
        target=sandbox["target"],
        output_template=sandbox["output_template"],
        media_dir=sandbox["media_dir"],
        rate_config=AGGRESSIVE_RATE,
        log_dir=sandbox["log_dir"],
    )

    rows_after = _read_rows(sandbox["output_path"])
    assert [r["shortcode"] for r in rows_after] == ["SC_existing1", "SC_existing2"]

    files_after = sorted(f.name for f in Path(sandbox["media_dir"]).iterdir())
    assert files_after == sandbox["pre_files"]

    records = _read_failure_records(sandbox["log_dir"])
    assert len(records) == 1
    r = records[0]
    assert r["service"] == "instagram"
    assert r["target"] == "acct"
    assert r["failure_type"] == "fetch_interrupted"
    assert "simulated DNS failure" in r["failure_detail"]
    assert r["rows_discarded"] == 2
    assert r["files_deleted"] == 2
    assert "connectivity" in r["operator_hint"].lower() or "instagram" in r["operator_hint"].lower()
    assert "logged_at" in r

    assert not os.path.exists(str(sandbox["output_path"]) + ".snapshot")


# ---------------------------------------------------------------------------
# Test 2 — Mid-stream InferenceHardBlockError → rollback + failure record
# ---------------------------------------------------------------------------

def test_inference_hard_block_mid_stream_rolls_back_pile(sandbox, monkeypatch):
    """When canonicalize_tagged_location raises InferenceHardBlockError on the
    SECOND post, the first post has already been written to TSV and its media
    downloaded. Rollback restores both."""

    def iter_factory(*args, **kwargs):
        yield _make_media("SC_new1", 1001, datetime(2024, 1, 3, tzinfo=timezone.utc))
        yield _make_media("SC_new2", 1002, datetime(2024, 1, 4, tzinfo=timezone.utc))

    canonicalize_mock = MagicMock(side_effect=[
        ("Canonical 1", "1.0", "2.0", "XYZ", ""),
        InferenceHardBlockError("RateLimitError: anthropic quota exhausted"),
    ])
    _patch_pipeline_collaborators(monkeypatch, iter_factory=iter_factory, canonicalize=canonicalize_mock)

    run_for_target(
        cl=MagicMock(),
        target=sandbox["target"],
        output_template=sandbox["output_template"],
        media_dir=sandbox["media_dir"],
        rate_config=AGGRESSIVE_RATE,
        log_dir=sandbox["log_dir"],
    )

    rows_after = _read_rows(sandbox["output_path"])
    assert [r["shortcode"] for r in rows_after] == ["SC_existing1", "SC_existing2"]

    files_after = sorted(f.name for f in Path(sandbox["media_dir"]).iterdir())
    assert files_after == sandbox["pre_files"]

    records = _read_failure_records(sandbox["log_dir"])
    assert len(records) == 1
    r = records[0]
    assert r["failure_type"] == "inference_hard_block"
    assert "RateLimitError" in r["failure_detail"]
    assert "ANTHROPIC_API_KEY" in r["operator_hint"]
    assert r["rows_discarded"] == 1
    # download_media runs BEFORE canonicalize_tagged_location in process_media,
    # so BOTH new media files were downloaded before the second post's
    # canonicalize raised the hard-block. Both get rolled back.
    assert r["files_deleted"] == 2


# ---------------------------------------------------------------------------
# Test 3 — Generic unexpected exception → rollback + traceback in record
# ---------------------------------------------------------------------------

def test_unexpected_exception_mid_stream_rolls_back_pile_with_traceback(sandbox, monkeypatch):
    """Any exception NOT in the FetchInterruptedError / InferenceHardBlockError
    set hits the catch-all `except Exception` clause. Rollback fires; the
    failure record carries `failure_type=unexpected_error` plus the formatted
    traceback so the admin can diagnose."""

    def iter_factory(*args, **kwargs):
        yield _make_media("SC_new1", 1001, datetime(2024, 1, 3, tzinfo=timezone.utc))
        # The next "fetch" raises something neither FetchInterruptedError nor
        # InferenceHardBlockError — an unexpected condition.
        raise ValueError("simulated unexpected condition in the iter generator")

    _patch_pipeline_collaborators(monkeypatch, iter_factory=iter_factory)

    run_for_target(
        cl=MagicMock(),
        target=sandbox["target"],
        output_template=sandbox["output_template"],
        media_dir=sandbox["media_dir"],
        rate_config=AGGRESSIVE_RATE,
        log_dir=sandbox["log_dir"],
    )

    rows_after = _read_rows(sandbox["output_path"])
    assert [r["shortcode"] for r in rows_after] == ["SC_existing1", "SC_existing2"]

    files_after = sorted(f.name for f in Path(sandbox["media_dir"]).iterdir())
    assert files_after == sandbox["pre_files"]

    records = _read_failure_records(sandbox["log_dir"])
    assert len(records) == 1
    r = records[0]
    assert r["failure_type"] == "unexpected_error"
    assert "ValueError" in r["failure_detail"]
    assert "traceback" in r
    assert "ValueError" in r["traceback"]
    assert "simulated unexpected condition" in r["traceback"]


# ---------------------------------------------------------------------------
# Test 4 — Clean completion → snapshot committed, no failure record
# ---------------------------------------------------------------------------

def test_clean_completion_commits_snapshot_and_writes_no_failure_record(sandbox, monkeypatch):
    """The success path: scrape yields some new posts, all succeed, snapshot
    is committed (file deleted), no failure record."""

    def iter_factory(*args, **kwargs):
        yield _make_media("SC_new1", 1001, datetime(2024, 1, 3, tzinfo=timezone.utc))

    _patch_pipeline_collaborators(monkeypatch, iter_factory=iter_factory)

    run_for_target(
        cl=MagicMock(),
        target=sandbox["target"],
        output_template=sandbox["output_template"],
        media_dir=sandbox["media_dir"],
        rate_config=AGGRESSIVE_RATE,
        log_dir=sandbox["log_dir"],
    )

    rows_after = _read_rows(sandbox["output_path"])
    assert len(rows_after) == 3
    assert sorted(r["shortcode"] for r in rows_after) == ["SC_existing1", "SC_existing2", "SC_new1"]

    assert not os.path.exists(str(sandbox["output_path"]) + ".snapshot")

    records = _read_failure_records(sandbox["log_dir"])
    assert records == []


# ---------------------------------------------------------------------------
# Test 5 — Leftover snapshot from killed run → auto-recovery at start
# ---------------------------------------------------------------------------

def test_leftover_snapshot_triggers_auto_rollback_at_start(sandbox, monkeypatch):
    """Simulate a process being killed mid-scrape: the .snapshot file is left
    behind. The NEXT scrape detects it, auto-rolls-back, logs a
    leftover_snapshot_recovered record, then proceeds with the new scrape."""

    # The "live" TSV has 3 rows — as if a partial scrape wrote an extra row
    # before the process was killed.
    partial_corrupt_rows = sandbox["pre_rows"] + [
        _existing_row("SC_partial", "2024-01-99T00:00:00+0000", local_id=3),
    ]
    with sandbox["output_path"].open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TSV_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(partial_corrupt_rows)

    # The .snapshot file holds the CLEAN pre-scrape state (just the 2 originals).
    snapshot_path = Path(str(sandbox["output_path"]) + ".snapshot")
    with snapshot_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TSV_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(sandbox["pre_rows"])

    # Also: a media file for the partial-corruption row that doesn't belong.
    (Path(sandbox["media_dir"]) / f"{sandbox['target']}_SC_partial.jpg").write_bytes(b"partial work")

    def empty_iter(*args, **kwargs):
        return
        yield  # marks this as a generator

    _patch_pipeline_collaborators(monkeypatch, iter_factory=empty_iter)

    run_for_target(
        cl=MagicMock(),
        target=sandbox["target"],
        output_template=sandbox["output_template"],
        media_dir=sandbox["media_dir"],
        rate_config=AGGRESSIVE_RATE,
        log_dir=sandbox["log_dir"],
    )

    # TSV is back to the 2-row pre-scrape state (recovered from the snapshot).
    rows_after = _read_rows(sandbox["output_path"])
    assert [r["shortcode"] for r in rows_after] == ["SC_existing1", "SC_existing2"]

    # The partial-work media file got swept by the rollback.
    files_after = sorted(f.name for f in Path(sandbox["media_dir"]).iterdir())
    assert files_after == sandbox["pre_files"]

    # The auto-recovery was logged.
    records = _read_failure_records(sandbox["log_dir"])
    assert len(records) == 1
    r = records[0]
    assert r["failure_type"] == "leftover_snapshot_recovered"
    assert r["files_deleted"] == 1

    # Snapshot is gone — current empty scrape committed cleanly.
    assert not os.path.exists(str(sandbox["output_path"]) + ".snapshot")
