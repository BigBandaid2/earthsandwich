# Data Model: Ingestion Pipeline

**Phase**: 1 | **Plan**: [plan.md](plan.md) | **Date**: 2026-05-22

## Schema deltas vs. 002-database-backend

**None.** This spec adds no new tables and no new columns. The full schema (`trips`, `stops`, `instagram_posts`, `substack_posts`) is defined in `specs/002-database-backend/data-model.md` and is treated as pre-existing here.

## Tables this spec writes to

| Table | Operation | Notes |
|-------|-----------|-------|
| `stops` | INSERT (one row per ingested Instagram post) | `id` is a fresh UUID; `trip_id` resolved per FR-040; `region_code` set by Claude per FR-019 / FR-020 |
| `instagram_posts` | INSERT (one row per ingested post) | Idempotent via UNIQUE on `instagram_id` (FR-022) |
| `substack_posts` | INSERT (one row per RSS entry) | Idempotent via UNIQUE on `substack_id` (FR-025); `stop_id` always null (FR-027) |

## Tables this spec reads from

| Table | Operation | Notes |
|-------|-----------|-------|
| `trips` | SELECT | Trip assignment per FR-040: range query on `start_date <= post.timestamp <= end_date`, tie-broken by `created_at DESC` |
| `instagram_posts` | SELECT | Latest `timestamp` per account to drive the since-cursor for the next fetch (FR-018) |
| `substack_posts` | SELECT | `substack_id` set for idempotency lookup |
| `stops` | SELECT | Most-recently-ingested `location` values to seed Claude location context per FR-020 |

## Trip Assignment Logic (FR-040)

When the ingestion job creates a new stop for an Instagram post with timestamp `T`:

1. Find all trips where `start_date <= T <= end_date`.
2. If exactly one match → assign to it.
3. If multiple matches → assign to the trip with the most recent `created_at`.
4. If no match → assign to the trip with `id = "miscellaneous-adventures"`. If that trip is absent, log ERROR and halt without writing any records.

## Region code derivation (FR-019, FR-020)

`stops.region_code` is the IATA 3-letter code of the nearest international airport within the same country as the stop. It is always set by Claude during ingestion (never by a heuristic, never by a third-party airport API).

- **Tagged-location path (FR-019)**: instagrapi returns a structured location object. The tagged name and coordinates are stored verbatim. Claude is called with `(location_name, lat, lng)` and asked to return only the IATA code.
- **Inferred-location path (FR-020)**: instagrapi returns no location tag. Claude is called with the post caption, the base64-encoded image (IMAGE posts), and the locations of up to the 5 most-recently-ingested stops, and is asked to return JSON `{location, lat, lng, region}`.

In both paths: if Claude's response is invalid, `region_code` is set to null and a warning is logged; processing continues.

## Substack post assignment state

```
unassigned (stop_id = null)
    │
    ▼  (manual operator action, out of scope for this spec)
assigned (stop_id = <stop_id>)
```

Substack posts are ingested without a `stop_id` per FR-027. The operator assigns them to a stop after the fact via direct database edit or via a future API endpoint. Unassigned posts are excluded from API responses (per 002 spec assumptions).
