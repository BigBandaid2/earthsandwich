"""FR-106 incidental upstream-deletion detection for Substack.

The Substack analogue of `instagram/deletion_detection.py`. A single RSS pull
returns a window of the publication's most-recent articles, which implicitly
defines a `published_at` range. Any existing pile row whose `published_at`
falls inside that range but whose `substack_id` (`<guid>`) is absent from the
feed has been deleted upstream.

The range guard is what keeps the RSS-window cap from causing false deletions:
articles that aged out of the feed window sit *older* than the feed's oldest
entry, so they fall outside the range and are never tombstoned (data-model.md
§ "Substack-specific notes" + the contract's consumer requirement #4). Pile
rows are never physically removed — they get a tombstone and stay in place.

This module imports nothing from `instagram/` or other services: each pipeline
service is self-contained (FR-101 / US3 segregation).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional


def _parse_iso_to_epoch(ts_str: str) -> Optional[int]:
    """Parse an ISO 8601 timestamp to a Unix epoch int, tolerantly.

    Handles the pile's `2025-06-02T10:00:00+0000` form (offset without colon)
    as well as standard `+00:00`. Returns None for empty/unparseable values.
    """
    if not ts_str:
        return None
    norm = ts_str.strip().replace(" ", "T")
    if norm.endswith("+00"):
        norm += ":00"
    try:
        return int(datetime.fromisoformat(norm).timestamp())
    except (ValueError, TypeError):
        return None


def find_tombstones_in_feed(
    feed_entries: list[dict],
    existing_rows_by_substack_id: dict[str, dict],
) -> set[str]:
    """Return the set of `substack_id`s that should be tombstoned.

    `feed_entries` are the normalized dicts from `rss_client.fetch_feed_entries`
    (each with `substack_id` + `published_at`). An existing row is tombstoned
    when its `published_at` falls within the feed's covered range AND its
    `substack_id` is absent from the feed. Rows already tombstoned are skipped
    (FR-106 is set-once-monotonic).
    """
    if not feed_entries:
        return set()

    feed_ids: set[str] = set()
    feed_epochs: list[int] = []
    for entry in feed_entries:
        sid = entry.get("substack_id", "")
        if sid:
            feed_ids.add(sid)
        epoch = _parse_iso_to_epoch(entry.get("published_at", ""))
        if epoch is not None:
            feed_epochs.append(epoch)

    if not feed_epochs:
        return set()

    feed_oldest = min(feed_epochs)
    feed_newest = max(feed_epochs)

    tombstones: set[str] = set()
    for substack_id, row in existing_rows_by_substack_id.items():
        if not substack_id:
            continue
        if row.get("deleted_upstream"):
            continue
        row_epoch = _parse_iso_to_epoch(row.get("published_at", ""))
        if row_epoch is None:
            continue
        if feed_oldest <= row_epoch <= feed_newest and substack_id not in feed_ids:
            tombstones.add(substack_id)
    return tombstones
