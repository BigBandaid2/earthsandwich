"""Unit tests for substack/archive_client.py.

The single network seam (`_request_json`) is monkeypatched to serve fixtures,
so nothing here touches the network. The headline test is pagination across a
SHORT first page — the bug that made the live RSS-vs-archive discrepancy
confusing (stepping by `limit` over a short page skips posts).
"""

from datetime import date, timedelta

import pytest

from substack import archive_client as ac

BASE = "https://welaquan.substack.com"


def make_archive_items(n: int) -> list[dict]:
    """n archive items, newest-first, with unique ascending publish dates."""
    start = date(2021, 1, 1)
    items = []
    for i in range(n):  # i=0 is newest
        slug = f"post-{n - i:03d}"
        d = start + timedelta(days=(n - 1 - i))  # newest → latest date
        items.append({
            "canonical_url": f"{BASE}/p/{slug}",
            "title": f"Title {slug}",
            "subtitle": f"Deck {slug}",
            "description": f"Desc {slug}",
            "post_date": f"{d.isoformat()}T10:00:00.000Z",
            "slug": slug,
            "type": "newsletter",
            "audience": "everyone",
            "body_html": None,  # archive listing carries no body
        })
    return items


def make_fake_transport(items, *, first_page_cap=3, fail_body_slug=None, fail_archive=False):
    """Return a fake `_request_json(url, params)` serving `items` + bodies.

    `first_page_cap` makes the offset=0 response short (fewer than the requested
    limit) to exercise offset-by-actual-count stepping. `fail_body_slug` raises
    on that one post's body; `fail_archive` raises on the archive endpoint.
    """
    def fake(url, params=None):
        if url.endswith(ac.ARCHIVE_PATH):
            if fail_archive:
                raise ac.ArchiveFetchError("archive unreachable (simulated)")
            off, lim = params["offset"], params["limit"]
            page = items[off:off + lim]
            if off == 0:
                page = page[:first_page_cap]  # short first page
            return page
        if "/api/v1/posts/" in url:
            slug = url.rsplit("/", 1)[-1]
            if slug == fail_body_slug:
                raise ac.ArchiveFetchError(f"body fetch failed for {slug} (simulated)")
            return {"body_html": f"<p>body of {slug}</p>"}
        raise AssertionError(f"unexpected url {url}")
    return fake


def test_pagination_captures_all_despite_short_first_page(monkeypatch):
    items = make_archive_items(25)
    monkeypatch.setattr(ac, "_request_json", make_fake_transport(items, first_page_cap=3))

    got = ac.fetch_archive_metadata("welaquan", page_size=10)

    assert len(got) == 25  # NOT 3+10=13 or a gapped count — every post captured
    assert [g["substack_id"] for g in got] == [it["canonical_url"] for it in items]
    assert len({g["substack_id"] for g in got}) == 25  # all unique


def test_max_posts_caps_enumeration(monkeypatch):
    items = make_archive_items(25)
    monkeypatch.setattr(ac, "_request_json", make_fake_transport(items))
    got = ac.fetch_archive_metadata("welaquan", page_size=10, max_posts=7)
    assert len(got) == 7


def test_empty_archive_returns_empty(monkeypatch):
    monkeypatch.setattr(ac, "_request_json", make_fake_transport([]))
    assert ac.fetch_archive_metadata("welaquan", page_size=10) == []


def test_item_normalization_and_iso_date():
    item = {
        "canonical_url": f"{BASE}/p/hello",
        "title": "Hello",
        "subtitle": "the deck",
        "description": "fallback deck",
        "post_date": "2024-03-15T13:19:14.000Z",
        "slug": "hello",
    }
    n = ac.normalize_archive_item(item)
    assert n["substack_id"] == f"{BASE}/p/hello"
    assert n["link"] == n["substack_id"]  # canonical_url == link == guid
    assert n["subtitle"] == "the deck"     # subtitle wins over description
    assert n["slug"] == "hello"
    assert n["published_at"] == "2024-03-15T13:19:14+0000"


def test_subtitle_falls_back_to_description():
    n = ac.normalize_archive_item({
        "canonical_url": f"{BASE}/p/x", "slug": "x",
        "description": "only a description", "post_date": "2024-01-01T00:00:00.000Z",
    })
    assert n["subtitle"] == "only a description"


def test_fetch_post_body(monkeypatch):
    monkeypatch.setattr(ac, "_request_json", make_fake_transport(make_archive_items(1)))
    assert ac.fetch_post_body("post-001") == "<p>body of post-001</p>"


def test_archive_fetch_error_propagates(monkeypatch):
    monkeypatch.setattr(ac, "_request_json", make_fake_transport([], fail_archive=True))
    with pytest.raises(ac.ArchiveFetchError):
        ac.fetch_archive_metadata("welaquan", page_size=10)
