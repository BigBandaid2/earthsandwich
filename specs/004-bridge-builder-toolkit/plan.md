# Implementation Plan: bridge-builder-toolkit

**Branch**: `004-bridge-builder-toolkit` | **Date**: 2026-06-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/004-bridge-builder-toolkit/spec.md`

## Summary

The **bridge-builder-toolkit** is a self-contained Python CLI App that produces **validated bridge _specifications_ — not the running bridge itself.** For a given pile + target it explores, proposes, and mechanically validates a pile→target mapping, then emits a **Final Bundle** suitable as `/speckit.specify` input for authoring the downstream **bridge-app** spec. The actual functioning bridge — the ETL that loads the pile into the target in production — is built *later, from that spec*, as a separate App.

> **Produces vs. doesn't.** The dbt project, the materialized `bridge.output.tsv`, and the oracle insert/delete round-trip are **validation evidence** that a proposed mapping works mechanically; they ship inside the Final Bundle to justify the spec it seeds. The toolkit does NOT deploy or operate a production bridge, and does NOT bulk-load the target (target stays read-only except the transactional oracle probe).

The toolkit wraps established prior-art tools (`ydata-profiling`, `eralchemy2`, `dbt`, `Valentine`/`Magneto` matchers) in an LLM-analyst layer surfaced through self-contained copy-out-a-prompt playgrounds, and walks the operator through: project creation → pile/target data-profile analysis → bridge-**mapping** synthesis → an automatic **oracle** that validates the proposed mapping → manual refinement → truth-baseline inference-quality review.

**Technical approach (from research.md):** Python 3.12+ / Typer CLI; per-project folders under `bridge-builder-toolkit/projects/<name>/`. The deterministic mapping is exercised **locally** via `dbt-core` + `dbt-duckdb` (pile TSV → DuckDB → a materialized local output artifact), keeping the target Postgres read-only except a transactional, rolled-back oracle round-trip. AI-inferred columns are produced by a **toolkit-side LLM step** (hybrid model, FR-047), separate from dbt. Target schema discovery via SQLAlchemy 2.x reflection. v1 scope is a **relational-DB target only**.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: Typer (CLI); `ydata-profiling` ≥4.18 (data profiling); `eralchemy2` + system GraphViz (ER diagrams); `dbt-core` + `dbt-duckdb` + `duckdb` (declarative mapping, run locally); SQLAlchemy 2.x + `psycopg[binary]` (Postgres reflection + oracle); `anthropic` (LLM analyst + bridge inference); `PyYAML` (project config); `filelock` (per-project lock); `pytest` (tests)
**Storage**: Filesystem — per-project folders (`project.yml`, `data-profiling/iteration-<N>/`, `bridge-mapping/iteration-<N>/`, `truth-baseline/`, `final-bundle/`) — two independent iteration loops; per-bridge-iteration DuckDB file; raw prior-art artifacts + enhanced playground HTML; truth-baseline TSV + edit-history sidecar. No toolkit-owned database server.
**Testing**: pytest — unit (mapping/transform/inference helpers, with mocked LLM + DuckDB fixtures), integration (oracle round-trip against the 002 Docker Postgres; full IG→Travelogue stage walkthrough), synthetic oracle cases (SC-007/008/009/010)
**Target Platform**: Local developer machine (Linux/macOS/Windows) with Python venv, Docker (for the 002 Postgres target), GraphViz, and an Anthropic API key
**Project Type**: Single-project CLI tool (one new App root `bridge-builder-toolkit/`)
**Performance Goals**: Human-time gates — project+validate < 5 min (SC-001); one profile pass < 30 min human (SC-002); all three enhanced playgrounds render < 3 s in a stock browser (SC-014). Oracle loop converges ≤ 3 automatic iterations for ≥ 80% synthetic cases (SC-007)
**Constraints**: Target DB read-only except the transactional oracle round-trip; enhanced playgrounds single-file/offline/≤ ~5 MB embedded (FR-050/FR-028); raw prior-art artifacts byte-for-byte canonical (FR-021/SC-003–005); inference inputs preserved (Constitution Principle V)
**Scale/Scope**: 6 user stories (P1–P6), 73 FRs, 23 SCs; first concrete run = IG→Travelogue (003 pile + 002 schema, ~322 rows); ≥ 5 coexisting projects (SC-016)

## Constitution Check

*GATE: evaluated against `.specify/memory/constitution.md` v2.1.0.*

| Principle / Rule | Status | Notes |
|---|---|---|
| **II — Apps via contracts, not shared code** | ✅ PASS | Self-contained App (FR-001/002/003); couples to 003/002 only through operator-supplied pile path + target connection string at runtime. No imports from `pile-app`/`backend`/`frontend`. |
| **IV — AI-driven; no model-specific names** | ✅ PASS (design constraint) | Identifiers role-based: `analyst_layer`, `inferred_columns`, `rationale` — never `claude_*`. LLM behind a swappable `inference` wrapper. |
| **V / Rule #4 — inference preserves inputs** | ✅ PASS (design constraint) | The FR-047 inference step persists its pile inputs alongside each inferred value in the output artifact (FR-048) and bundle (FR-090). Enforced in data-model.md. |
| **Foundational tech** (Python · Postgres · Docker · Spec Kit) | ✅ PASS | Python App; Postgres target via the 002 Docker stack; output is `/speckit.specify` input. dbt/duckdb/ydata/eralchemy2 are allowed App-local additions. |
| **Cardinal Rule #1 — tasks.md historical record** | ✅ N/A yet | First tasks.md is authored fresh by `/speckit.tasks`. |

**No violations → Complexity Tracking is empty.**

Re-check after Phase 1 design: still PASS — the data-model carries the inference-input-preservation and role-based-naming constraints into the on-disk column provenance; no shared-code coupling introduced.

## Project Structure

### Documentation (this feature)

```text
specs/004-bridge-builder-toolkit/
├── spec.md              # Feature spec (with Clarifications)
├── plan.md              # This file
├── research.md          # Phase 0 — tool currency + deferred-item decisions
├── data-model.md        # Phase 1 — entities → on-disk structures
├── quickstart.md        # Phase 1 — IG→Travelogue first-run walkthrough
├── contracts/
│   └── cli.md           # Phase 1 — CLI command contract (the toolkit's interface)
├── checklists/
│   └── requirements.md  # existing
└── tasks.md             # Phase 2 — created by /speckit.tasks (NOT here)
```

### Source Code (repository root)

```text
bridge-builder-toolkit/                 # the new self-contained App root (FR-001)
├── pyproject.toml                      # console_scripts: bridge_builder = cli:app
├── requirements.txt
├── .env.example                        # ANTHROPIC_API_KEY, target cred env-var names
├── .gitignore                          # projects/, venv/, .env, *.duckdb
├── README.md
├── cli.py                              # Typer app; one subcommand per stage (FR-004)
├── common/
│   ├── config.py                       # project.yml load/save, validation-status model
│   ├── inference.py                    # Anthropic wrapper (role-named, swappable); input-preserving
│   ├── playground.py                   # single-file HTML builder + copy-out-a-prompt (FR-050-054)
│   ├── locking.py                      # per-project PID lockfile (FR-110)
│   └── run_logging.py                  # per-run logs
├── project/
│   ├── create.py                       # project create + connection validation (US1)
│   └── registry.py                     # project list / status (US1)
├── analyze/
│   ├── pile.py                         # ydata raw + pile enhanced playground (US2)
│   ├── target.py                       # ydata raw + eralchemy2 ER + target enhanced (US2)
│   └── introspect.py                   # SQLAlchemy reflection of the target schema
├── synthesize/
│   ├── matcher.py                      # LLM mapping proposal (Magneto-style, cited) (US3)
│   ├── dbt_project.py                  # emit stock-runnable dbt-duckdb project (US3)
│   ├── transform.py                    # dbt run + FR-047 inference → bridge.output.tsv (US3)
│   └── bridge_playground.py            # enhanced bridge playground (US3)
├── oracle/
│   └── loop.py                         # sampled insert/delete round-trip + 5-fail loop (US4)
├── iterate/
│   ├── iterate.py                      # apply feedback → new iteration (US5)
│   └── accept_bundle.py                # materialize final bundle (US5)
├── review/
│   └── review.py                       # truth-baseline review playground + verdicts (US6)
├── projects/                           # gitignored — per-project workspaces live here
└── tests/
    ├── unit/
    ├── integration/                    # needs the 002 Docker Postgres
    └── fixtures/                       # synthetic piles + broken-mapping cases
```

**Structure Decision**: Single-project CLI App rooted at `bridge-builder-toolkit/`, organized by **stage** (project → analyze → synthesize → oracle → iterate → review) mirroring the user-story sequence, with a `common/` layer for cross-stage infrastructure (config, inference, playground builder, locking). This mirrors `pile-app`'s self-contained-App + stage-module shape while sharing zero code with it (Principle II). Per-project runtime workspaces live under `projects/` (gitignored, movable with the App per FR-003).

## Phasing (implementation order, by user story priority)

Each phase = one user story = independently testable + shippable, in priority order. `/speckit.tasks` expands these into tasks. Every phase's deliverable is **specification/validation evidence destined for the Final Bundle**, never a deployed bridge.

- **Setup** — App skeleton (`bridge-builder-toolkit/` scaffold, venv, deps, CLI entry, `common/` stubs).
- **Phase US1 (P1, MVP gate)** — `project create` + connection validation + `project list`. Nothing downstream is testable without it.
- **Phase US2 (P2)** — pile + target profile analysis: raw ydata + raw eralchemy2 ER (target) + the two enhanced playgrounds with prior-art-vs-toolkit labeling.
- **Phase US3 (P3)** — bridge-mapping synthesis: matcher proposal, stock-runnable dbt-duckdb project, FR-047 hybrid transform → local `bridge.output.tsv`, enhanced bridge playground.
- **Phase US4 (P4)** — automatic oracle loop: sampled transactional round-trip, feedback synthesis, 5-fail ceiling, skip-when-no-permissions.
- **Phase US5 (P5)** — manual `iterate` + `accept-bundle` (Final Bundle, FR-090/091/092).
- **Phase US6 (P6)** — truth-baseline `review` playground, verdict tagging, baseline edit-history, three-way compare, summary → `iterate` payload.
- **Polish** — the FR-091 IG→Travelogue end-to-end run as the integration acceptance; docs; prior-art-failure hard-error paths (FR-105).

## Complexity Tracking

> No Constitution violations — section intentionally empty.
