# Research: Data Ingestion & Backend

**Phase**: 0 | **Plan**: [plan.md](plan.md) | **Date**: 2026-05-12

## Decision 1: Python Web Framework

**Decision**: FastAPI 0.115

**Rationale**: Native async (ASGI), Pydantic v2 integration for request/response validation, automatic OpenAPI/Swagger docs, dependency injection built-in, high performance (on par with Node/Go for I/O-bound workloads). Ideal for an API-first backend at this scale.

**Alternatives considered**:
- Flask: synchronous by default (WSGI); async bolted on via `flask[async]`; no native schema validation; less ergonomic for REST APIs
- Django REST Framework: excellent ecosystem but heavyweight for this scope; opinionated ORM (Django ORM) conflicts with SQLAlchemy preference; much larger surface area than needed

---

## Decision 2: ORM and Migrations

**Decision**: SQLAlchemy 2.0 (async session with `asyncpg`) + Alembic

**Rationale**: SQLAlchemy 2.0 introduced a clean async API via `AsyncSession` + `asyncpg`; this is the idiomatic FastAPI pattern and avoids thread-pool overhead of sync drivers under concurrent requests. Alembic provides migration versioning and is the standard SQLAlchemy companion. The async approach avoids retrofitting later if the API ever handles concurrent ingestion runs.

**Alternatives considered**:
- SQLAlchemy sync + psycopg2-binary: simpler but requires `run_in_executor` wrappers for every DB call in async routes, adding boilerplate and latency
- Tortoise ORM: async-first but smaller ecosystem, fewer SQLAlchemy patterns transferable
- raw asyncpg queries: fast but no ORM; schema maintenance via raw SQL strings is fragile at this schema size

---

## Decision 3: Instagram Ingestion Library

**Decision**: `instagrapi` (session-based) as primary; existing Instagram Graph API code as fallback

**Rationale**: The travelers' account is a personal account — the Instagram Graph API requires a Business or Creator account and cannot access personal feeds. `instagrapi` uses the private Instagram API with session-based authentication (no account type restriction). It provides structured location objects including country code, which eliminates the need for a separate geocoding step when a tag exists. The existing `load_posts_tsv.py` Graph API code is retained as the fallback per FR-043/FR-044.

**Alternatives considered**:
- Instagram Graph API only: ruled out — does not support personal accounts
- `instagram-private-api` (Python): less actively maintained than instagrapi; fewer post metadata fields
- Manual TSV scraping (current approach): does not support personal accounts either; Claude-based geocoding for every post is slow and costly

**Session management**: The `python -m app.cli.manage login` command (FR-041) handles initial authentication and persists the session file to `INSTAGRAPI_SESSION_FILE`. Normal ingestion reuses the persisted session without re-authenticating.

---

## Decision 4: In-Process Job Scheduling

**Decision**: APScheduler 3.x with `BackgroundScheduler`

**Rationale**: The spec (Assumptions section) explicitly requires scheduling as background threads or APScheduler within the Python backend process — not an external cron. APScheduler satisfies this: it runs in the same process as FastAPI (started in the `lifespan` context manager), requires no external broker, and is trivially configurable via environment variable. The ingestion interval (default ~1 hour) is set via `INSTAGRAM_POLL_INTERVAL_MINUTES` and `SUBSTACK_POLL_INTERVAL_MINUTES`.

**Alternatives considered**:
- Celery + Redis/RabbitMQ: production-grade but requires a broker container and worker process — overkill for two scheduled jobs at low frequency
- External cron (host crontab): creates host-level dependency that conflicts with the Docker deployment model; also the current architecture we're replacing
- FastAPI BackgroundTasks: for one-off tasks, not recurring schedules

---

## Decision 5: IATA Airport Lookup

**Decision**: Airlabs API (`airlabs.co`) via `GET /airports?lat=X&lng=Y`

**Rationale**: Free tier (1,000 requests/month) is sufficient for the ingestion rate (at most a few posts per day). REST API returns airports ordered by distance with country code for filtering — directly maps to the spec requirement of finding the nearest in-country international airport. The `instagrapi` location object includes a country code that is used to filter Airlabs results, so no additional geocoding step is needed. If the key is absent or the API fails, `region_code` is stored as null per spec.

**Alternatives considered**:
- OpenFlights static dataset: free and unlimited but requires bundling a CSV file and implementing haversine distance sorting locally; more code, no maintenance path if airports change
- AirportAPI.com: paid tier required for country filtering
- Google Places API: overkill and expensive for this narrow use case

---

## Decision 6: Structured Logging

**Decision**: `structlog` with `JSONRenderer` in production, `ConsoleRenderer` in development

**Rationale**: structlog is the gold standard for structured logging in Python. Its processor pipeline model cleanly handles adding `timestamp`, `level`, `message`, and `logger` to every log entry (FR-042). The `ConsoleRenderer` in development gives human-readable output; `JSONRenderer` in production emits newline-delimited JSON to stdout for Docker log drivers. FastAPI's `uvicorn` access logs are also captured by structlog.

**Alternatives considered**:
- `python-json-logger`: simpler setup but less composable; processors must be added manually; less ergonomic for adding per-request context (e.g., request ID)
- Standard `logging` + custom formatter: works but requires more boilerplate to emit valid JSON consistently across all loggers

---

## Decision 7: Rate Limiting

**Decision**: `slowapi` (wraps the `limits` library for FastAPI/Starlette)

**Rationale**: Designed specifically for FastAPI; decorator-based application per route or globally; in-memory storage backend sufficient for single-server deployment; returns 429 with `Retry-After` header automatically.

**Alternatives considered**:
- `fastapi-limiter`: requires Redis as the storage backend — adds a dependency for a single-server deployment
- Custom middleware: possible but slowapi is well-maintained and saves the implementation effort

---

## Decision 8: Configuration Management

**Decision**: `pydantic-settings` (`BaseSettings`)

**Rationale**: Type-safe env var loading; validates all required secrets at startup before any network calls are made (fail-fast per spec edge case); `.env` file support out of the box; integrates naturally with Pydantic v2 models used throughout FastAPI. Missing required vars (e.g., `INSTA_USERNAME`) raise a clear `ValidationError` on startup.

**Alternatives considered**:
- `python-dotenv` + `os.environ`: no type validation; missing vars only fail at the point of use, not at startup
- Hardcoded defaults: prohibited by FR-028

---

## Decision 9: TypeScript Seed Export Runner

**Decision**: `tsx` (npm package)

**Rationale**: Runs TypeScript source files directly without a compilation step; fast startup; respects the existing `tsconfig.json`; the existing `package.json` already has a `devDependencies` section where `tsx` can be added. The export script (`scripts/export-seed-data.ts`) imports the existing data modules and writes JSON — one command, no build artifact.

**Alternatives considered**:
- `ts-node`: slower startup; requires additional `tsconfig-paths` for path aliases
- Compile first (`tsc`) then run: two-step process; generates `.js` files that need cleanup
- Port data to Python directly: tedious manual translation; doesn't stay in sync with future TS edits

---

## Decision 10: Email Notification for Session Errors

**Decision**: Python `smtplib` (stdlib) with environment-configured SMTP

**Rationale**: No external dependency needed; the notification is a one-shot fire-and-forget on session error. `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` are read from env. If SMTP is not configured, the email step is skipped and the error is logged only (per spec Assumptions).

**Alternatives considered**:
- SendGrid / Mailgun SDK: adds a third-party dependency for a low-frequency notification; overkill
- AWS SES: requires AWS credentials; not justified at this scale
