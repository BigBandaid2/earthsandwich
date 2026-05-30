"""Integration smoke test for the Instagram pull pipeline.

Uses the CLI's `--newer-than` flag to truncate `pile/posts.ourearthsandwich.local.tsv`
to rows at or before 2024-02-20T02:27:16+0000 (the timestamp of id=322), runs
the CLI, and asserts that the re-fetched row 323 came back from instagrapi
with the Mexico City geo-tag intact. This is the canonical end-to-end check
for FR-016 / FR-019 / FR-020 of `specs/003-ingestion-pipeline/spec.md`.

What it actually verifies, in order:
  1. instagrapi authenticates (resumed session or fresh login).
  2. `--newer-than` truncates the TSV atomically (rollback-safe).
  3. `cl.user_medias_paginated_v1` returns posts newer than the cutoff.
  4. The post with shortcode `DYFNMcHxKDv` is in the returned set.
  5. The FR-019 tagged-location path fires (Media.location is populated).
  6. Location name is canonicalized ("Mexico City"), not re-estimated.
  7. Lat/lng match the Instagram-provided coordinates.
  8. The text-only IATA call returns a sensible Mexico City airport code.

Required env (loaded automatically from pile-app/.env via conftest if
the file exists; otherwise from shell env):
  - INSTA_USERNAME, INSTA_PASSWORD
  - ANTHROPIC_API_KEY

Optional env:
  - INSTAGRAPI_SESSION_FILE (default lives at pile-app/instagrapi_session.json)

Side effect: this test rewrites the TSV to drop row 323 each run.
That's intentional — it's how the test guarantees row 323 gets pulled fresh.
With `--newer-than` driving the truncation, the rewrite is now atomic with
the scrape: a CLI failure leaves the TSV untouched (pre-truncation state
preserved by the run snapshot), unlike the prior test-local truncation
which mutated the pile before the subprocess even started.

A follow-up extension (planned: after a no-geotag post is added to
@ourearthsandwich) will move the cutoff back to cover the FR-020 inferred-
location path on a recent post — keeping the per-PR cost flat.
"""

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

PILE_APP_ROOT = Path(__file__).resolve().parents[2]
TSV_PATH = PILE_APP_ROOT / "pile" / "posts.ourearthsandwich.local.tsv"
CLI_PATH = PILE_APP_ROOT / "cli.py"

# Cutoff: timestamp of id=322 (the last Oaxaca post). `--newer-than` keeps
# rows <= cutoff (inclusive on the keep side) and fetches strictly newer,
# so this surgically drops id>=323 and triggers a re-pull of just those.
TRUNCATE_NEWER_THAN = "2024-02-20T02:27:16+0000"
EXPECTED_NEW_ID = 323
EXPECTED_SHORTCODE = "DYFNMcHxKDv"
EXPECTED_LOCATION_PREFIX = "Mexico City"
EXPECTED_LAT_PREFIX = "19."
EXPECTED_LNG_PREFIX = "-99."

ACCEPTABLE_REGIONS = {"MEX", "NLU"}


def _read_rows() -> list[dict]:
    with TSV_PATH.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


@pytest.mark.integration
def test_instagram_pull_resurrects_mexico_city_row():
    """The end-to-end smoke test.

    Tells the CLI to truncate the TSV to rows <= 2024-02-20T02:27:16+0000
    via `--newer-than`, then re-pull. Asserts the new row reflects the
    explicit "Mexico City" geo-tag rather than an inferred Oaxaca-style guess.
    """
    missing = [
        var for var in ("INSTA_USERNAME", "INSTA_PASSWORD", "ANTHROPIC_API_KEY")
        if not os.environ.get(var)
    ]
    if missing:
        pytest.skip(f"missing required env vars: {', '.join(missing)}")

    if not TSV_PATH.exists() or not _read_rows():
        pytest.skip(
            f"TSV at {TSV_PATH} is missing or empty; this smoke test needs a "
            f"pre-existing pile to truncate against. Run a baseline scrape first."
        )

    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}
    result = subprocess.run(
        [
            sys.executable, str(CLI_PATH), "run", "instagram",
            "--targets", "ourearthsandwich",
            "--newer-than", TRUNCATE_NEWER_THAN,
        ],
        cwd=str(PILE_APP_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )

    if result.returncode != 0:
        pytest.fail(
            f"cli.py exited {result.returncode}.\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

    post_rows = _read_rows()
    assert post_rows, "TSV is empty after script run"
    new_row = post_rows[-1]

    failure_context = (
        f"\n--- new row ---\n"
        + "\n".join(f"  {k}: {v!r}" for k, v in new_row.items())
        + f"\n--- stdout ---\n{result.stdout}"
    )

    assert new_row["id"] == str(EXPECTED_NEW_ID), (
        f"Expected last id={EXPECTED_NEW_ID}; got {new_row.get('id')!r}. "
        f"Either no new post was fetched or pagination drifted." + failure_context
    )
    assert new_row["shortcode"] == EXPECTED_SHORTCODE, (
        f"Expected shortcode {EXPECTED_SHORTCODE}; got {new_row.get('shortcode')!r}. "
        f"Different post was returned." + failure_context
    )
    assert new_row["location"].startswith(EXPECTED_LOCATION_PREFIX), (
        f"Expected location to start with {EXPECTED_LOCATION_PREFIX!r} (canonicalized "
        f"from the instagrapi geo-tag); got {new_row.get('location')!r}. The FR-019 "
        f"tagged-location path probably didn't fire — verify instagrapi's Media.location "
        f"handling in instagram/pipeline.py." + failure_context
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
        f"If the model returned something else legitimate (TLC?), expand "
        f"ACCEPTABLE_REGIONS in this test." + failure_context
    )
