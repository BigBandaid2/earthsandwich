"""Substack full-archive client (FR-028…FR-031).

The RSS feed (`rss_client`) only exposes the most-recent ~20 posts. This module
enumerates a publication's COMPLETE archive via Substack's archive JSON API and
fetches each post's full HTML body, so a backfill can capture everything older
than the RSS window.

Endpoints (undocumented but stable in practice):
  - `GET /api/v1/archive?sort=new&offset=N&limit=L`
      Paginated post METADATA (no body). Returns a JSON list; an empty list
      marks the end. **The first page can be SHORT** (fewer than `limit`)
      without meaning end-of-archive, so pagination steps by the *actual item
      count*, not by `limit` — stepping by `limit` over a short first page
      silently skips posts.
  - `GET /api/v1/posts/<slug>`
      Full post JSON including `body_html`.

Dedup identity: each archive item's `canonical_url` equals the RSS `<guid>`, so
backfilled rows share the pile's `substack_id` key and merge with RSS rows
without duplicates.

Self-contained: imports nothing from `instagram/` or other services. All HTTP
goes through `_request_json`, which the tests monkeypatch to serve fixtures.
"""

from __future__ import annotations

from datetime import datetime, timezone

import requests

DEFAULT_BASE = "https://{slug}.substack.com"
ARCHIVE_PATH = "/api/v1/archive"
POST_PATH = "/api/v1/posts/{slug}"

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pile-app/1.0; ingestion-pipeline)"}
_TIMEOUT = 30
_HARD_OFFSET_CEILING = 10000  # runaway-pagination backstop


class ArchiveFetchError(Exception):
    """The archive API or a post-body endpoint could not be reached or parsed.

    Raised on a network failure or an HTTP error status. The pipeline treats a
    wholesale archive failure as a clean exit (pile untouched) and a single
    post-body failure as log-and-skip (FR-031).
    """


def base_url_for(slug: str, base_url: str | None) -> str:
    """Resolve the publication base URL (override wins; else derive from slug)."""
    return (base_url or DEFAULT_BASE.format(slug=slug)).rstrip("/")


def _request_json(url: str, params: dict | None = None):
    """GET `url` and return parsed JSON, raising ArchiveFetchError on any failure.

    The single network seam — tests monkeypatch this to serve fixtures offline.
    """
    try:
        resp = requests.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        raise ArchiveFetchError(f"request to {url} failed: {type(exc).__name__}: {exc}") from exc
    if resp.status_code >= 400:
        raise ArchiveFetchError(f"{url} returned HTTP {resp.status_code}")
    try:
        return resp.json()
    except ValueError as exc:
        raise ArchiveFetchError(f"{url} returned non-JSON body: {exc}") from exc


def _iso_published_at(post_date: str) -> str:
    """Normalize an archive `post_date` to the pile's ISO 8601 UTC form.

    Archive dates look like `2024-03-15T13:19:14.000Z`. Returns
    `2024-03-15T13:19:14+0000`; falls back to the raw value if unparseable.
    """
    if not post_date:
        return ""
    raw = post_date.strip()
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return raw


def normalize_archive_item(item: dict) -> dict:
    """Map one archive API item to the flat dict the pipeline turns into a row.

    `substack_id` is the `canonical_url` (== RSS `<guid>`), so archive and RSS
    rows dedup against each other. `slug` is carried so the body can be fetched.
    """
    canonical = item.get("canonical_url") or ""
    return {
        "substack_id": canonical,
        "link": canonical,
        "title": item.get("title", "") or "",
        "subtitle": item.get("subtitle") or item.get("description") or "",
        "published_at": _iso_published_at(item.get("post_date", "") or ""),
        "slug": item.get("slug", "") or "",
    }


def fetch_archive_metadata(
    slug: str,
    *,
    base_url: str | None = None,
    page_size: int = 50,
    max_posts: int | None = None,
) -> list[dict]:
    """Enumerate ALL of a publication's posts (metadata only), newest-first.

    Pages `/api/v1/archive`, stepping `offset` by the number of items actually
    returned (NOT by `page_size`) so a short first page doesn't skip posts.
    De-dups by `substack_id` across pages. Stops on an empty page, on reaching
    `max_posts`, or at a hard offset ceiling. Raises ArchiveFetchError if the
    archive endpoint itself is unreachable.
    """
    archive_url = base_url_for(slug, base_url) + ARCHIVE_PATH
    seen: set[str] = set()
    entries: list[dict] = []
    offset = 0
    while offset < _HARD_OFFSET_CEILING:
        page = _request_json(archive_url, {"sort": "new", "offset": offset, "limit": page_size})
        if not page:
            break
        for item in page:
            norm = normalize_archive_item(item)
            sid = norm["substack_id"]
            if not sid or sid in seen:
                continue
            seen.add(sid)
            entries.append(norm)
            if max_posts is not None and len(entries) >= max_posts:
                return entries
        offset += len(page)  # step by ACTUAL count, not page_size
    return entries


def fetch_post_body(slug: str, *, base_url: str | None = None) -> str:
    """Fetch one post's full HTML body via `/api/v1/posts/<slug>`.

    Returns the `body_html` string (possibly empty). Raises ArchiveFetchError on
    a network/HTTP failure so the caller can log-and-skip that single post.
    """
    post_url = base_url_for(slug, base_url) + POST_PATH.format(slug=slug)
    data = _request_json(post_url)
    if isinstance(data, dict):
        return data.get("body_html") or ""
    raise ArchiveFetchError(f"unexpected post payload for {slug!r}")
