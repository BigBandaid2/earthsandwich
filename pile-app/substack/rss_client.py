"""Substack RSS client.

Fetches a publication's RSS feed (`https://<slug>.substack.com/feed`) via
`feedparser` and normalizes each `<item>` into a flat dict the pipeline can
turn into a pile row. The publication feed is the App's sole upstream source
for the Substack service — there is no private API, no auth, no media download.

Substack RSS quirks handled here:
  - `<guid>` is the canonical id (FR-024); feedparser exposes it as `entry.id`.
  - `<description>` is the article deck → feedparser `entry.summary`.
  - `<content:encoded>` is the full HTML body → feedparser `entry.content[0].value`.
  - `<pubDate>` (RFC-822) → normalized to ISO 8601 UTC (`+0000`) for stable,
    lexicographically-sortable `published_at` values.
  - The feed is typically capped at the most-recent ~20 entries; older articles
    are simply absent (the data-model's RSS-window cap — NOT a deletion signal).
"""

from __future__ import annotations

import calendar
from datetime import datetime, timezone

import feedparser

SUBSTACK_FEED_URL = "https://{slug}.substack.com/feed"


class FeedFetchError(Exception):
    """The publication feed could not be fetched or parsed into usable entries.

    Raised on network failure (unreachable host, DNS, timeout), an HTTP error
    status (4xx/5xx), or an unparseable response that yielded no entries. The
    pipeline catches this and exits cleanly with a logged failure record
    instead of crashing — the "unreachable URL → clean exit + logged error"
    behaviour in US4's Independent Test.
    """


def normalize_slug(slug: str) -> str:
    """Strip an optional leading @ and trailing slash from a publication slug."""
    return slug.strip().lstrip("@").rstrip("/")


def feed_url_for(slug: str) -> str:
    """Build the RSS feed URL for a publication slug."""
    return SUBSTACK_FEED_URL.format(slug=normalize_slug(slug))


def _iso_published_at(entry: "feedparser.FeedParserDict") -> str:
    """Return the entry's publish time as ISO 8601 UTC ('YYYY-MM-DDTHH:MM:SS+0000').

    feedparser parses `<pubDate>` into `published_parsed`, a UTC `time.struct_time`.
    `calendar.timegm` treats it as UTC (unlike `time.mktime`, which assumes local
    time). Falls back to the raw `published` string if parsing failed.
    """
    parsed = entry.get("published_parsed")
    if parsed:
        dt = datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    return entry.get("published", "")


def _body_html(entry: "feedparser.FeedParserDict") -> str:
    """Extract the full HTML body from `<content:encoded>`, falling back to the
    `<description>` deck if the publication doesn't emit content:encoded."""
    content = entry.get("content")
    if content:
        value = content[0].get("value", "")
        if value:
            return value
    return entry.get("summary", "")


def normalize_entry(entry: "feedparser.FeedParserDict") -> dict:
    """Map one feedparser entry to the flat dict shape the pipeline consumes."""
    guid = entry.get("id") or entry.get("link") or ""
    return {
        "substack_id": guid,
        "link": entry.get("link", ""),
        "title": entry.get("title", ""),
        "subtitle": entry.get("summary", ""),
        "body": _body_html(entry),
        "published_at": _iso_published_at(entry),
    }


def fetch_feed_entries(slug: str, *, url: str | None = None) -> list[dict]:
    """Fetch + parse a publication's RSS feed; return normalized entry dicts.

    `url` overrides the derived feed URL — it may be a real URL, a local file
    path, or a literal XML string (all accepted by `feedparser.parse`), which
    is how the tests feed fixtures without touching the network.

    Raises `FeedFetchError` when the feed is unreachable or unparseable:
      - an HTTP error status (>= 400), or
      - a parse/network failure (`bozo_exception` set) that produced no entries.
    A valid feed that simply has no items returns `[]` (not an error) — a
    legitimate state for a brand-new or fully-windowed-out publication.
    """
    parsed = feedparser.parse(url if url is not None else feed_url_for(slug))

    status = parsed.get("status")
    if status is not None and status >= 400:
        raise FeedFetchError(
            f"feed for {slug!r} returned HTTP {status} (url: {feed_url_for(slug) if url is None else url})"
        )

    if not parsed.entries:
        bozo_exc = parsed.get("bozo_exception")
        if bozo_exc is not None:
            raise FeedFetchError(
                f"feed for {slug!r} could not be parsed: "
                f"{type(bozo_exc).__name__}: {bozo_exc}"
            )

    return [normalize_entry(e) for e in parsed.entries]
