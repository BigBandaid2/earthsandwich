"""Pile I/O: TSV read/write, media download, sort+reid post-pass, orphan sweep.

The pile (`pile-app/pile/`) is the App's downstream surface — see FR-102,
FR-103, and the `contracts/pile-artifact-instagram.md` contract for the
column shape this module produces.

Path convention:
  - TSV files live at `pile-app/pile/posts.<target>.local.tsv`
  - Media files live at `pile-app/pile/media/instagram/<target>_<id>.<ext>`
  - All `media_url` column values are relative to APP_ROOT in POSIX form,
    e.g. `pile/media/instagram/ourearthsandwich_42.jpg`.
"""

from __future__ import annotations

import csv
import os
import posixpath
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

from common import APP_ROOT

PILE_DIR = APP_ROOT / "pile"
MEDIA_DIR = PILE_DIR / "media" / "instagram"
DEFAULT_OUTPUT_TEMPLATE = str(PILE_DIR / "posts.{target}.local.tsv")
DEFAULT_MEDIA_DIR = str(MEDIA_DIR)
RECENT_LOCATION_COUNT = 5

TSV_COLUMNS = [
    "id",
    "instagram_id",
    "shortcode",
    "tag_verbatim",          # FR-105 / Cardinal Rule #4 — tagged-path input (raw instagrapi Media.location.name)
    "lat_verbatim",          # FR-105 — raw instagrapi Media.location.lat (matches `lat` today; column is forward-compatible if canonicalization later snaps lat/lng)
    "lng_verbatim",          # FR-105 — raw instagrapi Media.location.lng
    "media_url",
    "caption",
    "timestamp",
    "location",
    "lat",
    "lng",
    "region",
    "reasoning",
    "deleted_upstream",      # FR-106 — set-once tombstone; "true" or empty
    "deleted_upstream_at",   # FR-106 — ISO 8601 UTC of first detection; never overwritten
]


def read_tsv_rows(tsv_path: str) -> list[dict]:
    """Read all rows from the TSV file."""
    if not os.path.exists(tsv_path):
        return []
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def download_media(media_url: str, target: str, shortcode: str, media_type: str, media_dir: str) -> str:
    """Download media from the Instagram CDN and save to media_dir/<target>_<shortcode>.jpg or .mp4.

    The shortcode is the canonical Instagram post identifier (FR-022), so the
    on-disk filename is stable across reruns and the sort+reid post-pass no
    longer has to rename media files. The target prefix keeps filenames
    unique across accounts when multiple target TSVs share one media dir.

    Returns the local relative path.
    """
    ext = "mp4" if media_type == "VIDEO" else "jpg"
    local_path = os.path.join(media_dir, f"{target}_{shortcode}.{ext}")

    resp = requests.get(media_url, timeout=60, stream=True)
    resp.raise_for_status()

    os.makedirs(media_dir, exist_ok=True)
    with open(local_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return os.path.normpath(local_path)


def normalize_media_url_for_tsv(local_media_path: str) -> str:
    """Strip the APP_ROOT prefix and normalize to POSIX separators.

    The TSV's `media_url` column is APP_ROOT-relative POSIX so the pile is
    self-contained per FR-110 (movable to a fresh repo without path drift).
    """
    if not local_media_path:
        return ""
    app_root_str = str(APP_ROOT)
    if local_media_path.startswith(app_root_str):
        local_media_path = os.path.relpath(local_media_path, app_root_str)
    return local_media_path.replace(os.sep, posixpath.sep)


def resort_tsv_and_sweep_media(path: str, target: str, media_dir: str) -> None:
    """Restore canonical oldest-first row order after a streaming scrape, then
    sweep orphan media files.

    Streaming writes rows in pagination order (newest-page first, oldest-of-
    page first within each page). After the scrape, we want the file to match
    the original convention: row 1 = oldest, row N = newest, ids sequential.

    Steps:
      1. Read all rows, sort by timestamp ASC.
      2. Reassign local `id` values 1..N. Media filenames are now keyed on
         `shortcode` (FR-022 + T225), so no media-file rename is needed —
         only the in-TSV `id` column changes.
      3. Write the sorted, re-id'd rows back to the TSV.
      4. Sweep orphan media files in `media_dir` matching `<target>_*` that
         aren't referenced by any TSV row — e.g., a `.mp4` left over from a
         prior scrape where that shortcode is now a different media type.
         Cross-target safe: only files matching THIS target's prefix are touched.
    """
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        cols = reader.fieldnames
        rows = list(reader)
    if not rows:
        return

    rows.sort(key=lambda r: r.get("timestamp", ""))

    for new_id, row in enumerate(rows, start=1):
        row["id"] = str(new_id)

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    # Orphan sweep: any file in media_dir matching this target's prefix that
    # isn't referenced by a row is a leftover from a prior scrape. Safe to
    # delete. Path comparison uses absolute + normcase'd paths on both sides
    # so a relative media_dir or a relative media_url doesn't cause a phantom
    # mismatch (the bug that previously wiped 323 real files because the
    # `referenced` set had absolute paths and the scan produced relative ones).
    app_root_str = str(APP_ROOT)

    def _abs_norm(p: str) -> str:
        return os.path.normcase(os.path.normpath(os.path.abspath(p)))

    if os.path.isdir(media_dir):
        referenced: set[str] = set()
        for row in rows:
            media_url = row.get("media_url", "")
            if media_url:
                referenced.add(_abs_norm(
                    os.path.join(app_root_str, *media_url.split(posixpath.sep))
                ))

        prefix = f"{target}_"
        swept: list[str] = []
        for entry in os.listdir(media_dir):
            if not entry.startswith(prefix):
                continue
            full = _abs_norm(os.path.join(media_dir, entry))
            if full in referenced:
                continue
            try:
                os.remove(full)
                swept.append(entry)
            except OSError as exc:
                print(f"  ! could not remove orphan {entry}: {exc}")
        if swept:
            sample = ", ".join(swept[:5])
            more = f" (+{len(swept) - 5} more)" if len(swept) > 5 else ""
            print(f"  swept {len(swept)} orphan media file(s): {sample}{more}")


def apply_tombstones(path: str, tombstone_shortcodes: set[str]) -> int:
    """Mark the given shortcodes' rows with `deleted_upstream=true` and
    `deleted_upstream_at=<now>` (FR-106). Set-once-monotonic: rows already
    tombstoned are skipped (their original detection timestamp is preserved).
    Returns the count of rows actually updated.
    """
    if not tombstone_shortcodes:
        return 0
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        cols = reader.fieldnames
        rows = list(reader)
    if not rows:
        return 0
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    updated = 0
    for row in rows:
        sc = row.get("shortcode", "")
        if sc and sc in tombstone_shortcodes and not row.get("deleted_upstream"):
            row["deleted_upstream"] = "true"
            row["deleted_upstream_at"] = now_iso
            updated += 1
    if updated == 0:
        return 0
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    return updated
