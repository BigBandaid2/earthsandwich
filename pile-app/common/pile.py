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
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

from common import APP_ROOT

PILE_DIR = APP_ROOT / "pile"
MEDIA_DIR = PILE_DIR / "media" / "instagram"
DEFAULT_OUTPUT_TEMPLATE = str(PILE_DIR / "posts.{target}.local.tsv")
DEFAULT_SUBSTACK_OUTPUT_TEMPLATE = str(PILE_DIR / "articles.{publication}.local.tsv")
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

# Substack pile artifact (data-model.md § "Pile artifact: Substack TSV",
# contracts/pile-artifact-substack.md). 9 flat string columns; no media,
# no verbatim-input columns (Substack v1 has no LLM inference step).
SUBSTACK_TSV_COLUMNS = [
    "id",                    # post-pass sort+reid; sequential 1..N after sort by published_at ASC
    "substack_id",           # FR-024 — RSS <guid>; canonical dedup key
    "link",                  # RSS <link>; retained for traceability (FR-024)
    "title",                 # RSS <title>
    "subtitle",              # RSS <description> (the article deck); optional
    "body",                  # RSS <content:encoded>; full HTML, never truncated
    "published_at",          # RSS <pubDate>, normalized to ISO 8601 UTC
    "deleted_upstream",      # FR-106 — set-once tombstone; "true" or empty
    "deleted_upstream_at",   # FR-106 — ISO 8601 UTC of first detection; never overwritten
]

# Columns where embedded newlines are preserved (body carries HTML structure).
# Everywhere else, newlines collapse to a space so each row stays single-line.
_SUBSTACK_NEWLINE_OK = frozenset({"body"})


def _tsv_clean(column: str, value: object) -> str:
    """Make a value safe for a TAB-delimited cell (Substack contract §2).

    Tabs become single spaces in every column. Newlines collapse to spaces
    too, EXCEPT in `body`, where HTML structure is preserved (the csv writer
    quotes the field so the embedded newlines round-trip). This keeps non-body
    cells single-line and greppable while honouring the "no body truncation /
    structure preserved" guarantee.
    """
    s = "" if value is None else str(value)
    s = s.replace("\t", " ")
    if column not in _SUBSTACK_NEWLINE_OK:
        s = s.replace("\r", " ").replace("\n", " ")
    return s


def write_substack_tsv(path: str, rows: list[dict]) -> None:
    """Write the full Substack pile for one publication, atomically.

    Reuses the Instagram post-pass shape: sort by `published_at` ASC, re-number
    local `id` 1..N, then write header + rows. Tabs/newlines are escaped per
    `_tsv_clean`. The write goes to a temp file and is swapped in with
    `os.replace`, so a crash mid-write leaves the prior pile intact — the
    "atomicity of a row" guarantee from the contract, achieved here by building
    the whole file in memory first (the RSS feed is bounded, unlike paginated
    Instagram scrapes, so no streaming snapshot is needed).
    """
    ordered = sorted(rows, key=lambda r: r.get("published_at", ""))
    for new_id, row in enumerate(ordered, start=1):
        row["id"] = str(new_id)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    # lineterminator="\n" honours the contract's LF-newline requirement; the
    # csv writer still quotes the body field (which contains newlines) so those
    # are preserved inside the quoted cell and round-trip on read.
    with open(tmp_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=SUBSTACK_TSV_COLUMNS, delimiter="\t",
            lineterminator="\n", extrasaction="ignore",
        )
        writer.writeheader()
        for row in ordered:
            writer.writerow({c: _tsv_clean(c, row.get(c, "")) for c in SUBSTACK_TSV_COLUMNS})
    os.replace(tmp_path, path)


def read_tsv_rows(tsv_path: str) -> list[dict]:
    """Read all rows from the TSV file."""
    if not os.path.exists(tsv_path):
        return []
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def truncate_tsv_to_timestamp(tsv_path: str, cutoff_ts: int) -> int:
    """Drop rows with timestamp > cutoff_ts from the TSV; keep rows <= cutoff_ts.

    `cutoff_ts` is a Unix timestamp (int). The caller is responsible for
    parsing the operator's ISO-format input via the same parser the rest of
    the pipeline uses (`parse_unix_timestamp`) so that comparison is numeric
    and immune to ISO format variations (date-only vs full, `+0000` vs
    `+00:00`, etc.).

    Returns the number of rows removed (0 if the file doesn't exist or no
    rows match). Does NOT touch media files — orphan-media cleanup for the
    removed rows happens in the success-path `resort_tsv_and_sweep_media`
    call, so a mid-run failure can still be cleanly rolled back via the
    snapshot (which captures pre-truncation TSV + media file set).

    Used by the `--newer-than` CLI flag to set up integration-test pile
    sizes in a single command, replacing the manual "truncate then re-run"
    pattern.
    """
    if not os.path.exists(tsv_path):
        return 0
    with open(tsv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        cols = reader.fieldnames or TSV_COLUMNS
        rows = list(reader)

    def _row_ts(row: dict) -> Optional[int]:
        ts_str = row.get("timestamp", "")
        if not ts_str:
            return None
        try:
            ts_str = ts_str.strip().replace(" ", "T")
            if ts_str.endswith("+00"):
                ts_str += ":00"
            return int(datetime.fromisoformat(ts_str).timestamp())
        except ValueError:
            return None

    kept = [r for r in rows if (_row_ts(r) is not None and _row_ts(r) <= cutoff_ts)]
    removed = len(rows) - len(kept)
    if removed == 0:
        return 0
    with open(tsv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        writer.writeheader()
        writer.writerows(kept)
    return removed


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


def resort_tsv_and_sweep_media(
    path: str,
    target: str,
    media_dir: str,
    sweep_orphans: bool = True,
) -> None:
    """Restore canonical oldest-first row order after a streaming scrape, then
    (optionally) sweep orphan media files.

    Streaming writes rows in pagination order (newest-page first, oldest-of-
    page first within each page). After the scrape, we want the file to match
    the original convention: row 1 = oldest, row N = newest, ids sequential.

    Steps:
      1. Read all rows, sort by timestamp ASC.
      2. Reassign local `id` values 1..N. Media filenames are now keyed on
         `shortcode` (FR-022 + T225), so no media-file rename is needed —
         only the in-TSV `id` column changes. Sort + reid is ALWAYS safe.
      3. Write the sorted, re-id'd rows back to the TSV.
      4. If `sweep_orphans=True`: sweep orphan media files in `media_dir`
         matching `<target>_*` that aren't referenced by any TSV row.

    `sweep_orphans` MUST be False when the scrape was interrupted mid-flight
    (any `FetchInterruptedError`, `InferenceHardBlockError`, or generic
    exception during streaming) — otherwise files belonging to posts the
    scrape didn't reach get mis-classified as orphans and deleted. The
    2026-05-29 rescrape DNS hiccup taught us this the hard way: 179 media
    files lost before the bug was found and recovered separately.
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

    if not sweep_orphans:
        return

    # Orphan sweep: any file in media_dir matching this target's prefix that
    # isn't referenced by a row is a leftover from a prior scrape. Safe to
    # delete WHEN the scrape completed cleanly. Path comparison uses absolute
    # + normcase'd paths on both sides so a relative media_dir or a relative
    # media_url doesn't cause a phantom mismatch (the bug that previously
    # wiped 323 real files because the `referenced` set had absolute paths
    # and the scan produced relative ones).
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


class RunSnapshot:
    """Pre-scrape snapshot of a target's TSV + media-files state.

    Used by `run_for_target` to make scrapes atomic: on any failure the
    pile is restored to its pre-run state via `.rollback()`, so a scheduler
    can safely retry without LLM-assisted recovery (the user/owner can
    troubleshoot later via the structured failure log in
    `<log_dir>/scrape-failures.jsonl`).

    Lifecycle:
      1. `snapshot = RunSnapshot(tsv_path, media_dir, target)`
      2. (Optional) `if snapshot.exists(): snapshot.rollback()` — recover
         from a previously-killed run before starting a new one.
      3. `snapshot.take()` — capture pre-scrape state.
      4. Run scrape...
      5. On success: `snapshot.commit()` — delete the snapshot.
         On failure: `summary = snapshot.rollback()` — restore pile state.

    What's snapshotted:
      - The full TSV file (cheap copy with shutil.copy2 preserves mtimes).
      - The set of `<target>_*` filenames currently in `media_dir`.

    What's restored on rollback:
      - TSV: live file replaced by the snapshot copy (or removed if the
        TSV didn't exist pre-scrape).
      - Media files: every `<target>_*` file in `media_dir` that wasn't
        in the pre-scrape snapshot is deleted. Files that existed before
        AND were overwritten during the scrape stay where they are — the
        Instagram CDN returns the same bytes for the same shortcode, so
        their content is still valid for the restored TSV's references.
    """

    SNAPSHOT_SUFFIX = ".snapshot"

    def __init__(self, tsv_path: str, media_dir: str, target: str):
        self.tsv_path = tsv_path
        self.media_dir = media_dir
        self.target = target
        self.snapshot_tsv_path = tsv_path + self.SNAPSHOT_SUFFIX
        self.tsv_existed_pre_scrape = False
        # None until `.take()` runs. Distinguishes "no files existed pre-scrape"
        # (empty set after take) from "take never ran" (None — happens when
        # rollback is called for a leftover snapshot from a previously-killed
        # run; in that case the file set is derived from the snapshot TSV).
        self.pre_scrape_media_filenames: Optional[set[str]] = None

    def exists(self) -> bool:
        """Whether a leftover snapshot already exists at the expected path.

        True means a previous run was killed (or crashed) before either
        committing or rolling back. Caller should rollback first, log it,
        then proceed with the new scrape.
        """
        return os.path.exists(self.snapshot_tsv_path)

    def take(self) -> None:
        """Capture the pre-scrape pile state for this target.

        Idempotent against a leftover snapshot: if `self.exists()` is True
        when this is called, the caller almost certainly intends to take
        a fresh snapshot — overwrite, don't error.
        """
        self.tsv_existed_pre_scrape = os.path.exists(self.tsv_path)
        if self.tsv_existed_pre_scrape:
            shutil.copy2(self.tsv_path, self.snapshot_tsv_path)
        else:
            # No live TSV → no snapshot file to write. Rollback later
            # means "remove the live TSV that this run created".
            if os.path.exists(self.snapshot_tsv_path):
                os.remove(self.snapshot_tsv_path)

        self.pre_scrape_media_filenames = set()
        if os.path.isdir(self.media_dir):
            prefix = f"{self.target}_"
            self.pre_scrape_media_filenames = {
                f for f in os.listdir(self.media_dir) if f.startswith(prefix)
            }

    def rollback(self) -> dict:
        """Restore TSV from snapshot, delete media files added since snapshot.

        Returns `{'files_deleted': N}` for the caller's failure log.

        Best-effort with respect to OS errors: a file the OS won't let us
        delete is logged but doesn't abort the rollback. The TSV restore
        is the atomic-critical step; the media-file cleanup is hygiene.

        Two modes:
          - In-process rollback: `.take()` ran, so `pre_scrape_media_filenames`
            is the set captured at snapshot time. Files in `media_dir` not in
            that set are deleted.
          - Leftover-snapshot recovery: `.take()` never ran (the caller just
            constructed a RunSnapshot to check `.exists()` after a killed
            previous run). In that case the pre-scrape file set is derived
            from the snapshot TSV's `media_url` columns BEFORE the TSV is
            restored, since that's the only record we have of what was
            legitimate at snapshot time.
        """
        files_deleted = 0

        # If we're recovering a leftover snapshot (no prior .take()), derive
        # the pre-scrape file set from the snapshot TSV BEFORE we overwrite it.
        if self.pre_scrape_media_filenames is None:
            self.pre_scrape_media_filenames = self._referenced_files_from_snapshot()

        # 1. Restore TSV.
        if os.path.exists(self.snapshot_tsv_path):
            try:
                os.replace(self.snapshot_tsv_path, self.tsv_path)
            except OSError as exc:
                print(f"  ! could not restore TSV from snapshot ({exc}); leaving live TSV in place")
        elif not self.tsv_existed_pre_scrape and os.path.exists(self.tsv_path):
            # The TSV didn't exist pre-scrape; the live one is entirely this
            # run's work. Remove it.
            try:
                os.remove(self.tsv_path)
            except OSError as exc:
                print(f"  ! could not remove partial TSV ({exc})")

        # 2. Delete media files added since the snapshot.
        if os.path.isdir(self.media_dir):
            prefix = f"{self.target}_"
            for f in os.listdir(self.media_dir):
                if f.startswith(prefix) and f not in self.pre_scrape_media_filenames:
                    try:
                        os.remove(os.path.join(self.media_dir, f))
                        files_deleted += 1
                    except OSError as exc:
                        print(f"  ! could not delete partial media file {f} ({exc})")

        return {"files_deleted": files_deleted}

    def commit(self) -> None:
        """Discard the snapshot — scrape completed successfully."""
        if os.path.exists(self.snapshot_tsv_path):
            try:
                os.remove(self.snapshot_tsv_path)
            except OSError as exc:
                print(f"  ! could not remove snapshot {self.snapshot_tsv_path} ({exc})")

    def _referenced_files_from_snapshot(self) -> set[str]:
        """Derive the set of media filenames legitimately present at snapshot
        time from the snapshot TSV's `media_url` columns.

        Used by leftover-snapshot recovery (rollback without a prior take):
        any file in `media_dir` matching `<target>_*` that ISN'T in this set
        is something the killed scrape created — safe to delete.
        """
        if not os.path.exists(self.snapshot_tsv_path):
            return set()
        filenames: set[str] = set()
        try:
            with open(self.snapshot_tsv_path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    media_url = (row.get("media_url") or "").strip()
                    if media_url:
                        filenames.add(posixpath.basename(media_url))
        except (OSError, csv.Error):
            pass
        return filenames


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
