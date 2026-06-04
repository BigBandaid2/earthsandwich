# Implementation Plan: Database & Backend

**Branch**: `002-database-backend` | **Date**: 2026-05-12 (updated 2026-05-22; overhauled 2026-06-04) | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/002-database-backend/spec.md`

## Summary

Build a Python/FastAPI backend with PostgreSQL that replaces the hard-coded TypeScript data with a relational database, exposes a REST API for the frontend, supports trip management writes with bearer-token auth, containerizes the full stack (backend + frontend + DB) with Docker Compose, and exposes an MCP interface for AI-assisted trip planning. All new backend code is built test-first (TDD, P1).

Phases 1–4 and 11 are complete: setup, foundational ORM/migrations, seed pipeline, read API with unit tests, and frontend API integration (Phase 11 / US7 shipped on this branch; ownership recorded in spec 001). Remaining work: write API (trip management + region end dates), MCP trip-intelligence interface (gated on a dedicated research + contract phase), full Docker Compose containerization (frontend service), health endpoint, and E2E validation. Ingestion (Instagram + Substack) is spec 003 (pile-app). Frontend components and API hooks are spec 001 (useful-app). Data normalization and stop linkage are the planned bridge-app's concern.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x (existing frontend + seed export script)
**Primary Dependencies**: FastAPI 0.115, SQLAlchemy 2.0 (async + asyncpg), Alembic, slowapi, structlog, pydantic-settings, httpx (async test client), pytest / pytest-asyncio; MCP library TBD pending US5 research
**Storage**: PostgreSQL 16 (all environments; SQLite dropped per spec clarification)
**Testing**: pytest, pytest-asyncio, httpx AsyncClient with AsyncMock get_db override; TDD mandate — failing test must exist before each new production code unit (FR-015); unit tests require no live database or external services
**Target Platform**: Linux server (Docker container); local Docker Compose for development
**Project Type**: REST API backend service + Docker Compose full-stack (backend + frontend + database)
**Performance Goals**: <500ms p95 for read endpoints under normal server load (SC-002)
**Constraints**: No hardcoded secrets; structured JSON logs to stdout only (FR-039); HTTPS in production; rate limiting on all public endpoints (FR-027); no internal identifiers or stack traces in API responses (FR-030)
**Scale/Scope**: ~3 trips, ~100s of stops and posts; small audience (travelers + friends/family); single-server deployment


## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Rule | Status | Notes |
|-----------------|--------|-------|
| I. Evolutionary Development | ✓ Pass | Plan reflects shipped state accurately — completed phases documented as complete; pending phases documented with actual blockers and deferred decisions (e.g. `POST /regions/end-date` storage deferred to design meeting) |
| II. Apps Are the Architectural Unit | ✓ Pass | 002 = useful-app persistence layer; 003 (pile-app) writes no tables here; bridge-app (planned) is the future intermediary; no shared code or filesystem reach-arounds between Apps |
| III. Project Purposes Are Authoritative | ✓ Pass | All requirements serve the Travelogue (useful-app) purpose catalogued in `docs/roadmap.md` |
| IV. AI-Driven Development as First-Class | ✓ Pass | MCP interface (US5) is a first-class planned feature; Claude Code is a primary development collaborator |
| V. Inference Inputs Preserved | ✓ Pass | MCP interface is a query surface for trip data, not an inference step; no model calls that would require input preservation today |
| Cardinal Rule #1: tasks.md historical record | ✓ Pass | Completed phases (1–4, 11) left intact; new work appends to the bottom |
| Cardinal Rule #3: No model-specific names | ✓ Pass | MCP tools and any AI-adjacent identifiers use role-based names; no Claude/GPT identifiers in code or schema |
| Cardinal Rule #5: Lean on references | ✓ Pass | Contracts reference spec; data-model references spec; this plan references rather than restates them |
| Foundational tech: Python · PostgreSQL · Docker | ✓ Pass | All three in active use; MCP library (TBD) is an App-local addition, not a constitutional change |

**Post-design re-check**: All gates clear. MCP implementation (FR-020–FR-023) is gated by FR-023 (research + contract prerequisites); implementation MUST NOT begin until that gate opens.

## Complexity Tracking

| Complexity | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Python backend | A queryable, filtered API requires server-side logic; static files cannot serve filtered queries efficiently | Static + manual TSV workflow doesn't support filtering, write endpoints, or future ingestion (specified in 003) |
| PostgreSQL | Relational FK constraints between trips → stops → posts and `stops.region_code → regions.iata_code`; queryable filters; unique constraints for idempotent ingestion | File-based storage (TSV/JSON) cannot enforce referential integrity or support efficient filtered queries |
| Docker Compose | Reproducible local dev, dependency isolation, and clean production deployment without host-level setup | Bare metal setup creates environment drift and increases onboarding friction (SC-005 targets <5 min to working local stack) |
| Async SQLAlchemy + asyncpg | FastAPI is async-first; mixing sync DB calls with async routes requires thread-pool workarounds that add latency under concurrent requests | For this scale sync would work, but asyncpg + SQLAlchemy async is the idiomatic FastAPI pattern and avoids retrofitting later |
| MCP interface (US5) | AI assistant must read live trip data to identify event-proximity conflicts; a structured machine-readable interface is required | Unstructured prompt injection of static data cannot support live trip queries or structured date-shift suggestions |

## Project Structure

### Documentation (this feature)

```text
specs/002-database-backend/
├── plan.md              # This file
├── research.md          # Phase 0 — technology decisions (framework, ORM, logging, rate limit, config, TS export)
│                        #           Decision 7+ (MCP event data sources) to be added before US5 implementation
├── data-model.md        # Phase 1 — DB schema and entity definitions (updated 2026-06-04: regions table, trips.id auto-gen)
├── quickstart.md        # Phase 1 — developer setup guide (DB + API + Docker)
├── contracts/
│   ├── api.md           # Phase 1 — REST API contract (updated 2026-06-04: GET /regions, GET /health, POST /trips id auto-gen)
│   └── mcp.md           # US5 — MCP trip-intelligence interface contract (PENDING: must precede US5 implementation)
└── tasks.md             # Phase 2 output
```

### Source Code

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, CORS, rate limit, structlog setup
│   ├── config.py            # pydantic-settings; all env vars validated at startup
│   ├── database.py          # SQLAlchemy async engine, session factory, get_db dependency
│   ├── models/              # SQLAlchemy ORM models (table definitions)
│   │   ├── __init__.py
│   │   ├── trip.py
│   │   ├── stop.py
│   │   ├── instagram_post.py
│   │   ├── substack_post.py
│   │   └── region.py        # regions reference table (FR-040)
│   ├── schemas/             # Pydantic v2 request/response schemas (API shapes)
│   │   ├── __init__.py
│   │   ├── trip.py
│   │   ├── stop.py
│   │   ├── post.py
│   │   └── region.py        # RegionResponse (FR-041)
│   └── api/                 # FastAPI route handlers
│       ├── __init__.py
│       ├── trips.py         # GET /trips, GET /trips/:id, POST /trips, PUT /trips/:id
│       ├── stops.py         # GET /stops
│       ├── posts.py         # GET /instagram-posts, GET /substack-posts
│       └── regions.py       # GET /regions (FR-041), POST /regions/end-date (FR-019 — pending contract)
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── unit/                # Async unit tests — mock get_db via AsyncMock (no live DB); test_trips.py ✓, test_stops.py ✓, test_posts.py ✓
│   ├── integration/         # DB-backed tests against test PostgreSQL (future)
│   └── contract/            # HTTP contract tests via httpx TestClient (future)
├── Dockerfile
├── requirements.txt
└── alembic.ini

scripts/
├── export-seed-data.ts      # tsx: imports TS data modules → writes JSON to scripts/seed-data/
├── seed.py                  # Python: reads seed-data JSON → inserts into PostgreSQL → pg_dump
├── seed-data/               # {trips,stops,instagram_posts,substack_posts,regions}.json ✓
└── seed-dump.sql            # Generated by seed.py; auto-applied by Docker DB container on first start ✓

frontend/                    # React/Vite frontend (moved from project root in T002)
├── src/
│   ├── api/                 # client.ts ✓, adapters.ts ✓  (spec 001 ownership)
│   └── hooks/               # useTrips.ts ✓, useTrip.ts ✓  (spec 001 ownership)
└── Dockerfile.frontend      # Pending — T045

public/
└── media/                   # Downloaded Instagram media files (served statically; populated by bridge-app)

docker-compose.yml           # Backend + frontend + PostgreSQL — pending T046
.env                         # Local secrets (gitignored)
.env.example                 # Committed; all required keys with placeholder values ✓
```

**Structure Decision**: Web application layout — `backend/` for the Python service, `frontend/` for the React frontend (moved from project root in Phase 1 T002), `scripts/` for the seed pipeline. The frontend Dockerfile serves the Vite `dist/` build via nginx. Docker Compose wires all three services together with the PostgreSQL database. 003 (pile-app) is a separate process with no shared code or tables.

> **Security note**: `backend/session.json` was accidentally committed on this branch (commit `ce55532`). It may contain pile-app (spec 003) authentication credentials. It MUST be added to `.gitignore` and removed from the git index before any public push (see FR-032 in spec.md).
