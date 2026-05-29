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
    "media_url",
    "caption",
    "timestamp",
    "location",
    "lat",
    "lng",
    "region",
    "reasoning",
]


def read_tsv_rows(tsv_path: str) -> list[dict]:
    """Read all rows from the TSV file."""
    if not os.path.exists(tsv_path):
        return []
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def download_media(media_url: str, target: str, local_id: int, media_type: str, media_dir: str) -> str:
    """Download media from the Instagram CDN and save to media_dir/<target>_<local_id>.jpg or .mp4.

    The target prefix keeps filenames unique across accounts when multiple
    target TSVs share one media directory (each TSV has its own id sequence
    starting at 1, so the raw id alone would collide).

    Returns the local relative path.
    """
    ext = "mp4" if media_type == "VIDEO" else "jpg"
    local_path = os.path.join(media_dir, f"{target}_{local_id}.{ext}")

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


def resort_tsv_and_rename_media(path: str, target: str, media_dir: str) -> None:
    """Restore canonical oldest-first row order after a streaming scrape.

    Streaming writes rows in pagination order (newest-page first, oldest-of-
    page first within each page). After the scrape, we want the file to match
    the original convention: row 1 = oldest, row N = newest, ids sequential.

    Steps:
      1. Read all rows, sort by timestamp ASC.
      2. Reassign ids 1..N.
      3. Rename media files whose id changed so `media_url` stays consistent
         with the on-disk filename. Uses a two-pass `.tmp` suffix rename so
         id swaps (e.g., file A→2 while file B→A's old id) don't collide.
      4. Write the sorted, re-id'd rows back to the TSV.
      5. Sweep orphan media files in `media_dir` matching `<target>_*` that
         aren't referenced by any TSV row — e.g., a `.mp4` left over from a
         prior scrape where that id was a video but this scrape made it an
         image. Cross-target safe: only files matching THIS target's prefix
         are touched.

    Safe on partial files: if a row's media file is missing (download failed
    earlier), the rename is skipped for that row but the id is still updated.
    """
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        cols = reader.fieldnames
        rows = list(reader)
    if not rows:
        return

    rows.sort(key=lambda r: r.get("timestamp", ""))

    rename_plan: list[tuple[str, str]] = []  # (old_abs, new_abs)
    app_root_str = str(APP_ROOT)
    for new_id, row in enumerate(rows, start=1):
        try:
            old_id = int(row.get("id", 0))
        except (TypeError, ValueError):
            old_id = 0

        old_media = row.get("media_url", "")
        if old_media and old_id != new_id:
            old_abs = os.path.join(app_root_str, *old_media.split(posixpath.sep))
            if os.path.exists(old_abs):
                ext = os.path.splitext(old_abs)[1].lstrip(".")
                old_dir_rel = posixpath.dirname(old_media)
                new_media_rel = posixpath.join(old_dir_rel, f"{target}_{new_id}.{ext}")
                new_abs = os.path.join(app_root_str, *new_media_rel.split(posixpath.sep))
                rename_plan.append((old_abs, new_abs))
                row["media_url"] = new_media_rel
        row["id"] = str(new_id)

    # Two-pass rename: stage every source to a `.rename-tmp` suffix first so
    # swaps (file at id=2 → 5 while file at id=5 → 2) don't clobber. Then
    # move each `.rename-tmp` to its final name.
    for old, _ in rename_plan:
        try:
            os.rename(old, old + ".rename-tmp")
        except OSError as exc:
            print(f"  ! failed to stage rename of {old}: {exc}")
    for old, new in rename_plan:
        staged = old + ".rename-tmp"
        if os.path.exists(staged):
            os.makedirs(os.path.dirname(new), exist_ok=True)
            try:
                os.replace(staged, new)
            except OSError as exc:
                print(f"  ! failed to finalize rename {staged} → {new}: {exc}")

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
