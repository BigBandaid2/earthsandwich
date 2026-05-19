# Tasks: Data Ingestion & Backend

**Input**: Design documents from `specs/002-data-ingestion/`
**Prerequisites**: plan.md ✓, spec.md ✓, data-model.md ✓, contracts/api.md ✓, research.md ✓, quickstart.md ✓

**Tests**: Not explicitly requested — no test tasks generated. Tests directory structure is created in Phase 2 for future use.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

> **Note on spec/plan drift**: The spec was updated (2026-05-15) to use Claude-only for all IATA region code determination. `plan.md` and `quickstart.md` still reference Airlabs and `AIRPORT_API_KEY`. Tasks in Phases 5 and 9 reflect the updated spec; T049 aligns the supporting artifacts.

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
- [ ] T021 [US1] Add sequence_order assignment to scripts/seed.py: derive each stop's sequence_order from its array index in the TS source data so ordered retrieval per trip matches the original frontend ordering
- [ ] T022 [US1] Add pg_dump invocation to scripts/seed.py after successful seeding: call `pg_dump` via subprocess using DATABASE_URL env var; write output to scripts/seed-dump.sql; log the dump path on completion

**Checkpoint**: US1 complete — database seeded, seed-dump.sql committed; run quickstart.md sections 2–3 to validate.

---

## Phase 4: User Story 2 — Read API Endpoints (Priority: P1)

**Goal**: Expose trips, stops, and posts as a filterable REST API consumed by the frontend and other clients.

**Independent Test**: Start backend with `uvicorn app.main:app --reload`; run all curl commands from quickstart.md section 8; verify response shapes match contracts/api.md exactly. Test invalid trip id → 404. Test invalid filter value → 422.

- [ ] T023 [P] [US2] Create backend/app/api/trips.py with GET /trips handler (reverse-chronological by start_date, optional status filter: active/completed/upcoming derived from dates vs. today) and GET /trips/:id handler (returns full trip with nested stops and each stop's post data using a join query; returns 404 if trip not found)
- [ ] T024 [P] [US2] Create backend/app/api/stops.py with GET /stops handler supporting all query filters from contracts/api.md: trip_id, status, region_code, post_type, after (date ≥), before (date ≤)
- [ ] T025 [P] [US2] Create backend/app/api/posts.py with GET /instagram-posts handler (filters: stop_id, after timestamp, before timestamp) and GET /substack-posts handler (same filters; only return rows where stop_id IS NOT NULL)
- [ ] T026 [US2] Register all read routers (trips, stops, posts) in backend/app/main.py with appropriate prefixes
- [ ] T027 [US2] Implement structured error responses in all route handlers: `{"error": "...", "detail": "..."}` for 404 (trip/stop not found), 422 (invalid query params), 500 (unexpected); ensure no stack traces or internal identifiers leak (FR-033)

**Checkpoint**: US1 + US2 complete — frontend can query trips, stops, and posts from the database; validate with quickstart.md section 8.

---

## Phase 5: User Story 3 — Instagram Ingestion (Priority: P2)

**Goal**: Automatically ingest new Instagram posts on a recurring schedule; geocode locations via Claude only; download media; assign stops to trips.

**Independent Test**: Set up credentials; trigger `python -m app.ingestion.instagram`; verify new stop + instagram_post records appear in DB with location, lat, lng, region_code, and media_url set. Re-run → zero new records. Test with a post that has a tagged location and one that does not.

- [ ] T028 [US3] Create backend/app/ingestion/location.py implementing Claude-only IATA determination: (a) **tagged location path** — when instagrapi provides a location name, pass name + lat + lng to Claude and ask only for the IATA code of the nearest in-country international airport; store tagged name/coords verbatim without modification; (b) **no-tag path** — call Claude with the post caption, base64-encoded image (IMAGE posts), and the location strings of up to 5 most-recently-ingested stops; prompt must explicitly instruct Claude to identify the location from observable content (visible signage, landmarks, recognizable geography) and not make a generic estimate; expect JSON `{"location": ..., "lat": ..., "lng": ..., "region": "IATA"}`. In both paths: if Claude returns invalid JSON, store raw text as location name with null lat/lng/region_code and log a warning.
- [ ] T029 [US3] Create backend/app/ingestion/instagram.py: authenticate via persisted instagrapi session file (INSTAGRAPI_SESSION_FILE); query DB for the most recent instagram_post.timestamp; fetch only posts newer than that timestamp from account feed; process oldest-first; skip any post already present by instagram_id (idempotency check, FR-022)
- [ ] T030 [US3] Add location resolution calls to backend/app/ingestion/instagram.py: for each new post call location.py (T028) to get location string, lat, lng, and region_code; log a warning and set region_code=null if determination fails; never abort remaining posts due to location failure (FR-019, FR-020)
- [ ] T031 [US3] Add trip assignment logic to backend/app/ingestion/instagram.py per FR-040: (1) query trips where start_date ≤ post.timestamp ≤ end_date; (2) if multiple matches, pick trip with most recent created_at; (3) if no match, assign to trip id="miscellaneous-adventures"; (4) if that trip is absent, log ERROR and halt ingestion without writing any records
- [ ] T032 [US3] Add media download to backend/app/ingestion/instagram.py: download IMAGE to public/media/<stop_id>.jpg or VIDEO to public/media/<stop_id>.mp4; store relative path in instagram_post.media_url; on download failure log a WARNING, store empty string in media_url, and continue processing remaining posts (FR-021)
- [ ] T033 [US3] Add Instagram Graph API fallback to backend/app/ingestion/instagram.py: when instagrapi raises a non-session exception and INSTAGRAM_GRAPH_API_TOKEN is set, re-attempt fetch via Graph API and log a WARNING; if fallback also fails, log ERROR and exit without modifying existing records (FR-043)
- [ ] T034 [US3] Add session error handling to backend/app/ingestion/instagram.py: catch instagrapi session/authentication exceptions; send SMTP email to automation@datacommlab.com with subject `[travelogue] Instagram session error` and body containing error message + timestamp (skip email if SMTP_HOST not configured); then attempt Graph API fallback if INSTAGRAM_GRAPH_API_TOKEN is set; exit cleanly if both fail (FR-044)
- [ ] T035 [US3] Create backend/app/cli/manage.py with `python -m app.cli.manage login` command: prompt interactively for INSTA_USERNAME and INSTA_PASSWORD, authenticate via instagrapi, persist session to INSTAGRAPI_SESSION_FILE (FR-041)
- [ ] T036 [US3] Create backend/app/ingestion/scheduler.py with APScheduler BackgroundScheduler; register Instagram ingestion job at interval from INSTAGRAM_POLL_INTERVAL_MINUTES (default 60); wire scheduler.start() and scheduler.shutdown() into the FastAPI lifespan hook in backend/app/main.py

**Checkpoint**: US3 complete — new Instagram posts are automatically ingested every hour; verify with quickstart.md sections 4–5.

---

## Phase 6: User Story 4 — Trip Management & Region End Date (Priority: P2)

**Goal**: Allow authorized operators to create/update trips and record region end dates via the API.

**Independent Test**: Use curl with `Authorization: Bearer <API_SECRET_KEY>` to POST /trips (201 response), PUT /trips/:id (200 response with updated fields), and POST /regions/end-date (200 response). Verify 401 for all three without a token. Verify 409 on duplicate trip id. Verify 422 on bad date format.

- [ ] T037 [P] [US4] Define POST /regions/end-date contract in specs/002-data-ingestion/contracts/api.md: request body (optional trip string, optional region string, optional date ISO 8601), response shape, storage strategy (e.g. new region_end_dates table or existing schema extension), and any new migration required — this task MUST be completed before T040
- [ ] T038 [P] [US4] Add POST /trips handler to backend/app/api/trips.py: validate body via TripCreate schema; insert trip; return 201 TripResponse; return 401 on missing/invalid bearer token; return 409 if trip id already exists; return 422 on invalid date format (FR-013, FR-029)
- [ ] T039 [P] [US4] Add PUT /trips/:id handler to backend/app/api/trips.py: validate body via TripUpdate (all fields optional); apply partial update; update updated_at; return 200 TripResponse; return 401/404/422 as appropriate
- [ ] T040 [US4] Create backend/app/api/regions.py with POST /regions/end-date handler per contract defined in T037: resolve defaults (most recent trip by created_at if trip omitted; most recent region_code seen in that trip's stops if region omitted; current date if date omitted); require bearer auth (FR-045) — depends on T037
- [ ] T041 [US4] Register POST /trips, PUT /trips/:id write handlers and POST /regions/end-date router in backend/app/main.py; add shared bearer token auth dependency enforcing FR-029 across all write endpoints

**Checkpoint**: US4 complete — operators can manage trips and record region transitions without code changes.

---

## Phase 7: User Story 5 — Substack Ingestion (Priority: P3)

**Goal**: Automatically ingest new Substack articles from RSS feed; store with null stop_id pending manual assignment.

**Independent Test**: Configure SUBSTACK_RSS_URL; trigger `python -m app.ingestion.substack`; verify new substack_post records appear (stop_id=null). Re-run → zero new records. Set SUBSTACK_RSS_URL to an unreachable URL → verify clean exit and logged error.

- [ ] T042 [US5] Create backend/app/ingestion/substack.py: fetch RSS via feedparser from SUBSTACK_RSS_URL; for each entry not already in DB (matched by substack_id = guid or link), create substack_post with title, subtitle (from description), body (from content:encoded), published_at (from pubDate), and stop_id=null; use INSERT ON CONFLICT DO NOTHING for idempotency (FR-025); log error and exit cleanly if feed is unreachable (FR-026)
- [ ] T043 [US5] Register Substack ingestion job in backend/app/ingestion/scheduler.py at interval from SUBSTACK_POLL_INTERVAL_MINUTES (default 60); ensure it starts alongside the Instagram job in the FastAPI lifespan

**Checkpoint**: US5 complete — Substack articles are ingested automatically; verify with quickstart.md section 5.

---

## Phase 8: User Story 6 — Containerization (Priority: P3)

**Goal**: Full stack (backend + frontend + database) starts with `docker compose up` on a clean machine; database is pre-populated from seed-dump.sql.

**Independent Test**: On a machine with Docker and no local Python/Node setup, run `docker compose up`; navigate to frontend URL; confirm travelogue loads data from backend. Stop and restart → data still present.

- [ ] T044 [P] [US6] Create backend/Dockerfile: Python 3.12 slim base; COPY requirements.txt and RUN pip install; COPY app/; EXPOSE 8000; CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
- [ ] T045 [P] [US6] Create Dockerfile.frontend: multi-stage — stage 1 Node 18 alpine, COPY package*.json, RUN npm ci, COPY frontend/src/ (updated path after T002 migration), RUN npm run build; stage 2 nginx:alpine, COPY --from=stage1 /app/dist /usr/share/nginx/html
- [ ] T046 [US6] Create docker-compose.yml: db service (postgres:16, named volume for data persistence, mounts scripts/seed-dump.sql into /docker-entrypoint-initdb.d/seed-dump.sql, health check via pg_isready); backend service (build backend/, depends_on db with health condition, env_file .env, health check via GET /health); frontend service (build Dockerfile.frontend, depends_on backend); all services on shared network (FR-036, FR-038, FR-039)
- [ ] T047 [US6] Verify backend can connect to db service using Docker Compose service name in DATABASE_URL (postgresql+asyncpg://user:pass@db:5432/earthsandwich); confirm Alembic migrations run on backend container start before accepting traffic

**Checkpoint**: US6 complete — validate with quickstart.md section 2 end-to-end (docker compose up → browser loads travelogue).

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Align supporting artifacts with updated spec, harden location prompts, and validate end-to-end flow.

- [ ] T048 [P] Remove AIRPORT_API_KEY from .env.example, backend/app/config.py optional vars, and quickstart.md section 1 env block; update plan.md ingestion/location.py comment from "Airlabs IATA lookup + Claude inference fallback" to "Claude-only IATA determination and location inference"; update quickstart.md to reflect that ANTHROPIC_API_KEY is required for all location logic (not just fallback)
- [ ] T049 [P] Refine Claude prompt engineering in backend/app/ingestion/location.py: add few-shot examples of specific vs. generic responses; require the model to cite visible evidence (text, landmarks) when inferring location; add a confidence field to the response schema; log a WARNING when confidence is low
- [ ] T050 [P] Add GET /health endpoint to backend/app/main.py returning `{"status": "ok"}` with 200; used by Docker Compose health check on the backend service (FR-039)
- [ ] T051 Validate end-to-end developer workflow per quickstart.md: `docker compose up` → seed pipeline → Instagram login → manual ingestion trigger → API queries → confirm all user stories work together; document any deviations in quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2; T019 should run after T002 (frontend move may shift TS data import paths)
- **US2 (Phase 4)**: Depends on Phase 2; no dependency on US1 (but seeded data needed for manual testing)
- **US3 (Phase 5)**: Depends on Phase 2; no dependency on US1/US2 for implementation (reads DB, does not depend on seed pipeline)
- **US4 (Phase 6)**: Depends on Phase 2; T040 depends on T037 (contract must be defined first)
- **US5 (Phase 7)**: Depends on Phase 2; T043 depends on T036 (scheduler must exist)
- **US6 (Phase 8)**: Depends on Phase 2; practically benefits from US1 (seed-dump.sql) existing; T045 Dockerfile.frontend COPY paths must reflect T002 frontend/ move
- **Polish (Phase 9)**: Depends on all user story phases

### User Story Dependencies

- **US1 + US2 (P1)**: Can start in parallel after Phase 2; US1 T019 should follow T002
- **US3 + US4 (P2)**: Can start in parallel after Phase 2; US4 T040 must follow US4 T037
- **US5 (P3)**: T043 must follow T036 from US3
- **US6 (P3)**: Independent of US1–US5 for the Dockerfiles; seed-dump.sql needed for DB init; T045 depends on T002 path changes

### Within Each User Story

- Models and schemas → services and ingestion logic → route handlers → scheduler registration
- T037 (contract definition) → T040 (implementation) within US4

### Parallel Opportunities

- T003, T004, T005 in Phase 1: all parallel (different files); T002 is sequential (filesystem move)
- T007, T010, T011, T012, T016, T017, T018 in Phase 2: all parallel (different files)
- T023, T024, T025 in US2: all parallel (different files)
- T037, T038, T039 in US4: all parallel (T040 waits on T037)
- T044, T045 in US6: parallel (different Dockerfiles)
- T048, T049, T050 in Polish: all parallel

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

### US4 Write Endpoints (T037 must complete first, then T038+T039 parallel):
```
Task T037: Define POST /regions/end-date contract in contracts/api.md  ← first
Then in parallel:
Task T038: Add POST /trips handler
Task T039: Add PUT /trips/:id handler
Task T040: Create backend/app/api/regions.py  ← after T037 only
```

---

## Implementation Strategy

### MVP First (US1 + US2 — both P1)

1. Complete Phase 1: Setup (including T002 frontend move)
2. Complete Phase 2: Foundational (**CRITICAL** — blocks everything)
3. Complete Phase 3: US1 (seed pipeline)
4. Complete Phase 4: US2 (read API)
5. **STOP and VALIDATE**: Seed data loads; API returns trips/stops/posts; quickstart sections 2–3 and 8 pass
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → skeleton ready
2. US1 → database seeded, SQL dump committed → **demo: data in DB**
3. US2 → read API live → **demo: frontend can query backend** (MVP!)
4. US3 → Instagram ingestion live → **demo: new posts appear automatically**
5. US4 → trip management + region end dates → **demo: operator can create trips via API**
6. US5 → Substack ingestion → **demo: articles ingested automatically**
7. US6 → containerized → **demo: `docker compose up` works from scratch**
8. Polish → artifacts aligned, prompts hardened

### Single Developer

Prioritize P1 stories first (US1 → US2), then P2 (US3 → US4), then P3 (US5 → US6). Complete each story fully before starting the next.

---

## Notes

- **[P]** = different files, no incomplete dependencies; safe to run in parallel
- **[Story]** label maps each task to a specific user story for traceability
- Each user story is independently completable and testable via its Independent Test
- **T002** (frontend/ move) is a Setup task that affects T019 (TS data import paths) and T045 (Dockerfile.frontend COPY paths) — complete T002 before those tasks
- **T037** (contract) is a blocking dependency for T040 — do not implement the region end-date handler before the contract is defined
- location.py (T028) must use Claude exclusively for IATA determination; no external airport API; prompt engineering (T049) is a polish task but should inform the initial implementation
- Commit after each task or logical group; stop at any checkpoint to validate the story independently
