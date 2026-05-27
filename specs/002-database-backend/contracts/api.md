# API Contract: Database & Backend

**Phase**: 1 | **Plan**: [../plan.md](../plan.md) | **Date**: 2026-05-12 (updated 2026-05-22)

## Base URL

`http://localhost:8000` (local Docker) — configurable via `API_BASE_URL` in `.env`.

## Common Headers

All responses include `Content-Type: application/json` and CORS headers permitting requests from the configured `FRONTEND_ORIGIN`.

## Authentication

Write endpoints require a bearer token:
```
Authorization: Bearer <API_SECRET_KEY>
```
Unauthenticated write requests return **401**. The `API_SECRET_KEY` is set in `.env`.

## Rate Limiting

All public endpoints: **60 requests/minute per IP**. Exceeding this limit returns **429** with a `Retry-After` header.

## Error Schema

All non-2xx responses use this shape:
```json
{
  "error": "Not Found",
  "detail": "Trip with id 'foo' does not exist."
}
```

---

## Endpoints

### `GET /trips`

Returns all trips in reverse-chronological order by `start_date`.

**Query parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | `active \| completed \| upcoming` | Optional filter by trip status (derived from dates relative to today) |

**Response 200**:
```json
[
  {
    "id": "earth-club-sandwich-2027",
    "title": "Earth Club Sandwich 2027",
    "description": "A round-the-world journey...",
    "start_date": "2027-03-26",
    "end_date": "2028-05-12",
    "created_at": "2026-05-12T00:00:00Z",
    "updated_at": "2026-05-12T00:00:00Z"
  }
]
```

---

### `GET /trips/:id`

Returns the full trip including all stops and each stop's post data.

**Response 200**:
```json
{
  "id": "miscellaneous-adventures",
  "title": "Miscellaneous Adventures",
  "description": "...",
  "start_date": "2019-05-13",
  "end_date": "2024-02-20",
  "created_at": "2026-05-12T00:00:00Z",
  "updated_at": "2026-05-12T00:00:00Z",
  "stops": [
    {
      "id": "23",
      "trip_id": "miscellaneous-adventures",
      "date": "2019-05-13",
      "location": "La Piedra del Peñol, Colombia",
      "lat": 6.2,
      "lng": -75.0667,
      "status": "visited",
      "region_code": "MDE",
      "post_type": "instagram",
      "caption": null,
      "post": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "instagram_id": "18001223977200451",
        "shortcode": "BxZ6Y-Zh1jC",
        "media_url": "/media/23.jpg",
        "caption": "700 steps up a vertical monolith...",
        "timestamp": "2019-05-13T12:00:00Z"
      }
    }
  ]
}
```

**Response 404**:
```json
{ "error": "Not Found", "detail": "Trip with id 'foo' does not exist." }
```

The `post` field shape depends on `post_type`:
- `instagram` → `InstagramPostResponse` (above)
- `substack` → `SubstackPostResponse` (see GET /substack-posts)
- `planned` → `null` (post field omitted or null; caption is on the stop itself)

---

### `POST /trips` *(auth required)*

Creates a new trip.

**Request body**:
```json
{
  "id": "new-adventure-2029",
  "title": "New Adventure 2029",
  "description": "Description here.",
  "start_date": "2029-01-01",
  "end_date": "2029-06-30"
}
```

**Response 201**:
```json
{
  "id": "new-adventure-2029",
  "title": "New Adventure 2029",
  "description": "Description here.",
  "start_date": "2029-01-01",
  "end_date": "2029-06-30",
  "created_at": "2026-05-12T10:00:00Z",
  "updated_at": "2026-05-12T10:00:00Z"
}
```

**Response 401**: Missing or invalid bearer token.
**Response 422**: Invalid date format or missing required fields.
**Response 409**: Trip with given `id` already exists.

---

### `PUT /trips/:id` *(auth required)*

Updates a trip's mutable fields. Only supplied fields are updated; omitted fields are preserved.

**Request body** (all fields optional):
```json
{
  "title": "Updated Title",
  "description": "Updated description.",
  "start_date": "2027-03-01",
  "end_date": "2028-06-30"
}
```

**Response 200**: Updated trip object (same shape as GET /trips/:id, without stops).
**Response 401**: Missing or invalid bearer token.
**Response 404**: Trip not found.
**Response 422**: Invalid date format.

---

### `GET /stops`

Returns stops with optional filters.

**Query parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `trip_id` | string | Filter by trip |
| `status` | `visited \| planned` | Filter by stop status |
| `region_code` | string | Filter by IATA region code |
| `post_type` | `instagram \| substack \| planned` | Filter by post type |
| `after` | ISO date | Stops with `date >= after` |
| `before` | ISO date | Stops with `date <= before` |

**Response 200**:
```json
[
  {
    "id": "23",
    "trip_id": "miscellaneous-adventures",
    "date": "2019-05-13",
    "location": "La Piedra del Peñol, Colombia",
    "lat": 6.2,
    "lng": -75.0667,
    "status": "visited",
    "region_code": "MDE",
    "post_type": "instagram",
    "caption": null
  }
]
```

Note: `post` data is **not** included in list responses — use `GET /trips/:id` for full post content.

---

### `GET /instagram-posts`

Returns Instagram posts with optional filters.

**Query parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `stop_id` | string | Filter by stop |
| `after` | ISO 8601 timestamp | Posts with `timestamp >= after` |
| `before` | ISO 8601 timestamp | Posts with `timestamp <= before` |

**Response 200**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "stop_id": "23",
    "instagram_id": "18001223977200451",
    "shortcode": "BxZ6Y-Zh1jC",
    "media_url": "/media/23.jpg",
    "caption": "700 steps up a vertical monolith...",
    "timestamp": "2019-05-13T12:00:00Z",
    "created_at": "2026-05-12T00:00:00Z"
  }
]
```

---

### `GET /substack-posts`

Returns Substack posts that have been assigned to a stop (`stop_id IS NOT NULL`).

**Query parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `stop_id` | string | Filter by stop |
| `after` | ISO 8601 timestamp | Posts with `published_at >= after` |
| `before` | ISO 8601 timestamp | Posts with `published_at <= before` |

**Response 200**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "stop_id": "10",
    "substack_id": "https://example.substack.com/p/my-post",
    "title": "Article Title",
    "subtitle": "A brief description.",
    "body": "Full article body text...",
    "published_at": "2024-03-01T10:00:00Z",
    "created_at": "2026-05-12T00:00:00Z"
  }
]
```

---

## Environment Variables Reference

Variables required by this spec (database, API, container concerns):

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://user:pass@host:5432/db` |
| `API_SECRET_KEY` | Yes | Bearer token for write endpoints |
| `FRONTEND_ORIGIN` | Yes | CORS allowed origin (e.g. `http://localhost:5173`) |
| `LOG_LEVEL` | No | Default: `INFO` |
| `ENVIRONMENT` | No | `development` (console logs) or `production` (JSON logs); default: `production` |

> Ingestion-specific env vars (`INSTA_USERNAME`, `INSTA_PASSWORD`, `INSTAGRAPI_SESSION_FILE`, `ANTHROPIC_API_KEY`, `SUBSTACK_RSS_URL`, `INSTAGRAM_GRAPH_API_TOKEN`, `INSTAGRAM_POLL_INTERVAL_MINUTES`, `SUBSTACK_POLL_INTERVAL_MINUTES`, `SMTP_*`) live in [`003-ingestion-pipeline/quickstart.md`](../../003-ingestion-pipeline/quickstart.md).
