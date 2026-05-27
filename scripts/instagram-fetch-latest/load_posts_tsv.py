#!/usr/bin/env python3
"""
load_posts_tsv.py — Incremental update: fetch new Instagram posts since last run.

Uses instagrapi as the primary fetcher (FR-016 in spec 003-ingestion-pipeline).
Personal-account compatible; supersedes the prior Graph API path which required
manual token refresh every ~60 days.

Reads the TSV to find the most recent known post timestamp, then walks back
through the account's media via instagrapi until reaching a post at or before
that timestamp. For each new post:
  1. Reads pk/code/caption/timestamp/media URL directly from the Media object
  2. Downloads the image/video into public/media/<local_id>.jpg or .mp4
  3. Dual-path location (FR-019 / FR-020):
       - If the Media has a Location tag → coords authoritative; the LLM
         canonicalizes the verbatim tag name and picks the IATA region code.
       - Else → the LLM inspects caption + image + recent context and returns
         the full (location, lat, lng, region). Empty inference falls back
         to the most recent prior post's location, noted in `reasoning`.
  4. Appends a new row to the TSV (oldest-first so the last row stays most recent)

The crawler credentials (`INSTA_USERNAME` / `INSTA_PASSWORD`) authenticate the
instagrapi client and are independent of the *target* account(s) being scraped.
Targets are listed via `--targets` or `$INSTAGRAM_TARGET_ACCOUNTS` and resolved
to their numeric `user_id` at run time, so one crawler login can feed any
public profile.

Usage:
    python load_posts_tsv.py                                          # targets from $INSTAGRAM_TARGET_ACCOUNTS (default @ourearthsandwich), rate=normal
    python load_posts_tsv.py --targets ourearthsandwich,welawen        # one TSV per target
    python load_posts_tsv.py --rate gentle                             # slower, safer pagination cadence
    python load_posts_tsv.py --rate aggressive                         # no delays — only if the crawler session is fully warmed up
    python load_posts_tsv.py --output "posts.{target}.local.tsv"       # custom TSV path template ({target} required for multi-target)
    python load_posts_tsv.py --media-dir public/media                  # shared media dir; filenames are <target>_<id>.<ext>
"""

import argparse
import base64
import csv
import json
import os
import posixpath
import random
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, Optional

import anthropic
import requests
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# Crawler credentials — the account instagrapi authenticates as. Separate from
# the target account(s) being scraped, which are resolved at run time.
INSTA_USERNAME = os.environ.get("INSTA_USERNAME", "")
INSTA_PASSWORD = os.environ.get("INSTA_PASSWORD", "")
INSTAGRAPI_SESSION_FILE = os.environ.get(
    "INSTAGRAPI_SESSION_FILE",
    os.path.join(os.path.dirname(__file__), "instagrapi_session.json"),
)

# Target accounts (independent of credentials above). Comma-separated env var
# overridable by the --targets CLI flag. One TSV is written per target.
DEFAULT_TARGETS = os.environ.get("INSTAGRAM_TARGET_ACCOUNTS", "ourearthsandwich")

TSV_COLUMNS = ["id", "instagram_id", "shortcode", "media_url", "caption", "timestamp", "location", "lat", "lng", "region", "reasoning"]
DEFAULT_OUTPUT_TEMPLATE = os.path.join(PROJECT_ROOT, "posts.{target}.local.tsv")
DEFAULT_MEDIA_DIR = os.path.join(PROJECT_ROOT, "public/media")
RECENT_LOCATION_COUNT = 5

# Anti-throttle presets. Instagram challenges sessions that paginate too
# aggressively from a single device fingerprint. Each preset defines:
#   - page_size: posts per pagination request (smaller = more human-scroll-like)
#   - page_delay: (min, max) seconds of random jitter between consecutive page fetches
#   - long_rest_every / long_rest: every N pages, take a longer "human pause"
# Throughput estimates assume ~3-5s of per-post processing (download + LLM calls).
#
#   aggressive: ~1500 posts/hr, hit a STEP_NAME challenge after ~7 pages in testing.
#               Use only when you've verified the account is warmed up and trusted.
#   normal:     ~300 posts/hr, mimics a casual scroll cadence. The default.
#   gentle:     ~120 posts/hr, the safest sustained rate. Use for large backfills.
RATE_PRESETS: dict[str, dict] = {
    "aggressive": {
        "page_size": 50,
        "page_delay": (0.0, 0.0),
        "long_rest_every": 0,  # 0 disables the long-rest periodic pause
        "long_rest": (0.0, 0.0),
        "media_delay": (0.0, 0.0),  # no jitter between per-post processing
    },
    "normal": {
        "page_size": 12,
        "page_delay": (30.0, 90.0),
        "long_rest_every": 5,
        "long_rest": (90.0, 180.0),
        "media_delay": (1.0, 3.0),  # mimics human dwell time on each post
    },
    "gentle": {
        "page_size": 12,
        "page_delay": (90.0, 180.0),
        "long_rest_every": 3,
        "long_rest": (180.0, 300.0),
        "media_delay": (2.0, 5.0),
    },
}
DEFAULT_RATE_PRESET = "normal"


def read_tsv_rows(tsv_path: str) -> list[dict]:
    """Read all rows from the TSV file."""
    if not os.path.exists(tsv_path):
        return []
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def parse_unix_timestamp(ts_str: str) -> int:
    """Convert an ISO timestamp string to a Unix timestamp integer.

    Python equivalent of PHP's strtotime(). Handles formats like
    "2024-02-20 02:27:16+00" or "2024-02-20T02:27:16+0000".
    """
    ts_str = ts_str.strip().replace(" ", "T")
    # Normalize "+00" → "+00:00" for fromisoformat (required in Python < 3.11)
    if ts_str.endswith("+00"):
        ts_str += ":00"
    dt = datetime.fromisoformat(ts_str)
    return int(dt.timestamp())


def download_media(media_url: str, target: str, local_id: int, media_type: str, media_dir: str) -> str:
    """Download media from the Instagram CDN and save to media_dir/<target>_<local_id>.jpg or .mp4.

    The target prefix keeps filenames unique across accounts when multiple
    target TSVs share one media directory (each TSV has its own id sequence
    starting at 1, so the raw id alone would collide).

    Returns the local relative path.
    """
    ext = "mp4" if media_type == "VIDEO" else "jpg"
    local_path = os.path.join(media_dir, f"{target}_{local_id}.{ext}")

    resp = requests.get(media_url, timeout=60, stream=True)
    resp.raise_for_status()

    os.makedirs(media_dir, exist_ok=True)
    with open(local_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return os.path.normpath(local_path)


def _extract_json_and_reasoning(raw: str) -> tuple[Optional[dict], str]:
    """Parse a model response that may have prose preamble before its JSON.

    Strips ``` fences first, then looks for the last balanced {...} block —
    that's the JSON we asked for. Anything before it is returned as
    ``reasoning`` so it isn't lost (helpful when the model's inference
    rationale is itself useful context for downstream review).

    Returns (parsed_dict_or_None, reasoning_string). When no JSON is parseable,
    the whole raw text becomes the reasoning and the dict is None.
    """
    raw = raw.strip()
    if raw.startswith("```"):
        first_nl = raw.find("\n")
        if first_nl != -1:
            raw = raw[first_nl + 1:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    last_open = raw.rfind("{")
    last_close = raw.rfind("}")
    if last_open != -1 and last_close > last_open:
        json_text = raw[last_open:last_close + 1]
        reasoning = raw[:last_open].strip()
        try:
            return json.loads(json_text), reasoning
        except json.JSONDecodeError:
            pass
    return None, raw


def infer_post_location(
    caption: str,
    local_media_path: str,
    media_type: str,
    recent_locations: list[str],
) -> tuple[str, str, str, str, str]:
    """FR-020 inferred-location path: identify the post's location from caption + image + nearby context.

    Used ONLY when the post has no explicit geo-tag (i.e. instagrapi returned no
    `Location` object or instagrapi is unavailable). Tagged posts go through
    `canonicalize_tagged_location` instead.

    Returns a (location, lat, lng, region, reasoning) tuple. Any field may be
    empty. ``reasoning`` captures any prose the model wrote before the JSON
    object — it's the inference rationale, preserved so downstream review can
    audit why a particular location was picked.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    recent_loc_text = ""
    known_locations = [loc for loc in recent_locations if loc]
    if known_locations:
        loc_list = "\n".join(f"- {loc}" for loc in known_locations)
        recent_loc_text = (
            "\n\nLocations of recent nearby posts (context only — do NOT assume "
            f"this post is at any of these places):\n{loc_list}"
        )

    prompt = (
        f"Caption: {caption or '(none)'}"
        f"{recent_loc_text}\n\n"
        "Identify the specific location of this Instagram post using observable evidence "
        "in the image and caption: visible signage, landmarks, recognizable geographic features, "
        "language cues, or place names mentioned in the caption. "
        "Do NOT default to a recent-posts location unless the image or caption provides a clear cue. "
        "If observable evidence is insufficient, return empty strings rather than guessing. "
        "Respond with only a JSON object with four keys: "
        '"location" (human-readable name, e.g. \'Times Square, New York, USA\'), '
        '"lat" (decimal latitude as a string, e.g. \'40.7580\'), '
        '"lng" (decimal longitude as a string, e.g. \'-73.9855\'), '
        'and "region" (IATA code of the nearest in-country international airport, e.g. \'JFK\'). '
        "If you cannot determine the location with reasonable confidence, set all four values to empty strings. "
        "If you cannot determine the lat/lng, provide the location and region but leave lat and lng as empty strings. "
        "If you cannot determine the nearest international airport, provide the location and lat/lng but leave region as an empty string. "
        "Do not include any text outside the JSON object. Do not wrap the JSON in markdown code fences."
    )

    content: list[dict] = []

    # Include image for IMAGE posts so the model can use visual context
    if media_type == "IMAGE" and local_media_path and os.path.exists(local_media_path):
        with open(local_media_path, "rb") as img_file:
            image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image_data,
            },
        })

    content.append({"type": "text", "text": prompt})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": content}],
    )

    raw = response.content[0].text
    data, reasoning = _extract_json_and_reasoning(raw)
    if data is not None:
        return (
            str(data.get("location", "")),
            str(data.get("lat", "")),
            str(data.get("lng", "")),
            str(data.get("region", "")),
            reasoning,
        )
    # No parseable JSON — treat the whole response as a location-name hint
    # and surface it as reasoning too, so the row records what the model said.
    return (raw.strip(), "", "", "", reasoning)


def _challenge_code_handler(username: str, choice) -> str:
    """Interactive challenge handler invoked by instagrapi when Instagram asks
    for a verification code (SMS / email / 2FA app)."""
    via_map = {0: "SMS", 1: "EMAIL"}
    try:
        via = via_map.get(int(choice), str(choice))
    except (TypeError, ValueError):
        via = str(choice)
    print(f"\n>>> Instagram challenge for @{username}: a code was sent via {via}.")
    print(">>> Check that channel and paste the code below (it expires quickly).")
    try:
        code = input(">>> Code: ").strip()
    except EOFError:
        code = ""
    return code


def _change_password_handler(username: str) -> str:
    """Stub handler for the rarer 'change your password' challenge.

    Returning an empty string tells instagrapi we can't satisfy the challenge
    in this run, so the login will fail cleanly and we fall back to the
    inferred-location path. Surface the situation so the operator can fix it
    via the Instagram app and re-run.
    """
    print(
        f"\n>>> Instagram is asking @{username} to change the password before continuing. "
        "Update the password via the Instagram app, update INSTA_PASSWORD in .env, and re-run."
    )
    return ""


def init_instagrapi_client() -> Optional["object"]:
    """Initialize an instagrapi session for FR-019 tagged-location lookups.

    Reads INSTA_USERNAME, INSTA_PASSWORD, INSTAGRAPI_SESSION_FILE from env.
    Resumes a saved session if one exists; otherwise does a fresh login and
    persists the session. Returns None if credentials are missing, instagrapi
    is not installed, or login fails — callers MUST fall back to the FR-020
    inferred-location path in that case.

    If Instagram raises a challenge during fresh login, prompts the operator
    interactively for the verification code via stdin.
    """
    if not INSTA_USERNAME or not INSTA_PASSWORD:
        print("instagrapi: INSTA_USERNAME or INSTA_PASSWORD not set; tagged-location path disabled")
        return None

    try:
        from instagrapi import Client
    except ImportError:
        print("instagrapi: package not installed; tagged-location path disabled")
        return None

    session_path = Path(INSTAGRAPI_SESSION_FILE)

    def _make_client():
        c = Client()
        c.challenge_code_handler = _challenge_code_handler
        c.change_password_handler = _change_password_handler
        return c

    cl = _make_client()

    if session_path.exists():
        try:
            cl.load_settings(str(session_path))
            cl.login(INSTA_USERNAME, INSTA_PASSWORD)
            print(f"instagrapi: resumed session from {session_path}")
            return cl
        except Exception as exc:
            print(f"instagrapi: session resume failed ({exc}); attempting fresh login")
            cl = _make_client()

    try:
        cl.login(INSTA_USERNAME, INSTA_PASSWORD)
        cl.dump_settings(str(session_path))
        print(f"instagrapi: logged in and saved session to {session_path}")
        return cl
    except Exception as exc:
        print(f"instagrapi: login failed ({exc}); tagged-location path disabled")
        return None


def get_instagrapi_location(cl: "object", shortcode: str) -> Optional[tuple[str, str, str]]:
    """Look up the explicit geo-tag for a post via instagrapi (FR-019).

    Returns (name, lat, lng) if the post has a tagged location, otherwise None.
    lat/lng may be empty strings if the tag is name-only or coordinates are (0, 0).
    """
    try:
        pk = cl.media_pk_from_url(f"https://www.instagram.com/p/{shortcode}/")
        info = cl.media_info(pk)
    except Exception as exc:
        print(f"  ! instagrapi media_info failed for shortcode={shortcode} ({exc})")
        return None

    loc = getattr(info, "location", None)
    if not loc or not getattr(loc, "name", None):
        return None

    name = loc.name
    raw_lat = getattr(loc, "lat", None)
    raw_lng = getattr(loc, "lng", None)

    # Filter (0.0, 0.0) which instagrapi sometimes returns when coords are absent
    if raw_lat in (None, 0, 0.0) and raw_lng in (None, 0, 0.0):
        return name, "", ""

    lat = "" if raw_lat is None else str(raw_lat)
    lng = "" if raw_lng is None else str(raw_lng)
    return name, lat, lng


def canonicalize_tagged_location(name: str, lat: str, lng: str) -> tuple[str, str, str]:
    """FR-019 tagged-path enrichment: canonicalize a verbatim geo-tag and pick its IATA region.

    Instagram geo-tags are whatever the poster typed — local language, typos,
    bare venue names with no city/country. The coordinates are authoritative,
    but the *name* needs a normalization pass before downstream use. This call
    asks the model for both a canonical "Venue, City, Country" string AND
    the nearest in-country IATA code in a single round-trip.

    Returns (canonical_name, region, reasoning). Any field may be empty.
    Callers should fall back to the verbatim tag when ``canonical_name`` is empty.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = (
        f"Verbatim Instagram geo-tag: {name}\n"
        f"Latitude: {lat or '(unknown)'}\n"
        f"Longitude: {lng or '(unknown)'}\n\n"
        "This is the location name a user typed when geo-tagging an Instagram post. "
        "It may be in the local language, abbreviated, missing city/country context, "
        "or contain typos. The latitude/longitude (when present) are authoritative "
        "for the location.\n\n"
        "Respond with only a JSON object with two keys:\n"
        '  "canonical_name" — a standardized English location string in the form '
        '"Venue, City, Country" (or "Neighborhood, City, Country" if the tag is a '
        'neighborhood, or "City, State, Country" if the tag is a city). Translate '
        "the name to English, correct typos, and add missing city/country context "
        "implied by the coordinates.\n"
        '  "region" — the 3-letter IATA code of the nearest major international '
        "airport within the same country as the location (e.g. 'JFK', 'MEX', 'CDG').\n\n"
        "If you cannot determine either value with reasonable confidence, leave it as "
        "an empty string. Do not include any text outside the JSON object. Do not "
        "wrap the JSON in markdown code fences."
    )
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=128,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        print(f"  ! canonicalize call failed ({exc})")
        return ("", "", "")

    raw = response.content[0].text
    data, reasoning = _extract_json_and_reasoning(raw)
    if data is None:
        return ("", "", reasoning)
    canonical = str(data.get("canonical_name", "")).strip()
    region_raw = str(data.get("region", "")).strip().upper()
    region = "".join(c for c in region_raw if c.isalpha())
    if len(region) != 3:
        region = ""
    return (canonical, region, reasoning)


def _jittered_sleep(low: float, high: float, label: str = "") -> None:
    """Sleep for a random duration in [low, high] seconds. Logs the chosen
    duration so operator output makes the wait visible. No-op when high<=0."""
    if high <= 0:
        return
    wait = random.uniform(max(0.0, low), high)
    if label:
        print(f"  … {label}: sleeping {wait:.1f}s")
    time.sleep(wait)


def _is_challenge_error(exc: Exception) -> bool:
    """Identify Instagram challenge-response errors that can't be auto-resolved.

    Distinguishes these from transient network/5xx errors: a challenge requires
    the operator to verify the account in the Instagram app, so retrying the
    same request is pointless. Transient errors are worth retrying / sleeping
    through; challenges are not.
    """
    s = str(exc).lower()
    return "challenge" in s or "step_name" in s or "checkpoint" in s


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
        if _is_challenge_error(exc):
            print(
                f"\n  ! page {page_num} blocked by Instagram challenge — {exc}\n"
                f"  ! the crawler account needs manual verification: open the "
                f"Instagram app, complete any 'Was this you?' / 2FA prompt, "
                f"then re-run."
            )
            return None
        # Transient — back off then retry once.
        print(f"\n  ! page {page_num} fetch failed transiently ({type(exc).__name__}: {exc})")
        _jittered_sleep(60.0, 180.0, label=f"backoff before retry of page {page_num}")
        try:
            return cl.user_medias_paginated_v1(user_id, page_size, end_cursor=end_cursor)
        except Exception as exc2:
            if _is_challenge_error(exc2):
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
) -> "Iterator":
    """Generator yielding one Media object at a time from the target's feed.

    Walks pages newest-first (instagrapi's natural order). Within each page,
    yields oldest-of-page first so the caller's per-post processing builds
    `recent_locations` context in roughly-chronological order. Across pages
    the yield order is still newest-page first — the caller must re-sort the
    final TSV by timestamp ASC to restore the canonical oldest-first
    convention (see `_resort_tsv_and_rename_media`).

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
            _jittered_sleep(*page_delay, label=f"between-pages pause before page {page_num}")
            # Long rest after every Nth page mimics a user pausing to read
            # rather than scrolling continuously. (page_num - 1) % N catches
            # pages 6, 11, 16, ... for long_rest_every=5.
            if long_rest_every and (page_num - 1) % long_rest_every == 0:
                _jittered_sleep(*long_rest, label=f"long rest after {long_rest_every} pages")
        # Wall-clock start of this page's full work (fetch + per-post yields).
        # `yield` blocks until the caller comes back asking for the next post,
        # so by the time we fall through the yield loop, the caller has fully
        # processed every post on this page — `time.monotonic()` then captures
        # the true end-to-end page duration.
        page_start = time.monotonic()
        result = _fetch_page_with_retry(cl, user_id, end_cursor, page_size, page_num)
        if result is None:
            print(f"  ! stopping pagination — {total_yielded} post(s) already streamed to disk.")
            return
        medias, end_cursor = result
        print(f"  [page {page_num}] {len(medias)} posts (cursor={'…' if end_cursor else 'end'})")
        if not medias:
            return
        # Filter the page by since_ts, then yield oldest-of-page first so
        # recent_locations context builds chronologically within each page.
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
            f"{_fmt_duration(page_elapsed)} ({per_post:.1f}s/post). "
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
      5. Path normalization for the TSV (relative to PROJECT_ROOT, posix
         separators).

    Returns a row dict matching the TSV column order. Does NOT mutate
    `recent_locations`, increment ids, or write to disk — those iteration
    concerns belong to the caller (`main`).
    """
    instagram_id = str(m.pk)
    shortcode = m.code or ""
    caption = m.caption_text or ""

    # Normalize the timestamp to match the existing TSV style (2026-05-08T14:39:41+0000).
    ts_dt = m.taken_at
    if ts_dt.tzinfo is None:
        ts_dt = ts_dt.replace(tzinfo=timezone.utc)
    timestamp = ts_dt.strftime("%Y-%m-%dT%H:%M:%S%z")

    # Resolve media URL and type. instagrapi media_type: 1=Photo, 2=Video, 8=Album.
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

    # Download media
    local_media_path = ""
    if remote_media_url:
        try:
            local_media_path = download_media(
                remote_media_url, target, local_id, media_type, media_dir
            )
            print(f"  ↓ saved {local_media_path}")
        except (requests.RequestException, OSError) as exc:
            print(f"  ! pk={instagram_id}  media download failed ({exc})")

    # Dual-path location:
    #   FR-019 tagged: Media has a Location → coords authoritative; canonicalize
    #     the verbatim poster-typed name and pick the IATA region via the LLM.
    #   FR-020 inferred: no tag → LLM inference from caption + image + recent context,
    #     with an explicit copy-from-prior-post fallback when inference returns nothing.
    location, lat, lng, region = "", "", "", ""
    reasoning = ""
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
        verbatim_name, lat, lng = tagged
        canonical_name, region, reasoning = canonicalize_tagged_location(verbatim_name, lat, lng)
        # Fall back to the verbatim tag when canonicalization is empty — better
        # to keep the poster's string than to blank the location entirely.
        location = canonical_name or verbatim_name
        canon_note = f" → {canonical_name}" if canonical_name and canonical_name != verbatim_name else ""
        print(f"  location (tagged): {verbatim_name}{canon_note}  lat={lat}  lng={lng}  region: {region or '(undetermined)'}")
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
            # When inference returns nothing AND we have prior context, copy the
            # most recent known location forward. The bias-guard in the inference
            # prompt forbids the model from defaulting to recent context on its
            # own (regression: a JFK boarding-pass photo was once mis-classified
            # as Oaxaca because surrounding posts were in Oaxaca). When the model
            # correctly returns empty, *the call site* — not the model — applies
            # the chronological-neighbor fallback, and the `reasoning` column
            # records that the value was a fallback rather than an inference.
            fallback_used = False
            if not location:
                fallback = next((loc_str for loc_str in recent_locations if loc_str), "")
                if fallback:
                    location = fallback
                    fallback_used = True
                    note = (
                        f"fallback: no observable evidence in image/caption; "
                        f"location copied from prior post ({fallback}). "
                        f"lat/lng/region left empty so downstream consumers can "
                        f"identify fallback rows."
                    )
                    reasoning = f"{reasoning}\n\n{note}" if reasoning else note
            label = "inferred — fallback to prior post" if fallback_used else "inferred — no tag found"
            print(f"  location ({label}): {location or '(undetermined)'}  lat={lat}  lng={lng}  region: {region or '(undetermined)'}")

    # Strip project root prefix and normalize to posix separators for the TSV row.
    if local_media_path.startswith(PROJECT_ROOT):
        local_media_path = os.path.relpath(local_media_path, PROJECT_ROOT)
    local_media_path = local_media_path.replace(os.sep, posixpath.sep)

    return {
        "id": local_id,
        "instagram_id": instagram_id,
        "shortcode": shortcode,
        "media_url": local_media_path,
        "caption": caption,
        "timestamp": timestamp,
        "location": location,
        "lat": lat,
        "lng": lng,
        "region": region,
        "reasoning": reasoning,
    }


def _resort_tsv_and_rename_media(path: str, target: str, media_dir: str) -> None:
    """Restore canonical oldest-first row order after a streaming scrape.

    Streaming writes rows in pagination order (newest-page first, oldest-of-
    page first within each page). After the scrape, we want the file to match
    the original convention: row 1 = oldest, row N = newest, ids sequential.

    Steps:
      1. Read all rows, sort by timestamp ASC.
      2. Reassign ids 1..N.
      3. Rename media files whose id changed so `media_url` stays consistent
         with the on-disk filename. Uses a two-pass `.tmp` suffix rename so
         id swaps (e.g., file A→2 while file B→A's old id) don't collide.
      4. Write the sorted, re-id'd rows back to the TSV.
      5. Sweep orphan media files in `media_dir` matching `<target>_*` that
         aren't referenced by any TSV row — e.g., a `.mp4` left over from a
         prior scrape where that id was a video but this scrape made it an
         image. Cross-target safe: only files matching THIS target's prefix
         are touched.

    Safe on partial files: if a row's media file is missing (download failed
    earlier), the rename is skipped for that row but the id is still updated.
    """
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        cols = reader.fieldnames
        rows = list(reader)
    if not rows:
        return

    rows.sort(key=lambda r: r.get("timestamp", ""))

    rename_plan: list[tuple[str, str]] = []  # (old_abs, new_abs)
    for new_id, row in enumerate(rows, start=1):
        try:
            old_id = int(row.get("id", 0))
        except (TypeError, ValueError):
            old_id = 0

        old_media = row.get("media_url", "")
        if old_media and old_id != new_id:
            old_abs = os.path.join(PROJECT_ROOT, *old_media.split(posixpath.sep))
            if os.path.exists(old_abs):
                ext = os.path.splitext(old_abs)[1].lstrip(".")
                old_dir_rel = posixpath.dirname(old_media)
                new_media_rel = posixpath.join(old_dir_rel, f"{target}_{new_id}.{ext}")
                new_abs = os.path.join(PROJECT_ROOT, *new_media_rel.split(posixpath.sep))
                rename_plan.append((old_abs, new_abs))
                row["media_url"] = new_media_rel
        row["id"] = str(new_id)

    # Two-pass rename: stage every source to a `.rename-tmp` suffix first so
    # swaps (file at id=2 → 5 while file at id=5 → 2) don't clobber. Then
    # move each `.rename-tmp` to its final name.
    for old, _ in rename_plan:
        try:
            os.rename(old, old + ".rename-tmp")
        except OSError as exc:
            print(f"  ! failed to stage rename of {old}: {exc}")
    for old, new in rename_plan:
        staged = old + ".rename-tmp"
        if os.path.exists(staged):
            os.makedirs(os.path.dirname(new), exist_ok=True)
            try:
                os.replace(staged, new)
            except OSError as exc:
                print(f"  ! failed to finalize rename {staged} → {new}: {exc}")

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    # Orphan sweep: any file in media_dir matching this target's prefix that
    # isn't referenced by a row is a leftover from a prior scrape. Safe to
    # delete. Path comparison uses absolute + normcase'd paths on both sides
    # so a relative media_dir or a relative media_url doesn't cause a phantom
    # mismatch (the bug that previously wiped 323 real files because the
    # `referenced` set had absolute paths and the scan produced relative ones).
    def _abs_norm(p: str) -> str:
        return os.path.normcase(os.path.normpath(os.path.abspath(p)))

    if os.path.isdir(media_dir):
        referenced: set[str] = set()
        for row in rows:
            media_url = row.get("media_url", "")
            if media_url:
                referenced.add(_abs_norm(
                    os.path.join(PROJECT_ROOT, *media_url.split(posixpath.sep))
                ))

        prefix = f"{target}_"
        swept: list[str] = []
        for entry in os.listdir(media_dir):
            if not entry.startswith(prefix):
                continue
            full = _abs_norm(os.path.join(media_dir, entry))
            if full in referenced:
                continue
            try:
                os.remove(full)
                swept.append(entry)
            except OSError as exc:
                print(f"  ! could not remove orphan {entry}: {exc}")
        if swept:
            sample = ", ".join(swept[:5])
            more = f" (+{len(swept) - 5} more)" if len(swept) > 5 else ""
            print(f"  swept {len(swept)} orphan media file(s): {sample}{more}")


def resolve_target_user_id(cl: "object", username: str) -> Optional[tuple[int, int]]:
    """Resolve a target Instagram username to its (user_id, media_count).

    Independent of `cl.user_id` (the crawler) — this is what makes the
    crawler / target separation possible.

    `media_count` is the total number of posts on the account; it comes back
    on the same response as the user_id (`user_info_by_username`), so it's
    free additional data we use to estimate scrape duration. Returns None
    on failure (private account the crawler can't see, deleted, rate-limit).
    """
    try:
        info = cl.user_info_by_username(username)
        media_count = int(getattr(info, "media_count", 0) or 0)
        return (int(info.pk), media_count)
    except Exception as exc:
        print(f"  ! could not resolve user_id for @{username}: {exc}")
        return None


def _fmt_duration(seconds: float) -> str:
    """Format a duration in seconds as a human-readable string.
    Examples: 45 → '45s', 125 → '2m 5s', 4200 → '1h 10m'."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes, secs = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"


def _estimate_scrape_seconds(num_posts: int, rate_config: dict) -> float:
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


def run_for_target(
    cl: "object",
    target: str,
    output_template: str,
    media_dir: str,
    rate_config: dict,
) -> None:
    """Run the incremental scrape for a single target account.

    Reads the target's TSV (creating it on first run with no since-timestamp),
    fetches everything newer than the most-recent existing row, and appends.
    Failures for one target are logged and don't stop other targets. `rate_config`
    controls the anti-throttle delays — see RATE_PRESETS.
    """
    output_path = output_template.format(target=target)
    print(f"\n=== Target: @{target} → {output_path} ===")

    resolved = resolve_target_user_id(cl, target)
    if resolved is None:
        return
    user_id, media_count = resolved

    existing_rows = read_tsv_rows(output_path)
    timestamped = [r for r in existing_rows if r.get("timestamp")]

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

    # Upfront estimate. `media_count` is total account posts (free from the
    # user_info call above); the diff against existing rows is how many we
    # still need to fetch. Estimate is a midpoint — random delay jitter and
    # variable LLM latency mean actual can be ±30%.
    expected_new = max(0, media_count - len(existing_rows)) if media_count else 0
    if expected_new > 0:
        eta = _estimate_scrape_seconds(expected_new, rate_config)
        completion_dt = datetime.now() + timedelta(seconds=eta)
        print(
            f"  account has {media_count} total post(s); TSV has {len(existing_rows)} → "
            f"expecting ~{expected_new} new post(s). Estimated runtime: "
            f"~{_fmt_duration(eta)} (≈ done by {completion_dt.strftime('%H:%M:%S')})."
        )
    elif media_count:
        print(f"  account has {media_count} total post(s); TSV already has {len(existing_rows)}. Looking for net-new posts only.")

    # Seed inference context with the target's own recent posts.
    sorted_rows = sorted(timestamped, key=lambda r: r["timestamp"], reverse=True)
    recent_locations = [r.get("location", "") for r in sorted_rows[:RECENT_LOCATION_COUNT]]

    print(f"Streaming new media via instagrapi (since {last_timestamp_str}):")
    write_header = not os.path.exists(output_path)
    total_written = 0
    media_delay = rate_config["media_delay"]

    # Streaming model: each Media object yielded by `iter_new_media` is
    # processed and written to disk before the next page is fetched. This
    # gives us page-level crash recovery — a mid-scrape interrupt only loses
    # the in-flight post, not all prior work. The TSV ends up in pagination
    # order (newest-page first) until the post-stream re-sort below restores
    # canonical chronological order.
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
            ):
                local_id = next_id
                row = process_media(m, target, local_id, media_dir, recent_locations)

                writer.writerow(row)
                out_file.flush()

                if row["location"]:
                    recent_locations.insert(0, row["location"])
                    recent_locations = recent_locations[:RECENT_LOCATION_COUNT]

                next_id += 1
                total_written += 1
                print(f"  + [{local_id}] pk={row['instagram_id']}  shortcode={row['shortcode']}")

                # Inter-post jitter spreads CDN downloads + LLM calls across
                # time so the request fingerprint looks more like a human
                # scrolling a feed than a machine processing it.
                _jittered_sleep(*media_delay, label="inter-post pause")
    except Exception as exc:
        print(f"\nERROR during streaming for @{target}: {exc}")
        print(f"  ! {total_written} row(s) persisted before failure; partial TSV will still be re-sorted.")

    if total_written == 0:
        print(f"No new posts found for @{target}.")
        return

    print(f"\nStreaming done — re-sorting {output_path} by timestamp ASC + renumbering ids.")
    _resort_tsv_and_rename_media(output_path, target, media_dir)
    print(f"Done. {total_written} new post(s) written to {output_path}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch new Instagram posts and append to per-target TSVs.")
    parser.add_argument(
        "--targets",
        default=DEFAULT_TARGETS,
        help=(
            "Comma-separated Instagram usernames to scrape "
            f"(default: ${{INSTAGRAM_TARGET_ACCOUNTS}} or {DEFAULT_TARGETS!r})."
        ),
    )
    parser.add_argument(
        "--output",
        metavar="TEMPLATE",
        default=DEFAULT_OUTPUT_TEMPLATE,
        help=(
            f"TSV path template; {{target}} is substituted per target "
            f"(default: {DEFAULT_OUTPUT_TEMPLATE}). Required when --targets has multiple entries."
        ),
    )
    parser.add_argument(
        "--media-dir",
        metavar="DIR",
        default=DEFAULT_MEDIA_DIR,
        help=(
            f"Single shared directory for downloaded media (default: {DEFAULT_MEDIA_DIR}). "
            "Filenames are <target>_<id>.<ext> to avoid cross-target collisions."
        ),
    )
    parser.add_argument(
        "--rate",
        choices=sorted(RATE_PRESETS.keys()),
        default=DEFAULT_RATE_PRESET,
        help=(
            f"Anti-throttle preset (default: {DEFAULT_RATE_PRESET}). "
            "'aggressive' = no delays (fast but trips Instagram challenges); "
            "'normal' = ~300 posts/hr, random 30-90s between pages + long rests; "
            "'gentle' = ~120 posts/hr, the safest sustained rate."
        ),
    )
    args = parser.parse_args()

    targets = [t.strip().lstrip("@") for t in args.targets.split(",") if t.strip()]
    if not targets:
        print("\nERROR: no target accounts specified. Set --targets or INSTAGRAM_TARGET_ACCOUNTS.")
        sys.exit(1)
    if len(targets) > 1 and "{target}" not in args.output:
        print("\nERROR: multiple targets require '{target}' in --output template.")
        sys.exit(1)

    # instagrapi is the primary fetcher (FR-016). Without it the script
    # cannot fetch new posts; fail fast with a clear message.
    ig_client = init_instagrapi_client()
    if ig_client is None:
        print(
            "\nERROR: instagrapi is required. Set INSTA_USERNAME and INSTA_PASSWORD "
            "in .env and re-run. If a previous session file is corrupted, delete "
            f"{INSTAGRAPI_SESSION_FILE} and try again."
        )
        sys.exit(1)

    rate_config = RATE_PRESETS[args.rate]
    print(f"Anti-throttle rate: {args.rate} (page_size={rate_config['page_size']}, page_delay={rate_config['page_delay']}s)")

    for target in targets:
        run_for_target(ig_client, target, args.output, args.media_dir, rate_config)


if __name__ == "__main__":
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    main()
