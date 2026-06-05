"""Substack pipeline service: RSS → pile, mirroring the Instagram service shape.

Top-level entry is `run_for_publication(slug, output_template, log_dir, ...)`.
Unlike the Instagram service, there is no pagination, no media download, and no
LLM inference — a Substack run is a single bounded RSS fetch. The whole run is
therefore atomic by construction: it reads the existing pile, merges the feed in
memory, and writes the complete file once via `write_substack_tsv` (temp +
`os.replace`). A failed fetch never touches the pile.

Per-run flow:
  1. Read the existing `articles.<publication>.local.tsv` (if any).
  2. Fetch + normalize the publication's RSS feed (`rss_client`).
     - On failure: log a structured failure record, print a banner, return.
       The pile is left exactly as it was (clean exit + logged error, US4).
  3. Dedup by `substack_id` (FR-024): feed entries already in the pile are
     skipped; only genuinely-new articles become new rows.
  4. Tombstone any existing row absent from the feed but within its
     `published_at` range (FR-106, `deletion_detection`).
  5. Write the merged set: sort by `published_at` ASC, re-id, atomic swap.

This module imports only from `common/` and its sibling `substack/` modules —
never from `instagram/` or any other service (FR-101 / US3 segregation).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from common.anti_throttle import jittered_sleep
from common.pile import SUBSTACK_TSV_COLUMNS, read_tsv_rows, write_substack_tsv
from common.run_logging import write_failure_record
from substack.archive_client import (
    ArchiveFetchError,
    base_url_for,
    fetch_archive_metadata,
    fetch_post_body,
)
from substack.deletion_detection import find_tombstones_in_feed
from substack.rss_client import FeedFetchError, fetch_feed_entries, normalize_slug


def _new_row(entry: dict) -> dict:
    """Build a fresh pile row from a normalized feed entry. `id` is assigned by
    the sort+reid post-pass in `write_substack_tsv`, so it's left blank here."""
    return {
        "id": "",
        "substack_id": entry["substack_id"],
        "link": entry.get("link", ""),
        "title": entry.get("title", ""),
        "subtitle": entry.get("subtitle", ""),
        "body": entry.get("body", ""),
        "published_at": entry.get("published_at", ""),
        "deleted_upstream": "",
        "deleted_upstream_at": "",
    }


def run_for_publication(
    slug: str,
    output_template: str,
    log_dir: str = "",
    *,
    feed_url: str | None = None,
) -> None:
    """Run the incremental Substack scrape for a single publication.

    `output_template` carries a `{publication}` placeholder. `feed_url` overrides
    the derived RSS URL (used by tests to pass a fixture feed); production leaves
    it None and the URL is derived from the slug.
    """
    slug = normalize_slug(slug)
    output_path = output_template.format(publication=slug)
    print(f"\n=== Substack: {slug} → {output_path} ===")

    run_started_at_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    run_started_at_mono = time.monotonic()

    existing_rows = read_tsv_rows(output_path)
    existing_by_id: dict[str, dict] = {
        r["substack_id"]: r for r in existing_rows if r.get("substack_id")
    }
    print(f"  existing pile: {len(existing_rows)} row(s).")

    # ===== Fetch the feed (the only failure-prone step) =====
    try:
        entries = fetch_feed_entries(slug, url=feed_url)
    except FeedFetchError as exc:
        elapsed = round(time.monotonic() - run_started_at_mono, 2)
        print(
            "\n" + "=" * 72
            + f"\nFAILURE — Substack {slug} feed unavailable; pile left unchanged."
            + f"\n  Failure detail: {exc}"
            + f"\n  Operator action: verify the publication slug and that "
            f"https://{slug}.substack.com/feed is reachable, then re-run."
            + "\n" + "=" * 72
        )
        write_failure_record(log_dir, {
            "target": slug,
            "service": "substack",
            "failure_type": "feed_fetch_error",
            "failure_detail": str(exc),
            "run_started_at": run_started_at_iso,
            "elapsed_seconds": elapsed,
            "output_path": output_path,
            "operator_hint": "Verify the publication slug and feed reachability.",
        })
        return

    print(f"  feed returned {len(entries)} entry(ies).")

    # ===== Dedup (FR-024): only genuinely-new substack_ids become new rows =====
    new_rows = [
        _new_row(e) for e in entries
        if e.get("substack_id") and e["substack_id"] not in existing_by_id
    ]

    # ===== Tombstone (FR-106): existing rows absent from the feed, in-range =====
    tombstones = find_tombstones_in_feed(entries, existing_by_id)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    tombstoned = 0
    for row in existing_rows:
        sid = row.get("substack_id", "")
        if sid in tombstones and not row.get("deleted_upstream"):
            row["deleted_upstream"] = "true"
            row["deleted_upstream_at"] = now_iso
            tombstoned += 1

    # ===== Merge + atomic write =====
    if not new_rows and not tombstoned and existing_rows:
        # Nothing changed — but still rewrite so a first-run ordering/normalization
        # is applied idempotently only when there IS a pile. Avoid creating an
        # empty file for a publication whose feed legitimately has no entries.
        print(f"  no new articles, no tombstones for {slug}. Pile unchanged.")
        return

    merged = existing_rows + new_rows
    if not merged:
        print(f"  feed for {slug} is empty and no prior pile exists; nothing to write.")
        return

    write_substack_tsv(output_path, merged)
    print(
        f"  done: {len(new_rows)} new article(s), {tombstoned} tombstoned, "
        f"{len(merged)} total row(s) written to {output_path}."
    )


def _apply_tombstones(existing_rows: list[dict], tombstones: set[str]) -> int:
    """Mark in-place any existing row whose substack_id is in `tombstones`
    (FR-106, set-once-monotonic). Returns the count newly tombstoned."""
    if not tombstones:
        return 0
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    count = 0
    for row in existing_rows:
        sid = row.get("substack_id", "")
        if sid in tombstones and not row.get("deleted_upstream"):
            row["deleted_upstream"] = "true"
            row["deleted_upstream_at"] = now_iso
            count += 1
    return count


def run_archive_backfill(
    slug: str,
    output_template: str,
    log_dir: str = "",
    *,
    base_url: str | None = None,
    page_delay: tuple[float, float] = (0.4, 1.0),
    max_posts: int | None = None,
) -> None:
    """Full-archive backfill (FR-028…FR-031): ingest a publication's COMPLETE
    archive, not just the RSS window.

    Enumerates every post via the archive API, fetches the body for each post
    not already in the pile (politely, with a jittered inter-request delay),
    tombstones in-range absent rows, and writes the merged pile atomically.
    Dedup by `substack_id` (= archive `canonical_url` = RSS `<guid>`) means this
    merges cleanly with rows a prior RSS pull wrote. A wholesale archive failure
    is a clean exit (pile untouched); a single post-body failure is logged and
    skipped (FR-031).
    """
    slug = normalize_slug(slug)
    output_path = output_template.format(publication=slug)
    print(f"\n=== Substack ARCHIVE backfill: {slug} → {output_path} ===")

    run_started_at_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    run_started_at_mono = time.monotonic()

    existing_rows = read_tsv_rows(output_path)
    existing_by_id: dict[str, dict] = {
        r["substack_id"]: r for r in existing_rows if r.get("substack_id")
    }
    print(f"  existing pile: {len(existing_rows)} row(s).")

    # Resolve the PUBLICATION base URL once. Both the archive listing and every
    # per-post body fetch must use this host — a post's own slug is a PATH
    # segment, never the subdomain (the 2026-06-05 backfill bug: fetch_post_body
    # was deriving the host from each post slug → asking-for-help.substack.com).
    pub_base = base_url_for(slug, base_url)

    try:
        meta = fetch_archive_metadata(slug, base_url=pub_base, max_posts=max_posts)
    except ArchiveFetchError as exc:
        elapsed = round(time.monotonic() - run_started_at_mono, 2)
        print(
            "\n" + "=" * 72
            + f"\nFAILURE — Substack {slug} archive unavailable; pile left unchanged."
            + f"\n  Failure detail: {exc}"
            + "\n" + "=" * 72
        )
        write_failure_record(log_dir, {
            "target": slug,
            "service": "substack",
            "failure_type": "archive_fetch_error",
            "failure_detail": str(exc),
            "run_started_at": run_started_at_iso,
            "elapsed_seconds": elapsed,
            "output_path": output_path,
            "operator_hint": "Verify the publication slug and that the archive API is reachable.",
        })
        return

    print(f"  archive lists {len(meta)} post(s).")
    new_meta = [m for m in meta if m["substack_id"] and m["substack_id"] not in existing_by_id]
    print(f"  {len(new_meta)} not yet in pile; fetching bodies...")

    new_rows: list[dict] = []
    skipped = 0
    for idx, m in enumerate(new_meta, start=1):
        try:
            body = fetch_post_body(m["slug"], base_url=pub_base)
        except ArchiveFetchError as exc:
            print(f"  ! [{idx}/{len(new_meta)}] skip {m['slug']!r}: body fetch failed ({exc})")
            write_failure_record(log_dir, {
                "target": slug,
                "service": "substack",
                "failure_type": "post_body_fetch_error",
                "failure_detail": str(exc),
                "slug": m["slug"],
                "substack_id": m["substack_id"],
            })
            skipped += 1
            continue
        new_rows.append(_new_row({**m, "body": body}))
        if idx < len(new_meta):
            jittered_sleep(*page_delay, label="")  # polite, silent

    tombstones = find_tombstones_in_feed(meta, existing_by_id)
    tombstoned = _apply_tombstones(existing_rows, tombstones)

    if not new_rows and not tombstoned:
        print(f"  no new articles, no tombstones for {slug}. Pile unchanged"
              + (f" ({skipped} post(s) skipped on body-fetch errors)." if skipped else "."))
        return

    merged = existing_rows + new_rows
    write_substack_tsv(output_path, merged)
    print(
        f"  done: {len(new_rows)} new article(s), {skipped} skipped, {tombstoned} tombstoned, "
        f"{len(merged)} total row(s) written to {output_path}."
    )


# Convenience alias so the service exposes a uniform `run(...)` entry point
# alongside the Instagram service's `run_for_target`.
run = run_for_publication

__all__ = ["run_for_publication", "run_archive_backfill", "run", "SUBSTACK_TSV_COLUMNS"]
