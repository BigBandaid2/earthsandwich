# Phase 0 Research: bridge-builder-toolkit

**Date**: 2026-06-08 · **Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

Resolves the "deferred to planning" items from the [Clarifications](spec.md#clarifications) session plus the prior-art-currency verification the spec's Assumptions call for. Format per decision: **Decision / Rationale / Alternatives considered**.

---

## 1. Prior-art tool currency (Assumptions §"live web-search verification")

### 1.1 Data profiling — `ydata-profiling`
- **Decision**: Use `ydata-profiling` (≥ 4.18) as the canonical Stage-2 data-profiling tool (FR-100). Pin a known-good version in `requirements.txt`.
- **Rationale**: Verified current (v4.18.4, 2026-04-22; Development Status 5 — Production/Stable; supports Python 3.10–3.14). It is the direct successor to `pandas-profiling` and the de-facto canonical one-line EDA report — exactly the recognizable baseline FR-021/SC-003 require.
- **Alternatives**: `sweetviz`, `dataprep` (less canonical, smaller mindshare); `great-expectations` (validation-focused, not profiling). Rejected — ydata is the tool an operator "immediately recognizes" (SC-003).

### 1.2 ER diagram — `eralchemy2`
- **Decision**: Use **`eralchemy2`** (not the original `eralchemy`) as the Stage-2 relational schema-visualization tool (FR-101). Requires a system **GraphViz** install (documented in quickstart + an environment check at `analyze target`).
- **Rationale**: The original `eralchemy` is unmaintained and breaks on SQLAlchemy > 1.4; `eralchemy2` is the maintained fork compatible with SQLAlchemy 2.x (which we need for target reflection, §4). It runs from a live DB connection or SQLAlchemy models, emits SVG/PNG/`.er`. Pure-Python install fits the self-contained-venv requirement (FR-001) better than SchemaSpy.
- **Alternatives**: **SchemaSpy** — powerful but Java (needs a JRE + GraphViz), heavier for a Python venv App; kept as a documented fallback if `eralchemy2` can't render a given schema. `sqlalchemy-schemadisplay` — lower-level, less canonical.

### 1.3 Declarative transform — `dbt-core` + `dbt-duckdb`
- **Decision**: Use `dbt-core` with the **`dbt-duckdb`** adapter (not `dbt-postgres`) for the Stage-3 artifact (FR-102). The pile TSV is loaded into a per-iteration local **DuckDB** file that dbt sources; dbt models the deterministic transform and materializes the output locally.
- **Rationale**: Three forces point to DuckDB: (a) **target stays read-only** — the deterministic transform never touches the target Postgres (Clarification: full output is a *local* artifact, FR-048); (b) **portability** (FR-003/SC-015) — the whole transform is a local file, no DB server needed to re-run an iteration; (c) DuckDB reads TSV/CSV natively, so staging the pile is trivial. The dbt project remains stock-runnable (`dbt parse` / `dbt compile` / `dbt docs serve`), satisfying SC-005. Target *column names/types* still come from the real Postgres schema via reflection (§4), so the mapping aims at the true target shape; the **oracle** (§5) is what validates real-Postgres type/constraint compatibility.
- **Alternatives**: **`dbt-postgres` against a toolkit-owned scratch schema** in the target instance — keeps one engine but mutates the target DB instance (scratch schema) and ties iteration replay to a live Postgres; rejected for portability + read-only cleanliness. **No dbt (hand-rolled SQL)** — loses the recognizable prior-art baseline (SC-005). The Edge Case "dbt unable to model raw-TSV cleanly" is mitigated: DuckDB-as-source makes raw-TSV → typed-columns a natural dbt source→model flow.

### 1.4 Schema matching — cite `Valentine` + `Magneto`
- **Decision**: The Stage-3 mapping-proposal layer is an **LLM-based matcher inspired by Magneto** (candidate generation + LLM reranking), and the bridge playground cites both **Valentine** (the classic matcher library + benchmark) and **Magneto** (VLDB'25, SLM+LLM reranking) as its algorithmic lineage (FR-045/FR-103).
- **Rationale**: Verified current — Magneto (VIDA-NYU, VLDB 2025) is the present SOTA LLM-based schema matcher, explicitly benchmarked on Valentine datasets, with public code. This matches the spec's named references and gives a defensible, citable algorithmic style. We do not vendor Magneto's full pipeline in v1; we borrow its *style* (generate candidates, have the LLM rerank/justify) and cite it.
- **Alternatives**: `Valentine` library matchers alone (Coma, Cupid, SimilarityFlooding) — classic, non-LLM, weaker on semantic matches; cited as the baseline lineage. `Schemora` (2025, arXiv) — newer multi-stage LLM matcher; noted as future direction. `Jellyfish` — an LLM for data-prep tasks; referenced but Magneto is the closer fit for schema matching specifically.

---

## 2. Runtime, language, CLI

- **Decision**: **Python 3.12+** (matches the project floor + spec Assumptions). CLI via **Typer** (Click-based). Self-contained App at `bridge-builder-toolkit/` with its own venv, `.env`, `pyproject.toml`, `requirements.txt` (FR-001).
- **Rationale**: Python is the constitution's foundational language and what every prior-art dep (ydata, eralchemy2, dbt, duckdb, SQLAlchemy, anthropic) is written for/around. Typer gives the rich nested subcommand surface FR-004 wants (`project create|list`, `analyze pile|target`, `synthesize bridge`, `iterate`, `accept-bundle`, `review`) with less boilerplate than argparse and good `--help`.
- **Alternatives**: argparse (pile-app's choice) — fine but more verbose for this many subcommands. `click` directly — Typer wraps it more ergonomically.

## 3. LLM provider

- **Decision**: Anthropic Claude API via the official SDK, wrapped behind a thin toolkit-local `inference` module. Identifiers are **role-based, never model-named** (Constitution Principle IV / Cardinal Rule #3): e.g. `analyst_layer`, `inferred_columns`, `rationale` — not `claude_*`.
- **Rationale**: Matches the rest of the project; the wrapper isolates the provider so it's swappable. The hybrid bridge inference (FR-047) and the enhanced-playground analyst layer both call through it.
- **Alternatives**: provider-agnostic LLM abstraction (LiteLLM) — deferred; one provider keeps v1 simple.

## 4. Target schema introspection

- **Decision**: **SQLAlchemy 2.x reflection** against the target Postgres for schema discovery (tables, columns, types, PK/FK, NOT-NULL). Feeds the target ydata profile, the eralchemy2 ER diagram, the mapping proposal, and the oracle's constraint awareness.
- **Rationale**: Standard, robust, drives every relational-target consumer in one pass. The 002 Travelogue stack is reachable via the existing `docker compose` Postgres.
- **Alternatives**: raw `information_schema` queries — reinventing reflection; SQLAlchemy already normalizes it.

## 5. Oracle round-trip mechanism (FR-070, sampled per Clarification)

- **Decision**: For the 3–5 constraint-stressing sample rows, the oracle transforms each via the current mapping and performs an **insert-then-delete round-trip against the real target inside a single transaction that is ROLLED BACK at the end** (crash-safety net so no residue can persist). It classifies each result as success / schema-violation / transient. The check passes only if ALL sampled rows insert cleanly. **Constraint-stressing selection** = rank pile rows by (count of empty fields, max field length) and take the top of that ranking plus one random row.
- **Rationale**: Insert+delete-in-a-rolled-back-transaction honors FR-070's "insert … delete on success" round-trip while guaranteeing the target's real tables are unchanged even if the process is killed mid-check (Key Entity "target … read-only"). Sampling constraint-stressing rows maximizes NOT-NULL/length/type-violation catch rate (SC-008) cheaply. Transient (network/availability) failures are distinguished by exception type and retried with backoff before counting toward the 5-fail ceiling (FR-072/SC-010).
- **Alternatives**: literal insert + `DELETE` committed — works but leaves a window where rows persist (crash between insert and delete); the rolled-back transaction is strictly safer. Savepoints per row — unnecessary; one transaction per check suffices.

## 6. Enhanced playgrounds (FR-050–054)

- **Decision**: Each enhanced playground is a **single self-contained HTML file generated by the toolkit** (Python builds it from an inline template; data embedded as a JS literal), vanilla HTML/CSS/JS, no remote assets, with a "copy out a prompt" button that degrades to a selectable textarea (FR-054). Follows the project's established `playground:playground` conventions (dark theme, inline data, copy-out-a-prompt). The raw prior-art artifacts (`*.ydata-profile.html`, `*.er-diagram.svg`, `bridge.dbt-project/`) are **separate files**, never embedded (FR-051).
- **Rationale**: Reuses the proven playground pattern already used for DoD reviews + time-log; satisfies the self-contained/offline/standalone-prompt requirements directly. Embedded data is sampled/summarized to stay under the ~5 MB render budget (FR-028, SC-014).
- **Alternatives**: a small JS framework / multi-file bundle — violates FR-050's single-file/no-dependency rule.

## 7. On-disk project layout & concurrency

- **Decision**: `bridge-builder-toolkit/projects/<name>/` per project (FR-006/009); inside it `project.yml`, `data-profiling/iteration-<N>/`, `bridge-mapping/iteration-<N>/`, `truth-baseline/`, and `final-bundle/` after acceptance. Per-project locking via a **lockfile holding PID + start time**, reclaimed if the PID is dead (FR-110) — using the `filelock` library or an os-level advisory lock.
- **Rationale**: Mirrors pile-app's "everything under one movable root" (FR-003/SC-015). Iteration-numbered subfolders give the inspectable history (FR-082) and side-by-side compare (US5). A PID lockfile is the simplest crash-reclaimable lock.
- **Alternatives**: a SQLite metadata DB per installation — heavier than flat folders + YAML; rejected for the same "legible, greppable, movable" reasons the pile is flat files.

## 8. Constitution alignment notes

- **Principle V / Cardinal Rule #4 (inference preserves inputs)**: the FR-047 toolkit-side inference step MUST persist, in the materialized output artifact (FR-048) and the final bundle (FR-090), the pile inputs it fed to each inference alongside the inferred value — so an inference can be re-run/audited with a different model. Carried into data-model.md as a column-provenance requirement.
- **Principle II (Apps via contracts, not shared code)**: the toolkit couples to 003/002 only through operator-supplied paths/URLs at runtime (FR-002) — no imports from `pile-app`/`backend`.
- **No NEEDS CLARIFICATION remain** for v1 scope: target = relational DB (Postgres), pile = filesystem TSV, single operator per project.

## 9. Web UI stack (US7, added 2026-06-10)

- **Decision**: `fastapi` + `uvicorn` serving **server-rendered vanilla HTML** (string templates in `ui/pages.py`, no jinja2, no Node/React), launched by `bridge_builder ui`, localhost-bound by default. Pages echo the enhanced-playground dark idiom; the UI calls the same `project/` core modules as the CLI (FR-171).
- **Rationale**: two small pure-Python deps in the one App venv keep the App movable (FR-003) and offline (FR-179); FastAPI's TestClient gives free route tests in the existing pytest patterns; no build step.
- **Alternatives**: Flask (equivalent; FastAPI's typing + TestClient fit the test suite better); stdlib `http.server` (too bare for forms/routing); any SPA stack (adds a Node toolchain inside a Python App and violates the offline/no-external-assets discipline).
