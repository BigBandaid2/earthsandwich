# Feature Specification: Ingestion Pipeline (Instagram + Substack)

**Feature Branch**: `003-ingestion-pipeline`
**Created**: 2026-05-22
**Status**: Draft
**Input**: Extracted from `002-data-ingestion` on 2026-05-22 when that spec was split. Covers all automated content ingestion: pulling new Instagram posts from a personal account via `instagrapi` (with an Instagram Graph API fallback), pulling new Substack articles via RSS, computing IATA region codes for new stops via Claude AI, and running both jobs on a recurring schedule within the backend process. Schema, REST API, and containerization remain in `002-database-backend`.

## Dependencies

This spec depends on **`002-database-backend`** for:
- Database schema (`trips`, `stops`, `instagram_posts`, `substack_posts` tables)
- Backend FastAPI application skeleton and `lifespan` hook (where the scheduler is wired)
- Configuration system (`pydantic-settings`) and structured logging (`structlog`)
- The `miscellaneous-adventures` default trip seeded into the database (FR-040 fallback target)

## Clarifications

### Session 2026-05-25

- Q: Should the Instagram Graph API fallback (originally specified in FR-043) be retained alongside `instagrapi`? → A: No. The Graph API path is dropped entirely; `instagrapi` is the sole ingestion mechanism. Personal accounts have no Graph API surface to fall back to in practice, and maintaining a second code path doubled testing surface for marginal robustness. If `instagrapi` becomes unreliable enough to warrant a fallback later, we revisit by spec amendment. **Effects**: FR-043 retired, FR-016 amended (drop the "secondary fallback" clause), FR-044's session-error path now exits cleanly after sending the alert email, `INSTAGRAM_GRAPH_API_TOKEN` is no longer a recognized env var.

### Session 2026-05-08 (inherited from the original 002-data-ingestion spec)

- Q: When ingesting an Instagram post, how should the ingestion job determine which trip to assign the new stop to? → A: Auto-assign by date range (find the trip whose start/end date encompasses the post timestamp). If no trip's date range covers the post, default to the `miscellaneous-adventures` trip. If multiple trips' date ranges cover the post, assign to the newest (most recently created) trip.
- Q: How should the operator perform the initial `instagrapi` login to create the session file? → A: The backend exposes a CLI command (e.g. `python manage.py login`) that prompts for credentials and persists the session file to the configured path.
- Q: US3 scenario 6 and FR-044 contradict on whether a Graph API fallback is attempted after a session error. Which is authoritative? → A: FR-044 is authoritative — on a session error, send the notification email then attempt the Graph API fallback if configured; exit only if both fail.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatically ingest new Instagram posts (Priority: P1)

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

### User Story 2 - Automatically ingest new Substack articles (Priority: P2)

New articles published to the travelers' Substack newsletter are fetched on a recurring schedule via the Substack RSS feed. Each new article is parsed for title, subtitle, and body content and stored as a Substack post record linked to a stop. The ingestion is idempotent and does not create duplicate records for articles already in the database.

**Why this priority**: Substack articles are the long-form narrative layer of the travelogue. Once a Substack account is active, the ingestion pipeline must be ready so articles enter the database automatically without manual intervention.

**Independent Test**: Configure a Substack RSS URL. Trigger a manual ingestion run. Confirm that articles not yet in the database are added as Substack post records. Re-run and confirm no duplicates are created.

**Acceptance Scenarios**:

1. **Given** a valid Substack RSS URL is configured, **When** an ingestion run completes, **Then** all articles not already in the database are added as new Substack post records with title, subtitle, body, and published date.
2. **Given** an article is already in the database (matched by Substack post id), **When** the ingestion runs again, **Then** no duplicate record is created.
3. **Given** the Substack RSS feed is unreachable, **When** the ingestion run fires, **Then** it exits cleanly with an error logged and does not affect existing records.

---

### Edge Cases

- What happens when the Instagram account used for ingestion is a personal (non-business/creator) account? (instagrapi handles personal accounts via session-based authentication, unlike the Graph API which requires a business account.)
- What happens when the instagrapi session expires or Instagram challenges the login? (The ingestion job sends a notification email to `automation@datacommlab.com`, logs the authentication error, and exits without modifying existing records. The operator must refresh the session via the CLI login command before the next scheduled run. — Amended 2026-05-25 to drop the Graph API fallback.)
- What happens when the AI reasoning engine cannot determine an IATA code for a location (whether from a tagged or inferred location)? (`region_code` is left null and a warning is logged; processing continues for the remaining posts.)
- What happens when the AI reasoning engine is asked to infer a location but the image and caption provide no identifiable cues? (The LLM MUST return its best attempt and flag low confidence in the response; `location`, `lat`, `lng`, and `region_code` are stored as returned, and the stop is created. Prompt engineering must discourage generic or fabricated responses.)
- What happens when `instagrapi` fails for a non-session reason (network timeout, unexpected response, etc.)? (The job logs the error at ERROR level and exits without modifying existing records. No external fallback exists as of the 2026-05-25 amendment.)
- What happens when an Instagram post's location tag provides a name but no coordinates? (The location name is stored; lat/lng are left empty. Claude is called only to determine the IATA region code, not to re-estimate the location name, which stays as-is.)
- What happens when an Instagram post has a tagged location and Claude is called to determine the IATA code but returns an invalid or unrecognized code? (`region_code` is set to null and a warning is logged; the tagged location name and coordinates are still stored correctly.)
- What happens when Claude returns malformed JSON for a location inference? (The raw text is stored as the location name with empty lat/lng; processing continues for remaining posts.)
- What happens when multiple new Instagram posts share the same timestamp? (All are ingested; they are processed in the order returned by instagrapi and each receives a unique database id.)
- What happens when `INSTA_USERNAME`, `INSTA_PASSWORD`, or `ANTHROPIC_API_KEY` is missing from the environment at startup? (The backend exits immediately with a clear error before making any network calls or writing any records.)
- What happens when a Substack article is published months after the actual visit? (The article is stored with its publication date; mapping it to the correct stop is done manually or by date-proximity logic — the Substack stop date is never used for region date-range computation per spec 001 FR-033.)
- What happens when the database is unavailable when an ingestion job fires? (The job logs the connection error, skips the run, and does not lose any previously ingested data.)
- What happens if a stop being ingested cannot be assigned to any existing trip (no trip covers its date range)? (The stop is assigned to the `miscellaneous-adventures` trip as the default fallback; see FR-040.)
- What happens when multiple trips have overlapping date ranges that all cover the same ingested post? (The post is assigned to the newest trip by creation date; see FR-040.)

## Requirements *(mandatory)*

> **FR numbering carried over from 002-data-ingestion to preserve cross-references in `plan.md`, `tasks.md`, and existing commits.** Non-sequential numbers are intentional.

### Functional Requirements

#### Instagram Ingestion

- **FR-016**: The Instagram ingestion pipeline MUST use `instagrapi` (session-based) for post fetching, enabling ingestion from personal (non-business, non-creator) accounts. No external Instagram API fallback is used; the pipeline depends solely on a valid `instagrapi` session. (Amended 2026-05-25 — previously specified a Graph API secondary fallback; see the 2026-05-25 clarification.)
- **FR-017**: The ingestion job MUST run on a recurring schedule, defaulting to approximately once per hour, configurable via environment variable.
- **FR-018**: On each run the job MUST query the database for the most recent Instagram post timestamp and fetch only posts newer than that timestamp from the account's feed, processing them oldest-first.
- **FR-019**: For each new post the job MUST attempt to read the structured location tag (name, lat, lng) directly from the instagrapi post object. If a tagged location name is present, it MUST be stored exactly as provided — the AI MUST NOT be called to re-estimate or override the tagged location name or coordinates. The job MUST then call Claude to determine the IATA code of the nearest international airport within the same country, passing the tagged location name and coordinates as input. The result is stored in `stops.region_code`. If Claude returns a null or unrecognizable IATA code, `region_code` is left null and a warning is logged; processing MUST continue.
- **FR-020**: When instagrapi returns no location tag, the job MUST call Claude with the post caption, the base64-encoded image (for IMAGE posts), and the locations of up to the 5 most-recently-processed posts as context. The prompt MUST explicitly instruct Claude to identify the specific location from observable content in the image and caption (e.g., visible signage, landmarks, recognizable geographic features) rather than making a generic estimate. Claude MUST return a JSON object with `location`, `lat`, `lng`, and `region` (the IATA code of the nearest international airport within the same country). The `region` value is stored in `stops.region_code`. If the response is malformed JSON the raw text MUST be stored as the location name with empty coordinates and a null `region_code`.
- **FR-021**: Each new Instagram post MUST have its media downloaded to `public/media/<stop_id>.jpg` (IMAGE) or `public/media/<stop_id>.mp4` (VIDEO). A media download failure MUST log a warning and leave `media_url` empty; it MUST NOT abort processing of remaining posts.
- **FR-022**: The ingestion job MUST be idempotent: re-running MUST NOT create duplicate records for posts already in the database, matched by `instagram_id`.
- **FR-040**: The ingestion job MUST assign each new stop to a trip using the following priority: (1) find all trips whose `start_date`/`end_date` range encompasses the post's timestamp — if exactly one match exists, assign to it; (2) if multiple trips match, assign to the trip with the most recent `created_at` value; (3) if no trip's date range matches, assign to the trip with `id = "miscellaneous-adventures"` as the default fallback. This default trip MUST exist in the database; if it is absent the ingestion job MUST log an error and halt rather than create a stop with a null `trip_id`.
- **FR-041**: The backend MUST expose a CLI command (e.g. `python manage.py login`) that prompts the operator for Instagram credentials interactively and persists the resulting `instagrapi` session file to the path configured by `INSTAGRAPI_SESSION_FILE`. This command is intended for one-time setup; normal scheduled ingestion MUST reuse the persisted session without re-authenticating.
- **FR-043**: ~~_Retired 2026-05-25._~~ Originally specified an Instagram Graph API fallback when `instagrapi` failed for non-session reasons. Removed when the implementation pivoted to instagrapi-only fetching; see the 2026-05-25 clarification. Kept as a numbered placeholder so existing cross-references (`plan.md`, `tasks.md`, prior commits) don't dangle.
- **FR-044**: If `instagrapi` raises a session or authentication exception (login challenge, session expired, 2FA required), the ingestion job MUST send a notification email to `automation@datacommlab.com` with a subject of `[travelogue] Instagram session error` and a body containing the error message and timestamp. The job MUST then exit cleanly without modifying existing records. The operator is responsible for refreshing the `instagrapi` session via the CLI login command (FR-041) before the next scheduled run. (Amended 2026-05-25 — previously included a Graph API fallback step.)

#### Substack Ingestion

- **FR-023**: The Substack ingestion pipeline MUST poll the configured Substack RSS feed URL on a recurring schedule to discover new articles.
- **FR-024**: For each RSS entry not already in the database (matched by a stable Substack post identifier such as the `<guid>` or `<link>` element), the pipeline MUST create a new `substack_posts` record with: `title`, `subtitle` (from `<description>`), `body` (from `<content:encoded>`), and `published_at` (from `<pubDate>`).
- **FR-025**: Substack ingestion MUST be idempotent: re-running MUST NOT create duplicate records for articles already in the database.
- **FR-026**: If the Substack RSS feed URL is not configured or is unreachable, the ingestion run MUST log the error and exit cleanly without affecting existing records.
- **FR-027**: Associating a newly ingested Substack post with a specific stop and trip is out of scope for automatic ingestion; the record is created without a `stop_id` and flagged for manual assignment.

### Key Entities *(include if feature involves data)*

The schema entities (`trips`, `stops`, `instagram_posts`, `substack_posts`) are defined in **`002-database-backend/data-model.md`** and are treated as pre-existing by this spec. The only entity introduced here:

- **instagrapi Session**: A persisted session credential used by the ingestion pipeline to authenticate with Instagram as a personal account. Not stored in the database; stored as a session file on the server filesystem and referenced by the `INSTAGRAPI_SESSION_FILE` environment variable.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> SC numbering carried over from 002-data-ingestion.

- **SC-002**: New Instagram posts appear in the database within 2 hours of being posted to Instagram under normal operating conditions.
- **SC-006**: Running the Instagram ingestion job twice in a row produces zero duplicate records in the database.
- **SC-007**: Running the Substack ingestion job twice in a row produces zero duplicate records in the database.

## Assumptions

- The travelers' Instagram account is a personal account, not a business or creator account; accordingly `instagrapi` (session-based) is used instead of the Instagram Graph API.
- A Substack account and RSS feed URL will be provided when the Substack ingestion pipeline is tested; the pipeline is specified now so it can be built and validated with any RSS-compatible test feed in the interim.
- Region computation (IATA code for the nearest in-country international airport) is handled entirely by the Claude AI reasoning engine; no external airport-lookup API is used. Prompt engineering work is required to ensure the AI consistently identifies actual locations rather than generating generic estimates.
- When an Instagram post has an explicitly tagged location, that tagged data is authoritative and must be stored verbatim; the AI is invoked only to derive the IATA region code from the known location, never to re-estimate the location itself.
- Substack posts ingested without a `stop_id` are stored in the database and excluded from API responses until manually assigned to a stop; this is acceptable for v1.
- The ingestion schedules (Instagram ~hourly, Substack configurable) are implemented as APScheduler jobs within the Python backend process, not as external cron jobs. This is consistent with the containerized deployment model defined in 002-database-backend.
- `instagrapi` session management (initial login, session refresh after expiry, handling 2FA challenges) is the operator's responsibility; automated session renewal is out of scope for v1.
- The notification email for session errors is sent via SMTP; `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, and `SMTP_PASSWORD` must be configured in the environment for email delivery to work. If SMTP is not configured, the email is skipped and the error is logged only.
- All media files are stored on the server filesystem alongside the application; object storage (e.g., S3) is out of scope for v1.
