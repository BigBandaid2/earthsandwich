# Tasks: Ingestion Pipeline

**Input**: Design documents from `specs/003-ingestion-pipeline/`
**Prerequisites**: plan.md ✓, spec.md ✓, data-model.md ✓, research.md ✓, quickstart.md ✓
**Depends on**: `specs/002-database-backend/` Phases 1–3 complete (schema + seed) plus Phase 2 ORM models for `instagram_posts` and `substack_posts`

**Tests**: Not explicitly requested — no test tasks generated. The 002 `tests/` skeleton is reused.

> Task IDs and Phase 5/7/9 numbering inherited from the original `002-data-ingestion/tasks.md` to preserve traceability with prior research and prior commits. Phases are renumbered sequentially (1, 2, 3) within this spec for readability; the original 002 phase numbers are noted in parentheses.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to

---

## Phase 1 (formerly 002 Phase 5): User Story 1 — Instagram Ingestion (Priority: P1) 🎯 MVP

**Goal**: Automatically ingest new Instagram posts on a recurring schedule; geocode locations via Claude only; download media; assign stops to trips.

**Independent Test**: Set up credentials; trigger `python -m app.ingestion.instagram`; verify new stop + instagram_post records appear in DB with location, lat, lng, region_code, and media_url set. Re-run → zero new records. Test with a post that has a tagged location and one that does not.

- [ ] T028 [US1] Create backend/app/ingestion/location.py implementing Claude-only IATA determination: (a) **tagged location path** — when instagrapi provides a location name, pass name + lat + lng to Claude and ask only for the IATA code of the nearest in-country international airport; store tagged name/coords verbatim without modification; (b) **no-tag path** — call Claude with the post caption, base64-encoded image (IMAGE posts), and the location strings of up to 5 most-recently-ingested stops; prompt must explicitly instruct Claude to identify the location from observable content (visible signage, landmarks, recognizable geography) and not make a generic estimate; expect JSON `{"location": ..., "lat": ..., "lng": ..., "region": "IATA"}`. In both paths: if Claude returns invalid JSON, store raw text as location name with null lat/lng/region_code and log a warning.
- [ ] T029 [US1] Create backend/app/ingestion/instagram.py: authenticate via persisted instagrapi session file (INSTAGRAPI_SESSION_FILE); query DB for the most recent instagram_post.timestamp; fetch only posts newer than that timestamp from account feed; process oldest-first; skip any post already present by instagram_id (idempotency check, FR-022)
- [ ] T030 [US1] Add location resolution calls to backend/app/ingestion/instagram.py: for each new post call location.py (T028) to get location string, lat, lng, and region_code; log a warning and set region_code=null if determination fails; never abort remaining posts due to location failure (FR-019, FR-020)
- [ ] T031 [US1] Add trip assignment logic to backend/app/ingestion/instagram.py per FR-040: (1) query trips where start_date ≤ post.timestamp ≤ end_date; (2) if multiple matches, pick trip with most recent created_at; (3) if no match, assign to trip id="miscellaneous-adventures"; (4) if that trip is absent, log ERROR and halt ingestion without writing any records
- [ ] T032 [US1] Add media download to backend/app/ingestion/instagram.py: download IMAGE to public/media/<stop_id>.jpg or VIDEO to public/media/<stop_id>.mp4; store relative path in instagram_post.media_url; on download failure log a WARNING, store empty string in media_url, and continue processing remaining posts (FR-021)
- [ ] T033 [US1] Add Instagram Graph API fallback to backend/app/ingestion/instagram.py: when instagrapi raises a non-session exception and INSTAGRAM_GRAPH_API_TOKEN is set, re-attempt fetch via Graph API and log a WARNING; if fallback also fails, log ERROR and exit without modifying existing records (FR-043)
- [ ] T034 [US1] Add session error handling to backend/app/ingestion/instagram.py: catch instagrapi session/authentication exceptions; send SMTP email to automation@datacommlab.com with subject `[travelogue] Instagram session error` and body containing error message + timestamp (skip email if SMTP_HOST not configured); then attempt Graph API fallback if INSTAGRAM_GRAPH_API_TOKEN is set; exit cleanly if both fail (FR-044)
- [ ] T035 [US1] Create backend/app/cli/manage.py with `python -m app.cli.manage login` command: prompt interactively for INSTA_USERNAME and INSTA_PASSWORD, authenticate via instagrapi, persist session to INSTAGRAPI_SESSION_FILE (FR-041)
- [ ] T036 [US1] Create backend/app/ingestion/scheduler.py with APScheduler BackgroundScheduler; register Instagram ingestion job at interval from INSTAGRAM_POLL_INTERVAL_MINUTES (default 60); wire scheduler.start() and scheduler.shutdown() into the FastAPI lifespan hook in backend/app/main.py

**Checkpoint**: US1 complete — new Instagram posts are automatically ingested every hour; verify with quickstart.md sections 2–3.

---

## Phase 2 (formerly 002 Phase 7): User Story 2 — Substack Ingestion (Priority: P2)

**Goal**: Automatically ingest new Substack articles from RSS feed; store with null stop_id pending manual assignment.

**Independent Test**: Configure SUBSTACK_RSS_URL; trigger `python -m app.ingestion.substack`; verify new substack_post records appear (stop_id=null). Re-run → zero new records. Set SUBSTACK_RSS_URL to an unreachable URL → verify clean exit and logged error.

- [ ] T042 [US2] Create backend/app/ingestion/substack.py: fetch RSS via feedparser from SUBSTACK_RSS_URL; for each entry not already in DB (matched by substack_id = guid or link), create substack_post with title, subtitle (from description), body (from content:encoded), published_at (from pubDate), and stop_id=null; use INSERT ON CONFLICT DO NOTHING for idempotency (FR-025); log error and exit cleanly if feed is unreachable (FR-026)
- [ ] T043 [US2] Register Substack ingestion job in backend/app/ingestion/scheduler.py at interval from SUBSTACK_POLL_INTERVAL_MINUTES (default 60); ensure it starts alongside the Instagram job in the FastAPI lifespan

**Checkpoint**: US2 complete — Substack articles are ingested automatically; verify with quickstart.md section 3.

---

## Phase 3 (formerly 002 Phase 9, partial): Polish & Cross-Cutting Concerns

**Purpose**: Align supporting artifacts with the Claude-only IATA decision and harden the location prompt.

- [ ] T048 [P] Remove AIRPORT_API_KEY from .env.example (002), backend/app/config.py optional vars (002), and quickstart.md section 1 env block; update 002 plan.md ingestion/location.py comment from "Airlabs IATA lookup + Claude inference fallback" to "Claude-only IATA determination and location inference"; update 002 quickstart.md to reflect that ANTHROPIC_API_KEY is required for all location logic
- [ ] T049 [P] Refine Claude prompt engineering in backend/app/ingestion/location.py: add few-shot examples of specific vs. generic responses; require the model to cite visible evidence (text, landmarks) when inferring location; add a confidence field to the response schema; log a WARNING when confidence is low

---

## Phase 17: Drift Reconciliation (2026-05-25 weekly scan)

**Status**: Backfill of prototype work for the location module (T028) and CLI login (T035), plus test scaffolding that landed before the implementation tasks. Work lives in `scripts/instagram-fetch-latest/` rather than the planned `backend/app/ingestion/` — patterns (instagrapi session resume, challenge handler, fence-strip parser, dual-path branching) should port over when backend implementation begins.

- [x] T100 Standalone-execution prep on `scripts/instagram-fetch-latest/load_posts_tsv.py`: UTF-8 stdout, token redaction, JSON fence stripping, env var rename. Commit: `504c617`.
- [x] T101 Pivot `load_posts_tsv.py` to instagrapi as primary fetcher with dual-path location logic (FR-016, FR-019, FR-020 prototyped). Adds `instagrapi` session resume + interactive `_challenge_code_handler`. Commit: `a5f5d9f`.
- [x] T102 Add live integration smoke test + `tests/` scaffolding with CI/CD wiring notes. Commit: `2629535`.
- [x] T103 Add 21 unit tests for `get_region_only_via_claude` and `get_location_via_claude` with mocked Anthropic. Commit: `8feb24e`.
- [x] T104 Extract `process_media(...)` from `main()` + 22 unit tests covering dual-path branching, media URL/type, timestamp, path normalization, field extraction. Commit: `df40169`.
- [x] T105 Retire FR-043 / T033 (Graph API fallback) per the 2026-05-25 spec amendment. `spec.md`, `quickstart.md`, and `research.md` updated; `tasks.md` T033 left in place per Cardinal Rule #1, but is now a no-op for the implementation phase.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1)**: Depends on 002 Phases 1–3 (skeleton, schema, seeded `trips` with `miscellaneous-adventures`)
- **Phase 2 (US2)**: Depends on 002 Phases 1–3; T043 depends on T036 from Phase 1 (scheduler must exist)
- **Phase 3 (Polish)**: Depends on Phase 1 implementation; T048 touches 002 supporting artifacts only (safe to run any time)

### Within Each Phase

- T028 (location.py) → T029, T030 (instagram.py uses location.py)
- T036 (scheduler.py) → T043 (Substack job registered in same scheduler)

### Parallel Opportunities

- T028 and T035 (location.py and manage.py CLI): no shared files
- T048 and T049 in Phase 3: parallel (different files)

---

## Implementation Strategy

### MVP First (US1)

1. Complete 002 Phases 1–3 (prerequisite)
2. Build T028 (Claude location module)
3. Build T029–T034 (Instagram ingestion + fallbacks)
4. Build T035 (CLI login)
5. Build T036 (scheduler) and verify hourly runs

### Then Substack (US2)

6. Build T042–T043

### Polish

7. Run T048 (artifact cleanup in 002) and T049 (prompt hardening) before declaring the pipeline production-ready

---

## Notes

- **[P]** = different files, no incomplete dependencies; safe to run in parallel
- **[Story]** label maps each task to a specific user story for traceability
- T028 (location.py) must use Claude exclusively for IATA determination; no external airport API
- T048 touches 002 supporting artifacts — coordinate with whoever is finishing 002 Phase 8 (containerization) to avoid merge conflicts in `.env.example` / `quickstart.md`
- Commit after each task or logical group
