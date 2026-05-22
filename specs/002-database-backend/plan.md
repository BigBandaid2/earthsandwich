# Implementation Plan: Database & Backend

**Branch**: `002-database-backend` | **Date**: 2026-05-12 (updated 2026-05-22) | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/002-database-backend/spec.md`

## Summary

Build a Python/FastAPI backend with PostgreSQL that replaces the hard-coded TypeScript data with a relational database, exposes a REST API for the frontend, supports trip management writes with bearer-token auth, and containerizes the full stack (backend + frontend + DB) with Docker Compose. The MVP sequence is: seed the DB from existing TS data → expose read API → add trip management → containerize everything. Automated content ingestion (Instagram + Substack) is specified separately in `003-ingestion-pipeline`.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x (existing frontend + seed export script)
**Primary Dependencies**: FastAPI 0.115, SQLAlchemy 2.0 (async + asyncpg), Alembic, slowapi, structlog, pydantic-settings, httpx (test client), pytest / pytest-asyncio
**Storage**: PostgreSQL 16 (all environments; SQLite dropped per spec clarification)
**Testing**: pytest, pytest-asyncio, httpx; contract tests against live API; integration tests against a test PostgreSQL instance
**Target Platform**: Linux server (Docker container); local Docker Compose for development
**Project Type**: REST API backend service + Docker Compose full-stack (backend + frontend + database)
**Performance Goals**: <500ms p95 for read endpoints under normal server load (SC-003)
**Constraints**: No hardcoded secrets; structured JSON logs to stdout only (FR-042); HTTPS in production; rate limiting on all public endpoints (FR-030); no internal identifiers or stack traces in API responses (FR-033)
**Scale/Scope**: ~3 trips, ~100s of stops and posts; small audience (travelers + friends/family); single-server deployment

> Ingestion-side dependencies (`instagrapi`, `feedparser`, `anthropic` SDK, APScheduler) live in `003-ingestion-pipeline/plan.md`. Both specs share the same FastAPI process and Docker stack.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Static First | ⚠ Justified violation | A queryable API and database-backed reads cannot be done statically. See Complexity Tracking. |
| II. Responsive Design | N/A | Backend feature; no UI added in this spec. |
| III. Accessibility | N/A | Backend feature; no UI added in this spec. |
| IV. Performance | ✓ Pass | SC-003 targets <500ms p95 for reads; FastAPI with asyncpg meets this at this scale. |
| V. Security | ✓ Pass | HTTPS in production (FR-032), rate limiting (FR-030), input validation (FR-031), secrets in env vars only (FR-028), no sensitive info in responses (FR-033). |
| Stack: Python | ✓ Justified addition | Consistent with the `003-ingestion-pipeline` runtime; the backend and the ingestion jobs share a process. |
| Stack: PostgreSQL | ✓ Justified addition | Relational FK constraints, ordered sequences, and future query flexibility; SQLite explicitly dropped by spec clarification. |
| Stack: Docker | ✓ Justified addition | Required by US6; enables reproducible local dev and clean production deployment. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Python backend (vs. static only) | A queryable, filtered API requires server-side logic; static files cannot serve filtered queries efficiently | Static + manual TSV workflow (current state) doesn't support filtering, write endpoints, or future ingestion (specified in 003) |
| PostgreSQL (vs. no storage) | Relational FK constraints between trips → stops → posts; queryable filters; future idempotent ingestion tracking via unique constraints | File-based storage (TSV/JSON) cannot enforce referential integrity or support efficient filtered queries |
| Docker Compose (vs. bare metal) | Reproducible local dev, dependency isolation, and clean production deployment without host-level setup | Bare metal setup creates environment drift and increases onboarding friction (SC-008 targets <5 min to working local stack) |
| Async SQLAlchemy + asyncpg (vs. sync) | FastAPI is async-first; mixing sync DB calls with async routes requires thread-pool workarounds that add latency under concurrent requests | For this scale sync would work, but asyncpg + SQLAlchemy async is the idiomatic FastAPI pattern and avoids retrofitting later |

## Project Structure

### Documentation (this feature)

```text
specs/002-database-backend/
├── plan.md              # This file
├── research.md          # Phase 0 — technology decisions (framework, ORM, logging, rate limit, config, TS export)
├── data-model.md        # Phase 1 — DB schema and entity definitions
├── quickstart.md        # Phase 1 — developer setup guide (DB + API + Docker)
├── contracts/
│   └── api.md           # Phase 1 — REST API contract
└── tasks.md             # Phase 2 output
```

### Source Code

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan (scheduler startup/shutdown is wired here by 003), CORS, rate limit
│   ├── config.py            # pydantic-settings; all env vars validated at startup
│   ├── database.py          # SQLAlchemy async engine, session factory, get_db dependency
│   ├── models/              # SQLAlchemy ORM models (table definitions)
│   │   ├── __init__.py
│   │   ├── trip.py
│   │   ├── stop.py
│   │   ├── instagram_post.py
│   │   └── substack_post.py
│   ├── schemas/             # Pydantic v2 request/response schemas (API shapes)
│   │   ├── __init__.py
│   │   ├── trip.py
│   │   ├── stop.py
│   │   └── post.py
│   └── api/                 # FastAPI route handlers
│       ├── __init__.py
│       ├── trips.py         # GET /trips, GET /trips/:id, POST /trips, PUT /trips/:id
│       ├── stops.py         # GET /stops
│       ├── posts.py         # GET /instagram-posts, GET /substack-posts
│       └── regions.py       # POST /regions/end-date (FR-045)
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── unit/                # Pure logic
│   ├── integration/         # DB-backed tests against test PostgreSQL
│   └── contract/            # HTTP contract tests via httpx TestClient
├── Dockerfile
├── requirements.txt
└── alembic.ini

scripts/
├── export-seed-data.ts      # tsx: imports TS data modules → writes JSON to scripts/seed-data/
├── seed.py                  # Python: reads seed-data JSON → inserts into PostgreSQL → pg_dump
└── seed-dump.sql            # Generated by seed.py; auto-applied by Docker DB container on first start

frontend/                    # Existing React frontend (moved from project root in T002)
public/
└── media/                   # Downloaded Instagram media files (served statically; populated by 003)

docker-compose.yml           # Backend + frontend + PostgreSQL; DB mounts seed-dump.sql on init
Dockerfile.frontend          # Nginx serving the Vite build output
.env                         # Local secrets (gitignored)
.env.example                 # Committed; all required keys with placeholder values
```

> `backend/app/ingestion/` and `backend/app/cli/manage.py` are owned by `003-ingestion-pipeline`. They run inside the same FastAPI process but their lifecycle and tasks are specified there.

**Structure Decision**: Web application layout — `backend/` for the Python service, `frontend/` for the existing React frontend (moved from project root in Phase 1 T002), `scripts/` for the seed pipeline. The frontend Dockerfile serves the Vite `dist/` build via nginx. Docker Compose wires all three services together with the PostgreSQL database.
