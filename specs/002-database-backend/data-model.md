# Data Model: Database & Backend

**Phase**: 1 | **Plan**: [plan.md](plan.md) | **Date**: 2026-05-12 (updated 2026-05-22)

## Entity Overview

Four tables mirror the existing `src/data/types.ts` interfaces and extend them with persistence metadata. Planned stops have no separate table — they are represented by `post_type = 'planned'` and an optional `caption` on the `stops` row.

```
trips
  └── stops (FK: trip_id)
        ├── instagram_posts (FK: stop_id)  [post_type = 'instagram']
        └── substack_posts  (FK: stop_id)  [post_type = 'substack', nullable]
```

> This schema is the canonical definition. `003-ingestion-pipeline` writes new rows into `stops`, `instagram_posts`, and `substack_posts` but does not modify the schema.

---

## Table: `trips`

Maps to `Trip` in `src/data/types.ts`.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | `VARCHAR(100)` | PRIMARY KEY | Stable slug (e.g. `"miscellaneous-adventures"`); set by operator at creation |
| `title` | `VARCHAR(255)` | NOT NULL | |
| `description` | `TEXT` | NOT NULL | |
| `start_date` | `DATE` | NOT NULL | Derived from the earliest stop date at seed time; operator-managed thereafter |
| `end_date` | `DATE` | NOT NULL | Derived from the latest stop date at seed time |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | Used by `003-ingestion-pipeline` for trip-assignment tie-breaking |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | Updated on every `PUT /trips/:id` |

**Indexes**: `(start_date, end_date)` for trip-assignment date range queries from the ingestion pipeline.

The seed pipeline MUST create a row with `id = "miscellaneous-adventures"`; the ingestion pipeline relies on it as the default fallback when no other trip date range matches a new post.

---

## Table: `stops`

Maps to `Stop` in `src/data/types.ts`.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | `VARCHAR(100)` | PRIMARY KEY | Stable string; existing IDs (`"23"`, `"ecs2027-01"`) preserved at seed; UUID for new ingested stops |
| `trip_id` | `VARCHAR(100)` | NOT NULL, FK → trips.id | Must reference a valid trip; ingestion uses `"miscellaneous-adventures"` as default |
| `date` | `DATE` | NOT NULL | Date of the visit or planned date |
| `location` | `VARCHAR(500)` | NOT NULL | Human-readable location string |
| `lat` | `DECIMAL(10, 7)` | NULLABLE | Null when location could not be geocoded |
| `lng` | `DECIMAL(10, 7)` | NULLABLE | Null when location could not be geocoded |
| `status` | `VARCHAR(20)` | NOT NULL, CHECK IN ('visited','planned') | |
| `region_code` | `VARCHAR(10)` | NULLABLE | IATA code of nearest in-country international airport; populated at seed time from source TS data; for new rows, written by ingestion (see `003-ingestion-pipeline`) |
| `post_type` | `VARCHAR(20)` | NOT NULL, CHECK IN ('instagram','substack','planned') | |
| `caption` | `TEXT` | NULLABLE | Used for `post_type = 'planned'` only |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | |

**Indexes**:
- `(trip_id, date)` for ordered stop retrieval per trip
- `(trip_id, status)` for status-filtered queries
- `(trip_id, region_code)` for region-filtered queries
- `(date)` for date-range filters

---

## Table: `instagram_posts`

Maps to `InstagramPost` in `src/data/types.ts`, extended with platform and ingestion metadata.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | `UUID` | PRIMARY KEY, DEFAULT gen_random_uuid() | |
| `stop_id` | `VARCHAR(100)` | NOT NULL, FK → stops.id, UNIQUE | One post per stop |
| `instagram_id` | `VARCHAR(100)` | NOT NULL, UNIQUE | Platform identifier; used for idempotency by `003-ingestion-pipeline` |
| `shortcode` | `VARCHAR(100)` | NOT NULL | Used to construct `instagram.com/p/<shortcode>/` URL |
| `media_url` | `VARCHAR(500)` | NOT NULL | Relative POSIX path (e.g. `/media/<stop_id>.jpg`); empty string if ingestion download failed |
| `caption` | `TEXT` | NOT NULL, DEFAULT '' | Post caption text |
| `timestamp` | `TIMESTAMPTZ` | NOT NULL | Original Instagram post timestamp |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | |

**Indexes**: `(instagram_id)` UNIQUE (deduplication); `(timestamp)` for since-timestamp ingestion queries; `(stop_id)` for join.

---

## Table: `substack_posts`

Maps to `SubstackPost` in `src/data/types.ts`, extended with platform metadata.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | `UUID` | PRIMARY KEY, DEFAULT gen_random_uuid() | |
| `stop_id` | `VARCHAR(100)` | NULLABLE, FK → stops.id | Null until manually assigned; excluded from API responses until assigned |
| `substack_id` | `VARCHAR(500)` | NOT NULL, UNIQUE | Stable identifier — `<guid>` or `<link>` from RSS; used for idempotency by `003-ingestion-pipeline` |
| `title` | `VARCHAR(500)` | NOT NULL | |
| `subtitle` | `TEXT` | NULLABLE | From RSS `<description>` |
| `body` | `TEXT` | NOT NULL | From RSS `<content:encoded>` |
| `published_at` | `TIMESTAMPTZ` | NOT NULL | From RSS `<pubDate>` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | |

**Indexes**: `(substack_id)` UNIQUE (deduplication); `(published_at)` for date filters; `(stop_id)` for join.

---

## State Transitions

### Stop Status

```
planned ──► visited
```

A stop moves from `planned` to `visited` when an Instagram post is ingested and matched to it by trip date range (logic in `003-ingestion-pipeline`). Status never regresses (visited stops cannot become planned again). The frontend derives `abandoned` as an effective status at render time — it is never stored in the database (consistent with the existing `StopStatus` type in `types.ts`).

### Substack Post Assignment

```
unassigned (stop_id = null)
    │
    ▼  (manual operator action via API or direct DB)
assigned (stop_id = <stop_id>)
```

Substack posts are ingested without a `stop_id`. The operator assigns them to a stop after the fact. Unassigned posts are stored but not included in API responses.

---

## Seed Pipeline

```
TypeScript source files (frontend/src/data/*.ts)
        │
        ▼ tsx scripts/export-seed-data.ts
scripts/seed-data/
├── trips.json
├── stops.json
├── instagram_posts.json
└── substack_posts.json
        │
        ▼ python scripts/seed.py
PostgreSQL (earthsandwich DB)
        │
        ▼ pg_dump (run by seed.py via subprocess)
scripts/seed-dump.sql   ← mounted into DB container on first start
```

The seed script is idempotent: it uses `INSERT ... ON CONFLICT DO NOTHING` on all primary keys and unique indexes. Running it twice produces no duplicate records (US1 scenario 3).

> Trip-assignment logic for newly ingested posts (FR-040) lives in `003-ingestion-pipeline/data-model.md`.
