#!/usr/bin/env python3
"""Export the hand-curated truth-baseline TSV to public/posts.json as a list of Stop objects.

LEGACY: this script bridges the truth file (`pile-app/instagram/validation/posts.local.tsv`)
to the frontend's static data layer (`public/posts.json`). It exists because the
production data path through the bridge-app + 002 backend isn't built yet — when
the bridge-app lands, this script is retired.

Each TSV row becomes a Stop with status "visited" and an InstagramPost,
matching the shape defined in src/data/types.ts. Rows with missing
coordinates are skipped since they cannot be placed on the map.

Usage:
    python scripts/export_posts_json.py
    python scripts/export_posts_json.py --input <tsv> --output <json>
"""

import argparse
import csv
import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_INPUT = os.path.join(PROJECT_ROOT, "pile-app", "instagram", "validation", "posts.local.tsv")
DEFAULT_OUTPUT = os.path.join(PROJECT_ROOT, "public", "posts.json")


def tsv_row_to_stop(row: dict) -> dict | None:
    def col(key: str) -> str:
        return (row.get(key) or "").strip()

    instagram_id = col("instagram_id")
    lat_str = col("lat")
    lng_str = col("lng")

    if not lat_str or not lng_str:
        return None  # skip — cannot place on map without coordinates

    try:
        lat = float(lat_str)
        lng = float(lng_str)
    except ValueError:
        return None

    timestamp = col("timestamp")
    date = timestamp[:10] if timestamp else ""

    media_url = col("media_url")
    # Vite serves public/ as the web root; strip the leading "public/" so the
    # served URL ends up rooted at "/".
    if media_url.startswith("public/"):
        media_url = media_url[len("public"):]

    location = col("location") or col("region")

    return {
        "id": f"ig-{instagram_id}",
        "date": date,
        "location": location,
        "coords": {"lat": lat, "lng": lng},
        "status": "visited",
        "regionCode": col("region"),
        "post": {
            "type": "instagram",
            "image": media_url,
            "caption": row.get("caption") or "",
            "instagramId": instagram_id,
            "shortcode": col("shortcode"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export TSV posts to Stop JSON.")
    parser.add_argument("--input", default=DEFAULT_INPUT, metavar="FILE")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, metavar="FILE")
    args = parser.parse_args()

    stops = []
    skipped = 0
    with open(args.input, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            stop = tsv_row_to_stop(row)
            if stop is not None:
                stops.append(stop)
            else:
                skipped += 1

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(stops, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(stops)} stops to {args.output}" +
          (f" ({skipped} skipped - missing coords)" if skipped else ""))


if __name__ == "__main__":
    main()
