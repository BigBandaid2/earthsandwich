"""FR-106 incidental upstream-deletion detection.

When the Instagram pipeline fetches a page from instagrapi, we get back a
contiguous timestamp range of posts. Any existing pile row whose timestamp
falls inside that range but whose `shortcode` is NOT in the page's posts
has been deleted upstream (or hidden via privacy settings, or shadow-banned
— from the producer's perspective, indistinguishable from deletion).

This is "incidental" detection per the 2026-05-29 clarification: we don't
run a separate audit pass over older rows. Detection is a free side-effect
of normal pagination. Pile rows are never physically deleted — they get a
tombstone (`deleted_upstream=true` + `deleted_upstream_at=<now>`) and stay
in place per FR-105 (preserve inference inputs).
"""

from __future__ import annotations


def find_tombstones_in_page(
    page_medias: list,
    existing_rows_by_shortcode: dict[str, dict],
) -> set[str]:
    """Inspect one page of instagrapi Media objects against the existing pile
    and return the set of shortcodes that should be tombstoned.

    The page implicitly defines a timestamp range (oldest-to-newest of its
    posts). Any existing-pile row whose timestamp falls inside that range
    but whose shortcode isn't in the page is considered absent — i.e.,
    deleted-upstream by FR-106's definition.

    Rows already tombstoned are skipped (FR-106 is set-once-monotonic;
    the original detection timestamp is preserved).
    """
    if not page_medias:
        return set()

    page_shortcodes: set[str] = set()
    page_timestamps: list[int] = []
    for m in page_medias:
        code = getattr(m, "code", "") or ""
        if code:
            page_shortcodes.add(code)
        ts_attr = getattr(m, "taken_at", None)
        if ts_attr is not None:
            try:
                page_timestamps.append(int(ts_attr.timestamp()))
            except (AttributeError, ValueError, OSError):
                continue

    if not page_timestamps:
        return set()

    page_oldest = min(page_timestamps)
    page_newest = max(page_timestamps)

    tombstones: set[str] = set()
    for shortcode, row in existing_rows_by_shortcode.items():
        if not shortcode:
            continue
        if row.get("deleted_upstream"):
            continue
        row_ts_str = row.get("timestamp", "")
        if not row_ts_str:
            continue
        # Parse the row's timestamp. Tolerate the existing TSV's
        # "2024-02-20T02:27:16+0000" form (offset without colon).
        ts_norm = row_ts_str.strip().replace(" ", "T")
        if ts_norm.endswith("+00"):
            ts_norm += ":00"
        try:
            from datetime import datetime
            row_ts = int(datetime.fromisoformat(ts_norm).timestamp())
        except (ValueError, TypeError):
            continue
        if page_oldest <= row_ts <= page_newest and shortcode not in page_shortcodes:
            tombstones.add(shortcode)
    return tombstones
