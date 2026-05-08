#!/usr/bin/env python3
"""
load_posts_tsv.py — Incremental update: fetch new Instagram posts since last run.

Reads the TSV to find the most recent known post timestamp, then fetches only
new posts from the API using since/until params (equivalent to PHP strtotime()).
For each new post it:
  1. Fetches post details from the Graph API
  2. Downloads the image/video into public/media/<local_id>.jpg or .mp4
  3. Calls Claude to determine the post location from caption, image, and context
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
import sys
from datetime import datetime, timezone

import anthropic
import requests
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

ACCESS_TOKEN = os.environ["INSTA_ACCESS_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
BASE_URL = "https://graph.instagram.com/v25.0"
POST_FIELDS = "caption,media_type,media_url,shortcode,timestamp"

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


def fetch_media_page(url: str) -> dict:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_post_details(post_id: str) -> dict:
    resp = requests.get(
        f"{BASE_URL}/{post_id}",
        params={"fields": POST_FIELDS, "access_token": ACCESS_TOKEN},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


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

    return local_path


def get_location_via_claude(
    url: str,
    caption: str,
    local_media_path: str,
    media_type: str,
    recent_locations: list[str],
) -> tuple[str, str, str, str]:
    """Use Claude to determine the location, latitude, and longitude of a post.

    Returns a (location, lat, lng, region) tuple. Any field may be an empty string if
    undetermined.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    recent_loc_text = ""
    known_locations = [loc for loc in recent_locations if loc]
    if known_locations:
        loc_list = "\n".join(f"- {loc}" for loc in known_locations)
        recent_loc_text = f"\n\nLocations of recent nearby posts (for context):\n{loc_list}"

    prompt = (
        f"Instagram URL: {url}\n"
        f"Caption: {caption or '(none)'}"
        f"{recent_loc_text}\n\n"
        "Based on the caption, image content, and the locations of recent posts, "
        "what is the location of this Instagram post? "
        "Additionally, return the latitude, longitude, and airport code of the nearest international airport where possible. "
        "First, try to pull up the Instagram post using the URL and see if it has an explicitly geotagged location. "
        "If a location is explicitly tagged or clearly stated in the caption, use that. "
        "Otherwise, estimate based on visual cues and the context of recent posts. "
        "Respond with only a JSON object with four keys: "
        '"location" (human-readable name, e.g. \'Times Square, New York, USA\'), '
        '"lat" (decimal latitude as a string, e.g. \'40.7580\'), '
        '"lng" (decimal longitude as a string, e.g. \'-73.9855\'), '
        'and "region" (code of the nearest international airport, e.g. \'JFK\'). '
        "If you cannot determine the location, set all four values to empty strings. "
        "If you cannot determine the lat/lng, provide the location and region but leave lat and lng as empty strings. "
        "If you cannot determine the nearest international airport, provide the location and lat/lng but leave region as an empty string. "
        "Do not include any text outside the JSON object."
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
        model="claude-opus-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": content}],
    )

    raw = response.content[0].text.strip()
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
    until_ts = int(datetime.now(tz=timezone.utc).timestamp())  # strtotime("now")

    # Determine next local ID
    try:
        next_id = max(int(r["id"]) for r in existing_rows if r.get("id")) + 1
    except (ValueError, KeyError):
        next_id = len(existing_rows) + 1

    # Build initial API URL with since/until time-based params
    next_url: str | None = (
        f"{BASE_URL}/me/media"
        f"?access_token={ACCESS_TOKEN}"
        f"&since={since_ts}"
        f"&until={until_ts}"
    )

    print(f"Fetching posts since {last_timestamp_str} (unix: {since_ts})")

    # Collect all new post IDs across pages (API returns newest-first)
    all_new_ids: list[str] = []
    page_num = 0

    while next_url:
        page_num += 1
        print(f"[page {page_num}] {next_url[:80]}...")

        try:
            page = fetch_media_page(next_url)
        except requests.HTTPError as exc:
            print(f"\nERROR: page {page_num} fetch failed — {exc}")
            sys.exit(1)
        except requests.RequestException as exc:
            print(f"\nERROR: network error on page {page_num} — {exc}")
            sys.exit(1)

        ids = [item["id"] for item in page.get("data", [])]
        all_new_ids.extend(ids)
        print(f"  {len(ids)} posts")
        next_url = page.get("paging", {}).get("next")

    if not all_new_ids:
        print("No new posts found.")
        return

    # Reverse so we append oldest-new-post first; newest ends up as the last row
    all_new_ids.reverse()

    # Seed Claude location context with the most recent existing posts
    sorted_rows = sorted(timestamped, key=lambda r: r["timestamp"], reverse=True)
    recent_locations = [r.get("location", "") for r in sorted_rows[:RECENT_LOCATION_COUNT]]

    with open(args.output, "a", newline="", encoding="utf-8") as out_file:
        # Ensure the file ends with a newline before appending new rows
        # out_file.seek(0, 2)  # seek to end
        # if out_file.tell() > 0:
        #     out_file.seek(out_file.tell() - 1)
        #     if out_file.read(1) != "\n":
        #         out_file.write("\n")

        writer = csv.DictWriter(out_file, fieldnames=TSV_COLUMNS, delimiter="\t")

        total_written = 0
        for post_id in all_new_ids:
            local_id = next_id

            try:
                details = fetch_post_details(post_id)
            except requests.RequestException as exc:
                print(f"  ! {post_id}  detail fetch failed ({exc}) — writing partial row")
                writer.writerow({
                    "id": local_id,
                    "instagram_id": post_id,
                    "shortcode": "",
                    "media_url": "",
                    "caption": "",
                    "timestamp": "",
                    "location": "",
                    "lat": "",
                    "lng": "",
                    "region": "",
                })
                out_file.flush()
                next_id += 1
                continue

            media_type = details.get("media_type", "IMAGE")
            remote_media_url = details.get("media_url", "")

            # Download image/video → public/media/<local_id>.jpg or .mp4
            local_media_path = ""
            if remote_media_url:
                try:
                    local_media_path = download_media(
                        remote_media_url, local_id, media_type, args.media_dir
                    )
                    print(f"  ↓ saved {local_media_path}")
                except (requests.RequestException, OSError) as exc:
                    print(f"  ! {post_id}  media download failed ({exc})")

            # Ask Claude for the location, lat, and lng
            location, lat, lng, region = "", "", "", ""

            # Include Instagram URL in the prompt so Claude can use it as a clue (e.g. for geotagged posts or if the location is mentioned in the caption). This is especially helpful for older posts that may not have media URLs that work anymore, since Claude can use the URL as a hint to look up the post's location from other sources.
            url = ""
            if details.get("shortcode"):
                url = f"https://www.instagram.com/p/{details.get('shortcode', '')}/"
            try:
                location, lat, lng, region = get_location_via_claude(
                    url=url,
                    caption=details.get("caption", ""),
                    local_media_path=local_media_path,
                    media_type=media_type,
                    recent_locations=recent_locations,
                )
                print(f"  location: {location or '(undetermined)'}  lat={lat}  lng={lng}  region: {region or '(undetermined)'}")
            except Exception as exc:
                print(f"  ! {post_id}  Claude location lookup failed ({exc})")

            # Strip project root path prefix from local_media_path for TSV storage (keep it relative)
            if local_media_path.startswith(PROJECT_ROOT):
                local_media_path = os.path.relpath(local_media_path, PROJECT_ROOT)
            
            # Normalize to posix-style path for consistency in TSV, even on Windows
            local_media_path = local_media_path.replace(os.sep, posixpath.sep)

            writer.writerow({
                "id": local_id,
                "instagram_id": post_id,
                "shortcode": details.get("shortcode", ""),
                "media_url": local_media_path,
                "caption": details.get("caption", ""),
                "timestamp": details.get("timestamp", ""),
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
            print(f"  + [{local_id}] {post_id}  shortcode={details.get('shortcode')}")

    print(f"\nDone. {total_written} new posts written to {args.output}.")


if __name__ == "__main__":
    main()
