"""End-to-end tests for substack/pipeline.py:run_for_publication.

Covers US4's Independent Test (configure a feed → TSV matches schema; re-run →
zero new rows; unreachable URL → clean exit + logged error) plus FR-106
tombstoning and the RSS-window-cap guard.

Feeds are literal XML strings passed via `feed_url=`; no network access.
"""

import csv
import json
from pathlib import Path

from common.pile import SUBSTACK_TSV_COLUMNS, read_tsv_rows
from substack.pipeline import run_for_publication

OUTPUT_TEMPLATE = "{publication}"  # tests pass an absolute path as the template


def _feed(*items: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">\n'
        "<channel><title>Wela Live</title>\n" + "\n".join(items) + "\n</channel></rss>"
    )


def _item(slug: str, pubdate: str, body: str = "<p>hi</p>") -> str:
    url = f"https://welalive.substack.com/p/{slug}"
    return (
        "<item>"
        f"<title>{slug}</title>"
        f"<description>deck for {slug}</description>"
        f"<link>{url}</link>"
        f'<guid isPermaLink="false">{url}</guid>'
        f"<pubDate>{pubdate}</pubDate>"
        f"<content:encoded><![CDATA[{body}]]></content:encoded>"
        "</item>"
    )


def _run(tmp_path: Path, feed: str | None, name="articles.welalive.local.tsv"):
    out = str(tmp_path / name)
    log_dir = str(tmp_path / "logs")
    run_for_publication(
        "welalive", out, log_dir=log_dir,
        feed_url=feed if feed is not None else "http://127.0.0.1:9/feed",
    )
    return out, log_dir


def test_first_run_writes_schema_conformant_tsv(tmp_path):
    feed = _feed(
        _item("second", "Tue, 03 Jun 2025 12:30:00 GMT"),
        _item("first", "Mon, 02 Jun 2025 10:00:00 GMT"),
    )
    out, _ = _run(tmp_path, feed)

    with open(out, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        assert reader.fieldnames == SUBSTACK_TSV_COLUMNS
        rows = list(reader)

    assert len(rows) == 2
    # Sorted published_at ASC → "first" is row 1.
    assert rows[0]["substack_id"].endswith("/first")
    assert rows[0]["id"] == "1"
    assert rows[1]["id"] == "2"
    assert rows[0]["published_at"] == "2025-06-02T10:00:00+0000"


def test_rerun_adds_zero_new_rows(tmp_path):
    feed = _feed(
        _item("second", "Tue, 03 Jun 2025 12:30:00 GMT"),
        _item("first", "Mon, 02 Jun 2025 10:00:00 GMT"),
    )
    out, _ = _run(tmp_path, feed)
    first = read_tsv_rows(out)
    # Same feed again.
    _run(tmp_path, feed)
    second = read_tsv_rows(out)

    assert len(first) == 2
    assert len(second) == 2  # dedup by substack_id → no growth
    assert {r["substack_id"] for r in first} == {r["substack_id"] for r in second}


def test_new_article_on_rerun_is_appended(tmp_path):
    feed1 = _feed(_item("first", "Mon, 02 Jun 2025 10:00:00 GMT"))
    out, _ = _run(tmp_path, feed1)
    assert len(read_tsv_rows(out)) == 1

    feed2 = _feed(
        _item("second", "Tue, 03 Jun 2025 12:30:00 GMT"),
        _item("first", "Mon, 02 Jun 2025 10:00:00 GMT"),
    )
    _run(tmp_path, feed2)
    rows = read_tsv_rows(out)
    assert len(rows) == 2
    assert {r["substack_id"].rsplit("/", 1)[-1] for r in rows} == {"first", "second"}


def test_unreachable_feed_clean_exit_and_logged_error(tmp_path):
    # No prior pile; feed unreachable → no TSV written, failure logged, no crash.
    out, log_dir = _run(tmp_path, None)  # None → localhost:9 (refused)

    assert not Path(out).exists()  # pile not created on a failed fetch
    failures = Path(log_dir) / "scrape-failures.jsonl"
    assert failures.exists()
    records = [json.loads(line) for line in failures.read_text().splitlines() if line.strip()]
    assert any(
        r["service"] == "substack" and r["failure_type"] == "feed_fetch_error"
        for r in records
    )


def test_unreachable_feed_leaves_existing_pile_untouched(tmp_path):
    feed = _feed(_item("first", "Mon, 02 Jun 2025 10:00:00 GMT"))
    out, _ = _run(tmp_path, feed)
    before = Path(out).read_bytes()

    # Now a failed fetch must not mutate the existing pile.
    _run(tmp_path, None)
    assert Path(out).read_bytes() == before


def test_tombstones_article_absent_from_feed_but_in_range(tmp_path):
    # Seed a pile with three consecutive articles.
    feed_all = _feed(
        _item("first", "Mon, 02 Jun 2025 10:00:00 GMT"),
        _item("second", "Tue, 03 Jun 2025 10:00:00 GMT"),
        _item("third", "Wed, 04 Jun 2025 10:00:00 GMT"),
    )
    out, _ = _run(tmp_path, feed_all)

    # New feed drops the MIDDLE article; the retained first+third still bracket
    # "second" (Jun 3 ∈ [Jun 2, Jun 4]), so it's an in-range deletion → tombstone.
    feed_missing_middle = _feed(
        _item("first", "Mon, 02 Jun 2025 10:00:00 GMT"),
        _item("third", "Wed, 04 Jun 2025 10:00:00 GMT"),
    )
    _run(tmp_path, feed_missing_middle)

    rows = {r["substack_id"].rsplit("/", 1)[-1]: r for r in read_tsv_rows(out)}
    assert rows["second"]["deleted_upstream"] == "true"
    assert rows["second"]["deleted_upstream_at"]
    assert rows["first"]["deleted_upstream"] == ""   # present in feed → not tombstoned
    assert rows["third"]["deleted_upstream"] == ""   # present in feed → not tombstoned


def test_rss_window_cap_does_not_tombstone_aged_out_article(tmp_path):
    # Seed with an OLD article.
    feed_old = _feed(_item("ancient", "Mon, 01 Jan 2024 10:00:00 GMT"))
    out, _ = _run(tmp_path, feed_old)

    # Later feed window is entirely newer — "ancient" aged out, falls BELOW the
    # feed's oldest entry, so it must NOT be tombstoned (RSS-window cap guard).
    feed_recent = _feed(
        _item("recent-a", "Mon, 02 Jun 2025 10:00:00 GMT"),
        _item("recent-b", "Tue, 03 Jun 2025 10:00:00 GMT"),
    )
    _run(tmp_path, feed_recent)

    rows = {r["substack_id"].rsplit("/", 1)[-1]: r for r in read_tsv_rows(out)}
    assert rows["ancient"]["deleted_upstream"] == ""  # aged out, not deleted
    assert len(rows) == 3
