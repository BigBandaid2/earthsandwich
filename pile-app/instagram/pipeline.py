"""Instagram pipeline service: orchestrates auth, pagination, per-post processing, and pile writes.

Top-level entry is `run_for_target(cl, target, output_template, media_dir, rate_config)`.
Per-post work splits into:
  - `iter_new_media(cl, user_id, since_ts, ...)` — generator that paginates
    instagrapi and yields oldest-first within each page (newest-page first
    across pages). Stops on at-or-before-since_ts, hard-block error, end-of-
    feed, or safety cap.
  - `process_media(m, target, local_id, media_dir, recent_locations, previous_row)` —
    field extraction, media download, dual-path location (tagged via
    `canonicalize_tagged_location`, inferred via `infer_post_location` with
    city-fallback to the prior row), returns the TSV row dict.

After streaming, `resort_tsv_and_rename_media` re-sorts by timestamp ASC,
re-numbers ids 1..N, renames media files via two-pass swap, and sweeps
orphan files matching the target's prefix.
"""

from __future__ import annotations

import csv
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Iterator, Optional

import requests

from common.anti_throttle import is_challenge_error, jittered_sleep
from common.pile import (
    RECENT_LOCATION_COUNT,
    TSV_COLUMNS,
    apply_tombstones,
    download_media,
    normalize_media_url_for_tsv,
    read_tsv_rows,
    resort_tsv_and_sweep_media,
)
from common.run_logging import prune_scrape_logs
from instagram.deletion_detection import find_tombstones_in_page
from instagram.inferred_location import extract_city_heuristic, infer_post_location
from instagram.instagrapi_client import resolve_target_user_id
from instagram.tagged_location import canonicalize_tagged_location


def parse_unix_timestamp(ts_str: str) -> int:
    """Convert an ISO timestamp string to a Unix timestamp integer.

    Python equivalent of PHP's strtotime(). Handles formats like
    "2024-02-20 02:27:16+00" or "2024-02-20T02:27:16+0000".
    """
    ts_str = ts_str.strip().replace(" ", "T")
    if ts_str.endswith("+00"):
        ts_str += ":00"
    dt = datetime.fromisoformat(ts_str)
    return int(dt.timestamp())


def fmt_duration(seconds: float) -> str:
    """Format a duration in seconds as a human-readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes, secs = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"


def estimate_scrape_seconds(num_posts: int, rate_config: dict) -> float:
    """Rough scrape-duration estimate in seconds for `num_posts` posts.

    Computed from the rate_config's average page/long-rest/media delays plus
    a fixed per-post-processing budget (download + LLM canonicalize/infer).
    Inputs are averages, so the estimate is a midpoint — actual runtime can
    be ±30% depending on which way the random jitter lands.
    """
    if num_posts <= 0:
        return 0.0
    page_size = rate_config["page_size"]
    pages = max(1, (num_posts + page_size - 1) // page_size)
    page_delay_avg = sum(rate_config["page_delay"]) / 2
    media_delay_avg = sum(rate_config["media_delay"]) / 2
    long_rest_every = rate_config["long_rest_every"]
    long_rest_avg = sum(rate_config["long_rest"]) / 2
    n_long_rests = (pages - 1) // long_rest_every if long_rest_every else 0
    per_post_work = 4.0  # observed average: ~1s media download + ~3s LLM round-trip
    return (
        (pages - 1) * page_delay_avg
        + n_long_rests * long_rest_avg
        + num_posts * (per_post_work + media_delay_avg)
    )


def _fetch_page_with_retry(
    cl: "object",
    user_id: int,
    end_cursor: str,
    page_size: int,
    page_num: int,
) -> Optional[tuple[list, str]]:
    """Fetch one page from instagrapi with single retry on transient errors.

    Returns (medias, new_end_cursor) on success, or None to signal "give up,
    let the caller persist partial progress." A challenge error is NOT
    retried (manual verification required); transient errors get one retry
    after a 60–180s backoff before giving up.
    """
    try:
        return cl.user_medias_paginated_v1(user_id, page_size, end_cursor=end_cursor)
    except Exception as exc:
        if is_challenge_error(exc):
            print(
                f"\n  ! page {page_num} blocked by Instagram challenge — {exc}\n"
                f"  ! the crawler account needs manual verification: open the "
                f"Instagram app, complete any 'Was this you?' / 2FA prompt, "
                f"then re-run."
            )
            return None
        # Transient — back off then retry once.
        print(f"\n  ! page {page_num} fetch failed transiently ({type(exc).__name__}: {exc})")
        jittered_sleep(60.0, 180.0, label=f"backoff before retry of page {page_num}")
        try:
            return cl.user_medias_paginated_v1(user_id, page_size, end_cursor=end_cursor)
        except Exception as exc2:
            if is_challenge_error(exc2):
                print(f"  ! retry of page {page_num} hit a challenge — {exc2}")
            else:
                print(f"  ! retry of page {page_num} also failed — {exc2}; giving up.")
            return None


def iter_new_media(
    cl: "object",
    user_id: int,
    since_ts: int,
    max_total: int = 1000,
    page_size: int = 50,
    page_delay: tuple[float, float] = (0.0, 0.0),
    long_rest_every: int = 0,
    long_rest: tuple[float, float] = (0.0, 0.0),
    on_page_fetched=None,
) -> "Iterator":
    """Generator yielding one Media object at a time from the target's feed.

    Walks pages newest-first (instagrapi's natural order). Within each page,
    yields oldest-of-page first so the caller's per-post processing builds
    `recent_locations` context in roughly-chronological order. Across pages
    the yield order is still newest-page first — the caller must re-sort the
    final TSV by timestamp ASC to restore the canonical oldest-first
    convention (see `resort_tsv_and_rename_media`).

    Stops on: a post at-or-before `since_ts`, `max_total` cap, end-of-feed,
    or an unrecoverable fetch error (challenge or transient that failed retry).
    Partial yields are kept by the caller — every Media yielded before the
    stop is on disk by the time the next page is fetched.

    `user_id` is the target account's numeric id, NOT the crawler's
    `cl.user_id` — that separation is what lets one logged-in client scrape
    multiple targets.
    """
    end_cursor = ""
    page_num = 0
    total_yielded = 0
    while True:
        page_num += 1
        if page_num > 1:
            jittered_sleep(*page_delay, label=f"between-pages pause before page {page_num}")
            if long_rest_every and (page_num - 1) % long_rest_every == 0:
                jittered_sleep(*long_rest, label=f"long rest after {long_rest_every} pages")
        page_start = time.monotonic()
        result = _fetch_page_with_retry(cl, user_id, end_cursor, page_size, page_num)
        if result is None:
            print(f"  ! stopping pagination — {total_yielded} post(s) already streamed to disk.")
            return
        medias, end_cursor = result
        print(f"  [page {page_num}] {len(medias)} posts (cursor={'…' if end_cursor else 'end'})")
        if not medias:
            return
        if on_page_fetched is not None:
            try:
                on_page_fetched(medias)
            except Exception as exc:
                print(f"  ! on_page_fetched callback raised ({exc}); continuing")
        page_new: list = []
        hit_since = False
        for m in medias:
            ts = int(m.taken_at.timestamp())
            if ts <= since_ts:
                hit_since = True
                break
            page_new.append(m)
        for m in reversed(page_new):
            yield m
            total_yielded += 1
            if total_yielded >= max_total:
                print(f"  ! safety cap of {max_total} posts reached; stopping pagination")
                return
        page_elapsed = time.monotonic() - page_start
        per_post = page_elapsed / max(1, len(page_new))
        print(
            f"  [page {page_num} done] processed {len(page_new)} post(s) in "
            f"{fmt_duration(page_elapsed)} ({per_post:.1f}s/post). "
            f"Running total: {total_yielded} post(s)."
        )
        if hit_since or not end_cursor:
            return


def process_media(
    m: "object",
    target: str,
    local_id: int,
    media_dir: str,
    recent_locations: list[str],
    previous_row: Optional[dict] = None,
) -> dict:
    """Process one instagrapi `Media` object into a TSV row dict.

    Pipeline (in order):
      1. Field extraction: pk, shortcode, caption, timestamp.
      2. Media URL + type resolution (handles IMAGE / VIDEO / Album with
         `media_type` codes 1 / 2 / 8 respectively).
      3. Media download via `download_media`; failures log and continue.
      4. Dual-path location resolution:
           FR-019 tagged path: `m.location.name` is populated → use name/
             coords verbatim, call `canonicalize_tagged_location` for the
             canonical name + IATA region.
           FR-020 inferred path: no tag → call `infer_post_location`
             with caption + image + recent_locations context. Falls back
             to the most recent prior location when inference is empty.
      5. Path normalization for the TSV (relative to APP_ROOT, posix
         separators).

    Returns a row dict matching the TSV column order. Does NOT mutate
    `recent_locations`, increment ids, or write to disk — those iteration
    concerns belong to the caller (`run_for_target`).
    """
    instagram_id = str(m.pk)
    shortcode = m.code or ""
    caption = m.caption_text or ""

    ts_dt = m.taken_at
    if ts_dt.tzinfo is None:
        ts_dt = ts_dt.replace(tzinfo=timezone.utc)
    timestamp = ts_dt.strftime("%Y-%m-%dT%H:%M:%S%z")

    media_type_code = getattr(m, "media_type", 1)
    if media_type_code == 2:
        media_type = "VIDEO"
        remote_media_url = str(m.video_url) if getattr(m, "video_url", None) else ""
    elif media_type_code == 8 and getattr(m, "resources", None):
        first = m.resources[0]
        if getattr(first, "media_type", 1) == 2:
            media_type = "VIDEO"
            remote_media_url = str(first.video_url) if getattr(first, "video_url", None) else ""
        else:
            media_type = "IMAGE"
            remote_media_url = str(first.thumbnail_url) if getattr(first, "thumbnail_url", None) else ""
    else:
        media_type = "IMAGE"
        remote_media_url = str(m.thumbnail_url) if getattr(m, "thumbnail_url", None) else ""

    local_media_path = ""
    if remote_media_url and shortcode:
        try:
            local_media_path = download_media(
                remote_media_url, target, shortcode, media_type, media_dir
            )
            print(f"  ↓ saved {local_media_path}")
        except (requests.RequestException, OSError) as exc:
            print(f"  ! pk={instagram_id}  media download failed ({exc})")

    location, lat, lng, region = "", "", "", ""
    reasoning = ""
    tag_verbatim, lat_verbatim, lng_verbatim = "", "", ""
    tagged: Optional[tuple[str, str, str]] = None
    loc = getattr(m, "location", None)
    if loc and getattr(loc, "name", None):
        raw_lat = getattr(loc, "lat", None)
        raw_lng = getattr(loc, "lng", None)
        if raw_lat in (None, 0, 0.0) and raw_lng in (None, 0, 0.0):
            tagged = (loc.name, "", "")
        else:
            lat_s = "" if raw_lat is None else str(raw_lat)
            lng_s = "" if raw_lng is None else str(raw_lng)
            tagged = (loc.name, lat_s, lng_s)

    if tagged:
        verbatim_name, verbatim_lat, verbatim_lng = tagged
        # Capture verbatim columns (FR-105 / Cardinal Rule #4) BEFORE the
        # canonicalization LLM call so they're preserved even if the call
        # fails. canonicalize_tagged_location internally catches its own
        # exceptions, so this is belt-and-suspenders.
        tag_verbatim, lat_verbatim, lng_verbatim = verbatim_name, verbatim_lat, verbatim_lng
        canonical_name, canonical_lat, canonical_lng, region, reasoning = canonicalize_tagged_location(
            verbatim_name, verbatim_lat, verbatim_lng
        )
        location = canonical_name or verbatim_name
        lat = canonical_lat or verbatim_lat
        lng = canonical_lng or verbatim_lng
        canon_note = f" → {canonical_name}" if canonical_name and canonical_name != verbatim_name else ""
        coord_note = ""
        if canonical_lat and verbatim_lat and canonical_lat != verbatim_lat:
            coord_note = f" [coord override: tag-coords were ({verbatim_lat},{verbatim_lng})]"
        print(f"  location (tagged): {verbatim_name}{canon_note}  lat={lat}  lng={lng}  region: {region or '(undetermined)'}{coord_note}")
    else:
        try:
            location, lat, lng, region, reasoning = infer_post_location(
                caption=caption,
                local_media_path=local_media_path,
                media_type=media_type,
                recent_locations=recent_locations,
            )
        except Exception as exc:
            print(f"  ! pk={instagram_id}  location inference failed ({exc})")
        else:
            fallback_used = False
            if not location and previous_row and previous_row.get("location"):
                fallback_full = previous_row["location"]
                fallback_city = extract_city_heuristic(fallback_full)
                location = fallback_city
                lat = previous_row.get("lat", "")
                lng = previous_row.get("lng", "")
                region = previous_row.get("region", "")
                fallback_used = True
                note = (
                    f"fallback: no observable evidence in image/caption; "
                    f"used the prior post's city ({fallback_city}, derived from "
                    f"'{fallback_full}'); lat/lng/region inherited from that post."
                )
                reasoning = f"{reasoning}\n\n{note}" if reasoning else note
            label = "inferred — fallback to prior post's city" if fallback_used else "inferred — no tag found"
            print(f"  location ({label}): {location or '(undetermined)'}  lat={lat}  lng={lng}  region: {region or '(undetermined)'}")

    local_media_path = normalize_media_url_for_tsv(local_media_path)

    return {
        "id": local_id,
        "instagram_id": instagram_id,
        "shortcode": shortcode,
        "tag_verbatim": tag_verbatim,
        "lat_verbatim": lat_verbatim,
        "lng_verbatim": lng_verbatim,
        "media_url": local_media_path,
        "caption": caption,
        "timestamp": timestamp,
        "location": location,
        "lat": lat,
        "lng": lng,
        "region": region,
        "reasoning": reasoning,
        "deleted_upstream": "",
        "deleted_upstream_at": "",
    }


def run_for_target(
    cl: "object",
    target: str,
    output_template: str,
    media_dir: str,
    rate_config: dict,
    log_dir: str = "",
) -> None:
    """Run the incremental scrape for a single target account.

    Reads the target's TSV (creating it on first run with no since-timestamp),
    fetches everything newer than the most-recent existing row, and appends.
    Failures for one target are logged and don't stop other targets. `rate_config`
    controls the anti-throttle delays — see RATE_PRESETS.
    """
    output_path = output_template.format(target=target)
    print(f"\n=== Target: @{target} → {output_path} ===")

    # Sweep old scrape logs — keeps the most recent 4 prior runs; the current
    # run's log (shell tee, if any) brings the on-disk total back to 5.
    if log_dir:
        prune_scrape_logs(target, log_dir)

    resolved = resolve_target_user_id(cl, target)
    if resolved is None:
        return
    user_id, media_count = resolved

    existing_rows = read_tsv_rows(output_path)
    timestamped = [r for r in existing_rows if r.get("timestamp")]

    # FR-022: shortcode is the canonical dedup key. Build a set from the
    # existing pile so the per-post loop can skip anything that's already
    # present without spending an LLM call on it. Tombstoned rows still
    # count as "known" — we don't want to re-create them.
    known_shortcodes: set[str] = {
        r.get("shortcode", "") for r in existing_rows if r.get("shortcode")
    }
    existing_rows_by_shortcode: dict[str, dict] = {
        r["shortcode"]: r for r in existing_rows if r.get("shortcode")
    }
    pending_tombstones: set[str] = set()

    if timestamped:
        last_timestamp_str = max(r["timestamp"] for r in timestamped)
        since_ts = parse_unix_timestamp(last_timestamp_str)
        try:
            next_id = max(int(r["id"]) for r in existing_rows if r.get("id")) + 1
        except (ValueError, KeyError):
            next_id = len(existing_rows) + 1
    else:
        last_timestamp_str = "(fresh scrape — no prior rows)"
        since_ts = 0
        next_id = 1

    def _on_page_fetched(page_medias: list) -> None:
        # FR-106: incidental deletion detection. The page implicitly defines
        # a timestamp range; any in-range existing row whose shortcode is
        # absent from the page is tombstoned (set-once-monotonic).
        toms = find_tombstones_in_page(page_medias, existing_rows_by_shortcode)
        if toms:
            pending_tombstones.update(toms)

    expected_new = max(0, media_count - len(existing_rows)) if media_count else 0
    if expected_new > 0:
        eta = estimate_scrape_seconds(expected_new, rate_config)
        completion_dt = datetime.now() + timedelta(seconds=eta)
        print(
            f"  account has {media_count} total post(s); TSV has {len(existing_rows)} → "
            f"expecting ~{expected_new} new post(s). Estimated runtime: "
            f"~{fmt_duration(eta)} (≈ done by {completion_dt.strftime('%H:%M:%S')})."
        )
    elif media_count:
        print(f"  account has {media_count} total post(s); TSV already has {len(existing_rows)}. Looking for net-new posts only.")

    sorted_rows = sorted(timestamped, key=lambda r: r["timestamp"], reverse=True)
    recent_locations = [r.get("location", "") for r in sorted_rows[:RECENT_LOCATION_COUNT]]
    previous_row: Optional[dict] = sorted_rows[0] if sorted_rows else None

    print(f"Streaming new media via instagrapi (since {last_timestamp_str}):")
    write_header = not os.path.exists(output_path)
    total_written = 0
    media_delay = rate_config["media_delay"]

    # Ensure the parent dir exists (e.g., pile-app/pile/ on first scrape).
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        with open(output_path, "a", newline="", encoding="utf-8") as out_file:
            writer = csv.DictWriter(out_file, fieldnames=TSV_COLUMNS, delimiter="\t")
            if write_header:
                writer.writeheader()

            for m in iter_new_media(
                cl,
                user_id,
                since_ts,
                page_size=rate_config["page_size"],
                page_delay=rate_config["page_delay"],
                long_rest_every=rate_config["long_rest_every"],
                long_rest=rate_config["long_rest"],
                on_page_fetched=_on_page_fetched,
            ):
                # FR-022: shortcode-keyed dedup. Belt-and-suspenders against
                # the timestamp filter — if the same shortcode somehow comes
                # back (e.g., timestamp ties at the cursor boundary), skip
                # it before any LLM/download spend.
                m_code = getattr(m, "code", "") or ""
                if m_code and m_code in known_shortcodes:
                    print(f"  · skipping {m_code} — already in pile")
                    continue

                local_id = next_id
                row = process_media(m, target, local_id, media_dir, recent_locations, previous_row)

                writer.writerow(row)
                out_file.flush()

                if m_code:
                    known_shortcodes.add(m_code)

                if row["location"]:
                    recent_locations.insert(0, row["location"])
                    recent_locations = recent_locations[:RECENT_LOCATION_COUNT]
                    previous_row = row

                next_id += 1
                total_written += 1
                print(f"  + [{local_id}] pk={row['instagram_id']}  shortcode={row['shortcode']}")

                jittered_sleep(*media_delay, label="inter-post pause")
    except Exception as exc:
        print(f"\nERROR during streaming for @{target}: {exc}")
        print(f"  ! {total_written} row(s) persisted before failure; partial TSV will still be re-sorted.")

    if pending_tombstones:
        tombstoned = apply_tombstones(output_path, pending_tombstones)
        print(f"  FR-106: tombstoned {tombstoned} row(s) absent from fetched pages: "
              f"{sorted(pending_tombstones)[:5]}"
              + (f" (+{len(pending_tombstones) - 5} more)" if len(pending_tombstones) > 5 else ""))

    if total_written == 0:
        print(f"No new posts found for @{target}.")
        return

    print(f"\nStreaming done — re-sorting {output_path} by timestamp ASC + renumbering ids.")
    resort_tsv_and_sweep_media(output_path, target, media_dir)
    print(f"Done. {total_written} new post(s) written to {output_path}.")
