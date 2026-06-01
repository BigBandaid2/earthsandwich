# Research: Database & Backend

**Phase**: 0 | **Plan**: [plan.md](plan.md) | **Date**: 2026-05-12 (trimmed 2026-05-22 for the 002 split)

> Ingestion-related decisions (Instagram library, scheduler, IATA determination, email notification) moved to `003-ingestion-pipeline/research.md`.

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

## Decision 3: Structured Logging

**Decision**: `structlog` with `JSONRenderer` in production, `ConsoleRenderer` in development

**Rationale**: structlog is the gold standard for structured logging in Python. Its processor pipeline model cleanly handles adding `timestamp`, `level`, `message`, and `logger` to every log entry (FR-042). The `ConsoleRenderer` in development gives human-readable output; `JSONRenderer` in production emits newline-delimited JSON to stdout for Docker log drivers. FastAPI's `uvicorn` access logs are also captured by structlog.

**Alternatives considered**:
- `python-json-logger`: simpler setup but less composable; processors must be added manually; less ergonomic for adding per-request context (e.g., request ID)
- Standard `logging` + custom formatter: works but requires more boilerplate to emit valid JSON consistently across all loggers

---

## Decision 4: Rate Limiting

**Decision**: `slowapi` (wraps the `limits` library for FastAPI/Starlette)

**Rationale**: Designed specifically for FastAPI; decorator-based application per route or globally; in-memory storage backend sufficient for single-server deployment; returns 429 with `Retry-After` header automatically.

**Alternatives considered**:
- `fastapi-limiter`: requires Redis as the storage backend — adds a dependency for a single-server deployment
- Custom middleware: possible but slowapi is well-maintained and saves the implementation effort

---

## Decision 5: Configuration Management

**Decision**: `pydantic-settings` (`BaseSettings`)

**Rationale**: Type-safe env var loading; validates all required secrets at startup before any network calls are made (fail-fast per spec edge case); `.env` file support out of the box; integrates naturally with Pydantic v2 models used throughout FastAPI. Missing required vars raise a clear `ValidationError` on startup.

**Alternatives considered**:
- `python-dotenv` + `os.environ`: no type validation; missing vars only fail at the point of use, not at startup
- Hardcoded defaults: prohibited by FR-028

---

## Decision 6: TypeScript Seed Export Runner

**Decision**: `tsx` (npm package)

**Rationale**: Runs TypeScript source files directly without a compilation step; fast startup; respects the existing `tsconfig.json`; the existing `package.json` already has a `devDependencies` section where `tsx` can be added. The export script (`scripts/export-seed-data.ts`) imports the existing data modules and writes JSON — one command, no build artifact.

**Alternatives considered**:
- `ts-node`: slower startup; requires additional `tsconfig-paths` for path aliases
- Compile first (`tsc`) then run: two-step process; generates `.js` files that need cleanup
- Port data to Python directly: tedious manual translation; doesn't stay in sync with future TS edits
