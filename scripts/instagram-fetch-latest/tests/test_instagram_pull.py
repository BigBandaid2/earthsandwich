"""Integration smoke test for the Instagram pull pipeline.

Truncates `posts.local.tsv` to row 322, runs `load_posts_tsv.py`, and asserts
that row 323 came back from instagrapi with the Mexico City geo-tag intact.
This is the canonical end-to-end check for FR-016 / FR-019 / FR-020 of
`specs/003-ingestion-pipeline/spec.md`.

What it actually verifies, in order:
  1. instagrapi authenticates (resumed session or fresh login).
  2. `cl.user_medias_paginated_v1` returns posts newer than the TSV cursor.
  3. The post with shortcode `DYFNMcHxKDv` is in the returned set.
  4. The FR-019 tagged-location path fires (Media.location is populated).
  5. Location name is stored verbatim ("Mexico City"), not re-estimated.
  6. Lat/lng match the Instagram-provided coordinates.
  7. Claude's text-only IATA call returns a sensible Mexico City airport code.

Required env (loaded automatically from `.env` via conftest):
  - INSTA_USERNAME, INSTA_PASSWORD
  - ANTHROPIC_API_KEY

Optional env:
  - INSTAGRAPI_SESSION_FILE (default lives next to load_posts_tsv.py)

Side effect: this test rewrites `posts.local.tsv` to drop row 323 each run.
That's intentional — it's how the test guarantees row 323 gets pulled fresh.
"""

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TSV_PATH = PROJECT_ROOT / "posts.local.tsv"
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "instagram-fetch-latest" / "load_posts_tsv.py"

TRUNCATE_TO_ID = 322
EXPECTED_NEW_ID = 323
EXPECTED_SHORTCODE = "DYFNMcHxKDv"
EXPECTED_LOCATION = "Mexico City"
EXPECTED_LAT_PREFIX = "19."
EXPECTED_LNG_PREFIX = "-99."

# IATA codes acceptable for Mexico City. MEX is the legacy main airport
# (Benito Juárez); NLU is the newer Felipe Ángeles. Either is a defensible
# answer from Claude — both serve Mexico City as the nearest international
# airport. Add more if a third option ever shows up legitimately.
ACCEPTABLE_REGIONS = {"MEX", "NLU"}

TSV_COLUMNS = [
    "id", "instagram_id", "shortcode", "media_url", "caption",
    "timestamp", "location", "lat", "lng", "region",
]


def _read_rows() -> list[dict]:
    with TSV_PATH.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _write_rows(rows: list[dict]) -> None:
    with TSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TSV_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _truncate_tsv_to_id(target_id: int) -> None:
    """Drop any TSV rows with id > target_id, in place."""
    rows = _read_rows()
    kept = [r for r in rows if r.get("id") and int(r["id"]) <= target_id]
    _write_rows(kept)


@pytest.mark.integration
def test_instagram_pull_resurrects_mexico_city_row():
    """The end-to-end smoke test.

    Truncates the TSV to id=322 (so id=323 must be re-pulled), runs the
    script, and asserts the new row reflects the explicit "Mexico City"
    geo-tag rather than an inferred Oaxaca-style guess.
    """
    missing = [
        var for var in ("INSTA_USERNAME", "INSTA_PASSWORD", "ANTHROPIC_API_KEY")
        if not os.environ.get(var)
    ]
    if missing:
        pytest.skip(f"missing required env vars: {', '.join(missing)}")

    # Step 1: reset state. Drop row 323 (and anything past it, defensively).
    _truncate_tsv_to_id(TRUNCATE_TO_ID)
    pre_rows = _read_rows()
    assert pre_rows, "TSV is empty after truncation — refusing to test"
    assert pre_rows[-1]["id"] == str(TRUNCATE_TO_ID), (
        f"Truncation produced unexpected last id={pre_rows[-1].get('id')!r} "
        f"(expected {TRUNCATE_TO_ID})"
    )

    # Step 2: run the script. sys.executable points at whichever Python
    # invoked pytest — so under CI this is the venv's Python, no hardcoded
    # path needed.
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )

    if result.returncode != 0:
        pytest.fail(
            f"load_posts_tsv.py exited {result.returncode}.\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

    # Step 3: inspect the row that came back.
    post_rows = _read_rows()
    assert post_rows, "TSV is empty after script run"
    new_row = post_rows[-1]

    failure_context = (
        f"\n--- new row ---\n"
        + "\n".join(f"  {k}: {v!r}" for k, v in new_row.items())
        + f"\n--- script stdout ---\n{result.stdout}"
    )

    assert new_row["id"] == str(EXPECTED_NEW_ID), (
        f"Expected last id={EXPECTED_NEW_ID}; got {new_row.get('id')!r}. "
        f"Either no new post was fetched or pagination drifted." + failure_context
    )
    assert new_row["shortcode"] == EXPECTED_SHORTCODE, (
        f"Expected shortcode {EXPECTED_SHORTCODE}; got {new_row.get('shortcode')!r}. "
        f"Different post was returned." + failure_context
    )

    # FR-019 tagged-path assertions. If any of these fail, the most likely
    # explanation is that the Media.location object wasn't populated and
    # the script fell through to the FR-020 inferred path.
    assert new_row["location"] == EXPECTED_LOCATION, (
        f"Expected location {EXPECTED_LOCATION!r} (verbatim from instagrapi geo-tag); "
        f"got {new_row.get('location')!r}. The FR-019 tagged-location path "
        f"probably didn't fire — verify instagrapi's Media.location handling "
        f"in load_posts_tsv.py." + failure_context
    )
    assert new_row["lat"].startswith(EXPECTED_LAT_PREFIX), (
        f"Expected lat starting {EXPECTED_LAT_PREFIX} (Mexico City); "
        f"got {new_row.get('lat')!r}." + failure_context
    )
    assert new_row["lng"].startswith(EXPECTED_LNG_PREFIX), (
        f"Expected lng starting {EXPECTED_LNG_PREFIX} (Mexico City); "
        f"got {new_row.get('lng')!r}." + failure_context
    )
    assert new_row["region"] in ACCEPTABLE_REGIONS, (
        f"Expected region in {ACCEPTABLE_REGIONS}; got {new_row.get('region')!r}. "
        f"If Claude returned something else legitimate (TLC?), expand "
        f"ACCEPTABLE_REGIONS in this test." + failure_context
    )
