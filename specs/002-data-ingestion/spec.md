# Feature Specification: Data Ingestion & Backend

**Feature Branch**: `002-data-ingestion`
**Created**: 2026-05-08
**Updated**: 2026-05-08
**Status**: Draft
**Updated**: 2026-05-15
**Input**: User description: "Move User Story 6 from specs/001-world-travelogue/spec.md and related features into this spec. Covers all data ingestion and data handling related features. Instagram ingestion leverages instagrapi for more reliable location fetching and consuming the feed of non-creative/business accounts. A new ingestion pipeline for Substack posts is needed. The first concern is refactoring existing hardcoded data to a proper backend and database with tables for instagram_posts, substack_posts, stops, and trips. The backend is written in Python, handles automatic ingestion, and has read endpoints with basic filters plus a create/update trips endpoint. Standard security measures for public-facing traffic. Backend and frontend are containerized for easy local development and deployment."

## Clarifications

### Session 2026-05-08

- Q: When ingesting an Instagram post, how should the ingestion job determine which trip to assign the new stop to? → A: Auto-assign by date range (find the trip whose start/end date encompasses the post timestamp). If no trip's date range covers the post, default to the `miscellaneous-adventures` trip. If multiple trips' date ranges cover the post, assign to the newest (most recently created) trip.
- Q: What format should the Python seed script consume to read the existing hard-coded TypeScript data? → A: Build-time JSON export — a small TypeScript script (e.g. `tsx export-seed-data.ts`) imports the data files and writes JSON; the Python seed script reads those JSON files.
- Q: Where should the optional `caption` for planned stops be stored in the database schema? → A: Add a nullable `caption` column to the `stops` table (applies to planned stops only; ignored for instagram/substack stops, which store their text in their own tables).
- Q: How should the operator perform the initial `instagrapi` login to create the session file? → A: The backend exposes a CLI command (e.g. `python manage.py login`) that prompts for credentials and persists the session file to the configured path.
- Q: What logging strategy should the backend use? → A: Structured JSON logs emitted to stdout (Docker-native; compatible with any external log aggregator).
- Q: Are `region_code` and `nearest_airport_iata` the same concept? → A: Yes — merge into one. The ingestion pipeline (Claude) writes the computed IATA code directly to `region_code`; `nearest_airport_iata` is removed from the schema.
- Q: US3 scenario 6 and FR-044 contradict on whether a Graph API fallback is attempted after a session error. Which is authoritative? → A: FR-044 is authoritative — on a session error, send the notification email then attempt the Graph API fallback if configured; exit only if both fail.
- Q: FR-013 references `(see FR-021)` for authorization but FR-021 is the media download requirement; should it reference FR-029 instead? → A: Yes — fix the cross-reference to FR-029.
- Q: How should the Docker database container consume the seed dump on first start? → A: Mount `scripts/seed-dump.sql` into the DB container's init directory (e.g. `/docker-entrypoint-initdb.d/`) so it runs automatically on first start when the data volume is empty.
- Q: Which database engine should the seed dump target — PostgreSQL only, or also SQLite? → A: PostgreSQL everywhere; SQLite is dropped as an option entirely to simplify the toolchain.

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

### User Story 3 - Automatically ingest new Instagram posts (Priority: P2)

New posts from the travelers' Instagram account are fetched automatically on a recurring schedule (approximately once per hour). Each new post is geocoded, its media is downloaded and stored, and a corresponding stop and instagram post record are created in the database. No manual action is needed by the travelers.

**Why this priority**: Instagram posts are the primary source of visited-stop content for the live trip. Without automated ingestion the database goes stale the moment the traveler posts a new photo.

**Independent Test**: With valid credentials configured, trigger an ingestion run manually. Confirm that any Instagram posts newer than the latest database record are added to the database with location, lat/lng, and a downloaded media file, and that re-running produces no duplicates.

**Acceptance Scenarios**:

1. **Given** new Instagram posts exist since the last ingestion, **When** an ingestion run completes, **Then** one new stop and instagram post record is created per new post, in oldest-to-newest order.
2. **Given** an Instagram post has an explicitly tagged location (name, lat, lng), **When** it is ingested, **Then** the tagged location name, latitude, and longitude are stored exactly as provided — they are never re-estimated — and the IATA region code is determined by the AI reasoning engine and stored in `stops.region_code`.
3. **Given** an Instagram post has no location tag, **When** it is ingested, **Then** the AI reasoning engine is called with the post caption and image content to identify the specific location from observable visual and textual cues (not a generic estimate), and the resulting location name, coordinates, and IATA region code are stored.
4. **Given** no new posts exist since the last ingestion, **When** an ingestion run completes, **Then** no new records are written and the run exits cleanly.
5. **Given** a media download fails for one post, **When** the run continues, **Then** the remaining posts are still processed and a record is written for the failed post with an empty media path and a logged warning.
6. **Given** instagrapi raises a session or authentication exception, **When** the ingestion run fires, **Then** a notification email is sent to `automation@datacommlab.com`, the Graph API fallback is attempted if `INSTAGRAM_GRAPH_API_TOKEN` is configured, and the job exits cleanly without modifying existing records only if both methods fail.
7. **Given** instagrapi fails for a non-session reason and the Instagram Graph API token is configured, **When** the ingestion job retries, **Then** it falls back to fetching posts via the Instagram Graph API and completes the run.

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

### User Story 5 - Automatically ingest new Substack articles (Priority: P3)

New articles published to the travelers' Substack newsletter are fetched on a recurring schedule via the Substack RSS feed. Each new article is parsed for title, subtitle, and body content and stored as a Substack post record linked to a stop. The ingestion is idempotent and does not create duplicate records for articles already in the database.

**Why this priority**: Substack articles are the long-form narrative layer of the travelogue. Once a Substack account is active, the ingestion pipeline must be ready so articles enter the database automatically without manual intervention.

**Independent Test**: Configure a Substack RSS URL. Trigger a manual ingestion run. Confirm that articles not yet in the database are added as Substack post records. Re-run and confirm no duplicates are created.

**Acceptance Scenarios**:

1. **Given** a valid Substack RSS URL is configured, **When** an ingestion run completes, **Then** all articles not already in the database are added as new Substack post records with title, subtitle, body, and published date.
2. **Given** an article is already in the database (matched by Substack post id), **When** the ingestion runs again, **Then** no duplicate record is created.
3. **Given** the Substack RSS feed is unreachable, **When** the ingestion run fires, **Then** it exits cleanly with an error logged and does not affect existing records.

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

- What happens when the Instagram account used for ingestion is a personal (non-business/creator) account? (instagrapi handles personal accounts via session-based authentication, unlike the Graph API which requires a business account.)
- What happens when the instagrapi session expires or Instagram challenges the login? (The ingestion job sends a notification email to `automation@datacommlab.com`, logs the authentication error, then falls back to the Instagram Graph API if `INSTAGRAM_GRAPH_API_TOKEN` is configured. If the fallback also fails, the job exits without modifying existing records. The operator is responsible for refreshing the session via the CLI login command.)
- What happens when the AI reasoning engine cannot determine an IATA code for a location (whether from a tagged or inferred location)? (`region_code` is left null and a warning is logged; processing continues for the remaining posts.)
- What happens when the AI reasoning engine is asked to infer a location but the image and caption provide no identifiable cues? (The LLM MUST return its best attempt and flag low confidence in the response; `location`, `lat`, `lng`, and `region_code` are stored as returned, and the stop is created. Prompt engineering must discourage generic or fabricated responses.)
- What happens when `instagrapi` fails for a non-session reason but `INSTAGRAM_GRAPH_API_TOKEN` is not configured? (The job logs the error at ERROR level and exits without modifying existing records; no fallback is attempted.)
- What happens when an Instagram post's location tag provides a name but no coordinates? (The location name is stored; lat/lng are left empty. Claude is called only to determine the IATA region code, not to re-estimate the location name, which stays as-is.)
- What happens when an Instagram post has a tagged location and Claude is called to determine the IATA code but returns an invalid or unrecognized code? (`region_code` is set to null and a warning is logged; the tagged location name and coordinates are still stored correctly.)
- What happens when Claude returns malformed JSON for a location inference? (The raw text is stored as the location name with empty lat/lng; processing continues for remaining posts.)
- What happens when multiple new Instagram posts share the same timestamp? (All are ingested; they are processed in the order returned by instagrapi and each receives a unique database id.)
- What happens when `INSTA_USERNAME`, `INSTA_PASSWORD`, or `ANTHROPIC_API_KEY` is missing from the environment at startup? (The backend exits immediately with a clear error before making any network calls or writing any records.)
- What happens when a Substack article is published months after the actual visit? (The article is stored with its publication date; mapping it to the correct stop is done manually or by date-proximity logic — the Substack stop date is never used for region date-range computation per spec 001 FR-033.)
- What happens when the database is unavailable when an ingestion job fires? (The job logs the connection error, skips the run, and does not lose any previously ingested data.)
- What happens when the frontend is running in a Docker container but the backend URL is not configured? (The frontend fails to load data and displays a graceful error; it does not crash the container.)
- What happens when the trip create/update endpoint receives invalid date formats? (The API returns a 422 Unprocessable Entity with a structured error body describing the validation failure.)
- What happens if a stop being ingested cannot be assigned to any existing trip (no trip covers its date range)? (The stop is assigned to the `miscellaneous-adventures` trip as the default fallback; see FR-040.)
- What happens when multiple trips have overlapping date ranges that all cover the same ingested post? (The post is assigned to the newest trip by creation date; see FR-040.)

## Requirements *(mandatory)*

### Functional Requirements

#### Database

- **FR-001**: The system MUST use PostgreSQL as the relational database engine in all environments (local development and production). The database MUST have four core tables: `trips`, `stops`, `instagram_posts`, and `substack_posts`. Schemas MUST reflect the data shapes defined in the existing `src/data/types.ts` interfaces.
- **FR-002**: The `trips` table MUST store: `id` (stable string slug), `title`, `description`, `start_date`, `end_date`, `created_at`, `updated_at`.
- **FR-003**: The `stops` table MUST store: `id`, `trip_id` (foreign key → trips), `date`, `location` (human-readable string), `lat` (decimal), `lng` (decimal), `status` (`visited` | `planned`), `region_code` (3-letter IATA code of the nearest international airport within the same country as the stop; used for sidebar region grouping), `post_type` (`instagram` | `substack` | `planned`), `sequence_order` (integer for ordered rendering), `caption` (nullable text, used for planned stops only), `created_at`.
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
- **FR-045**: The backend MUST expose an endpoint to record the end date of a region within a trip. All parameters are optional: `trip` (trip id; defaults to the most recently created trip), `region` (IATA region code; defaults to the most recently active region within the resolved trip), and `date` (ISO 8601 date; defaults to the current date). The endpoint MUST require authorization (see FR-029). Unauthenticated requests MUST receive a 401 response. The exact data model implications and storage mechanism are to be determined during planning; the endpoint contract and persistence strategy MUST be defined in `specs/002-data-ingestion/contracts/api.md` before implementation.
- **FR-014**: The API MUST include CORS headers allowing requests from the configured frontend origin.
- **FR-015**: All endpoints MUST return structured error responses (`{ "error": "...", "detail": "..." }`) with appropriate HTTP status codes (400, 401, 404, 422, 500).

#### Instagram Ingestion

- **FR-016**: The Instagram ingestion pipeline MUST use `instagrapi` (session-based) as the primary method for post fetching, enabling ingestion from personal (non-business, non-creator) accounts. The Instagram Graph API is a secondary fallback (see FR-043).
- **FR-041**: The backend MUST expose a CLI command (e.g. `python manage.py login`) that prompts the operator for Instagram credentials interactively and persists the resulting `instagrapi` session file to the path configured by `INSTAGRAPI_SESSION_FILE`. This command is intended for one-time setup; normal scheduled ingestion MUST reuse the persisted session without re-authenticating.
- **FR-043**: If `instagrapi` fails for a non-session reason (e.g., network timeout, unexpected API change) and `INSTAGRAM_GRAPH_API_TOKEN` is present in the environment, the ingestion job MUST automatically fall back to fetching posts via the Instagram Graph API. The fallback MUST be logged at `WARNING` level. If neither method succeeds, the job logs the error and exits without modifying existing records.
- **FR-044**: If `instagrapi` raises a session or authentication exception (login challenge, session expired, 2FA required), the ingestion job MUST send a notification email to `automation@datacommlab.com` with a subject of `[travelogue] Instagram session error` and a body containing the error message and timestamp. The job MUST then attempt the Instagram Graph API fallback if `INSTAGRAM_GRAPH_API_TOKEN` is configured; if the fallback also fails, the job exits cleanly without modifying existing records.
- **FR-017**: The ingestion job MUST run on a recurring schedule, defaulting to approximately once per hour, configurable via environment variable.
- **FR-018**: On each run the job MUST query the database for the most recent Instagram post timestamp and fetch only posts newer than that timestamp from the account's feed, processing them oldest-first.
- **FR-019**: For each new post the job MUST attempt to read the structured location tag (name, lat, lng) directly from the instagrapi post object. If a tagged location name is present, it MUST be stored exactly as provided — the AI MUST NOT be called to re-estimate or override the tagged location name or coordinates. The job MUST then call Claude to determine the IATA code of the nearest international airport within the same country, passing the tagged location name and coordinates as input. The result is stored in `stops.region_code`. If Claude returns a null or unrecognizable IATA code, `region_code` is left null and a warning is logged; processing MUST continue.
- **FR-020**: When instagrapi returns no location tag, the job MUST call Claude (`claude-opus-4-5`) with the post caption, the base64-encoded image (for IMAGE posts), and the locations of up to the 5 most-recently-processed posts as context. The prompt MUST explicitly instruct Claude to identify the specific location from observable content in the image and caption (e.g., visible signage, landmarks, recognizable geographic features) rather than making a generic estimate. Claude MUST return a JSON object with `location`, `lat`, `lng`, and `region` (the IATA code of the nearest international airport within the same country). The `region` value is stored in `stops.region_code`. If the response is malformed JSON the raw text MUST be stored as the location name with empty coordinates and a null `region_code`.
- **FR-021**: Each new Instagram post MUST have its media downloaded to `public/media/<stop_id>.jpg` (IMAGE) or `public/media/<stop_id>.mp4` (VIDEO). A media download failure MUST log a warning and leave `media_url` empty; it MUST NOT abort processing of remaining posts.
- **FR-022**: The ingestion job MUST be idempotent: re-running MUST NOT create duplicate records for posts already in the database, matched by `instagram_id`.
- **FR-040**: The ingestion job MUST assign each new stop to a trip using the following priority: (1) find all trips whose `start_date`/`end_date` range encompasses the post's timestamp — if exactly one match exists, assign to it; (2) if multiple trips match, assign to the trip with the most recent `created_at` value; (3) if no trip's date range matches, assign to the trip with `id = "miscellaneous-adventures"` as the default fallback. This default trip MUST exist in the database; if it is absent the ingestion job MUST log an error and halt rather than create a stop with a null `trip_id`.

#### Substack Ingestion

- **FR-023**: The Substack ingestion pipeline MUST poll the configured Substack RSS feed URL on a recurring schedule to discover new articles.
- **FR-024**: For each RSS entry not already in the database (matched by a stable Substack post identifier such as the `<guid>` or `<link>` element), the pipeline MUST create a new `substack_posts` record with: `title`, `subtitle` (from `<description>`), `body` (from `<content:encoded>`), and `published_at` (from `<pubDate>`).
- **FR-025**: Substack ingestion MUST be idempotent: re-running MUST NOT create duplicate records for articles already in the database.
- **FR-026**: If the Substack RSS feed URL is not configured or is unreachable, the ingestion run MUST log the error and exit cleanly without affecting existing records.
- **FR-027**: Associating a newly ingested Substack post with a specific stop and trip is out of scope for automatic ingestion; the record is created without a `stop_id` and flagged for manual assignment.

#### Security

- **FR-028**: All credentials and secrets (`INSTA_USERNAME`, `INSTA_PASSWORD`, `ANTHROPIC_API_KEY`, `SUBSTACK_RSS_URL`, `API_SECRET_KEY`) MUST be read from environment variables at startup and MUST NOT be hard-coded anywhere in the source. No external airport-lookup API key is required; all IATA code determination is performed via the Claude AI.
- **FR-029**: The trip create/update endpoints (`POST /trips`, `PUT /trips/:id`) MUST require a valid bearer token or API key. Unauthenticated requests MUST receive a 401 response.
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
- **Stop**: A single itinerary entry linked to exactly one trip. Stores date, location string, decimal coordinates, status (`visited` | `planned`), `region_code` (IATA code of the nearest in-country international airport, used for sidebar region grouping), post type, optional planned-stop caption, and sequence order. Mirrors the `Stop` interface in `src/data/types.ts`; `region_code` is always determined by the AI reasoning engine — using the Instagram-tagged location data (name + coordinates) as input when available, or inferring from post caption and image content otherwise.
- **Instagram Post**: Rich content record linked to one stop. Stores the Instagram platform id, shortcode, relative media path, caption text, and original timestamp. Mirrors the `InstagramPost` interface in `src/data/types.ts`, extended with `instagram_id` and `shortcode`.
- **Substack Post**: Long-form article record linked to one stop (or unlinked pending manual assignment). Stores the Substack post identifier, title, subtitle, body, and publication date. Mirrors the `SubstackPost` interface in `src/data/types.ts`, extended with `substack_id` and `published_at`.
- **Planned Post**: Represented solely by the stop record's `post_type = "planned"` and an optional `caption` field on the stop; no separate table is needed. Mirrors the `PlannedPost` interface.
- **instagrapi Session**: A persisted session credential used by the ingestion pipeline to authenticate with Instagram as a personal account. Not stored in the database; stored as a session file on the server filesystem and referenced by environment configuration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After seeding, every trip, stop, and post record in the database matches the source TypeScript data files exactly — same count, same field values, same ordering — with no missing or duplicate records.
- **SC-002**: New Instagram posts appear in the database within 2 hours of being posted to Instagram under normal operating conditions.
- **SC-003**: The read API endpoints respond in under 500 milliseconds for typical queries (single trip with all stops and posts) under normal server load.
- **SC-004**: The full stack starts correctly with `docker compose up` on a clean machine with no additional setup steps beyond filling in `.env`.
- **SC-005**: All trip create/update requests without a valid token are rejected; zero unauthorized writes reach the database.
- **SC-006**: Running the Instagram ingestion job twice in a row produces zero duplicate records in the database.
- **SC-007**: Running the Substack ingestion job twice in a row produces zero duplicate records in the database.
- **SC-008**: A developer with Docker can start the full local stack and have a working travelogue in their browser within 5 minutes of cloning the repository.
- **SC-009**: Every backend log line MUST be valid JSON emitted to stdout; no plain-text log output and no log files written inside the container.

## Assumptions

- The travelers' Instagram account is a personal account, not a business or creator account; accordingly `instagrapi` (session-based) is used instead of the Instagram Graph API.
- A Substack account and RSS feed URL will be provided when the Substack ingestion pipeline is tested; the pipeline is specified now so it can be built and validated with any RSS-compatible test feed in the interim.
- The Python backend MUST use PostgreSQL as the database engine in all environments (local development and production). SQLite is not used; all developers are expected to run PostgreSQL locally via Docker (`docker compose up`).
- The existing TypeScript data files (`miscellaneous-adventures.ts`, `earth-sandwich-2015.ts`, `earth-club-sandwich-2027.ts`) are the authoritative source for the initial database seed; no manual data entry is required.
- Region computation (grouping stops by nearest airport) is handled entirely by the AI reasoning engine; no external airport-lookup API is used. Region codes are stored on each stop record at ingestion time.
- The `sequence_order` field on stops is an integer that mirrors the existing array index ordering in the hard-coded data files.
- Substack posts ingested without a `stop_id` are stored in the database and excluded from API responses until manually assigned to a stop; this is acceptable for v1.
- The ingestion schedules (Instagram ~hourly, Substack configurable) are implemented as background threads or an APScheduler job within the Python backend process, not as external cron jobs. This is consistent with the containerized deployment model.
- The frontend will be updated (in a follow-on task tracked in spec 001) to call the backend API instead of importing hard-coded TypeScript modules; that frontend change is out of scope for this spec.
- `instagrapi` session management (initial login, session refresh after expiry, handling 2FA challenges) is the operator's responsibility; automated session renewal is out of scope for v1.
- All IATA region code determination is performed by the Claude AI reasoning engine. No external airport-lookup API key (`AIRPORT_API_KEY`) is required. The AI is provided with the tagged location name and coordinates when available, or prompted to infer location from image and caption content otherwise. Prompt engineering work is required to ensure the AI consistently identifies actual locations rather than generating generic estimates.
- When an Instagram post has an explicitly tagged location, that tagged data is authoritative and must be stored verbatim; the AI is invoked only to derive the IATA region code from the known location, never to re-estimate the location itself.
- The notification email for session errors is sent via SMTP; `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, and `SMTP_PASSWORD` must be configured in the environment for email delivery to work. If SMTP is not configured, the email is skipped and the error is logged only.
- The Instagram Graph API fallback requires a valid `INSTAGRAM_GRAPH_API_TOKEN` in the environment; it is strictly optional and the system functions correctly without it (instagrapi only).
- All media files are stored on the server filesystem alongside the application; object storage (e.g., S3) is out of scope for v1.
- Security scanning and formal penetration testing are out of scope; standard OWASP Top 10 mitigations (input validation, rate limiting, no secret leakage, HTTPS in production) are sufficient for this audience scale.
