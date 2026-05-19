"""
Seed the PostgreSQL database from the JSON files produced by export-seed-data.ts.

Usage (from project root):
    python scripts/seed.py

Reads DATABASE_URL from the environment (or backend/.env).
Inserts in FK order: trips → stops → instagram_posts → substack_posts.
All inserts use ON CONFLICT DO NOTHING so the script is safe to re-run.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

SCRIPTS_DIR = Path(__file__).parent
SEED_DIR = SCRIPTS_DIR / "seed-data"


def _load_json(name: str) -> list[dict]:
    path = SEED_DIR / f"{name}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _parse_ts(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _pg_url(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://")


async def seed(conn: asyncpg.Connection) -> None:
    trips = _load_json("trips")
    stops = _load_json("stops")
    instagram_posts = _load_json("instagram_posts")
    substack_posts = _load_json("substack_posts")

    # ── trips ─────────────────────────────────────────────────────────────────
    result = await conn.executemany(
        """
        INSERT INTO trips (id, title, description, start_date, end_date)
        VALUES ($1, $2, $3, $4::date, $5::date)
        ON CONFLICT DO NOTHING
        """,
        [
            (t["id"], t["title"], t["description"], t["start_date"], t["end_date"])
            for t in trips
        ],
    )
    print(f"trips:           {len(trips)} records processed  ({result})")

    # ── stops ─────────────────────────────────────────────────────────────────
    result = await conn.executemany(
        """
        INSERT INTO stops
            (id, trip_id, date, location, lat, lng, status,
             region_code, post_type, sequence_order, caption)
        VALUES ($1, $2, $3::date, $4, $5, $6, $7, $8, $9, $10, $11)
        ON CONFLICT DO NOTHING
        """,
        [
            (
                s["id"],
                s["trip_id"],
                s["date"],
                s["location"],
                s["lat"],
                s["lng"],
                s["status"],
                s["region_code"],
                s["post_type"],
                s["sequence_order"],
                s["caption"],
            )
            for s in stops
        ],
    )
    print(f"stops:           {len(stops)} records processed  ({result})")

    # ── instagram_posts ───────────────────────────────────────────────────────
    result = await conn.executemany(
        """
        INSERT INTO instagram_posts
            (stop_id, instagram_id, shortcode, media_url, caption, timestamp)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT DO NOTHING
        """,
        [
            (
                p["stop_id"],
                p["instagram_id"],
                p["shortcode"],
                p["media_url"],
                p["caption"],
                _parse_ts(p["timestamp"]),
            )
            for p in instagram_posts
        ],
    )
    print(f"instagram_posts: {len(instagram_posts)} records processed  ({result})")

    # ── substack_posts ────────────────────────────────────────────────────────
    result = await conn.executemany(
        """
        INSERT INTO substack_posts
            (stop_id, substack_id, title, subtitle, body, published_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT DO NOTHING
        """,
        [
            (
                p["stop_id"],
                p["substack_id"],
                p["title"],
                p["subtitle"],
                p["body"],
                _parse_ts(p["published_at"]),
            )
            for p in substack_posts
        ],
    )
    print(f"substack_posts:  {len(substack_posts)} records processed  ({result})")


async def main() -> None:
    # Load DATABASE_URL — check backend/.env first, then environment
    env_path = SCRIPTS_DIR.parent / "backend" / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Connecting to database...")
    conn = await asyncpg.connect(_pg_url(database_url))
    try:
        await seed(conn)
        print("Seed complete.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
