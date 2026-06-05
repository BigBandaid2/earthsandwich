"""End-to-end tests for substack/pipeline.py:run_for_publication.

Covers US4's Independent Test (configure a feed → TSV matches schema; re-run →
zero new rows; unreachable URL → clean exit + logged error) plus FR-106
tombstoning and the RSS-window-cap guard.

Feeds are literal XML strings passed via `feed_url=`; no network access.
"""

import csv
import json
from pathlib import Path

from common.pile import SUBSTACK_TSV_COLUMNS, read_tsv_rows, write_substack_tsv
from substack import archive_client as ac
from substack.pipeline import run_archive_backfill, run_for_publication
from tests.substack.test_archive_client import make_archive_items, make_fake_transport

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


# ===== Phase 28: full-archive backfill (FR-028…FR-031) =====

def _backfill(tmp_path, monkeypatch, items, **fakekw):
    monkeypatch.setattr(ac, "_request_json", make_fake_transport(items, **fakekw))
    out = str(tmp_path / "articles.welaquan.local.tsv")
    log = str(tmp_path / "logs")
    run_archive_backfill("welaquan", out, log_dir=log, page_delay=(0, 0))
    return out, log


def test_backfill_ingests_full_archive_beyond_rss_window(tmp_path, monkeypatch):
    items = make_archive_items(25)  # far more than the ~20 RSS window
    out, _ = _backfill(tmp_path, monkeypatch, items, first_page_cap=3)

    with open(out, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        assert reader.fieldnames == SUBSTACK_TSV_COLUMNS
        rows = list(reader)

    assert len(rows) == 25                      # every archived post, despite short first page
    assert all(r["body"] for r in rows)         # each got its body fetched
    assert [r["id"] for r in rows] == [str(i) for i in range(1, 26)]
    assert rows == sorted(rows, key=lambda r: r["published_at"])


def test_backfill_merges_with_existing_rss_rows_no_dupes(tmp_path, monkeypatch):
    items = make_archive_items(25)
    out = str(tmp_path / "articles.welaquan.local.tsv")
    # Pre-seed two rows as if a prior RSS pull wrote them (newest two).
    seed = []
    for it in items[:2]:
        row = {c: "" for c in SUBSTACK_TSV_COLUMNS}
        row.update(substack_id=it["canonical_url"], link=it["canonical_url"],
                   title=it["title"], body="<p>from RSS</p>",
                   published_at=it["post_date"][:19] + "+0000")
        seed.append(row)
    write_substack_tsv(out, seed)

    monkeypatch.setattr(ac, "_request_json", make_fake_transport(items))
    run_archive_backfill("welaquan", out, log_dir=str(tmp_path / "logs"), page_delay=(0, 0))

    rows = read_tsv_rows(out)
    assert len(rows) == 25                                   # union, no duplicates
    assert len({r["substack_id"] for r in rows}) == 25
    # The pre-seeded RSS rows are preserved (not re-fetched/overwritten).
    rss_rows = [r for r in rows if r["body"] == "<p>from RSS</p>"]
    assert len(rss_rows) == 2


def test_backfill_idempotent_rerun(tmp_path, monkeypatch):
    items = make_archive_items(12)
    out, _ = _backfill(tmp_path, monkeypatch, items)
    assert len(read_tsv_rows(out)) == 12
    # Re-run against the same archive → zero new.
    monkeypatch.setattr(ac, "_request_json", make_fake_transport(items))
    run_archive_backfill("welaquan", out, log_dir=str(tmp_path / "logs"), page_delay=(0, 0))
    assert len(read_tsv_rows(out)) == 12


def test_backfill_skips_post_on_body_failure(tmp_path, monkeypatch):
    items = make_archive_items(10)
    fail_slug = items[4]["slug"]
    out, log = _backfill(tmp_path, monkeypatch, items, fail_body_slug=fail_slug)

    rows = read_tsv_rows(out)
    assert len(rows) == 9  # the one failed post is skipped, not aborted
    assert fail_slug not in {r["substack_id"].rsplit("/", 1)[-1] for r in rows}
    failures = (Path(log) / "scrape-failures.jsonl").read_text()
    assert "post_body_fetch_error" in failures


def test_backfill_wholesale_failure_clean_exit_pile_intact(tmp_path, monkeypatch):
    # Pre-existing pile, then the archive endpoint fails entirely.
    items = make_archive_items(5)
    out, _ = _backfill(tmp_path, monkeypatch, items)
    before = Path(out).read_bytes()

    monkeypatch.setattr(ac, "_request_json", make_fake_transport([], fail_archive=True))
    log2 = str(tmp_path / "logs2")
    run_archive_backfill("welaquan", out, log_dir=log2, page_delay=(0, 0))

    assert Path(out).read_bytes() == before  # pile untouched
    failures = (Path(log2) / "scrape-failures.jsonl").read_text()
    assert "archive_fetch_error" in failures
