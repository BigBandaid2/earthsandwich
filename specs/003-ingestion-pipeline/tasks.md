# Tasks: Ingestion Pipeline App

**Input**: Design documents from `specs/003-ingestion-pipeline/`
**Prerequisites**: plan.md ✓, spec.md ✓, data-model.md ✓, research.md ✓, quickstart.md ✓, contracts/ ✓

**Tests**: Not explicitly requested for new phases. Existing test suite (`scripts/instagram-fetch-latest/tests/`, 79 unit tests + 1 integration) migrates with the code and remains the regression gate. Specific FR-targeted validation tasks (SC-010, SC-011, FR-101, FR-107) are included as their own non-unit-test items.

> **2026-05-29 update**: Phases 1–3 (T028–T049) — the original envisioned tasks targeting backend integration (writing into 002's tables, APScheduler inside the FastAPI process, SMTP email on session error, etc.) — were removed per the Cardinal Rule #1 nuance ("envisioned-but-not-started tasks MAY be discarded during a spec overhaul"). They reflected the pre-2026-05-27 scope that the spec re-author superseded. Phase 17 (Drift Reconciliation, 2026-05-25 scan) is preserved unchanged — its tasks are completed. New phases 18+ reflect the App-shaped spec and the 2026-05-29 `/speckit.plan` design artifacts.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to

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

## Phase 18: Setup — pile-app/ skeleton

**Purpose**: Stand up the App root directory and packaging so subsequent migration tasks have a destination.

- [X] T200 Create `pile-app/` directory at repo root with subdirs: `instagram/`, `instagram/validation/`, `substack/`, `common/`, `tests/`, `pile/`, `pile/media/instagram/`, `logs/`
- [X] T201 [P] Create `pile-app/pyproject.toml` with project metadata, console_scripts entry `pile_app = cli:main` (flat-layout reconciliation — see Phase 18 note), and a Python 3.14 floor
- [X] T202 [P] Create `pile-app/requirements.txt` enumerating: instagrapi, anthropic, requests, python-dotenv, feedparser, APScheduler, PyYAML, pytest
- [X] T203 [P] Create `pile-app/.env.example` with documented placeholders for `INSTA_USERNAME`, `INSTA_PASSWORD`, `ANTHROPIC_API_KEY`, optional `ANTHROPIC_MODEL`
- [X] T204 [P] Create `pile-app/.gitignore` with patterns: `.env`, `pile/`, `logs/`, `instagrapi_session.json`, `venv/`, `__pycache__/`, `*.pyc`
- [X] T205 [P] Create `pile-app/README.md` with App-level overview, install instructions linking to `specs/003-ingestion-pipeline/quickstart.md`, and the FR-110/FR-111 portability note

> Phase 18 implementation note (2026-05-29): T200 prescribed a flat directory layout (`pile-app/instagram/`, `pile-app/substack/`, `pile-app/common/`) but T201 originally specified `pyproject.toml` console_scripts entry `pile_app = pile_app.cli:main` — implying a wrapped `pile-app/pile_app/` package. The two were inconsistent. Resolved in favor of the flat layout per T200 (the structural source of truth). Console_scripts entry adjusted to `pile_app = cli:main`. Consequence: the `python -m pile_app ...` invocation pattern documented in `quickstart.md` and `contracts/cli.md` no longer works directly; the equivalents are `pile_app ...` (after `pip install -e .`) or `python cli.py ...` (dev, from inside `pile-app/`). Updating those docs is a follow-up before Phase 19 closes.

**Checkpoint**: Skeleton exists; nothing functional yet.

---

## Phase 19: Foundational — migrate Instagram service into pile-app/

**Purpose**: Move the existing `scripts/instagram-fetch-latest/` code into the new App root and split the monolithic `load_posts_tsv.py` into per-service + common modules. Required before any user story phase can begin.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete. Per FR-110/FR-111 the migration is what makes the App physically self-contained.

- [X] T206 Split `scripts/instagram-fetch-latest/load_posts_tsv.py`'s instagrapi auth + session resume into `pile-app/instagram/instagrapi_client.py`
- [X] T207 Split the dual-path orchestration loop (page fetch, per-post processing, write-then-advance) into `pile-app/instagram/pipeline.py`
- [X] T208 [P] Extract the FR-019 tagged-path canonicalization into `pile-app/instagram/tagged_location.py`
- [X] T209 [P] Extract the FR-020 inferred-path + fallback into `pile-app/instagram/inferred_location.py`
- [X] T210 [P] Extract TSV read/write + sort+reid + orphan-sweep helpers into `pile-app/common/pile.py`
- [X] T211 [P] Extract LLM SDK wrapper + JSON-and-prose parser into `pile-app/common/inference.py`
- [X] T212 [P] Extract rate presets + jittered sleep + challenge detection into `pile-app/common/anti_throttle.py`
- [X] T213 [P] Extract per-run log file + 5-most-recent sweep into `pile-app/common/run_logging.py`
- [X] T214 Create top-level CLI entry at `pile-app/cli.py` exposing `pile_app run instagram <target>` (post-pip-install) or `python cli.py run instagram <target>` (dev). Note: the `python -m pile_app ...` form documented in `quickstart.md` and `contracts/cli.md` doesn't work with the flat layout chosen in Phase 18; updating those docs is deferred to Phase 26 polish (T249)
- [X] T215 Moved existing pile data: `posts.ourearthsandwich.local.tsv` + `posts.welawen.local.tsv` → `pile-app/pile/` (with `media_url` column path rewrite `public/media/` → `pile/media/instagram/`); `public/media/ourearthsandwich_*` + `public/media/welawen_*` (1016 files) → `pile-app/pile/media/instagram/`; `scripts/instagram-fetch-latest/instagrapi_session.json{,.bak}` → `pile-app/`
- [X] T216 Moved Instagram validation scaffolding: repo-root `posts.local.tsv` → `pile-app/instagram/validation/posts.local.tsv`; `docs/planning/scrape-diff.txt` + `scrape-diff-v3.txt` + `scrape-diff-v4.txt` → `pile-app/instagram/validation/`
- [X] T217 Moved tests: `scripts/instagram-fetch-latest/tests/` → `pile-app/tests/instagram/`. Updated monkeypatches to target import sites in `instagram.pipeline` (download_media, canonicalize_tagged_location, infer_post_location), `common.inference.anthropic` (Anthropic client class), and `common.pile.APP_ROOT` (replacing `load_posts_tsv.PROJECT_ROOT`). Added `pile-app/tests/conftest.py` to wire sys.path + dummy `ANTHROPIC_API_KEY`
- [X] T218 Updated repo-root `README.md` (Apps section + project layout + pile-app section), `docs/roadmap.md` (004 spec reference to `pile-app/tests/`). Repo-root `.gitignore`'s `instagrapi_session.json` and `public/media/` patterns left in place as defense-in-depth (no longer-active patterns but harmless). `CLAUDE.md` already updated in earlier phase
- [X] T219 Ran `cd pile-app && pytest tests/instagram` → **85 passed, 1 skipped** (the integration test, which requires `INSTA_USERNAME`/`INSTA_PASSWORD`/`ANTHROPIC_API_KEY` — skipped automatically without them)
- [X] T220 Deleted `scripts/instagram-fetch-latest/` (including the local venv — operator needs to recreate at `pile-app/venv` via `pip install -e .`). Preserved `export_posts_json.py` at `scripts/export_posts_json.py` since the frontend still depends on the public/posts.json data path; updated its DEFAULT_INPUT to point at the new truth-file location (`pile-app/instagram/validation/posts.local.tsv`) — flagged as a transitional cross-App-boundary read until the bridge-app replaces it

**Checkpoint**: All Instagram-service behaviour preserved; codebase now satisfies the App-root structural property of FR-110/FR-111.

---

## Phase 20: User Story 1 — Scrape a target Instagram account into the pile (Priority: P1) 🎯 MVP

**Goal**: Formalize the in-place Instagram scrape to match the spec re-author. Add the missing verbatim-input columns (Cardinal Rule #4), shift dedup to the canonical `shortcode`, add upstream-deletion tombstoning.

**Independent Test**: Quickstart §"Run a real first-scrape" — configure crawler creds + a small public target, run `python -m pile_app run instagram <target>`, verify TSV has the new column shape and media files use `<target>_<shortcode>.ext` naming. Re-run; verify zero new rows.

- [ ] T221 [P] [US1] Add `tag_verbatim` column to the Instagram TSV writer in `pile-app/common/pile.py` (column 4 per data-model.md)
- [ ] T222 [P] [US1] Add `lat_verbatim` + `lng_verbatim` columns to the Instagram TSV writer in `pile-app/common/pile.py` (columns 5–6)
- [ ] T223 [US1] Wire `tag_verbatim` + `lat_verbatim` + `lng_verbatim` population into `pile-app/instagram/tagged_location.py` so the verbatim instagrapi `Media.location.{name,lat,lng}` triple is written BEFORE the canonicalization LLM call dispatches
- [ ] T224 [US1] Migrate dedup key from numeric `instagram_id` to `shortcode` in `pile-app/common/pile.py` (re-read existing TSV rows, key the in-memory dedup set on column 3 not column 2)
- [ ] T225 [US1] Rename media file scheme from `<target>_<id>.<ext>` to `<target>_<shortcode>.<ext>` in `pile-app/instagram/pipeline.py` (download step) and `pile-app/common/pile.py` (sort+reid post-pass: stop renaming media files, since the on-disk name is now stable per `shortcode`)
- [ ] T226 [US1] Add `deleted_upstream` + `deleted_upstream_at` columns (15–16) to the Instagram TSV writer; default empty on row creation
- [ ] T227 [US1] Implement incidental deletion detection (FR-106) in `pile-app/instagram/deletion_detection.py`: on each fetched page, compare its timestamp range against existing pile rows; mark `deleted_upstream=true` + `_at=<now>` for any row whose `shortcode` is absent from the fetched page despite its timestamp falling in the page's range
- [ ] T228 [US1] One-time backfill: re-process `pile-app/pile/posts.ourearthsandwich.local.tsv` + `pile-app/pile/posts.welawen.local.tsv` to populate the new verbatim columns and rename media files to use `<shortcode>` (re-run with `--backfill` flag or write a one-shot migration script at `pile-app/instagram/migrate_2026_05_29.py` that's deleted after use)

**Checkpoint**: US1 complete — the Instagram service produces TSVs matching the data-model.md schema; existing pile data is conformant; dedup is shortcode-keyed; tombstoning works.

---

## Phase 21: User Story 2 — Pipeline service survives upstream throttling (Priority: P1)

**Goal**: Document the in-place anti-throttle + resilience implementation against the formalized spec, plug the remaining gaps (inference-exhaustion handling, ETA accuracy verification).

**Independent Test**: Inject a transient error mid-pagination via a test fixture; verify backoff + retry. Inject a hard-block challenge; verify clean halt + operator-facing prompt + preserved pile state. Inject inference rate-limit; verify same hard-block treatment.

- [ ] T229 [US2] Add inference-exhaustion handling to `pile-app/instagram/inferred_location.py`: catch `anthropic.RateLimitError`, `anthropic.AuthenticationError`, and credit-exhaustion responses; treat as hard-block per FR-052 + edge-case bullet (halt, no retry, surface operator-facing prompt, preserve pile state)
- [ ] T230 [US2] Verify ETA accuracy (SC-008) by inspecting recent run logs in `pile-app/logs/`: confirm ≥80% of runs fall within ±30% of the start-of-run ETA; if below the threshold, adjust the per-page time estimate in `pile-app/common/anti_throttle.py` against the active rate-preset
- [ ] T231 [US2] Audit `pile-app/instagram/pipeline.py`'s transient-vs-hard error categorization (FR-052) — make sure connection-reset / 5xx flows through the single-retry-with-backoff path, while challenge_required / checkpoint_required / login_required flows through the immediate-halt path with no retry

**Checkpoint**: US2 complete — the service correctly halts on hard blocks, retries transients once, and surfaces operator prompts.

---

## Phase 22: User Story 3 — Pile consumed only via bridge-app / physical segregation (Priority: P2)

**Goal**: Make FR-110/FR-111/SC-010/SC-011 testable + enforceable. The Foundational phase already moved the code; this phase verifies the move actually satisfies the segregation properties and locks them in.

**Independent Test**: (a) Run the SC-010 portability check: copy `pile-app/` to an empty dir and confirm tests pass + a scrape runs. (b) Run the SC-011 grep check: confirm no path in `pile-app/` references a directory outside the App.

- [ ] T232 [US3] Create `pile-app/tests/integration/test_portability.py` implementing the SC-010 check: copy the `pile-app/` directory to a temp directory, install requirements in an isolated venv, run `pytest`, assert exit code 0
- [ ] T233 [US3] Create `pile-app/tests/integration/test_self_containment.py` implementing the SC-011 check: grep `pile-app/` source for `\.\./`, absolute paths starting with `C:\workspace` or `/workspace`, and references to known external dirs (`scripts/`, `backend/`, `frontend/`, `public/`); assert zero matches outside the allow-list (`os.path.expanduser`, `/tmp`, network endpoints)
- [ ] T234 [US3] Add an "App Boundary" section to `pile-app/README.md` documenting the bridge-app contract (pile = sole surface; never read directly by other Apps) and pointing readers at `specs/003-ingestion-pipeline/contracts/pile-artifact-instagram.md` + `pile-artifact-substack.md`

**Checkpoint**: US3 complete — the segregation properties are verified by the test suite and explicit to readers.

---

## Phase 23: User Story 4 — Scrape a Substack publication into the pile (Priority: P2)

**Goal**: Add the Substack pipeline service from scratch, following the same App-level conventions as Instagram.

**Independent Test**: Quickstart §"Add a Substack publication" — configure a publication slug, run `python -m pile_app run substack <pub>`, verify TSV at `pile-app/pile/articles.<pub>.local.tsv` matches the data-model.md schema. Re-run; zero new rows. Configure an unreachable URL; verify clean exit + logged error.

- [ ] T235 [US4] Create `pile-app/substack/__init__.py` + `pile-app/substack/pipeline.py` skeleton (service orchestrator with `run()` entry point)
- [ ] T236 [P] [US4] Implement `pile-app/substack/rss_client.py` using `feedparser`: fetch publication's RSS at `https://<slug>.substack.com/feed`, return a list of entry dicts with `<guid>`, `<link>`, `<title>`, `<description>`, `<content:encoded>`, `<pubDate>`
- [ ] T237 [P] [US4] Implement Substack TSV writer in `pile-app/common/pile.py` matching data-model.md columns 1–9; reuse the same TAB-escaping + sort+reid post-pass logic
- [ ] T238 [US4] Wire `pile-app/substack/pipeline.py` end-to-end: poll RSS via T236, dedup against existing pile rows by `substack_id`, write new rows via T237
- [ ] T239 [US4] Implement Substack incidental deletion detection (FR-106) in `pile-app/substack/deletion_detection.py`: any pile row whose `substack_id` is absent from the current feed but whose `published_at` falls within the feed's covered date range gets tombstoned
- [ ] T240 [US4] Add Substack handling to `pile-app/cli.py`: `python -m pile_app run substack <publication>` dispatches into `substack/pipeline.py`
- [ ] T241 [US4] Add Substack-specific tests at `pile-app/tests/substack/` covering: idempotent re-run, unreachable feed error path, RSS-window-cap behaviour

**Checkpoint**: US4 complete — Substack publications scrape end-to-end alongside Instagram.

---

## Phase 24: User Story 5 — Pipeline services run on a recurring schedule (Priority: P3)

**Goal**: Add the in-process scheduler so the operator doesn't have to manually invoke services.

**Independent Test**: Quickstart §"Run on a schedule (in-process)" — configure short-interval schedules in `config.yml`, run `python -m pile_app schedule`, verify each service fires at its configured cadence and produces the expected pile artifacts.

- [ ] T242 [P] [US5] Implement `pile-app/common/scheduler.py` using APScheduler's `BackgroundScheduler` in thread-pool mode (per research.md decision); register each enabled service from `config.yml` as a job; support `interval:` and `cron:` trigger specs
- [ ] T243 [P] [US5] Create `pile-app/config.yml` with default schedules: Instagram = `interval:hours=1` at `normal` preset for the two existing targets; Substack = `cron:hour=6,minute=0` at `aggressive` preset for one default publication
- [ ] T244 [US5] Add `schedule` subcommand to `pile-app/cli.py`: starts the scheduler in the foreground, halts on Ctrl-C, surfaces hard-block exit codes per `contracts/cli.md`
- [ ] T245 [US5] Add a cross-service concurrency test at `pile-app/tests/integration/test_concurrency.py` verifying FR-107: two services with simultaneous schedule fires DO run in parallel (different threads) and within-service work IS sequential (no page-N+1 fetch before page-N persist)

**Checkpoint**: US5 complete — the operator runs `python -m pile_app schedule` once and gets unattended recurring ingestion.

---

## Phase 25: User Story 6 — A new pipeline service is added for a new source (Priority: P3)

**Goal**: Validate FR-101 / SC-005 by codifying the "add a new service" path. No new functional service is added by this story — this is a structural verification + documentation task.

**Independent Test**: Add a stub `pile-app/test_source/` service that writes one fake artifact to `pile-app/pile/fake.test_source.local.tsv`. Verify Instagram and Substack still scrape unchanged; verify zero modifications to either of their files were required.

- [ ] T246 [P] [US6] Add a "Adding a new pipeline service" section to `pile-app/README.md` walking through the required files (`<source>/pipeline.py`, `<source>/__init__.py`, optional `<source>/deletion_detection.py`), CLI registration, `config.yml` entry, and pile namespacing conventions
- [ ] T247 [US6] Create a minimal stub service `pile-app/test_source/pipeline.py` that writes one row to `pile-app/pile/fake.test_source.local.tsv` on invocation; add the corresponding CLI dispatch in `pile-app/cli.py`; verify Instagram + Substack source files were untouched by inspecting the diff (FR-101 / SC-005)
- [ ] T248 [US6] Delete the stub service from T247 once the verification passes (the stub was a probe, not a permanent service; the documented "add a new service" path in T246 is the durable artefact)

**Checkpoint**: US6 complete — the extensibility property is documented and verified.

---

## Phase 26: Polish & Cross-Cutting Concerns

- [ ] T249 [P] Update `specs/003-ingestion-pipeline/quickstart.md` post-migration to reflect the final command shapes (drop "if the migration is complete" caveats once they're inaccurate)
- [ ] T250 [P] Add a `pile-app/instagram/README.md` documenting the service-internal architecture (auth flow, dual-path location resolution, anti-throttle preset semantics)
- [ ] T251 [P] Add a `pile-app/substack/README.md` mirror for the Substack service
- [ ] T252 Mark the truth-baseline + scrape-diff workflow as "to-be-formalized" in `pile-app/instagram/validation/README.md`, with a pointer to the future spec amendment that'll define `python -m pile_app validate ...`
- [ ] T253 Audit that every FR in `spec.md` has at least one task in Phases 18–26 touching its implementation; cross-reference into `jira-mapping.json` (read-only — no PM state added per Cardinal Rule #2)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 17 (Drift Reconciliation)**: Already complete; preserved as historical record.
- **Phase 18 (Setup)**: No dependencies — can start immediately.
- **Phase 19 (Foundational — Migration)**: Depends on Phase 18 completion. Blocks all user-story phases.
- **Phase 20 (US1)** through **Phase 25 (US6)**: All depend on Phase 19 completion; can proceed in parallel afterwards if staffed.
- **Phase 26 (Polish)**: Depends on Phase 25 (or whichever user-story phases are in scope for the increment).

### User Story Dependencies

- **US1 (P1) MVP**: Independent after Phase 19.
- **US2 (P1)**: Independent after Phase 19. Largely already implemented; T229–T231 are gap-fillers.
- **US3 (P2)**: Independent after Phase 19. SC-010 / SC-011 test tasks are verification, not implementation.
- **US4 (P2)**: Independent after Phase 19. Brand-new service; doesn't touch Instagram code.
- **US5 (P3)**: Depends on US1 and US4 existing (otherwise the scheduler has nothing to schedule); the scheduler implementation itself is independent and could be built first as scaffolding.
- **US6 (P3)**: Best deferred to after at least one of US1 / US4 is shipped, since the FR-101 verification is more meaningful with real services in the App.

### Within Each User Story

- T221 + T222 (verbatim column writers) → T223 (population logic uses both columns) → T224 (dedup migration depends on the new writer)
- T235 (Substack skeleton) → T236 + T237 (rss_client + TSV writer) → T238 (wires them together)
- T242 (scheduler.py) → T244 (CLI subcommand registers jobs from scheduler.py)

### Parallel Opportunities

- Phase 18 has 5 [P] tasks (T201–T205) — all separate files, no deps.
- Phase 19 has 6 [P] extraction tasks (T208–T213) — each splits a different concern out of `load_posts_tsv.py` into a new file.
- Phase 23 has 2 [P] tasks (T236 + T237) — `rss_client.py` (new file) and `common/pile.py` extension (existing file but different function area).
- Phase 24 has 2 [P] tasks (T242 + T243) — `scheduler.py` and `config.yml` are independent.
- Phase 25's T246 (README docs) is parallel with any other phase's work.
- Phase 26 has 3 [P] doc-only tasks (T249–T251) parallel with each other.

---

## Implementation Strategy

### MVP path (US1 only)

1. Phase 18 — stand up `pile-app/` skeleton.
2. Phase 19 — migrate code; verify tests pass; delete `scripts/instagram-fetch-latest/`.
3. Phase 20 — formalize Instagram schema (verbatim columns, shortcode dedup, tombstones).
4. **STOP and VALIDATE**: run an incremental scrape on `@ourearthsandwich`; verify the new TSV shape; ship.

### Incremental delivery

1. Setup + Foundational → ready for any story.
2. US1 → Travelogue's primary scrape is on the new App shape.
3. US2 → resilience gaps closed (mostly verification work).
4. US3 → portability guarantees enforced by tests.
5. US4 → Substack lights up.
6. US5 → unattended operation.
7. US6 → extensibility doc + verification.
8. Polish.

### Parallel team strategy

After Phase 19 ships:

- Dev A: US1 (T221–T228) + US3 (T232–T234).
- Dev B: US2 audit (T229–T231) + US4 (T235–T241).
- Dev C: US5 (T242–T245) + US6 (T246–T248).

US3 and US5 both depend conceptually on US1+US4 being real, so phase them late on each dev's queue.

---

## Notes

- **[P]** = different files, no incomplete dependencies; safe to run in parallel.
- **[Story]** label maps each task to a specific user story for traceability.
- Phase 17 IS the historical record per Cardinal Rule #1 — do not modify completed tasks. Phase 1–3 (T028–T049) were removed under the Cardinal Rule #1 nuance for envisioned-but-not-started tasks during a spec overhaul; their content is preserved in git history at commit `e31a233` and prior.
- Commit after each task or logical group.
- The truth-baseline + scrape-diff workflow (T216, T252) is informal until a future spec amendment formalizes it; treat it as scaffolding the Instagram service maintainer keeps, not a public contract.
