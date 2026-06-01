# Feature Specification: Database & Backend

**Feature Branch**: `002-database-backend`
**Created**: 2026-05-08
**Updated**: 2026-05-22 (split from `002-data-ingestion`)
**Status**: Draft
**Input**: Originally a single `002-data-ingestion` spec covering both database/API/container *and* automated ingestion. On 2026-05-22 the spec was split: this spec retains everything related to schema, seeding, REST API, trip management, security, and containerization. Automated Instagram and Substack ingestion lives in `003-ingestion-pipeline`.

## Clarifications

### Session 2026-05-08

- Q: What format should the Python seed script consume to read the existing hard-coded TypeScript data? → A: Build-time JSON export — a small TypeScript script (e.g. `tsx export-seed-data.ts`) imports the data files and writes JSON; the Python seed script reads those JSON files.
- Q: Where should the optional `caption` for planned stops be stored in the database schema? → A: Add a nullable `caption` column to the `stops` table (applies to planned stops only; ignored for instagram/substack stops, which store their text in their own tables).
- Q: What logging strategy should the backend use? → A: Structured JSON logs emitted to stdout (Docker-native; compatible with any external log aggregator).
- Q: Are `region_code` and `nearest_airport_iata` the same concept? → A: Yes — merge into one. The ingestion pipeline (Claude) writes the computed IATA code directly to `region_code`; `nearest_airport_iata` is removed from the schema. (Implementation of the Claude call lives in `003-ingestion-pipeline`; the column lives in this spec.)
- Q: FR-013 references `(see FR-021)` for authorization but FR-021 is the media download requirement; should it reference FR-029 instead? → A: Yes — fix the cross-reference to FR-029.
- Q: How should the Docker database container consume the seed dump on first start? → A: Mount `scripts/seed-dump.sql` into the DB container's init directory (e.g. `/docker-entrypoint-initdb.d/`) so it runs automatically on first start when the data volume is empty.
- Q: Which database engine should the seed dump target — PostgreSQL only, or also SQLite? → A: PostgreSQL everywhere; SQLite is dropped as an option entirely to simplify the toolchain.

> Three clarifications about ingestion (trip assignment, instagrapi login, FR-044 fallback ordering) moved to `003-ingestion-pipeline/spec.md` on 2026-05-22.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Seed the database from existing hard-coded data (Priority: P1)

All trip, stop, and post data currently hard-coded in TypeScript source files is migrated into a relational database. A two-step seed process exports the TypeScript data to JSON and then imports it into the database. After seeding the database contains the same records — in the same order — as the original source files, ready to be served by the API.

**Why this priority**: The database must be populated before any other story can be exercised. Ingestion, API reads, and trip management all depend on an existing, correctly structured dataset.

**Independent Test**: Run the export script to produce JSON, then run the Python seed script against a fresh database. Inspect the database directly (e.g. via a SQL client) and verify all trips, stops, and posts are present with correct field values and ordering. No running backend or frontend is required.

**Acceptance Scenarios**:

1. **Given** the TypeScript data files exist, **When** the export script runs, **Then** valid JSON files are produced containing all trips, stops, and posts with no data loss.
2. **Given** the JSON export files exist, **When** the Python seed script runs against a fresh database, **Then** all trips, stops, and posts are present in the database with field values matching the source TypeScript data.
3. **Given** the seed script has already been run once, **When** it is run again, **Then** no duplicate records are created.
4. **Given** a stop in the source data has no optional content (no image or no article body), **When** the seed runs, **Then** the stop record is created with those optional fields null rather than missing or erroring.
5. **Given** the seed script completes successfully, **When** it finishes, **Then** a SQL dump file is written to `scripts/seed-dump.sql` capturing the full seeded database state, so that new environments (US6) can be initialized from the dump without re-running the export and seed steps.

---

### User Story 2 - Query travelogue content via the backend API (Priority: P1)

Trips, stops, and posts stored in the database are accessible to any HTTP client through a REST API. Basic filters allow narrowing results by status, trip, region, and date range. This is the interface contract that allows the frontend (in a follow-on change) and any future clients to decouple from hard-coded TypeScript modules.

**Why this priority**: Without working read endpoints no consumer — frontend or otherwise — can read from the database. Every subsequent story that surfaces data to users depends on these endpoints.

**Independent Test**: Start the backend in isolation (no frontend). Use an HTTP client (e.g. curl) to call each read endpoint and confirm it returns correctly structured data with expected fields, and that filter parameters narrow results as described.

**Acceptance Scenarios**:

1. **Given** the backend is running and the database has been seeded (US1), **When** `GET /trips` is called, **Then** all trips are returned in reverse-chronological order, each with id, title, description, and date range.
2. **Given** the backend is running, **When** `GET /trips/:id` is called with a valid trip id, **Then** the full trip is returned including all its stops and each stop's associated post.
3. **Given** the backend is running, **When** `GET /stops` is called with a `status=visited` filter, **Then** only stops with that status are returned.
4. **Given** the backend is running, **When** an invalid trip id is passed to `GET /trips/:id`, **Then** the API returns a 404 with a structured error body.

---

> **US3 (Automated Instagram ingestion) and US5 (Automated Substack ingestion) moved to `003-ingestion-pipeline/spec.md` on 2026-05-22.**

---

### User Story 4 - Manage trips via the API (Priority: P2)

An authorized operator can create a new trip or update an existing trip's name, description, and date range via an API endpoint, without any code deployment or database migration. This enables planning future trips and correcting trip metadata after the fact.

**Why this priority**: Trips need to be created before stops can be attached to them. Without a management endpoint, every new trip requires a code change and redeployment.

**Independent Test**: Use an HTTP client with a valid authorization token to call `POST /trips` and `PUT /trips/:id`. Confirm the trip is created or updated as specified, and that calling without a token returns a 401.

**Acceptance Scenarios**:

1. **Given** a valid authorization token, **When** `POST /trips` is called with a name, description, and date range, **Then** a new trip record is created and its id is returned.
2. **Given** a valid authorization token and an existing trip id, **When** `PUT /trips/:id` is called with updated fields, **Then** those fields are updated and unchanged fields are preserved.
3. **Given** no authorization token, **When** `POST /trips` or `PUT /trips/:id` is called, **Then** the API returns 401 Unauthorized.
4. **Given** a valid authorization token, **When** the region end-date endpoint is called with no parameters, **Then** the end date for the most recently active region within the most recently created trip is set to the current date.
5. **Given** a valid authorization token, **When** the region end-date endpoint is called with explicit `trip`, `region`, and `date` parameters, **Then** the specified region's end date within the specified trip is recorded using the provided date.
6. **Given** no authorization token, **When** the region end-date endpoint is called, **Then** the API returns 401 Unauthorized.

---

### User Story 6 - Run the full stack with a single command (Priority: P3)

A developer clones the repository, copies `.env.example` to `.env`, fills in credentials, and runs `docker compose up`. The backend, database, and frontend all start together. No manual dependency installation or database setup is required beyond filling in the `.env`.

**Why this priority**: Containerization reduces the barrier for the project to be transferred to a new developer or deployed to a new host. It also eliminates environment drift between development and production.

**Independent Test**: On a clean machine with Docker installed, run `docker compose up` from the project root. Navigate to the frontend URL and confirm the travelogue loads data from the backend. Navigate to the backend base URL and confirm the API responds.

**Acceptance Scenarios**:

1. **Given** Docker and Docker Compose are installed, **When** `docker compose up` is run from the project root, **Then** the frontend, backend, and database are all reachable on their configured ports.
2. **Given** the containers are running for the first time (empty volume), **When** the database container starts, **Then** `scripts/seed-dump.sql` is automatically applied and all seed data is present without any manual import step.
3. **Given** the containers are running, **When** the frontend is opened in a browser, **Then** it retrieves trip data from the backend API and renders the travelogue correctly.
4. **Given** the containers are stopped and restarted, **When** the database container starts, **Then** previously ingested data is still present (persisted via a Docker volume).

---

### Edge Cases

- What happens when the trip create/update endpoint receives invalid date formats? (The API returns a 422 Unprocessable Entity with a structured error body describing the validation failure.)
- What happens when the database is unavailable when a backend request fires? (Read endpoints return 503 with a structured error; write endpoints return the same. Ingestion behavior on DB outage is specified in `003-ingestion-pipeline`.)
- What happens when the frontend is running in a Docker container but the backend URL is not configured? (The frontend fails to load data and displays a graceful error; it does not crash the container.)

> Ingestion-specific edge cases (instagrapi sessions, Graph API fallback, Claude location inference, multi-trip date overlap, Substack feed availability, etc.) moved to `003-ingestion-pipeline/spec.md`.

## Requirements *(mandatory)*

### Functional Requirements

#### Database

- **FR-001**: The system MUST use PostgreSQL as the relational database engine in all environments (local development and production). The database MUST have four core tables: `trips`, `stops`, `instagram_posts`, and `substack_posts`. Schemas MUST reflect the data shapes defined in the existing `src/data/types.ts` interfaces.
- **FR-002**: The `trips` table MUST store: `id` (stable string slug), `title`, `description`, `start_date`, `end_date`, `created_at`, `updated_at`.
- **FR-003**: The `stops` table MUST store: `id`, `trip_id` (foreign key → trips), `date`, `location` (human-readable string), `lat` (decimal), `lng` (decimal), `status` (`visited` | `planned`), `region_code` (3-letter IATA code of the nearest international airport within the same country as the stop; used for sidebar region grouping; written by the ingestion pipeline in `003-ingestion-pipeline`), `post_type` (`instagram` | `substack` | `planned`), `sequence_order` (integer for ordered rendering), `caption` (nullable text, used for planned stops only), `created_at`.
- **FR-004**: The `instagram_posts` table MUST store: `id`, `stop_id` (foreign key → stops), `instagram_id` (platform identifier), `shortcode`, `media_url` (relative POSIX path to downloaded file), `caption`, `timestamp` (ISO 8601 UTC), `created_at`.
- **FR-005**: The `substack_posts` table MUST store: `id`, `stop_id` (foreign key → stops), `substack_id` (platform identifier), `title`, `subtitle`, `body` (long-form text), `published_at` (ISO 8601 UTC), `created_at`.
- **FR-006**: The system MUST include a seed script that populates the database from the existing hard-coded TypeScript data files. The process is two steps: (1) a TypeScript export script (`scripts/export-seed-data.ts`, runnable via `tsx`) imports the data modules and writes them to JSON files; (2) the Python seed script reads those JSON files and inserts records into a PostgreSQL database. After successfully seeding, the seed script MUST produce a PostgreSQL-compatible SQL dump at `scripts/seed-dump.sql` (generated via `pg_dump`); this file is used by the Docker environment (see US6 / FR-036) to pre-populate new deployments without re-running the export and seed pipeline.

#### Backend API

- **FR-007**: The backend MUST be written in Python and expose a REST API. All responses MUST use JSON.
- **FR-008**: `GET /trips` MUST return all trips in reverse-chronological order by start date. Optional query filters: `status` (active | completed | upcoming).
- **FR-009**: `GET /trips/:id` MUST return the full trip object including all its stops and each stop's associated post data (instagram, substack, or planned).
- **FR-010**: `GET /stops` MUST support query filters: `trip_id`, `status` (`visited` | `planned`), `region_code`, `post_type`, `after` (date), `before` (date).
- **FR-011**: `GET /instagram-posts` MUST support query filters: `stop_id`, `after` (timestamp), `before` (timestamp).
- **FR-012**: `GET /substack-posts` MUST support query filters: `stop_id`, `after` (published_at), `before` (published_at).
- **FR-013**: `POST /trips` and `PUT /trips/:id` MUST allow creating and updating a trip's `title`, `description`, `start_date`, and `end_date`. These endpoints MUST require authorization (see FR-029).
- **FR-045**: The backend MUST expose an endpoint to record the end date of a region within a trip. All parameters are optional: `trip` (trip id; defaults to the most recently created trip), `region` (IATA region code; defaults to the most recently active region within the resolved trip), and `date` (ISO 8601 date; defaults to the current date). The endpoint MUST require authorization (see FR-029). Unauthenticated requests MUST receive a 401 response. The exact data model implications and storage mechanism are to be determined during planning; the endpoint contract and persistence strategy MUST be defined in `specs/002-database-backend/contracts/api.md` before implementation.
- **FR-014**: The API MUST include CORS headers allowing requests from the configured frontend origin.
- **FR-015**: All endpoints MUST return structured error responses (`{ "error": "...", "detail": "..." }`) with appropriate HTTP status codes (400, 401, 404, 422, 500).

> Ingestion FRs (FR-016 through FR-022, FR-040, FR-041, FR-043, FR-044, FR-023 through FR-027) moved to `003-ingestion-pipeline/spec.md`.

#### Security

- **FR-028**: All credentials and secrets (`API_SECRET_KEY`, database credentials in `DATABASE_URL`) MUST be read from environment variables at startup and MUST NOT be hard-coded anywhere in the source. (Ingestion-specific secrets — Instagram credentials, Anthropic key for geocoding, Substack RSS URL, SMTP, Instagram Graph API token — are specified in `003-ingestion-pipeline`.)
- **FR-029**: The trip create/update endpoints (`POST /trips`, `PUT /trips/:id`) and the region end-date endpoint MUST require a valid bearer token or API key. Unauthenticated requests MUST receive a 401 response.
- **FR-030**: All public API endpoints MUST enforce rate limiting to protect against abuse. Exceeding the limit MUST return a 429 response.
- **FR-031**: All request parameters and body fields MUST be validated and sanitized before use. Invalid input MUST return a 422 response; no raw user input MUST reach the database layer.
- **FR-032**: The backend MUST enforce HTTPS in production. In local Docker development, HTTP on a loopback port is acceptable.
- **FR-033**: API responses MUST NOT include internal database identifiers, stack traces, or implementation details beyond what is necessary for the client.

#### Containerization

- **FR-034**: A `Dockerfile` MUST exist for the Python backend service.
- **FR-035**: A `Dockerfile` MUST exist for the frontend service (or the frontend MUST be served as static files by the backend in production mode).
- **FR-036**: A `docker-compose.yml` MUST exist at the project root that starts the backend, database, and frontend together with a single `docker compose up` command. The database service MUST mount `scripts/seed-dump.sql` into the container's init directory (e.g. `/docker-entrypoint-initdb.d/seed-dump.sql`) so the database is pre-populated with seed data automatically on first start (when the named volume is empty). Subsequent starts MUST skip the init script because the volume already contains data.
- **FR-037**: All runtime configuration (credentials, ports, DB connection string) MUST be injectable via environment variables defined in a `.env` file; a `.env.example` MUST be committed showing all required keys with placeholder values.
- **FR-038**: The database container MUST mount a named Docker volume so that data persists across container restarts.
- **FR-039**: The `docker-compose.yml` MUST define health checks for the backend and database services so that dependent containers do not start before their dependencies are ready.

#### Observability

- **FR-042**: The backend MUST emit all log output as structured JSON to stdout. No plain-text log lines and no log files MUST be written inside the container. Each log entry MUST include at minimum: `timestamp` (ISO 8601), `level` (e.g. `INFO`, `WARNING`, `ERROR`), `message`, and `logger` (module name). This enables Docker log drivers and external aggregators to parse and route logs without additional configuration.

### Key Entities *(include if feature involves data)*

- **Trip**: A named journey with a stable slug id, title, description, start date, and end date. Contains an ordered sequence of stops. Directly mirrors the `Trip` interface in `src/data/types.ts`.
- **Stop**: A single itinerary entry linked to exactly one trip. Stores date, location string, decimal coordinates, status (`visited` | `planned`), `region_code` (IATA code of the nearest in-country international airport, used for sidebar region grouping; written by ingestion in `003-ingestion-pipeline`), post type, optional planned-stop caption, and sequence order. Mirrors the `Stop` interface in `src/data/types.ts`.
- **Instagram Post**: Rich content record linked to one stop. Stores the Instagram platform id, shortcode, relative media path, caption text, and original timestamp. Mirrors the `InstagramPost` interface in `src/data/types.ts`, extended with `instagram_id` and `shortcode`. Populated by ingestion (see `003-ingestion-pipeline`).
- **Substack Post**: Long-form article record linked to one stop (or unlinked pending manual assignment). Stores the Substack post identifier, title, subtitle, body, and publication date. Mirrors the `SubstackPost` interface in `src/data/types.ts`, extended with `substack_id` and `published_at`. Populated by ingestion (see `003-ingestion-pipeline`).
- **Planned Post**: Represented solely by the stop record's `post_type = "planned"` and an optional `caption` field on the stop; no separate table is needed. Mirrors the `PlannedPost` interface.

> The `instagrapi Session` entity moved to `003-ingestion-pipeline/spec.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After seeding, every trip, stop, and post record in the database matches the source TypeScript data files exactly — same count, same field values, same ordering — with no missing or duplicate records.
- **SC-003**: The read API endpoints respond in under 500 milliseconds for typical queries (single trip with all stops and posts) under normal server load.
- **SC-004**: The full stack starts correctly with `docker compose up` on a clean machine with no additional setup steps beyond filling in `.env`.
- **SC-005**: All trip create/update requests without a valid token are rejected; zero unauthorized writes reach the database.
- **SC-008**: A developer with Docker can start the full local stack and have a working travelogue in their browser within 5 minutes of cloning the repository.
- **SC-009**: Every backend log line MUST be valid JSON emitted to stdout; no plain-text log output and no log files written inside the container.

> SC-002 (Instagram ingest latency), SC-006 (IG idempotency), SC-007 (Substack idempotency) moved to `003-ingestion-pipeline/spec.md`.

## Assumptions

- The Python backend MUST use PostgreSQL as the database engine in all environments (local development and production). SQLite is not used; all developers are expected to run PostgreSQL locally via Docker (`docker compose up`).
- The existing TypeScript data files (`miscellaneous-adventures.ts`, `earth-sandwich-2015.ts`, `earth-club-sandwich-2027.ts`) are the authoritative source for the initial database seed; no manual data entry is required.
- The `sequence_order` field on stops is an integer that mirrors the existing array index ordering in the hard-coded data files.
- Substack posts ingested without a `stop_id` are stored in the database and excluded from API responses until manually assigned to a stop; this is acceptable for v1.
- The frontend will be updated (in a follow-on task tracked in spec 001) to call the backend API instead of importing hard-coded TypeScript modules; that frontend change is out of scope for this spec.
- All media files are stored on the server filesystem alongside the application; object storage (e.g., S3) is out of scope for v1.
- Security scanning and formal penetration testing are out of scope; standard OWASP Top 10 mitigations (input validation, rate limiting, no secret leakage, HTTPS in production) are sufficient for this audience scale.

> Ingestion-specific assumptions (personal Instagram account, Substack feed availability, Claude for IATA determination, SMTP for session alerts, Graph API fallback, instagrapi session management) moved to `003-ingestion-pipeline/spec.md`.
