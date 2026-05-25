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
       - If the Media has a Location tag → name/lat/lng authoritative; Claude
         consulted only for the IATA region code.
       - Else → Claude inspects caption + image + recent context and returns
         the full (location, lat, lng, region).
  4. Appends a new row to the TSV (oldest-first so the last row stays most recent)

Usage:
    python load_posts_tsv.py                     # fetch new posts since last run
    python load_posts_tsv.py --output posts.tsv  # use a different TSV file
    python load_posts_tsv.py --media-dir path/   # use a different media directory
"""

import argparse
import base64
import csv
import json
import os
import posixpath
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import anthropic
import requests
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# instagrapi credentials (required — script cannot fetch without them).
INSTA_USERNAME = os.environ.get("INSTA_USERNAME", "")
INSTA_PASSWORD = os.environ.get("INSTA_PASSWORD", "")
INSTAGRAPI_SESSION_FILE = os.environ.get(
    "INSTAGRAPI_SESSION_FILE",
    os.path.join(os.path.dirname(__file__), "instagrapi_session.json"),
)

TSV_COLUMNS = ["id", "instagram_id", "shortcode", "media_url", "caption", "timestamp", "location", "lat", "lng", "region"]
DEFAULT_OUTPUT = os.path.join(PROJECT_ROOT, "posts.local.tsv")
DEFAULT_MEDIA_DIR = os.path.join(PROJECT_ROOT, "public/media")
RECENT_LOCATION_COUNT = 5


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


def download_media(media_url: str, local_id: int, media_type: str, media_dir: str) -> str:
    """Download media from the Instagram CDN and save to media_dir/<local_id>.jpg or .mp4.

    Returns the local relative path.
    """
    ext = "mp4" if media_type == "VIDEO" else "jpg"
    local_path = os.path.join(media_dir, f"{local_id}.{ext}")

    resp = requests.get(media_url, timeout=60, stream=True)
    resp.raise_for_status()

    os.makedirs(media_dir, exist_ok=True)
    with open(local_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return os.path.normpath(local_path)


def get_location_via_claude(
    caption: str,
    local_media_path: str,
    media_type: str,
    recent_locations: list[str],
) -> tuple[str, str, str, str]:
    """FR-020 inferred-location path: identify the post's location from caption + image + nearby context.

    Used ONLY when the post has no explicit geo-tag (i.e. instagrapi returned no
    `Location` object or instagrapi is unavailable). Tagged posts go through
    `get_region_only_via_claude` instead.

    Returns a (location, lat, lng, region) tuple. Any field may be an empty string.
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

    # Include image for IMAGE posts so Claude can use visual context
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

    raw = response.content[0].text.strip()
    # Strip markdown code fences if Claude wrapped the JSON despite the prompt.
    if raw.startswith("```"):
        first_nl = raw.find("\n")
        if first_nl != -1:
            raw = raw[first_nl + 1 :]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
    try:
        data = json.loads(raw)
        return (
            str(data.get("location", "")),
            str(data.get("lat", "")),
            str(data.get("lng", "")),
            str(data.get("region", "")),
        )
    except (json.JSONDecodeError, AttributeError):
        # Fallback: treat the raw text as just a location name
        return (raw, "", "", "")


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
    Claude-inferred path in that case.

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


def get_region_only_via_claude(name: str, lat: str, lng: str) -> str:
    """FR-019 region-only path: derive the IATA code given a known location.

    Used when instagrapi returns a tagged location — name and coordinates are
    authoritative; Claude is consulted only for the nearest in-country
    international airport. Returns an empty string if undetermined.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = (
        f"Location name: {name}\n"
        f"Latitude: {lat or '(unknown)'}\n"
        f"Longitude: {lng or '(unknown)'}\n\n"
        "Return only the 3-letter IATA code of the nearest major international "
        "airport within the same country as this location (e.g. 'JFK', 'MEX', 'CDG'). "
        "Reply with just the 3-letter code, nothing else. "
        "If you cannot determine the code with reasonable confidence, reply with an empty string."
    )
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip().upper()
        cleaned = "".join(c for c in raw if c.isalpha())
        if len(cleaned) == 3:
            return cleaned
        return ""
    except Exception as exc:
        print(f"  ! Claude IATA lookup failed ({exc})")
        return ""


def fetch_new_media_instagrapi(cl: "object", since_ts: int, max_total: int = 1000) -> list:
    """Fetch posts newer than since_ts from the logged-in account, oldest-first.

    Walks the account feed via paginated instagrapi calls, batch-by-batch newest
    first, and stops when it hits a post at or before since_ts. Returns the new
    posts in oldest-first order so the TSV row order matches the existing
    "newest-row-is-last" convention. A safety cap of max_total stops runaway
    pagination if since_ts is way back in time.
    """
    user_id = cl.user_id
    collected: list = []
    end_cursor = ""
    page_num = 0
    while True:
        page_num += 1
        try:
            medias, end_cursor = cl.user_medias_paginated_v1(
                user_id, 50, end_cursor=end_cursor
            )
        except Exception as exc:
            print(f"\nERROR: page {page_num} fetch failed — {exc}")
            sys.exit(1)
        print(f"  [page {page_num}] {len(medias)} posts (cursor={'…' if end_cursor else 'end'})")
        if not medias:
            break
        for m in medias:
            ts = int(m.taken_at.timestamp())
            if ts <= since_ts:
                return list(reversed(collected))
            collected.append(m)
            if len(collected) >= max_total:
                print(f"  ! safety cap of {max_total} posts reached; stopping pagination")
                return list(reversed(collected))
        if not end_cursor:
            break
    return list(reversed(collected))


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch new Instagram posts and append to TSV.")
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=DEFAULT_OUTPUT,
        help=f"TSV file to read/append (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--media-dir",
        metavar="DIR",
        default=DEFAULT_MEDIA_DIR,
        help=f"Directory to save downloaded media (default: {DEFAULT_MEDIA_DIR}).",
    )
    args = parser.parse_args()

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

    # Read existing rows to determine since-timestamp and next local ID
    existing_rows = read_tsv_rows(args.output)

    if not existing_rows:
        print("No existing TSV rows found. Run the initial load script first.")
        sys.exit(1)

    # Find the most recent timestamp across all rows (robust to any row ordering).
    # This is the Python equivalent of PHP's strtotime($last_timestamp).
    timestamped = [r for r in existing_rows if r.get("timestamp")]
    if not timestamped:
        print("No rows with a timestamp found. Cannot determine 'since' param.")
        sys.exit(1)

    most_recent_row = max(timestamped, key=lambda r: r["timestamp"])
    last_timestamp_str = most_recent_row["timestamp"]

    since_ts = parse_unix_timestamp(last_timestamp_str)

    # Determine next local ID
    try:
        next_id = max(int(r["id"]) for r in existing_rows if r.get("id")) + 1
    except (ValueError, KeyError):
        next_id = len(existing_rows) + 1

    print(f"\nFetching new media via instagrapi (since {last_timestamp_str}):")
    try:
        new_media = fetch_new_media_instagrapi(ig_client, since_ts)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"\nERROR: instagrapi fetch failed — {exc}")
        sys.exit(1)

    if not new_media:
        print("No new posts found.")
        return
    print(f"\n{len(new_media)} new post(s) to process (oldest-first):")

    # Seed Claude location context with the most recent existing posts
    sorted_rows = sorted(timestamped, key=lambda r: r["timestamp"], reverse=True)
    recent_locations = [r.get("location", "") for r in sorted_rows[:RECENT_LOCATION_COUNT]]

    with open(args.output, "a", newline="", encoding="utf-8") as out_file:
        writer = csv.DictWriter(out_file, fieldnames=TSV_COLUMNS, delimiter="\t")

        total_written = 0
        for m in new_media:
            local_id = next_id
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
                        remote_media_url, local_id, media_type, args.media_dir
                    )
                    print(f"  ↓ saved {local_media_path}")
                except (requests.RequestException, OSError) as exc:
                    print(f"  ! pk={instagram_id}  media download failed ({exc})")

            # Dual-path location:
            #   FR-019 tagged: Media has a Location → name/lat/lng authoritative; Claude only for IATA.
            #   FR-020 inferred: no tag → Claude full inference from caption + image + recent context.
            location, lat, lng, region = "", "", "", ""
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
                location, lat, lng = tagged
                region = get_region_only_via_claude(location, lat, lng)
                print(f"  location (tagged): {location}  lat={lat}  lng={lng}  region: {region or '(undetermined)'}")
            else:
                try:
                    location, lat, lng, region = get_location_via_claude(
                        caption=caption,
                        local_media_path=local_media_path,
                        media_type=media_type,
                        recent_locations=recent_locations,
                    )
                    print(f"  location (inferred — no tag found): {location or '(undetermined)'}  lat={lat}  lng={lng}  region: {region or '(undetermined)'}")
                except Exception as exc:
                    print(f"  ! pk={instagram_id}  Claude location lookup failed ({exc})")

            # Strip project root prefix and normalize to posix separators for the TSV row.
            if local_media_path.startswith(PROJECT_ROOT):
                local_media_path = os.path.relpath(local_media_path, PROJECT_ROOT)
            local_media_path = local_media_path.replace(os.sep, posixpath.sep)

            writer.writerow({
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
            })
            out_file.flush()

            # Feed this post's location into context for subsequent Claude calls
            if location:
                recent_locations.insert(0, location)
                recent_locations = recent_locations[:RECENT_LOCATION_COUNT]

            next_id += 1
            total_written += 1
            print(f"  + [{local_id}] pk={instagram_id}  shortcode={shortcode}")

    print(f"\nDone. {total_written} new posts written to {args.output}.")


if __name__ == "__main__":
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    main()
