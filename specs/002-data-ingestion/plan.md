# Implementation Plan: Data Ingestion & Backend

**Branch**: `002-data-ingestion` | **Date**: 2026-05-12 | **Spec**: [specs/002-data-ingestion/spec.md](specs/002-data-ingestion/spec.md)
**Input**: Feature specification from `specs/002-data-ingestion/spec.md`

## Summary

Build a Python/FastAPI backend with PostgreSQL that replaces the hard-coded TypeScript data with a relational database, automates Instagram and Substack content ingestion, exposes a REST API for the frontend, and containerizes the full stack with Docker Compose. The MVP sequence is: seed the DB from existing TS data → expose read API → automate Instagram ingestion via instagrapi → add Substack RSS ingestion → containerize everything.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x (existing frontend + seed export script)
**Primary Dependencies**: FastAPI 0.115, SQLAlchemy 2.0 (async + asyncpg), Alembic, APScheduler 3.x, instagrapi, feedparser, anthropic SDK, slowapi, structlog, pydantic-settings, httpx (test client), pytest / pytest-asyncio
**Storage**: PostgreSQL 16 (all environments; SQLite dropped per spec clarification)
**Testing**: pytest, pytest-asyncio, httpx; contract tests against live API; integration tests against a test PostgreSQL instance
**Target Platform**: Linux server (Docker container); local Docker Compose for development
**Project Type**: REST API backend service + Docker Compose full-stack (backend + frontend + database)
**Performance Goals**: <500ms p95 for read endpoints under normal server load (SC-003)
**Constraints**: No hardcoded secrets; structured JSON logs to stdout only (FR-042); HTTPS in production; rate limiting on all public endpoints (FR-030); no internal identifiers or stack traces in API responses (FR-033)
**Scale/Scope**: ~3 trips, ~100s of stops and posts; small audience (travelers + friends/family); single-server deployment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Static First | ⚠ Justified violation | Server-side processing is the core requirement — automated ingestion and a queryable API cannot be done statically. See Complexity Tracking. |
| II. Responsive Design | N/A | Backend feature; no UI added in this spec. |
| III. Accessibility | N/A | Backend feature; no UI added in this spec. |
| IV. Performance | ✓ Pass | SC-003 targets <500ms p95 for reads; FastAPI with asyncpg meets this at this scale. |
| V. Security | ✓ Pass | HTTPS in production (FR-032), rate limiting (FR-030), input validation (FR-031), secrets in env vars only (FR-028), no sensitive info in responses (FR-033). |
| Stack: Python | ✓ Justified addition | Only language with instagrapi support; consistent with existing ingestion scripts. |
| Stack: PostgreSQL | ✓ Justified addition | Relational FK constraints, ordered sequences, and future query flexibility; SQLite explicitly dropped by spec clarification. |
| Stack: Docker | ✓ Justified addition | Required by US6; enables reproducible local dev and clean production deployment. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Python backend (vs. static only) | Automated Instagram/Substack ingestion requires server-side scheduling and API calls; static files cannot self-update | Static + manual TSV workflow (current state) doesn't scale once active travel begins; misses the Substack pipeline entirely |
| PostgreSQL (vs. no storage) | Relational FK constraints between trips → stops → posts; queryable filters; idempotent ingestion tracking via unique instagram_id | File-based storage (TSV/JSON) cannot enforce referential integrity or support efficient filtered queries |
| Docker Compose (vs. bare metal) | Reproducible local dev, dependency isolation, and clean production deployment without host-level setup | Bare metal setup creates environment drift and increases onboarding friction (SC-008 targets <5 min to working local stack) |
| Async SQLAlchemy + asyncpg (vs. sync) | FastAPI is async-first; mixing sync DB calls with async routes requires thread-pool workarounds that add latency under concurrent requests | For this scale sync would work, but asyncpg + SQLAlchemy async is the idiomatic FastAPI pattern and avoids retrofitting later |

## Project Structure

### Documentation (this feature)

```text
specs/002-data-ingestion/
├── plan.md              # This file
├── research.md          # Phase 0 — technology decisions
├── data-model.md        # Phase 1 — DB schema and entity definitions
├── quickstart.md        # Phase 1 — developer setup guide
├── contracts/
│   └── api.md           # Phase 1 — REST API contract
└── tasks.md             # Phase 2 output (speckit.tasks — NOT created here)
```

### Source Code

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan (scheduler startup/shutdown), CORS, rate limit
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
│   ├── api/                 # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── trips.py         # GET /trips, GET /trips/:id, POST /trips, PUT /trips/:id
│   │   ├── stops.py         # GET /stops
│   │   └── posts.py         # GET /instagram-posts, GET /substack-posts
│   ├── ingestion/           # Scheduled ingestion jobs
│   │   ├── __init__.py
│   │   ├── instagram.py     # instagrapi primary + Graph API fallback + email alert
│   │   ├── substack.py      # feedparser RSS ingestion
│   │   ├── location.py      # Airlabs IATA lookup + Claude inference fallback
│   │   └── scheduler.py     # APScheduler BackgroundScheduler, job registration
│   └── cli/
│       └── manage.py        # `python -m app.cli.manage login` — interactive instagrapi login
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── unit/                # Pure logic (location parsing, trip assignment, dedup)
│   ├── integration/         # DB-backed tests against test PostgreSQL
│   └── contract/            # HTTP contract tests via httpx TestClient
├── Dockerfile
├── requirements.txt
└── alembic.ini

scripts/
├── export-seed-data.ts      # tsx: imports TS data modules → writes JSON to scripts/seed-data/
├── seed.py                  # Python: reads seed-data JSON → inserts into PostgreSQL → pg_dump
└── seed-dump.sql            # Generated by seed.py; auto-applied by Docker DB container on first start

src/                         # Existing React frontend (unchanged by this spec)
public/
└── media/                   # Downloaded Instagram media files (served statically)

docker-compose.yml           # Backend + frontend + PostgreSQL; DB mounts seed-dump.sql on init
Dockerfile.frontend          # Nginx serving the Vite build output
.env                         # Local secrets (gitignored)
.env.example                 # Committed; all required keys with placeholder values
```

**Structure Decision**: Web application layout — `backend/` for the Python service, `src/` for the existing React frontend (unchanged), `scripts/` for the seed pipeline. The frontend Dockerfile serves the Vite `dist/` build via nginx. Docker Compose wires all three services together with the PostgreSQL database.
