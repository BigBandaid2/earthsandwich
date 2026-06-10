# Tasks: bridge-builder-toolkit

**Input**: Design documents from `specs/004-bridge-builder-toolkit/`
**Prerequisites**: plan.md ✓, spec.md ✓ (with Clarifications), research.md ✓, data-model.md ✓, contracts/cli.md ✓, quickstart.md ✓

**Deliverable reminder**: the toolkit produces **validated bridge _specifications_** (a Final Bundle that seeds `/speckit.specify`), NOT a running bridge. The dbt project, materialized output, and oracle round-trip are validation evidence; the target DB stays read-only except the transactional oracle probe.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: parallelizable (different files, no dependency on an incomplete task)
- **[Story]**: the user story a task serves (US1–US6); Setup/Foundational/Polish carry no story label
- Tests: 004 is not TDD; test tasks are included only where a Success Criterion requires explicit validation (oracle synthetic cases, per-story integration acceptance)

---

## Phase 1: Setup

- [ ] T001 Create the `bridge-builder-toolkit/` App root with the dir skeleton (`common/`, `project/`, `analyze/`, `synthesize/`, `oracle/`, `iterate/`, `review/`, `projects/`, `tests/{unit,integration,fixtures}`) per plan.md Project Structure
- [ ] T002 [P] Create `bridge-builder-toolkit/pyproject.toml` (console_scripts `bridge_builder = cli:app`, `py-modules = ["cli"]`, Python 3.12 floor) + `requirements.txt` (typer, ydata-profiling, eralchemy2, dbt-core, dbt-duckdb, duckdb, SQLAlchemy, psycopg[binary], anthropic, PyYAML, filelock, pytest)
- [ ] T003 [P] Create `bridge-builder-toolkit/.env.example` (ANTHROPIC_API_KEY + target-cred env-var name placeholders), `.gitignore` (`projects/`, `venv/`, `.env`, `*.duckdb`, `__pycache__/`), and `README.md` (App overview + GraphViz/Docker/Anthropic prereqs + movability note)
- [ ] T004 Create `bridge-builder-toolkit/cli.py` — Typer app registering all subcommands as stubs (`project create|list`, `analyze pile|target`, `synthesize bridge`, `iterate`, `accept-bundle`, `review`) per contracts/cli.md

**Checkpoint**: App installs (`pip install -e .`); `bridge_builder --help` lists every stage subcommand.

---

## Phase 2: Foundational (blocking prerequisites — no story label)

**⚠️ Every user story depends on this phase.**

- [ ] T005 [P] Implement `bridge-builder-toolkit/common/config.py` — `project.yml` load/save + `BridgeProject` and `ConnectionValidationResult` models per data-model.md (paths relative/env-referenced for movability)
- [ ] T006 [P] Implement `bridge-builder-toolkit/common/locking.py` — per-project PID lockfile acquire/release, reclaimable if the holding PID is dead (FR-110)
- [ ] T007 [P] Implement `bridge-builder-toolkit/common/run_logging.py` — per-run log files under the project folder
- [ ] T008 Implement `bridge-builder-toolkit/common/inference.py` — Anthropic SDK wrapper with **role-based** names (`analyst_layer`, `inferred_columns`, `rationale` — never `claude_*`, Rule #3), input-preserving (persists inputs alongside outputs, Principle V), and a mock-friendly seam for tests
- [ ] T009 Implement `bridge-builder-toolkit/common/playground.py` — single-file HTML builder: inline-data embedding, per-section provenance labels, and a copy-out-a-prompt affordance with clipboard→selectable-textarea fallback (FR-050–054). Shared by US2/US3/US6 playgrounds

**Checkpoint**: config round-trips a project.yml; a project folder can be locked/unlocked; the inference wrapper returns a mocked response in tests; `playground.build()` emits a valid standalone HTML with a working copy button.

---

## Phase 3: User Story 1 — Create a project + validate connections (Priority: P1) 🎯 MVP

**Goal**: A named, isolated project with up-front connection validation — the gate everything downstream scopes to.

**Independent Test**: Run `project create` with valid IG→Travelogue inputs → project folder + `project.yml` + a validation report (both endpoints reachable, per-endpoint read/insert/delete). Re-run with wrong inputs → clear errors, no project state mutated.

- [ ] T010 [US1] Implement `bridge-builder-toolkit/project/create.py` — create `projects/<name>/`, write `project.yml`, run the connection-validation step (pile readable; target reachable + read/insert/delete probes via SQLAlchemy), record per-endpoint status; abort cleanly (no folder) on pile-unreadable / target-unreachable (FR-007/008); reject a non-relational target with a "deferred" message (FR-005 v1 scope); honor `--force` (FR-011); credentials by env-var name only (FR-012)
- [ ] T011 [P] [US1] Implement `bridge-builder-toolkit/project/registry.py` — `project list` printing each project's name, pile path, target endpoint, validation status (FR-010)
- [ ] T012 [US1] Wire `project create` (`--pile`, `--target`, `--target-cred-env`, `--pile-sample`, `--force`) and `project list` into `cli.py`
- [ ] T013 [US1] Integration test `bridge-builder-toolkit/tests/integration/test_project_create.py` — valid IG→Travelogue create against the 002 Docker Postgres → folder + config + validation report; deliberately-wrong inputs → clean abort with no folder (US1 Independent Test; SC-001, SC-017)

**Checkpoint**: US1 independently testable — a validated project exists; the oracle-run-vs-skip decision is recorded.

---

## Phase 4: User Story 2 — Pile & target data-profiling (Priority: P2)

**Goal**: Raw prior-art baselines + enhanced LLM-analyst playgrounds for both sides, with transparent prior-art-vs-toolkit labeling. Writes into the **data-profiling loop** (its own iteration history, independent of bridge-mapping).

**Independent Test**: `analyze pile` + `analyze target` on the validated project produce `pile.ydata-profile.html`, `pile.enhanced.html`, `target.ydata-profile.html`, `target.er-diagram.svg`, `target.enhanced.html` in `data-profiling/iteration-1/`. Raw artifacts are canonical; enhanced sections are labeled baseline/LLM-extended/toolkit-novel.

- [ ] T014 [P] [US2] Implement `bridge-builder-toolkit/analyze/introspect.py` — SQLAlchemy 2.x reflection of the target schema (tables, columns, types, PK/FK, NOT-NULL constraints)
- [ ] T015 [US2] Implement `bridge-builder-toolkit/analyze/pile.py` — run `ydata-profiling` on a sampled pile → `pile.ydata-profile.html` (raw, FR-021); build `pile.enhanced.html` covering ID-candidates, entity classification, pipeline-metadata-vs-source, likely-inferred fields, AI-workflow evidence, public-knowledge enrichment w/ citations, sampled linked-media (FR-023/024) with per-section labels; hard-error (exit 2) if ydata fails (FR-105)
- [ ] T016 [US2] Implement `bridge-builder-toolkit/analyze/target.py` — `ydata-profiling` on the introspected schema → `target.ydata-profile.html`; `eralchemy2` → `target.er-diagram.svg` (raw, FR-101; skipped + label-absent for a non-relational side, FR-027); `target.enhanced.html` with ranked candidate-table reasoning (FR-025/026); missing-GraphViz → clear exit-1 with install guidance
- [ ] T017 [US2] Wire `analyze pile` + `analyze target` into `cli.py`
- [ ] T018 [US2] Integration test `bridge-builder-toolkit/tests/integration/test_analyze.py` — IG→Travelogue analyses produce all artifacts; raw artifacts canonical; ER skipped for the TSV pile; enhanced sections carry valid provenance labels (SC-003/004/006)

**Checkpoint**: US2 independently testable — both sides profiled; labels readable; raw baselines recognizable.

---

## Phase 5: User Story 3 — Bridge-mapping synthesis (Priority: P3)

**Goal**: A proposed pile→target mapping with a stock-runnable dbt artifact, the hybrid (deterministic + toolkit-inference) transform materialized locally, and an interactive bridge playground.

**Independent Test**: `synthesize bridge` produces `mapping.yml`, a `dbt parse`-able `bridge.dbt-project/`, `bridge.output.tsv`, and `bridge.enhanced.html` (pile↔target, labeled, matcher cited). With insert+delete perms, the oracle (US4) runs before the bridge is shown.

- [ ] T019 [US3] Implement `bridge-builder-toolkit/synthesize/matcher.py` — LLM mapping proposal (candidate generation + rerank, Magneto-style; cite Valentine/Magneto) → `mapping.yml` with per-column `kind: direct|deterministic|ai_inferred`, the AI-inferred designation, and `preserved_inputs` for inferred columns (FR-045/047/103/153, Principle V)
- [ ] T020 [US3] Implement `bridge-builder-toolkit/synthesize/dbt_project.py` — stage the pile into a per-iteration DuckDB; emit a stock-runnable `dbt-duckdb` project (`dbt_project.yml`, `profiles.yml`, `models/sources.yml`, deterministic-only `models/*.sql`, `models/schema.yml` with column tests + `ai_inferred` meta, generated `dbt docs`) (FR-040/041/102, SC-005)
- [ ] T021 [US3] Implement `bridge-builder-toolkit/synthesize/transform.py` — `dbt run` (deterministic mappings) + the toolkit-side LLM inference step for `ai_inferred` columns (FR-047) → materialize `bridge.output.tsv` keyed by the pile dedup id, with `*__inputs` + `*__rationale` provenance companion columns (FR-048, Principle V)
- [ ] T022 [US3] Implement `bridge-builder-toolkit/synthesize/bridge_playground.py` — `bridge.enhanced.html`: pile↔target side-by-side, proposed mappings, add/remove/edit + comment controls, `dbt baseline`/`LLM-extended`/`toolkit-novel` labels, matcher citation, copy-out-a-prompt (FR-042–045)
- [ ] T023 [US3] Wire `synthesize bridge` into `cli.py`; auto-pass control to the oracle loop (US4) when insert+delete perms are present, else straight to manual review (FR-046)
- [ ] T024 [US3] Integration test `bridge-builder-toolkit/tests/integration/test_synthesize.py` — IG→Travelogue synth: `bridge.dbt-project/` parses with stock dbt (SC-005); `bridge.output.tsv` present with provenance columns; bridge playground labels + citation present

**Checkpoint**: US3 independently testable — a proposed mapping + output + playground exist (oracle wired but separately verified in US4).

---

## Phase 6: User Story 4 — Automatic oracle-driven refinement (Priority: P4)

**Goal**: An automatic insert/delete acceptance oracle that refines the mapping until it round-trips or hits the 5-fail ceiling — without operator intervention.

**Independent Test**: With the 002 Postgres target (full perms), synth a deliberately-broken mapping → the oracle fires, auto-iterates, and converges to oracle-validated or halts at 5-fail; intermediate iterations persisted for post-hoc inspection; operator never intervenes during the loop.

- [ ] T025 [US4] Implement `bridge-builder-toolkit/oracle/loop.py` round-trip — constraint-stressing sample selection (3–5 rows: most empty fields / longest values + 1 random); transform each per the mapping; insert+delete in a **rolled-back transaction** against the real target; classify each as success / schema-violation / transient; the check passes only if all sampled rows round-trip cleanly (FR-070); transient failures retry with backoff before counting (FR-072)
- [ ] T026 [US4] Implement the loop control in `oracle/loop.py` — synthesize a feedback prompt from the DB error + transformed record (FR-071), re-run synthesis, increment the iteration, enforce the 5-consecutive-failure halt with an operator-intervention banner + counter-reset rules (FR-073/078), skip-when-no-perms with a recorded reason (FR-075), and persist every automatic iteration (raw + enhanced + oracle result + synthesized feedback) (FR-076/077)
- [ ] T027 [US4] Synthetic oracle test harness `bridge-builder-toolkit/tests/integration/test_oracle.py` + `tests/fixtures/` — broken-mapping cases (type mismatch, NOT-NULL, FK) assert flagged-as-failed (SC-008), ≤3-iteration convergence (SC-007), 5-fail halt within one iteration (SC-009), transient-not-counted (SC-010); verify the target's real tables are unchanged after every check

**Checkpoint**: US4 independently testable — the oracle loop validates/refines/halts automatically; target tables untouched.

---

## Phase 7: User Story 5 — Manual iterate + accept-bundle (Priority: P5)

**Goal**: Operator-driven semantic refinement and Final Bundle materialization.

**Independent Test**: Adjust a mapping + comment in the bridge playground, copy the prompt, run `iterate` → new iteration (re-synth, re-oracle if perms). Run `accept-bundle` → a `/speckit.specify`-ready bundle.

- [ ] T028 [US5] Implement `bridge-builder-toolkit/iterate/iterate.py` — accept a feedback payload (bridge-playground prompt OR a US6 review summary), produce a new **bridge-mapping iteration**: re-run synthesis, re-enter the oracle loop if perms; when feedback surfaces an uncovered property, produce a new **data-profiling iteration** (in its own loop) that the new bridge-mapping iteration `profiling_ref`s — NOT embedded in the bridge iteration (FR-080/081); persist alongside prior iterations of each loop (FR-082)
- [ ] T029 [US5] Implement `bridge-builder-toolkit/iterate/accept_bundle.py` — materialize `final-bundle/`: a `bundle.yml` manifest + all iteration artifacts (raw + enhanced × stage) from BOTH the data-profiling and bridge-mapping iteration histories + final `mapping.yml` + `bridge.output.tsv` + captured prompt payloads + the two **verbatim 003-US3 carry-forward items** (FR-083/090/091/092)
- [ ] T030 [US5] Wire `iterate` (`--feedback`) + `accept-bundle` (`--iteration`) into `cli.py`
- [ ] T031 [US5] Integration test `bridge-builder-toolkit/tests/integration/test_iterate_bundle.py` — feedback → new iteration produced; `accept-bundle` → bundle structure usable as `/speckit.specify` input without structural hand-editing (SC-011); FR-092 carry-forward items present verbatim

**Checkpoint**: US5 independently testable — manual iteration + a deliverable Final Bundle.

---

## Phase 8: User Story 6 — Truth-baseline review of bridge output (Priority: P6)

**Goal**: Measure AI-inference quality across iterations against an editable truth baseline.

**Independent Test**: `review` with a truth-baseline TSV + join key → a review playground pairing rows with AI-inferred columns emphasized; tag verdicts; `bridge-improved` updates the baseline (+ edit history); a session summary persists and can feed `iterate`.

- [ ] T032 [US6] Implement `bridge-builder-toolkit/review/review.py` pairing + playground — join `bridge.output.tsv` vs the truth baseline on the join key; bucket `shared`/`only-truth`/`only-bridge`; read the AI-inferred designation (FR-153); build the review playground with AI-inferred-column emphasis, an inferred/direct/all filter, and per-pair verdict tagging (`exact-match`/`bridge-improved`/`bridge-regressed`/`truly-different`) (FR-150–154, SC-021); refuse (exit 1) if the join key is missing from either side
- [ ] T033 [US6] Implement baseline write-back in `review/review.py` — on save, `bridge-improved` → write `baseline.tsv` + append `baseline.edit-history.jsonl` (prior/new/session/timestamp/rationale); other verdicts leave the baseline unchanged; bootstrap an empty baseline on a brand-new domain (FR-155/156/157/161, SC-020)
- [ ] T034 [US6] Implement the session summary + three-way mode in `review/review.py` — persist `session-<ts>.summary.json` (per-bucket counts, per-pair verdicts, baseline edits, AI-col focus list, timestamp); three-way compare (truth + iteration N + M) scoped to AI-inferred columns (FR-158/159); summary acceptable as an `iterate` payload (FR-160)
- [ ] T035 [US6] Wire `review` (`--baseline`, `--join-key`, `--iteration`, `--vs-iteration`, `--ai-columns`) into `cli.py`
- [ ] T036 [US6] Integration test `bridge-builder-toolkit/tests/integration/test_review.py` — IG→Travelogue review: correct pairing + AI-col emphasis (SC-021), a `bridge-improved` edit captured with full history (SC-020), summary persisted, three-way mode works (SC-022)

**Checkpoint**: US6 independently testable — inference-quality review with an editable, history-tracked baseline.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T037 [P] Consolidate prior-art-failure hard-error paths across `analyze/` + `synthesize/` — any pinned tool (ydata-profiling, eralchemy2, dbt) failing → exit 2, never a fabricated enhanced playground (FR-105, SC-018)
- [ ] T038 [P] Flesh out `bridge-builder-toolkit/README.md` + per-stage docs (prereqs, the IG→Travelogue walkthrough cross-link to quickstart.md, movability instructions)
- [ ] T039 FR-091 end-to-end acceptance — run the full IG→Travelogue pipeline (003 pile + 002 Postgres) `project → analyze → synthesize → oracle → iterate → review → accept-bundle`; verify the Final Bundle is `/speckit.specify`-ready (SC-011)
- [ ] T040 [P] Cross-cutting Success-Criteria checks `bridge-builder-toolkit/tests/integration/test_cross_cutting.py` — enhanced playgrounds render < 3 s with representative embedded data (SC-014); ≥ 5 concurrent projects without state corruption (SC-016); `mv bridge-builder-toolkit/ /elsewhere/` re-run (SC-015)

---

## Dependencies & Execution Order

### Phase dependencies
- **Setup (P1)** → **Foundational (P2)** → all user stories. Foundational (config, locking, inference, playground) blocks every story.
- **US1 (P1)** has no story dependency beyond Foundational — it's the MVP gate; every later story operates on a project US1 creates.
- **US2 (P2)** depends on US1 (needs a validated project).
- **US3 (P3)** depends on US2 (bridge-mapping synthesis consumes the latest data-profiling iteration).
- **US4 (P4)** depends on US3 (oracle validates a produced mapping) + US1's permission status.
- **US5 (P5)** depends on US3 (and US4 if perms) — iteration re-runs synthesis/oracle.
- **US6 (P6)** depends on US3–US5 having produced output to review.
- **Polish** depends on the stories in scope for the increment.

### Within a story
- US1: T010 → T012 (wire) ; T011 [P] parallel ; T013 last.
- US2: T014 [P] (introspect) → T016 (target uses it) ; T015 [P] parallel with T014 ; T017 wire ; T018 last.
- US3: T019 (matcher) → T020 (dbt project) → T021 (transform) → T022 (playground) → T023 (wire) → T024.
- US4: T025 → T026 → T027.
- US5: T028 → T029 → T030 → T031.
- US6: T032 → T033 → T034 → T035 → T036.

### Parallel opportunities
- Setup: T002 + T003 [P] (different files).
- Foundational: T005 + T006 + T007 [P] (config/locking/logging are independent). T008/T009 follow.
- US1: T011 [P] alongside T010.
- US2: T014 + T015 [P].
- Polish: T037 + T038 + T040 [P].

---

## Implementation Strategy

### MVP (US1 only)
1. Setup + Foundational → ready for any story.
2. US1 → a validated IG→Travelogue project exists with a recorded connection-validation report. **Ship + validate** (`project create`/`list` + `test_project_create`).

### Incremental delivery
1. US1 → projects exist and validate.
2. US2 → both sides profiled with labeled enhanced playgrounds.
3. US3 → a proposed mapping + dbt artifact + materialized output + bridge playground.
4. US4 → the oracle auto-refines mechanically-broken mappings.
5. US5 → manual refinement + the deliverable Final Bundle.
6. US6 → inference-quality review across iterations.
7. Polish → the FR-091 end-to-end run as the integration acceptance + cross-cutting SC checks.
