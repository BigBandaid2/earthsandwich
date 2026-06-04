# Tasks: Database & Backend

**Input**: Design documents from `specs/002-database-backend/`
**Prerequisites**: plan.md ✓, spec.md ✓, data-model.md ✓, contracts/api.md ✓, research.md ✓, quickstart.md ✓

**Tests**: Not explicitly requested — no test tasks generated. Tests directory structure is created in Phase 2 for future use.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

> **2026-05-22 split**: This spec was originally `002-data-ingestion`. The automated ingestion phases (Phase 5 — US3 Instagram, Phase 7 — US5 Substack) and the ingestion-side Phase 9 polish tasks (T048, T049) were moved to `003-ingestion-pipeline/tasks.md`. Their original numbering is preserved here as stubs to maintain traceability. Per Cardinal Rule #1 (`tasks.md` is a historical record), all completed phases (1, 2, 3) remain in place untouched.

> **Note on spec/plan drift**: The spec was updated (2026-05-15) to use Claude-only for all IATA region code determination. `plan.md` and `quickstart.md` are aligned; the prompt-engineering polish task lives in `003-ingestion-pipeline` (T049).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create the directory skeleton and base configuration files before any implementation begins.

- [x] T001 Create backend/ directory structure: app/, app/models/, app/schemas/, app/api/, app/ingestion/, app/cli/, alembic/versions/, tests/unit/, tests/integration/, tests/contract/ with __init__.py files per plan.md
- [x] T002 Move all frontend-specific files and folders from the project root into a new frontend/ directory: src/, index.html, vite.config.ts, tsconfig.json, tsconfig.node.json, public/images/, public/posts.json; keep public/media/ at project root (backend writes Instagram media here); package.json and package-lock.json live in frontend/ (backend is Python — no shared JS tooling at root); scripts/ stays at project root
- [x] T003 [P] Create backend/requirements.txt with all dependencies: fastapi==0.115.*, uvicorn[standard], sqlalchemy==2.0.*, asyncpg, alembic, apscheduler==3.*, instagrapi, feedparser, anthropic, slowapi, structlog, pydantic-settings, httpx, pytest, pytest-asyncio
- [x] T004 [P] Add tsx to package.json devDependencies for the TypeScript seed export script
- [x] T005 [P] Create .env.example listing all required variables from contracts/api.md (ANTHROPIC_API_KEY required for all location logic; AIRPORT_API_KEY excluded per updated spec)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure — config, database connection, ORM models, migrations, app skeleton, and response schemas — that MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T006 Create backend/app/config.py with pydantic-settings BaseSettings; validate all required env vars at startup (INSTA_USERNAME, INSTA_PASSWORD, ANTHROPIC_API_KEY, DATABASE_URL, API_SECRET_KEY, SUBSTACK_RSS_URL, FRONTEND_ORIGIN, INSTAGRAPI_SESSION_FILE); optional vars with defaults (INSTAGRAM_POLL_INTERVAL_MINUTES=60, SUBSTACK_POLL_INTERVAL_MINUTES=60, SMTP_*, LOG_LEVEL, ENVIRONMENT); raise clear ValidationError on missing required vars
- [x] T007 [P] Create backend/app/database.py with SQLAlchemy 2.0 async engine (asyncpg), AsyncSession factory, and get_db dependency for FastAPI injection
- [x] T008 Create backend/app/main.py with FastAPI app, lifespan hook (scheduler start/stop), CORS middleware (FRONTEND_ORIGIN), slowapi rate limiter (60 req/min per IP → 429), and structlog setup (JSONRenderer in production, ConsoleRenderer in development)
- [x] T009 Create backend/app/models/trip.py with Trip SQLAlchemy ORM model: id VARCHAR(100) PK, title, description, start_date DATE, end_date DATE, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ; index on (start_date, end_date)
- [x] T010 [P] Create backend/app/models/stop.py with Stop SQLAlchemy ORM model: id VARCHAR(100) PK, trip_id FK→trips, date DATE, location VARCHAR(500), lat DECIMAL(10,7) nullable, lng DECIMAL(10,7) nullable, status CHECK('visited','planned'), region_code VARCHAR(10) nullable, post_type CHECK('instagram','substack','planned'), sequence_order INTEGER, caption TEXT nullable, created_at TIMESTAMPTZ; indexes on (trip_id, sequence_order), (trip_id, status), (trip_id, region_code), (date)
- [x] T011 [P] Create backend/app/models/instagram_post.py with InstagramPost SQLAlchemy ORM model: id UUID PK default gen_random_uuid(), stop_id FK→stops UNIQUE, instagram_id VARCHAR(100) UNIQUE, shortcode, media_url VARCHAR(500), caption TEXT, timestamp TIMESTAMPTZ, created_at TIMESTAMPTZ; indexes on instagram_id UNIQUE, timestamp, stop_id
- [x] T012 [P] Create backend/app/models/substack_post.py with SubstackPost SQLAlchemy ORM model: id UUID PK, stop_id FK→stops nullable, substack_id VARCHAR(500) UNIQUE, title, subtitle TEXT nullable, body TEXT, published_at TIMESTAMPTZ, created_at TIMESTAMPTZ; indexes on substack_id UNIQUE, published_at, stop_id
- [x] T013 Update backend/app/models/__init__.py to import Trip, Stop, InstagramPost, SubstackPost so Alembic autogenerate detects all tables
- [x] T014 Initialize Alembic in backend/ (alembic.ini, alembic/env.py); configure env.py for async SQLAlchemy using asyncpg and target_metadata from app.models
- [x] T015 Generate initial Alembic migration (`alembic revision --autogenerate -m "initial schema"`) creating all four tables with all columns, constraints, and indexes from data-model.md; apply with `alembic upgrade head`
- [x] T016 [P] Create backend/app/schemas/trip.py with Pydantic v2 TripBase, TripCreate (id + title + description + start_date + end_date), TripUpdate (all optional), TripResponse (adds created_at, updated_at), TripDetailResponse (adds stops list)
- [x] T017 [P] Create backend/app/schemas/stop.py with StopResponse including all stop fields and a nullable post field (InstagramPostResponse | SubstackPostResponse | None)
- [x] T018 [P] Create backend/app/schemas/post.py with InstagramPostResponse and SubstackPostResponse matching the shapes in contracts/api.md

**Checkpoint**: Foundation ready — all four ORM models exist, migration applied, app skeleton starts without errors, schemas defined. User story implementation can begin.

---

## Phase 3: User Story 1 — Seed the Database (Priority: P1) 🎯 MVP

**Goal**: Migrate all hard-coded TypeScript trip/stop/post data into PostgreSQL via a two-step seed pipeline; generate a SQL dump for Docker initialization.

**Independent Test**: Run `npx tsx scripts/export-seed-data.ts` → confirm JSON files appear in scripts/seed-data/. Run `python scripts/seed.py` against a fresh DB → inspect record counts match the TS source arrays. Re-run → verify no duplicates. Confirm scripts/seed-dump.sql is generated.

- [x] T019 [US1] Create scripts/export-seed-data.ts using tsx: import src/data/miscellaneous-adventures.ts, earth-sandwich-2015.ts, earth-club-sandwich-2027.ts (update import paths if frontend/ move in T002 changed these locations); serialize trips, stops, instagram_posts, and substack_posts to scripts/seed-data/{trips,stops,instagram_posts,substack_posts}.json preserving all fields and array ordering
- [x] T020 [US1] Create scripts/seed.py: read the four JSON files from scripts/seed-data/; insert records into PostgreSQL in FK order (trips first, then stops, then instagram_posts and substack_posts) using `INSERT ... ON CONFLICT DO NOTHING` on all primary keys and unique indexes
- [x] T021 [US1] ~~Add sequence_order assignment to scripts/seed.py~~ Removed sequence_order from the data model entirely — stop ordering is derived from (trip_id, date, region_code); updated Stop model, migration, schemas, export script, and seed script accordingly
- [x] T022 [US1] Add pg_dump invocation to scripts/seed.py after successful seeding: call `pg_dump` via subprocess using DATABASE_URL env var; write output to scripts/seed-dump.sql; log the dump path on completion

**Checkpoint**: US1 complete — database seeded, seed-dump.sql committed; run quickstart.md sections 2–3 to validate.

---

## Phase 4: User Story 2 — Read API Endpoints (Priority: P1)

**Goal**: Expose trips, stops, and posts as a filterable REST API consumed by the frontend and other clients.

**Independent Test**: Start backend with `uvicorn app.main:app --reload`; run all curl commands from quickstart.md section 6; verify response shapes match contracts/api.md exactly. Test invalid trip id → 404. Test invalid filter value → 422.

- [x] T023 [P] [US2] Create backend/app/api/trips.py with GET /trips handler (reverse-chronological by start_date, optional status filter: active/completed/upcoming derived from dates vs. today) and GET /trips/:id handler (returns full trip with nested stops and each stop's post data using a join query; returns 404 if trip not found)
- [x] T024 [P] [US2] Create backend/app/api/stops.py with GET /stops handler supporting all query filters from contracts/api.md: trip_id, status, region_code, post_type, after (date ≥), before (date ≤)
- [x] T025 [P] [US2] Create backend/app/api/posts.py with GET /instagram-posts handler (filters: stop_id, after timestamp, before timestamp) and GET /substack-posts handler (same filters; only return rows where stop_id IS NOT NULL)
- [x] T026 [US2] Register all read routers (trips, stops, posts) in backend/app/main.py with appropriate prefixes
- [x] T027 [US2] Implement structured error responses in all route handlers: `{"error": "...", "detail": "..."}` for 404 (trip/stop not found), 422 (invalid query params), 500 (unexpected); ensure no stack traces or internal identifiers leak (FR-033)
- [x] T052 [US2] Create backend/tests/conftest.py with pytest-asyncio configuration (asyncio_mode = "auto") and an async `client` fixture using `httpx.AsyncClient` with the FastAPI app; override `get_db` to yield an `AsyncMock` that returns controlled query results; add factory helpers that build realistic mock Trip, Stop, InstagramPost, and SubstackPost objects for reuse across unit test modules
- [x] T053 [P] [US2] Write backend/tests/unit/api/test_trips.py: test GET /trips returns 200 with trips sorted reverse-chronologically by start_date; test `status=active`, `status=completed`, and `status=upcoming` each return only matching trips; test GET /trips/:id returns 200 with nested stops where `post` is `InstagramPostResponse` for instagram stops, `SubstackPostResponse` for substack stops, and null for planned stops; test GET /trips/:id returns 404 with `{"error": "Not Found", ...}` for an unknown id
- [x] T054 [P] [US2] Write backend/tests/unit/api/test_stops.py: test GET /stops with no filters returns 200 with all stops; test each query param (trip_id, status, region_code, post_type, after, before) filters results correctly in isolation; test combined filters narrow results correctly; verify response items do not include a `post` field
- [x] T055 [P] [US2] Write backend/tests/unit/api/test_posts.py: test GET /instagram-posts returns 200; test stop_id, after, and before query params each filter correctly; test GET /substack-posts returns only rows where stop_id IS NOT NULL; test stop_id, after, and before query params filter substack posts correctly

**Checkpoint**: US1 + US2 complete — frontend can query trips, stops, and posts from the database; validate with quickstart.md section 6.

---

## Phase 5: User Story 3 — Instagram Ingestion (MOVED)

> **Moved to `003-ingestion-pipeline/tasks.md` on 2026-05-22 as that spec's Phase 1.** T028 through T036 are tracked there. Task IDs preserved.

---

## Phase 6: User Story 4 — Trip Management & Region End Date (Priority: P2)

**Goal**: Allow authorized operators to create/update trips and record region end dates via the API.

**Independent Test**: Use curl with `Authorization: Bearer <API_SECRET_KEY>` to POST /trips (201 response), PUT /trips/:id (200 response with updated fields), and POST /regions/end-date (200 response). Verify 401 for all three without a token. Verify 409 on duplicate trip id. Verify 422 on bad date format.

- [ ] T037 [P] [US4] Define POST /regions/end-date contract in specs/002-database-backend/contracts/api.md: request body (optional trip string, optional region string, optional date ISO 8601), response shape, storage strategy (decided in a design meeting — do NOT begin this task until that meeting has been held and a storage model chosen; see Clarifications in spec.md), and any required migration — this task MUST be completed before T040
- [ ] T038 [P] [US4] Add POST /trips handler to backend/app/api/trips.py: validate body (title, description, start_date, end_date — no id field); auto-generate id by slugifying title (lowercase, hyphens); if a trip with the same title already exists return 409; if the generated slug collides with an existing id, append an incrementing counter (e.g. `my-trip-2`); on success return 201 with the generated id; return 401 on missing/invalid bearer token; return 422 on invalid date format (FR-017, FR-026) — TDD: T072 test must exist and fail before this task begins
- [ ] T039 [P] [US4] Add PUT /trips/:id handler to backend/app/api/trips.py: validate body via TripUpdate (all fields optional); apply partial update (last-write-wins, no optimistic locking); update updated_at; return 200 TripResponse; return 401/404/422 as appropriate (FR-018, FR-026) — TDD: T072 test must exist and fail before this task begins
- [ ] T040 [US4] Add POST /regions/end-date handler to backend/app/api/regions.py per contract defined in T037: resolve defaults (most recent trip by created_at if trip omitted; most recent region_code seen in that trip's stops if region omitted; current date if date omitted); require bearer auth (FR-026) — depends on T037
- [ ] T041 [US4] Register POST /trips, PUT /trips/:id write handlers and POST /regions/end-date router in backend/app/main.py; add shared bearer token auth dependency enforcing FR-029 across all write endpoints

**Checkpoint**: US4 complete — operators can manage trips and record region transitions without code changes.

---

## Phase 7: User Story 5 — Substack Ingestion (MOVED)

> **Moved to `003-ingestion-pipeline/tasks.md` on 2026-05-22 as that spec's Phase 2.** T042 and T043 are tracked there. Task IDs preserved.

---

## Phase 8: User Story 6 — Containerization (Priority: P3)

**Goal**: Full stack (backend + frontend + database) starts with `docker compose up` on a clean machine; database is pre-populated from seed-dump.sql.

**Independent Test**: On a machine with Docker and no local Python/Node setup, run `docker compose up`; navigate to frontend URL; confirm travelogue loads data from backend. Stop and restart → data still present.

- [x] T044 [P] [US6] Create backend/Dockerfile: Python 3.12 slim base; COPY requirements.txt and RUN pip install; COPY app/; EXPOSE 8000; CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
- [ ] T045 [P] [US6] Create Dockerfile.frontend: multi-stage — stage 1 Node 18 alpine, COPY package*.json, RUN npm ci, COPY frontend/src/ (updated path after T002 migration), RUN npm run build; stage 2 nginx:alpine, COPY --from=stage1 /app/dist /usr/share/nginx/html
- [ ] T046 [US6] Create docker-compose.yml: db service (postgres:16, named volume for data persistence, mounts scripts/seed-dump.sql into /docker-entrypoint-initdb.d/seed-dump.sql, health check via pg_isready); backend service (build backend/, depends_on db with health condition, env_file .env, health check via GET /health); frontend service (build Dockerfile.frontend, depends_on backend); all services on shared network (FR-036, FR-038, FR-039)
- [X] T047 [US6] Verify backend can connect to db service using Docker Compose service name in DATABASE_URL (postgresql+asyncpg://user:pass@db:5432/earthsandwich); confirm Alembic migrations run on backend container start before accepting traffic

**Checkpoint**: US6 complete — validate with quickstart.md section 2 end-to-end (docker compose up → browser loads travelogue).

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Container health endpoint and end-to-end validation. Ingestion-side polish (T048 supporting-artifact cleanup, T049 Claude prompt engineering) moved to `003-ingestion-pipeline/tasks.md` Phase 3.

- [ ] T050 [P] Add GET /health endpoint to backend/app/main.py returning `{"status": "ok"}` with 200; used by Docker Compose health check on the backend service (FR-039)
- [ ] T051 Validate end-to-end developer workflow per quickstart.md: `docker compose up` → seed pipeline → Instagram login → manual ingestion trigger → API queries → confirm all user stories work together; document any deviations in quickstart.md

---

## Phase 10: Drift Reconciliation (2026-05-25 weekly scan)

**Status**: Dev-infrastructure work that shipped without a prior task entry.

- [x] T052 Add temporary `docker-compose.db.yml` (Postgres-only stack) used during seed-script development. Superseded by the full `docker-compose.yml` in T046. Commit: `ce55532`. **Security note**: `backend/session.json` was committed in the same change — verify whether it contains real auth state before pushing to a public remote.

---

## Phase 11: User Story 7 — Frontend API Integration (Priority: P1)

**Goal**: Replace all hardcoded TypeScript data imports and the `/posts.json` static fetch with live calls to the backend REST API. After this phase, trips, stops, and posts are all served from the database with no TypeScript data files imported at runtime.

**Independent Test**: Start both backend and frontend (`uvicorn` + `npm run dev`). Open the browser — confirm trips load from the API. Switch trips in the dropdown — confirm stops update from the API. Open a stop modal — confirm post data (image or article) appears. Kill the backend — confirm the frontend shows an error/loading state rather than crashing.

- [x] T056 [P] [US7] Add `VITE_API_BASE_URL=http://localhost:8000` to `frontend/.env.example`; this env var points the frontend at the backend API in all environments; in the Docker Compose setup this will be overridden to the backend service name
- [x] T057 [P] [US7] Create `frontend/src/api/client.ts`: define TypeScript interfaces for all API response shapes (`ApiTrip`, `ApiTripDetail`, `ApiStop`, `ApiInstagramPost`, `ApiSubstackPost`); implement typed async fetch functions `getTrips(params?: { status?: string })`, `getTripDetail(id: string)`, `getStops(params?)`, `getInstagramPosts(params?)`, `getSubstackPosts(params?)`; each reads `import.meta.env.VITE_API_BASE_URL` as the base URL and throws `Error` on non-2xx responses using the `{"error", "detail"}` error shape from contracts/api.md
- [x] T058 [P] [US7] Create `frontend/src/api/adapters.ts`: implement `adaptStop(apiStop: ApiStop): Stop` mapping flat `lat`/`lng` → `coords: { lat, lng }`, `post_type` + post object → `StopPost` with `type` discriminator (`media_url` → `image`, `instagram_id` → `instagramId` for instagram stops; substack shape maps directly; planned stop → `{ type: 'planned', caption: stop.caption ?? undefined }`); implement `adaptTrip(apiTrip: ApiTripDetail): Trip` mapping its stop list through `adaptStop`; implement `adaptTripSummary(apiTrip: ApiTrip): Trip` returning the trip with `stops: []` for the list view
- [x] T059 [P] [US7] Create `frontend/src/hooks/useTrips.ts`: fetch `getTrips()` on mount, map each result through `adaptTripSummary`, return `{ trips: Trip[], loading: boolean, error: string | null }`; this hook drives the trip selector dropdown in App.tsx
- [x] T060 [P] [US7] Create `frontend/src/hooks/useTrip.ts`: accept `tripId: string | null`; fetch `getTripDetail(tripId)` whenever `tripId` changes (skip if null), map through `adaptTrip`, return `{ trip: Trip | null, loading: boolean, error: string | null }`; this hook provides full stop and post data for the active trip, replacing the hardcoded data import and the `usePosts` merge in App.tsx
- [x] T061 [US7] Update `frontend/src/App.tsx`: remove `import { trips } from './data/itinerary'`; replace the hardcoded `TRIPS` constant with the `trips` array from `useTrips()`; use `useTrip(activeTrip?.id ?? null)` to get full stop data for the active trip; remove the `usePosts()` call and the `effectiveActiveTrip` merge logic (API now returns all stops); initialize `activeTrip` by resolving `window.location.hash` against the fetched trips list once loaded (keep `tripFromHash` logic, run it after trips arrive); render a loading indicator while initial trips fetch is in flight; keep all hash-based navigation and `handleSelectTrip` working as before
- [x] T062 [US7] Delete `frontend/src/hooks/usePosts.ts` (its function is now covered by `useTrip`); confirm no remaining `import.*usePosts` references exist in the codebase; the `frontend/public/posts.json` static file can remain in place as a data artifact but is no longer fetched by the frontend

**Checkpoint**: US7 complete — browser renders all trip/stop/post content from the live backend; no TypeScript data modules are imported at runtime. Validate by inspecting browser DevTools network tab for API calls.

---

## Phase 12: Regions Reference Table (FR-040, FR-041)

**Purpose**: Implement the `regions` reference table added in the spec overhaul. Blocks the FK constraint on `stops.region_code` and the `GET /regions` read endpoint.

**Independent Test**: Run `npx tsx scripts/export-seed-data.ts` → confirm `scripts/seed-data/regions.json` is produced. Run `python scripts/seed.py` against a fresh DB → confirm `regions` rows are present and `stops.region_code` FK is enforced. Call `GET /regions` → verify all regions returned with correct shape. Call `GET /regions?country=Colombia` → verify filtered results.

- [x] T063 Create `backend/app/models/region.py` with Region SQLAlchemy ORM model: `iata_code VARCHAR(10) PK`, `name VARCHAR(255) NOT NULL`, `airport_name VARCHAR(500) NOT NULL`, `country VARCHAR(255) NOT NULL`, `lat DECIMAL(10,7) NOT NULL`, `lng DECIMAL(10,7) NOT NULL`; no indexes beyond PK (reference table, full-table scans acceptable)
- [x] T064 [P] Update `backend/app/models/__init__.py` to import Region so Alembic autogenerate detects the new table
- [x] T065 [P] Create `backend/app/schemas/region.py` with RegionResponse Pydantic v2 model: all six fields matching the `regions` table; shape must match contracts/api.md GET /regions response
- [x] T066 Generate Alembic migration (`alembic revision --autogenerate -m "add regions table and stops region_code fk"`): creates `regions` table with all columns; adds FK constraint `stops.region_code → regions.iata_code` (NULLABLE, ON DELETE SET NULL); apply with `alembic upgrade head` — depends on T063 and T064
- [x] T067 Update `scripts/export-seed-data.ts` to import `frontend/src/data/regions.ts` and serialize to `scripts/seed-data/regions.json`
- [x] T068 Update `scripts/seed.py` to read `scripts/seed-data/regions.json` and insert all region records using `INSERT ... ON CONFLICT DO NOTHING` on `iata_code` BEFORE inserting stops (FK order); re-run seed against a fresh DB and regenerate `scripts/seed-dump.sql` — depends on T066
- [ ] T069 [P] [US2] Write `backend/tests/unit/api/test_regions.py` (TDD — must precede T070): test GET /regions returns 200 with a list of RegionResponse objects; test `country=Colombia` filter returns only regions where country matches; test GET /regions with no filter returns all regions; verify response shape matches contracts/api.md
- [ ] T070 [US2] Add GET /regions handler to `backend/app/api/regions.py`: query all `regions` rows; apply optional `country` query param filter (exact match); return list of RegionResponse; no authentication required (FR-041) — depends on T069 TDD test existing and failing
- [ ] T071 Register GET /regions router in `backend/app/main.py`

**Checkpoint**: Phase 12 complete — `regions` table seeded, FK constraint on stops enforced, GET /regions endpoint live. Validate by running the updated seed pipeline and calling the endpoint.

---

## Phase 13: TDD Tests — Write API & Health Endpoint; Security Fix (US3, P1)

**Purpose**: Write failing unit tests for all write endpoints and the health endpoint (TDD prerequisite for Phase 6 and Phase 9 implementation tasks); remove the accidentally committed `backend/session.json` from the git index (FR-032).

> **Execution note**: T072 MUST be completed before Phase 6 tasks T038 and T039 begin. T073 MUST be completed before Phase 9 task T050 begins. T074 is independent and can run at any time.

**Independent Test**: Run `pytest backend/tests/unit/api/test_write_trips.py` — all tests must FAIL before T038/T039 are implemented. Run `pytest backend/tests/unit/api/test_health.py` — must FAIL before T050. Run `git status backend/session.json` — file must be untracked (removed from index).

- [ ] T072 [P] [US3] Write `backend/tests/unit/api/test_write_trips.py` (TDD — must precede Phase 6 T038/T039): test POST /trips with valid body returns 201 with auto-generated slug id derived from title (e.g. `"New Adventure 2029"` → `"new-adventure-2029"`); test POST /trips with duplicate title returns 409; test POST /trips whose title slug collides with existing id returns 201 with counter-suffixed id (e.g. `"my-trip-2"`); test POST /trips without auth header returns 401; test POST /trips with invalid date format returns 422; test PUT /trips/:id with partial body returns 200 with supplied fields updated and omitted fields preserved; test PUT /trips/:id without auth returns 401; test PUT /trips/:id with unknown id returns 404; test PUT /trips/:id with invalid date returns 422
- [ ] T073 [P] [US3] Write `backend/tests/unit/api/test_health.py` (TDD — must precede Phase 9 T050): test GET /health returns 200 with body `{"status": "ok"}`; test GET /health returns 200 with no Authorization header (authentication not required)
- [ ] T074 [P] Fix security issue per FR-032: add `backend/session.json` to `.gitignore`; run `git rm --cached backend/session.json` to remove the file from the git index without deleting the local file; commit the `.gitignore` change

**Checkpoint**: Phase 13 complete — TDD tests written and failing (confirming tests are real), session.json removed from git tracking.

---

## Phase 14: MCP Trip Intelligence — Research & Contract (US5, P2)

**Purpose**: Complete the research and contract prerequisites for the MCP trip-intelligence interface. No implementation tasks are included — those will be added in a future phase once the contract is reviewed.

> **Gate**: Implementation of US5 (FR-020–FR-023) MUST NOT begin until T075 (research) and T076 (contract) are both complete and reviewed. See FR-023 in spec.md.

**Independent Test**: Confirm `specs/002-database-backend/research.md` contains Decision 7+ documenting at least two evaluated event data sources (coverage, rate limits, format, chosen approach). Confirm `specs/002-database-backend/contracts/mcp.md` exists with: tool names and descriptions, input/output schemas, authentication model (API_SECRET_KEY bearer token), external data source integration pattern, and error responses.

- [ ] T075 [US5] Research MCP event data sources: evaluate at least two public holiday / festival APIs (e.g. Calendarific, Nager.Date, OpenHolidays, or others); assess free tier request limits, regional coverage for planned trip destinations (Colombia, Mexico, New Zealand, …), response format, and date-range query support; document findings in `specs/002-database-backend/research.md` as Decision 7 using the existing decision format (Decision / Rationale / Alternatives considered)
- [ ] T076 [US5] Define MCP contract in `specs/002-database-backend/contracts/mcp.md` (depends on T075): specify MCP tool names and descriptions; input schemas (trip_id, proximity_window in days); output schemas (stop id, event_name, event_date, suggested_date_shift_range); authentication model (same API_SECRET_KEY bearer token as write endpoints); external data source integration pattern (which API, request shape, response mapping); error responses; contract must be reviewed before any implementation begins (FR-023)

**Checkpoint**: Phase 14 complete — research documented, MCP contract file exists and reviewed. Ready to add US5 implementation tasks in a subsequent tasks phase.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2; T019 should run after T002 (frontend move may shift TS data import paths)
- **US2 (Phase 4)**: Depends on Phase 2; no dependency on US1 (but seeded data needed for manual testing)
- **US4 (Phase 6)**: Depends on Phase 2; T040 depends on T037 (contract must be defined first; T037 itself cannot begin until the design meeting for the storage model is held); T038 and T039 each require T072 (TDD test) to exist and fail before implementation begins
- **US6 (Phase 8)**: Depends on Phase 2; practically benefits from US1 (seed-dump.sql) existing; T045 Dockerfile.frontend COPY paths must reflect T002 frontend/ move
- **Polish (Phase 9)**: T050 requires T073 (TDD test) to exist and fail before implementation begins; T051 depends on all user story phases
- **US7 (Phase 11)**: Depends on US2 (Phase 4) completion — API endpoints must exist before frontend consumes them; T061 depends on T056–T060 all completing first; T062 can run after T061
- **Regions (Phase 12)**: Depends on Phase 2; T066 depends on T063 + T064; T068 depends on T066; T070 depends on T069 (TDD); T071 depends on T070
- **TDD Tests + Security (Phase 13)**: T072 must precede Phase 6 T038/T039; T073 must precede Phase 9 T050; T074 is independent
- **MCP Research (Phase 14)**: T076 depends on T075; no further implementation tasks until contract is reviewed

### Parallel Opportunities

- T003, T004, T005 in Phase 1: all parallel (different files); T002 is sequential (filesystem move)
- T007, T010, T011, T012, T016, T017, T018 in Phase 2: all parallel (different files)
- T023, T024, T025 in US2: all parallel (different files); T052 (conftest) must precede T053, T054, T055
- T053, T054, T055 in US2: all parallel after T052 (different test files)
- T037, T038, T039 in US4: all parallel (T040 waits on T037)
- T044, T045 in US6: parallel (different Dockerfiles)
- T048, T049, T050 in Polish: all parallel
- T056, T057, T058, T059, T060 in US7: all parallel (different files); T061 waits for all five; T062 runs after T061

---

## Parallel Examples

### Phase 2 Models (can all run simultaneously):
```
Task T009: Create backend/app/models/trip.py
Task T010: Create backend/app/models/stop.py
Task T011: Create backend/app/models/instagram_post.py
Task T012: Create backend/app/models/substack_post.py
```

### US2 Read Endpoints (can all run simultaneously):
```
Task T023: Create backend/app/api/trips.py (GET /trips, GET /trips/:id)
Task T024: Create backend/app/api/stops.py (GET /stops)
Task T025: Create backend/app/api/posts.py (GET /instagram-posts, GET /substack-posts)
```

### US2 Unit Tests (T052 first, then T053–T055 parallel):
```
Task T052: Create backend/tests/conftest.py  ← first (test infrastructure)
Then in parallel:
Task T053: Write backend/tests/unit/api/test_trips.py
Task T054: Write backend/tests/unit/api/test_stops.py
Task T055: Write backend/tests/unit/api/test_posts.py
```

### US4 Write Endpoints (T037 must complete first, then T038+T039 parallel):
```
Task T037: Define POST /regions/end-date contract in contracts/api.md  ← first
Then in parallel:
Task T038: Add POST /trips handler
Task T039: Add PUT /trips/:id handler
Task T040: Create backend/app/api/regions.py  ← after T037 only
```

### US7 Frontend API Integration (T056–T060 parallel first, then T061):
```
In parallel:
Task T056: Add VITE_API_BASE_URL to frontend/.env.example
Task T057: Create frontend/src/api/client.ts
Task T058: Create frontend/src/api/adapters.ts
Task T059: Create frontend/src/hooks/useTrips.ts
Task T060: Create frontend/src/hooks/useTrip.ts
Then sequentially:
Task T061: Update frontend/src/App.tsx  ← after all five above
Task T062: Delete frontend/src/hooks/usePosts.ts  ← after T061
```

### Phase 12 Regions (T063–T065 parallel, then T066, then T067+T069 parallel, then T068+T070 parallel, then T071):
```
In parallel:
Task T063: Create backend/app/models/region.py
Task T064: Update backend/app/models/__init__.py
Task T065: Create backend/app/schemas/region.py
Then sequentially:
Task T066: Generate and apply Alembic migration  ← after T063 + T064
In parallel (after T066):
Task T067: Update scripts/export-seed-data.ts
Task T069: Write backend/tests/unit/api/test_regions.py (TDD)
Then in parallel:
Task T068: Update scripts/seed.py + regenerate seed-dump.sql  ← after T066
Task T070: Add GET /regions handler  ← after T069 (TDD test must fail first)
Then sequentially:
Task T071: Register GET /regions router in main.py  ← after T070
```

### Phase 13 TDD Tests (T072, T073, T074 all parallel):
```
In parallel (all independent):
Task T072: Write backend/tests/unit/api/test_write_trips.py
Task T073: Write backend/tests/unit/api/test_health.py
Task T074: Fix backend/session.json security issue
```

### Phase 14 MCP Research (T075 then T076):
```
Sequentially:
Task T075: Research MCP event data sources → document in research.md
Task T076: Define MCP contract in contracts/mcp.md  ← after T075
```

---

## Implementation Strategy

### MVP First (US1 + US2 — both P1)

1. Complete Phase 1: Setup (including T002 frontend move)
2. Complete Phase 2: Foundational (**CRITICAL** — blocks everything)
3. Complete Phase 3: US1 (seed pipeline)
4. Complete Phase 4: US2 (read API)
5. **STOP and VALIDATE**: Seed data loads; API returns trips/stops/posts; quickstart sections 2–3 and 6 pass
6. Complete Phase 11: US7 (frontend API integration)
7. **STOP and VALIDATE**: Browser renders live data from API; no hardcoded TS data imported at runtime
8. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → skeleton ready
2. US1 → database seeded, SQL dump committed → **demo: data in DB**
3. US2 → read API live → **demo: API returns trips/stops/posts**
4. US7 → frontend calls API → **demo: browser renders live data from DB** (MVP! — recorded in spec 001)
5. Phase 12 → regions table seeded, FK constraint enforced, GET /regions live → **demo: regions endpoint works**
6. Phase 13 → TDD test tasks written (failing), security fix committed → **demo: tests fail as expected; session.json untracked**
7. US4 → trip management (write tests T072 pass) → **demo: operator can create/update trips via API**
8. US6 → containerized → **demo: `docker compose up` works from scratch**
9. Polish (T050 after T073 passes, T051) → **demo: GET /health works, E2E validated**
10. Phase 14 → MCP research + contract reviewed → **gate open for US5 implementation tasks**

---

## Notes

- **[P]** = different files, no incomplete dependencies; safe to run in parallel
- **[Story]** label maps each task to a specific user story for traceability
- Each user story is independently completable and testable via its Independent Test
- **T002** (frontend/ move) is a Setup task that affects T019 (TS data import paths) and T045 (Dockerfile.frontend COPY paths) — complete T002 before those tasks
- **T037** (contract) is a blocking dependency for T040 — do not implement the region end-date handler before the contract is defined; T037 itself cannot begin until a design meeting settles the storage model
- **T072** (write API TDD tests) must exist and fail before Phase 6 T038/T039 begin — TDD mandate (FR-015)
- **T073** (health endpoint TDD test) must exist and fail before Phase 9 T050 begins — TDD mandate (FR-015)
- Phase 5 (US3 Instagram) and Phase 7 (US5 Substack) stubs preserve the original phase numbering after the 2026-05-22 split — the actual tasks live in `003-ingestion-pipeline/tasks.md`
- Phase 12 adds the `regions` table (FR-040) which was introduced in the spec overhaul (2026-06-01); T066 migration must precede any seed pipeline re-run
- Phase 14 (MCP research + contract) gates all US5 implementation; no implementation tasks exist until T076 is reviewed
- Commit after each task or logical group; stop at any checkpoint to validate the story independently
