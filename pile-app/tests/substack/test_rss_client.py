"""Unit tests for substack/rss_client.py + the common.pile Substack writer.

Feeds are passed to fetch_feed_entries via the `url=` override as literal XML
strings, so nothing here touches the network.
"""

import csv

import pytest

from common.pile import SUBSTACK_TSV_COLUMNS, write_substack_tsv
from substack.rss_client import (
    FeedFetchError,
    feed_url_for,
    fetch_feed_entries,
    normalize_slug,
)

SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
  <title>Wela Live</title>
  <link>https://welalive.substack.com</link>
  <item>
    <title>Second Post</title>
    <description>The deck of the second post</description>
    <link>https://welalive.substack.com/p/second-post</link>
    <guid isPermaLink="false">https://welalive.substack.com/p/second-post</guid>
    <pubDate>Tue, 03 Jun 2025 12:30:00 GMT</pubDate>
    <content:encoded><![CDATA[<p>Body of the <b>second</b> post.</p>]]></content:encoded>
  </item>
  <item>
    <title>First Post</title>
    <description>The deck of the first post</description>
    <link>https://welalive.substack.com/p/first-post</link>
    <guid isPermaLink="false">https://welalive.substack.com/p/first-post</guid>
    <pubDate>Mon, 02 Jun 2025 10:00:00 GMT</pubDate>
    <content:encoded><![CDATA[<p>Body of the first post.</p>]]></content:encoded>
  </item>
</channel>
</rss>
"""


def test_feed_url_and_slug_normalization():
    assert feed_url_for("welalive") == "https://welalive.substack.com/feed"
    assert feed_url_for("@welalive/") == "https://welalive.substack.com/feed"
    assert normalize_slug("  @welalive/ ") == "welalive"


def test_fetch_parses_entries_with_all_fields():
    entries = fetch_feed_entries("welalive", url=SAMPLE_FEED)
    assert len(entries) == 2

    # feedparser yields items in document order (newest-first here).
    second = entries[0]
    assert second["substack_id"] == "https://welalive.substack.com/p/second-post"
    assert second["link"] == "https://welalive.substack.com/p/second-post"
    assert second["title"] == "Second Post"
    assert second["subtitle"] == "The deck of the second post"
    assert "<b>second</b>" in second["body"]  # content:encoded, CDATA stripped
    # RFC-822 pubDate normalized to ISO 8601 UTC.
    assert second["published_at"] == "2025-06-03T12:30:00+0000"


def test_fetch_uses_guid_as_substack_id():
    entries = fetch_feed_entries("welalive", url=SAMPLE_FEED)
    ids = {e["substack_id"] for e in entries}
    assert ids == {
        "https://welalive.substack.com/p/first-post",
        "https://welalive.substack.com/p/second-post",
    }


def test_empty_but_valid_feed_returns_empty_list():
    empty_feed = (
        '<?xml version="1.0"?><rss version="2.0"><channel>'
        "<title>Empty</title></channel></rss>"
    )
    assert fetch_feed_entries("welalive", url=empty_feed) == []


def test_unparseable_feed_raises_feedfetcherror():
    # A non-feed string yields no entries + a bozo_exception → error path.
    with pytest.raises(FeedFetchError):
        fetch_feed_entries("welalive", url="this is not xml at all <<<")


def test_unreachable_host_raises_feedfetcherror():
    # Port 9 (discard) on localhost refuses fast → URLError, no entries.
    with pytest.raises(FeedFetchError):
        fetch_feed_entries("welalive", url="http://127.0.0.1:9/feed")


# ---------- common.pile.write_substack_tsv ----------

def _make_row(sid, published_at, **over):
    row = {c: "" for c in SUBSTACK_TSV_COLUMNS}
    row.update(substack_id=sid, published_at=published_at, title=sid)
    row.update(over)
    return row


def test_writer_sorts_by_published_at_and_reids(tmp_path):
    path = str(tmp_path / "articles.welalive.local.tsv")
    rows = [
        _make_row("b", "2025-06-03T12:30:00+0000"),
        _make_row("a", "2025-06-02T10:00:00+0000"),
        _make_row("c", "2025-06-04T09:00:00+0000"),
    ]
    write_substack_tsv(path, rows)

    with open(path, encoding="utf-8", newline="") as f:
        out = list(csv.DictReader(f, delimiter="\t"))

    assert [r["substack_id"] for r in out] == ["a", "b", "c"]  # published_at ASC
    assert [r["id"] for r in out] == ["1", "2", "3"]           # reid 1..N
    assert list(out[0].keys()) == SUBSTACK_TSV_COLUMNS         # header order


def test_writer_escapes_tabs_and_preserves_body_newlines(tmp_path):
    path = str(tmp_path / "articles.welalive.local.tsv")
    rows = [_make_row(
        "x", "2025-06-02T10:00:00+0000",
        title="has\ttab", body="<p>line one</p>\n<p>line two</p>",
    )]
    write_substack_tsv(path, rows)

    with open(path, encoding="utf-8", newline="") as f:
        out = list(csv.DictReader(f, delimiter="\t"))

    assert out[0]["title"] == "has tab"            # tab → single space
    assert out[0]["body"] == "<p>line one</p>\n<p>line two</p>"  # newline preserved
