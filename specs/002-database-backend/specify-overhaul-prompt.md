# /speckit.specify input prompt — 002 overhaul (DRAFT)

> Edit the **Vision** section freely. The **Context** sections are background
> for `/speckit.specify` to read; trim them if needed but don't let them grow.
> After you're satisfied, paste the whole document as input to `/speckit.specify`.

---

## Context — original 002 scope (split from `002-data-ingestion` on 2026-05-22)

When 002 was carved out of the original monolithic `002-data-ingestion` spec, the assumed scope was:

- **PostgreSQL schema** for four tables: `trips`, `stops`, `instagram_posts`, `substack_posts`. Stop rows include a `sequence_order` integer for ordered rendering.
- **Two-step seed pipeline**: a `tsx` TypeScript export script writes JSON; a Python `seed.py` reads JSON and inserts records, then `pg_dump`s to `scripts/seed-dump.sql`.
- **REST read API** (`GET /trips`, `GET /trips/:id`, `GET /stops`, `GET /instagram-posts`, `GET /substack-posts`) using FastAPI + SQLAlchemy 2.0 async.
- **Write API** for trip management (`POST /trips`, `PUT /trips/:id`) and recording region end dates (`POST /regions/end-date`), guarded by a bearer token.
- **Docker Compose stack** starting backend + frontend + database with `docker compose up`; database pre-populated from `scripts/seed-dump.sql`.
- Config via `pydantic-settings`; structured JSON logs via `structlog`; slowapi rate limiting.
- INSTA_USERNAME/INSTA_PASSWORD listed as required backend env vars (inherited from the pre-split 002 where the backend ran the ingestion scheduler).

## Context — what's been built and decided since (as of 2026-05-29)

### Shipped work (completed tasks in tasks.md Phases 1–4, 8 partial, 10, 11)

1. **Full directory skeleton**, `requirements.txt`, Alembic config, and project setup are in place (Phase 1, T001–T005).

2. **ORM models + initial migration** for all four tables are deployed and working. `sequence_order` was **removed** from the `stops` table — stop ordering is now derived from `(trip_id, date, region_code)`. This is already in the migration and the ORM model; the original spec's FR-003 and Assumptions still reference `sequence_order` erroneously (they must be corrected in the new spec). (T021)

3. **Full seed pipeline** (T019–T022): `scripts/export-seed-data.ts` exports all TypeScript data to JSON; `scripts/seed.py` inserts records and writes `scripts/seed-dump.sql` via `pg_dump`. All seed tasks are complete and verified.

4. **Full REST read API** (T023–T027): `GET /trips`, `GET /trips/:id`, `GET /stops`, `GET /instagram-posts`, `GET /substack-posts` are implemented, registered, and returning correctly structured responses. Unit tests (T052–T055) cover all read endpoints; a pytest conftest with async test client and mock factory helpers exists in `backend/tests/conftest.py`.

5. **Backend Dockerfile** exists and passes Docker connectivity verification (T044, T047).

6. **`docker-compose.db.yml`** (Postgres-only stack, used during seed development) was committed as a dev convenience; it has been superseded by the full `docker-compose.yml` and can be treated as ephemeral infrastructure. The full `docker-compose.yml` exists at the project root but does not yet include a frontend service (T045–T046 are incomplete).

7. **Frontend API integration** (Phase 11, T056–T062) is fully complete — the frontend now calls the backend API exclusively, with no hardcoded TypeScript data imports at runtime. **However, this work belongs in spec 001, not spec 002.** The new 002 spec should explicitly declare frontend-side changes out of scope and reference spec 001 for that work.

8. **`backend/session.json` was committed** during the seed-script development window (commit `ce55532`). It may contain real instagrapi auth state (an Instagram session belonging to the 003 pile-app). This is a **security concern**: the file should be added to `.gitignore` before the branch is pushed to a public remote. This is a pile-app credential — not a 002 concern architecturally — but it needs to be resolved on this branch.

### Decisions and clarifications since the split

- **No ingestion credentials in 002.** `INSTA_USERNAME`, `INSTA_PASSWORD`, and `SUBSTACK_RSS_URL` are pile-app concerns (spec 003). The 002 backend requires only `DATABASE_URL`, `API_SECRET_KEY`, `FRONTEND_ORIGIN`, and optionally `LOG_LEVEL` / `ENVIRONMENT`. The new spec should reflect this.
- **Tests are now in scope.** The original spec's header said "Tests: Not explicitly requested." That is no longer true — unit tests for the read API (T052–T055) were written and are tracked in tasks.md. The new spec should acknowledge that a test suite exists and is expected to grow.
- **`sequence_order` is permanently gone.** Stop ordering is by `(trip_id, date, region_code)`. The new spec must not reference `sequence_order` anywhere.
- **Frontend API integration is a spec 001 concern.** US7 shipped in this branch but should live in spec 001's spec/tasks. The new 002 spec should note its completion as a dependency satisfied for 001 and remove it from 002's scope.

### Still not built (outstanding planned work)

- **Trip management write API** (Phase 6, T037–T041): `POST /trips`, `PUT /trips/:id`, `POST /regions/end-date`, and the bearer-auth dependency. The `POST /regions/end-date` contract is not yet defined in `contracts/api.md`. These are P2 priority.
- **Frontend Dockerfile and full `docker-compose.yml`** (Phase 8, T045–T046): The frontend service is missing from the compose stack. P3.
- **`GET /health` endpoint and end-to-end validation** (Phase 9, T050–T051): Health check endpoint and full-stack smoke test against `quickstart.md`. P3.

---

## Vision — what the new 002 spec should cover

> Rewrite this section freely. The bullets below are a first-pass starting
> point; trim, add, reframe at will.

The new 002 spec should describe the **persistence layer and REST API for the Earth Sandwich travelogue** — scoped tightly to schema, seeding, read API, write API, containerization, and observability. It does not own any ingestion logic (that is spec 003), any frontend rendering (that is spec 001), or any data-normalization ETL from the pile (that is the planned bridge-app spec — see [`docs/roadmap.md`](../../docs/roadmap.md)).

**In scope:**

- **PostgreSQL schema** for `trips`, `stops`, `instagram_posts`, `substack_posts`. Stop ordering is by `(trip_id, date, region_code)`; there is no `sequence_order` column. The `region_code` column on stops holds a 3-letter IATA code computed upstream by the pile-app (003) and written into this column by the planned bridge-app.
- **Two-step seed pipeline**: TypeScript export → Python import → `pg_dump`. Already complete; the spec should capture the design as-shipped and the acceptance criteria for its correctness.
- **REST read API** (FastAPI, SQLAlchemy 2.0 async, asyncpg): `GET /trips`, `GET /trips/:id`, `GET /stops`, `GET /instagram-posts`, `GET /substack-posts` with the filter contracts already in `contracts/api.md`. Already complete.
- **Unit test suite** for the read API (pytest-asyncio, httpx AsyncClient, AsyncMock for DB). Tests exist for all read endpoints. The new spec should include testing as an explicit requirement.
- **Write API** for trip management and region end-date recording. `POST /trips` (201), `PUT /trips/:id` (200 partial update), and `POST /regions/end-date` (all params optional with smart defaults). All write endpoints require bearer-token auth. The region end-date contract and storage strategy still need to be defined before implementation can proceed.
- **Docker Compose stack** starting backend + Postgres + frontend with `docker compose up`; Postgres pre-populated from `scripts/seed-dump.sql` on first start; data persists across restarts via a named volume. Backend Dockerfile exists; frontend Dockerfile and the compose frontend service are still outstanding.
- **`GET /health`** endpoint returning `{"status": "ok"}` for Docker Compose health checks.
- **Config** via `pydantic-settings`; required env vars: `DATABASE_URL`, `API_SECRET_KEY`, `FRONTEND_ORIGIN`; optional: `LOG_LEVEL`, `ENVIRONMENT`. No ingestion credentials.
- **Structured JSON logging** via `structlog` (production) / ConsoleRenderer (development).
- **Rate limiting** (slowapi): 60 req/min per IP → 429.
- **Security**: CORS per `FRONTEND_ORIGIN`; HTTPS enforced in production; no secrets in code; structured error responses with no internal detail leakage; input validation via Pydantic.

**Out of scope (delegate to other specs):**

- Any Instagram or Substack ingestion logic — that is spec 003 (pile-app).
- Frontend rendering, components, API client, hooks, adapters — that is spec 001. (Phase 11 / US7 shipped on this branch and should be recorded as complete in spec 001.)
- Data normalization, stop linkage, IATA derivation, trip auto-assignment — those belong in the planned bridge-app spec.
- Object storage / S3, email notifications, APScheduler jobs inside the backend process.

**Additional notes and open questions for the overhaul:**

- The `POST /regions/end-date` endpoint contract (storage model, migration) still needs to be decided; the spec should acknowledge this as a design task that precedes implementation (as the current tasks.md already documents via T037).
- The spec should call out the `backend/session.json` security concern — even though it is not a 002 artifact architecturally, it was committed on this branch and needs to be addressed before a public push.
- The spec should explicitly state that `sequence_order` was removed from the schema in the initial migration phase and must not be re-introduced.
- The new spec should acknowledge the existing unit tests (T052–T055 in tasks.md) and set an expectation that new endpoints and behaviors should have corresponding test coverage.

**Designer notes and addendums: Points here take precedence over any contradictions with above**

- Backend coding work should follow Test Driven Development principles.
- There is a new feature request, for using an LLM to assist with trip planning and suggest adjustments. One such use case is to check for festivals and holidays (like Rio de Janeiro's Carnival) near the planned trip date/locations and suggest shifting dates around should one fall near but just outside the planned itinerary. To facilitate this, work needs to be done to research and implement an MCP for making such requests.