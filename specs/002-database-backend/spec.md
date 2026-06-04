# Feature Specification: Database Backend & REST API

**Feature Branch**: `002-database-backend`
**Created**: 2026-05-08
**Overhauled**: 2026-06-01 (rewritten from scratch to reflect shipped work, retired assumptions, and new requirements)
**Addendum**: 2026-06-01 — added `regions` reference table (FR-040), `GET /regions` read endpoint (FR-041), and updated `stops.region_code` to be a foreign key into `regions`.
**Status**: Active — Phases 1–4 complete; Phases 5–9 in progress or pending
**Input**: Persistence layer, REST API, automated test suite, AI-assisted trip planning (MCP), and containerization for the Earth Sandwich travelogue. Split from `002-data-ingestion` on 2026-05-22; overhauled 2026-06-01 to remove `sequence_order`, correct env var scope, add TDD mandate, and add the MCP/trip-intelligence feature.

> **Out of scope**: Instagram/Substack ingestion logic → spec 003 (pile-app). Frontend rendering, components, API client hooks → spec 001 (useful-app). Data normalization, stop linkage, IATA derivation, trip auto-assignment → planned bridge-app spec. Object storage, email notifications, scheduled jobs inside the backend process.

> **Dependency note**: Phase 11 / US7 (frontend API integration) shipped on this branch but is recorded as complete in spec 001 (useful-app). This spec does not claim ownership of frontend code changes.

> **Security note**: `backend/session.json` was accidentally committed on this branch (commit `ce55532`). The file may contain real instagrapi auth state (a pile-app credential from spec 003). It MUST be added to `.gitignore` before this branch is pushed to any public remote. See FR-032.

## Prior Clarifications (Preserved from 2026-05-08 — Incorporated into this Overhaul)

> These answers are now baked into the requirements below. Preserved for audit trail only.

- Seed pipeline: TypeScript export → JSON → Python import → `pg_dump` to `scripts/seed-dump.sql`.
- `caption` is a nullable column on `stops` for planned stops only.
- Logging: structured JSON to stdout.
- `region_code` = 3-letter IATA code; `nearest_airport_iata` is retired (merged into `region_code`).
- Docker DB container: mount `scripts/seed-dump.sql` into `/docker-entrypoint-initdb.d/` for first-start auto-seeding.
- PostgreSQL everywhere; SQLite dropped entirely.
- `sequence_order` is permanently removed from the `stops` table (shipped in the initial migration). Stop ordering is derived from `(trip_id, date, region_code)`. Do not re-introduce.

> Clarifications about ingestion (trip assignment, instagrapi login, fallback ordering) live in `003-ingestion-pipeline/spec.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Seed the database from existing travelogue data (Priority: P1) ✅ COMPLETE

All trip, stop, and post data previously hard-coded in TypeScript source files is migrated into a relational database. A two-step seed process exports the TypeScript data to JSON and then imports it into the database. After seeding, the database contains the same records — in the same stop ordering — as the original source files, ready to be served by the API. The seed process also produces a portable SQL dump that can initialize any future deployment without re-running the export.

**Why this priority**: The database must be populated before any other story can be exercised.

**Independent Test**: Run the TypeScript export script, then run the Python seed script against a fresh database. Inspect the database via a SQL client and verify all trips, stops, and posts are present with correct field values and ordering. Confirm `scripts/seed-dump.sql` exists and is non-empty.

**Acceptance Scenarios**:

1. **Given** the TypeScript data files exist, **When** the export script runs, **Then** valid JSON files are produced containing all trips, stops, and posts with no data loss.
2. **Given** the JSON export files exist, **When** the Python seed script runs against a fresh database, **Then** all trips, stops, and posts are present with field values matching the source data.
3. **Given** the seed script has already been run once, **When** it is run again, **Then** no duplicate records are created.
4. **Given** a stop has no optional content (no image or no article body), **When** the seed runs, **Then** the stop record is created with those optional fields null.
5. **Given** the seed script completes successfully, **When** it finishes, **Then** `scripts/seed-dump.sql` is written capturing the full seeded database state.

---

### User Story 2 — Query travelogue content via the REST API (Priority: P1) ✅ COMPLETE

Trips, stops, and posts stored in the database are accessible to any HTTP client through a REST API. Filters allow narrowing results by status, trip, region, and date range. This is the interface contract that decouples the frontend (and any future clients) from hard-coded TypeScript modules.

**Why this priority**: Without working read endpoints, no consumer can read from the database. Every subsequent story depends on these endpoints.

**Independent Test**: Start the backend in isolation. Use an HTTP client to call each read endpoint and confirm correctly structured data is returned, filters work as described, and error responses are structured.

**Acceptance Scenarios**:

1. **Given** the backend is running and the database is seeded, **When** `GET /trips` is called, **Then** all trips are returned in reverse-chronological order with id, title, description, and date range.
2. **Given** the backend is running, **When** `GET /trips/:id` is called with a valid trip id, **Then** the full trip is returned including all stops and each stop's associated post.
3. **Given** the backend is running, **When** `GET /stops` is called with a `status=visited` filter, **Then** only visited stops are returned.
4. **Given** the backend is running, **When** an invalid trip id is passed to `GET /trips/:id`, **Then** the API returns 404 with a structured error body.
5. **Given** the backend is running, **When** `GET /health` is called, **Then** the response is `{"status": "ok"}` with HTTP 200.
6. **Given** the backend is running, **When** `GET /regions` is called, **Then** all region records are returned with IATA code, name, airport name, country, and coordinates.

---

### User Story 3 — Verify backend correctness through an automated test suite (Priority: P1)

Every backend endpoint and significant behavior is covered by automated tests. New functionality is built test-first: a test is written that specifies the expected behavior, and then the implementation is written to make that test pass. This ensures correctness is maintained as the backend evolves and provides a safety net for future changes.

**Why this priority**: A test suite is the primary assurance mechanism for a backend that serves a live travelogue. Without it, regressions in read or write endpoints go undetected until a user notices broken data. TDD also clarifies requirements before code is written, reducing rework.

**Independent Test**: Run the test suite in isolation (no running database, no external services required). All tests must pass. Observe that tests for each read endpoint exist, each write endpoint has tests for both authorized and unauthorized paths, and there are tests for invalid input scenarios.

**Acceptance Scenarios**:

1. **Given** the test suite, **When** it is run against the codebase, **Then** all tests pass without requiring a live database or external services.
2. **Given** a new endpoint or behavior, **When** a developer begins implementation, **Then** a failing test defining the expected behavior exists before the first line of production code is written.
3. **Given** all read endpoints, **When** the test suite runs, **Then** each endpoint has at least one test covering the happy path and one test covering an error scenario.
4. **Given** all write endpoints, **When** the test suite runs, **Then** each endpoint has tests for the authorized success path, the unauthorized path (401), and the invalid-input path (422).
5. **Given** the test suite, **When** an endpoint implementation is deleted or broken, **Then** at least one test fails, catching the regression automatically.

---

### User Story 4 — Manage trips via the write API (Priority: P2)

An authorized operator can create a new trip or update an existing trip's name, description, and date range via an API endpoint — without code deployment or database migration. The operator can also record when a specific geographic region within a trip ended, enabling the frontend to group stops by region with accurate date boundaries. All write operations require a valid authorization token; unauthenticated requests are rejected.

**Why this priority**: Trips must be created before stops can be attached. Without a write API, every new trip requires a code change and redeployment. Region end-date recording enables accurate sidebar navigation in the frontend.

**Independent Test**: Use an HTTP client with a valid bearer token to call `POST /trips`, `PUT /trips/:id`, and `POST /regions/end-date`. Verify creates and updates take effect in the database. Call the same endpoints without a token and confirm 401 responses.

**Acceptance Scenarios**:

1. **Given** a valid authorization token, **When** `POST /trips` is called with name, description, and date range, **Then** a new trip record is created and its id is returned with HTTP 201.
2. **Given** a valid token and an existing trip id, **When** `PUT /trips/:id` is called with a subset of fields, **Then** only those fields are updated; unchanged fields are preserved.
3. **Given** no authorization token, **When** any write endpoint is called, **Then** the API returns 401.
4. **Given** a valid token, **When** `POST /regions/end-date` is called with no parameters, **Then** the end date for the most recently active region in the most recently created trip is set to today's date.
5. **Given** a valid token, **When** `POST /regions/end-date` is called with explicit `trip`, `region`, and `date` parameters, **Then** the specified region's end date in the specified trip is recorded.
6. **Given** a valid token, **When** `POST /trips` is called with an invalid date format, **Then** the API returns 422 with a structured error describing the validation failure.

> **Design task**: The storage model and migration for `POST /regions/end-date` must be defined in `specs/002-database-backend/contracts/api.md` before implementation begins. The endpoint contract is sketched in the existing contract file; the persistence strategy and any required schema changes are pending.

---

### User Story 5 — Plan trips with AI assistance (Priority: P2)

A trip planner interacting with an AI assistant can ask it to review a planned itinerary and check whether any stops are near significant local events — festivals, public holidays, or major cultural occasions — that fall close to but outside the planned dates. The assistant can then suggest specific date-shift options to capture those events, or flag conflicts the planner may wish to avoid. The AI assistant accesses live trip and stop data through a structured interface the system exposes for this purpose.

**Why this priority**: The travelogue is used to plan real trips. Event-proximity awareness can significantly improve itinerary quality and is not feasible to do manually at scale across many stops and destinations.

**Independent Test**: Connect an AI assistant to the system's trip-intelligence interface. Ask it to review a planned trip and report whether any stops are within a configurable window of a notable local event. Confirm the assistant can retrieve real stop data (dates, locations, regions) and return an actionable suggestion based on it.

**Acceptance Scenarios**:

1. **Given** the trip intelligence interface is running, **When** an AI assistant queries it for a trip's planned stops, **Then** the assistant receives the stop dates, locations, and region codes for that trip.
2. **Given** a planned stop with a date close to a known local festival or public holiday, **When** the AI assistant is asked to check event proximity for that stop, **Then** the assistant identifies the event and reports the date offset relative to the stop date.
3. **Given** an event is identified within a configurable number of days of a stop, **When** the assistant formulates a suggestion, **Then** it recommends a specific date shift (or a range) that would include the event in the itinerary.
4. **Given** no events are found near any planned stop, **When** the assistant checks, **Then** it reports no adjustments are needed and the itinerary is clear.
5. **Given** the trip intelligence interface, **When** a developer reviews its contract, **Then** a documented interface definition exists in `specs/002-database-backend/contracts/` before implementation begins.

> **Research task**: Before implementation, a research phase is required to evaluate available event data sources (public holiday APIs, festival calendars) and define the MCP contract (tools, inputs, outputs, auth model). Results to be documented in `specs/002-database-backend/research.md` and the interface contract in `specs/002-database-backend/contracts/`.

---

### User Story 6 — Run the full stack with a single command (Priority: P3)

A developer clones the repository, copies `.env.example` to `.env`, fills in the required values, and runs a single command. The backend, database, and frontend all start together; the database is automatically pre-populated with seed data on first start; data persists across restarts. No manual dependency installation or database bootstrapping is required beyond filling in the environment file.

**Why this priority**: Containerization reduces the setup barrier for new developers and production deployments and eliminates environment drift.

**Independent Test**: On a clean machine with only Docker installed, run the startup command from the project root. Navigate to the frontend URL and confirm the travelogue loads data from the backend. Stop and restart the containers and confirm previously present data is still there.

**Acceptance Scenarios**:

1. **Given** Docker is installed, **When** `docker compose up` is run from the project root, **Then** the frontend, backend, and database are all reachable on their configured ports.
2. **Given** the containers are running for the first time (empty volume), **When** the database container starts, **Then** `scripts/seed-dump.sql` is automatically applied and all seed data is present without any manual import step.
3. **Given** the containers are running, **When** the frontend is opened in a browser, **Then** it retrieves and renders trip data from the backend.
4. **Given** the containers are stopped and restarted, **When** the database container starts again, **Then** previously present data is still there (persisted via a named volume).
5. **Given** the backend container is starting, **When** the database is not yet ready, **Then** the backend waits (via health check) rather than crashing.

---

### Edge Cases

- What happens when a write endpoint receives invalid date formats? (API returns 422 with a structured error body describing the validation failure; no partial write occurs.)
- What happens when the database is unavailable when a request fires? (All endpoints return 503 with a structured error body. The pile-app (spec 003) does not write to this database — its output is the pile, consumed by the future bridge-app — so its behavior is unaffected.)
- What happens when the frontend container starts but the backend URL is not configured? (The frontend displays a graceful error; it does not crash the container.)
- What happens when a `POST /trips` request is made and a trip with the same id already exists? (The API returns 409 Conflict with a structured error body.)
- What happens when `POST /regions/end-date` is called with `region` but no matching region exists in the resolved trip? (The API returns 404 with a structured error identifying the missing region.)
- What happens when the AI trip-planning interface is queried for a trip with no planned stops? (The interface returns an empty stop list and the assistant reports nothing to evaluate.)
- What happens when an external event data source is unavailable during an AI trip-planning query? (The interface returns a structured error to the AI assistant; the assistant informs the user that event data is temporarily unavailable.)

## Requirements *(mandatory)*

### Functional Requirements

#### Database Schema

- **FR-001**: The system MUST use PostgreSQL as the relational database engine in all environments. The schema MUST include five tables: `trips`, `stops`, `instagram_posts`, `substack_posts`, and `regions`.
- **FR-002**: The `trips` table MUST store: `id` (stable string slug), `title`, `description`, `start_date`, `end_date`, `created_at`, `updated_at`.
- **FR-003**: The `stops` table MUST store: `id`, `trip_id` (foreign key → `trips`), `date`, `location` (human-readable string), `lat` (decimal), `lng` (decimal), `status` (`visited` | `planned`), `region_code` (foreign key → `regions.iata_code`; identifies the nearest international airport within the same country as the stop; the IATA code is computed by spec 003 pile-app and the FK value is written by the planned bridge-app — see [`docs/roadmap.md`](../../docs/roadmap.md)), `post_type` (`instagram` | `substack` | `planned`), `caption` (nullable text, for planned stops only), `created_at`. **There is no `sequence_order` column**; stop ordering is derived from `(trip_id, date, region_code)`.
- **FR-004**: The `instagram_posts` table MUST store: `id`, `stop_id` (foreign key → `stops`), `instagram_id` (platform identifier), `shortcode`, `media_url` (relative path to downloaded file), `caption`, `timestamp` (ISO 8601 UTC), `created_at`.
- **FR-005**: The `substack_posts` table MUST store: `id`, `stop_id` (foreign key → `stops`), `substack_id` (platform identifier), `title`, `subtitle`, `body` (long-form text), `published_at` (ISO 8601 UTC), `created_at`.
- **FR-040**: The `regions` table MUST store: `iata_code` (3-letter IATA airport code, primary key), `name` (human-readable city or region name), `airport_name` (full official airport name), `country` (country name), `lat` (decimal latitude), `lng` (decimal longitude). This is a reference/lookup table; the `iata_code` values in this table are the only valid values for `stops.region_code`.

#### Seed Pipeline

- **FR-006**: The system MUST include a two-step seed process: (1) a TypeScript export script imports the authoritative TypeScript data modules (including trip/stop/post data and `frontend/src/data/regions.ts`) and writes JSON files; (2) a Python seed script reads those JSON files and inserts records into a fresh PostgreSQL database. After successful seeding the seed script MUST produce a PostgreSQL-compatible SQL dump at `scripts/seed-dump.sql`, generated from the live database state. This dump is used by the Docker environment (FR-035) to pre-populate new deployments.

#### REST Read API

- **FR-007**: The backend MUST expose a REST API. All responses MUST use JSON. All endpoints MUST return structured error responses (`{"error": "...", "detail": "..."}`) with standard HTTP status codes (400, 401, 404, 409, 422, 429, 503).
- **FR-008**: `GET /trips` MUST return all trips in reverse-chronological order by `start_date`. Optional query filter: `status` (`active` | `completed` | `upcoming`).
- **FR-009**: `GET /trips/:id` MUST return the full trip including all stops and each stop's associated post data (instagram, substack, or planned caption). An invalid trip id MUST return 404.
- **FR-010**: `GET /stops` MUST support query filters: `trip_id`, `status` (`visited` | `planned`), `region_code`, `post_type`, `after` (date), `before` (date).
- **FR-011**: `GET /instagram-posts` MUST support query filters: `stop_id`, `after` (timestamp), `before` (timestamp).
- **FR-012**: `GET /substack-posts` MUST support query filters: `stop_id`, `after` (published_at), `before` (published_at).
- **FR-013**: `GET /health` MUST return `{"status": "ok"}` with HTTP 200. This endpoint is used by Docker Compose health checks and MUST NOT require authentication.
- **FR-041**: `GET /regions` MUST return all region records. Optional query filter: `country` (filter by country name). Each record MUST include `iata_code`, `name`, `airport_name`, `country`, `lat`, and `lng`.

#### Automated Testing & Development Process

- **FR-014**: The backend MUST have an automated unit test suite covering all read endpoints, all write endpoints, and all error response scenarios. Tests MUST be runnable without a live database or external services.
- **FR-015**: All new backend endpoints and significant behaviors MUST be developed using Test-Driven Development: a failing test defining the expected behavior MUST exist before the production code that satisfies it is written.
- **FR-016**: The test suite MUST include at minimum: one happy-path test and one error-path test per read endpoint; one authorized success test, one 401 test, and one 422 test per write endpoint.

#### Write API — Trip Management

- **FR-017**: `POST /trips` MUST create a new trip from `title`, `description`, `start_date`, and `end_date`. On success it MUST return HTTP 201 and the new trip's id. This endpoint MUST require authorization (see FR-026).
- **FR-018**: `PUT /trips/:id` MUST support partial updates to a trip's `title`, `description`, `start_date`, and `end_date`. Omitted fields MUST remain unchanged. On success it MUST return HTTP 200 and the updated trip. This endpoint MUST require authorization (see FR-026).
- **FR-019**: `POST /regions/end-date` MUST record the end date of a geographic region within a trip. All parameters are optional: `trip` (trip id; defaults to most recently created trip), `region` (IATA region code; defaults to the most recently active region in the resolved trip), `date` (ISO 8601 date; defaults to today). This endpoint MUST require authorization (see FR-026). The storage model and any required schema migration MUST be defined in `specs/002-database-backend/contracts/api.md` before implementation begins.

#### AI-Assisted Trip Planning

- **FR-020**: The system MUST expose a structured machine-readable interface (using the Model Context Protocol) that allows an AI assistant to query planned trip data: stop dates, locations, region codes, trip date ranges, and region metadata (name, country, and coordinates) sourced from the `regions` table.
- **FR-021**: The trip intelligence interface MUST provide a tool that accepts a trip id and a proximity window (number of days) and returns a list of significant local events (festivals, public holidays, major cultural occasions) falling within that window of any planned stop's date.
- **FR-022**: When events are identified, the interface MUST return structured suggestions: each suggestion MUST include the affected stop, the event name and date, and a recommended date-shift range that would place the stop within the event window.
- **FR-023**: The interface contract (available tools, inputs, outputs, authentication model, external data sources used) MUST be documented in `specs/002-database-backend/contracts/` before implementation begins. A research phase evaluating available event data sources MUST be completed and documented in `specs/002-database-backend/research.md` before the contract is finalized.

#### Security

- **FR-024**: All credentials and secrets (`API_SECRET_KEY`, database credentials, any external API keys for event data sources) MUST be read from environment variables at startup and MUST NOT be hard-coded anywhere in the source. Required backend env vars: `DATABASE_URL`, `API_SECRET_KEY`, `FRONTEND_ORIGIN`. Optional: `LOG_LEVEL`, `ENVIRONMENT`. No ingestion credentials (`INSTA_USERNAME`, `INSTA_PASSWORD`, `SUBSTACK_RSS_URL`) belong in this spec — those are spec 003 concerns.
- **FR-025**: All request parameters and body fields MUST be validated before use. Invalid input MUST return a 422 response with a structured error body. No raw user input MUST reach the database layer.
- **FR-026**: All write endpoints (`POST /trips`, `PUT /trips/:id`, `POST /regions/end-date`) MUST require a valid bearer token. Unauthenticated requests MUST receive 401. The token value is the configured `API_SECRET_KEY`.
- **FR-027**: All public API endpoints MUST enforce rate limiting: a maximum of 60 requests per minute per IP address. Exceeding this limit MUST return 429 with a `Retry-After` header.
- **FR-028**: The backend MUST enforce CORS, permitting requests only from the configured `FRONTEND_ORIGIN`. Requests from other origins MUST be rejected.
- **FR-029**: The backend MUST enforce HTTPS in production. HTTP on a loopback port is acceptable in local Docker development.
- **FR-030**: API error responses MUST NOT include stack traces, internal identifiers, or implementation details beyond what is necessary for the client.
- **FR-032**: `backend/session.json` MUST be added to `.gitignore`. The file was accidentally committed on this branch and may contain pile-app authentication credentials. It MUST be removed from the git index before any public push.

#### Containerization

- **FR-033**: A `Dockerfile` MUST exist for the Python backend service.
- **FR-034**: A `Dockerfile` MUST exist for the frontend service.
- **FR-035**: A `docker-compose.yml` MUST exist at the project root that starts the backend, database, and frontend together with `docker compose up`. The database service MUST mount `scripts/seed-dump.sql` into its initialization directory so the database is pre-populated automatically on first start (when the named volume is empty). Subsequent starts MUST skip the init script because the volume already contains data.
- **FR-036**: All runtime configuration MUST be injectable via environment variables defined in a `.env` file. A `.env.example` MUST be committed showing all required keys with placeholder values.
- **FR-037**: The database container MUST use a named Docker volume so data persists across restarts.
- **FR-038**: The `docker-compose.yml` MUST define health checks for the backend and database services so dependent containers do not start until their dependencies are ready.

#### Observability

- **FR-039**: The backend MUST emit all log output as structured JSON to stdout. No plain-text log lines or log files inside the container. Each log entry MUST include at minimum: `timestamp` (ISO 8601), `level`, `message`, and `logger` (module name). In local development environments a human-readable console format is acceptable.

### Key Entities *(include if feature involves data)*

- **Trip**: A named journey with a stable slug id, title, description, start date, and end date. Contains an ordered sequence of stops; ordering is by `(trip_id, date, region_code)` — there is no `sequence_order` column.
- **Stop**: A single itinerary entry linked to exactly one trip. Stores date, human-readable location, decimal coordinates, status (`visited` | `planned`), `region_code` (foreign key → `regions.iata_code`; produced by the pile-app and written by the bridge-app), post type, and an optional planned-stop caption. No `sequence_order` field — ordering is derived from the date and region_code.
- **Instagram Post**: Rich content record linked to one stop. Stores the Instagram platform id, shortcode, relative media path, caption, and original timestamp. Populated by the planned bridge-app.
- **Substack Post**: Long-form article record linked to one stop. Stores the Substack post id, title, subtitle, body, and publication date. Populated by the planned bridge-app.
- **Planned Post**: Represented by the stop record's `post_type = "planned"` and an optional `caption` on the stop; no separate table.
- **Region**: A reference record for a geographic area identified by its IATA airport code. Stores the 3-letter IATA code (primary key), a human-readable city or region name, the full official airport name, the country, and decimal latitude/longitude coordinates. Used to normalize region data across stops and to provide location context to the AI trip-planning interface. Authoritative source: `frontend/src/data/regions.ts`.
- **Trip Intelligence Interface**: The machine-readable protocol surface that exposes trip and stop data to AI assistants. Provides tools for querying planned stops, checking event proximity, and receiving date-shift suggestions. Contract and data sources to be defined before implementation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After seeding, every trip, stop, and post record in the database matches the source TypeScript data files exactly — same count, same field values, same ordering — with no missing or duplicate records.
- **SC-002**: All read endpoints respond in under 500 milliseconds for typical queries (single trip with all stops and posts) under normal server load.
- **SC-003**: The full stack starts correctly with `docker compose up` on a clean machine with no additional setup steps beyond filling in `.env`.
- **SC-004**: Every write request submitted without a valid bearer token receives a 401 response; zero unauthorized writes reach the database.
- **SC-005**: A developer with Docker can clone the repository, fill in `.env`, and have a working travelogue in their browser within 5 minutes.
- **SC-006**: Every backend log line is valid JSON emitted to stdout; no plain-text log output and no log files exist inside any container.
- **SC-007**: 100% of read endpoints and all write endpoints have automated unit tests covering at minimum the happy path and at least one error scenario each.
- **SC-008**: No new endpoint or significant behavior is merged without a corresponding test written before the implementation. Code review confirms test-first commit ordering.
- **SC-009**: The AI trip-planning interface contract is documented and reviewed before the first line of implementation code is written.
- **SC-010**: Given a planned stop within a configurable day window of a known local festival or public holiday, an AI assistant connected to the trip intelligence interface correctly identifies the event and returns a date-shift suggestion.

## Assumptions

- PostgreSQL is the database engine in all environments. SQLite is not used; all developers run PostgreSQL locally via Docker.
- The existing TypeScript data files (`miscellaneous-adventures.ts`, `earth-sandwich-2015.ts`, `earth-club-sandwich-2027.ts`) are the authoritative source for the initial trip/stop/post seed. No manual data entry is required.
- `frontend/src/data/regions.ts` is the authoritative source for the `regions` reference table. This file is already complete for all regions in the current travelogue and MUST be exported and imported as part of the seed pipeline.
- **`sequence_order` is permanently removed** from the `stops` table. It was dropped in the initial migration (Phase 2) and MUST NOT be re-introduced. Stop ordering is by `(trip_id, date, region_code)`.
- Substack posts ingested without a `stop_id` are stored in the database and excluded from API responses until manually assigned to a stop; this is acceptable for v1.
- Frontend rendering, components, hooks, and API adapters are out of scope for this spec; that work belongs in spec 001 (useful-app). Phase 11 / US7 (frontend API integration) shipped on this branch and is recorded as complete in spec 001.
- All media files are stored on the server filesystem. Object storage (S3) is out of scope for v1.
- Security scanning and formal penetration testing are out of scope. Standard OWASP Top 10 mitigations (input validation, rate limiting, no secret leakage, HTTPS in production) are the baseline.
- `backend/session.json` is a pile-app artifact that does not belong in this repo. It must be gitignored and removed from the git index before any public push (see FR-032).
- The MCP research and contract phases are prerequisites for the AI trip-planning implementation. Implementation MUST NOT begin until the research is documented and the contract is reviewed.
- No ingestion credentials (`INSTA_USERNAME`, `INSTA_PASSWORD`, `SUBSTACK_RSS_URL`, Anthropic API key) belong in this spec or in the backend service. Those are spec 003 (pile-app) concerns.
- The `POST /regions/end-date` persistence strategy is a design task that precedes implementation. Until it is decided, the endpoint MUST NOT be implemented (see FR-019).
- The bridge-app (planned, no spec yet) is the eventual writer of `region_code` and post foreign keys from the pile into this schema. This spec does not own bridge-app logic.

> Pile-app assumptions (instagrapi session management, LLM-based IATA derivation, Substack feed availability) live in `003-ingestion-pipeline/spec.md`. Bridge-app assumptions (cross-source trip auto-assignment, Substack→stop linkage, IATA column population) will land in the planned bridge-app spec.

