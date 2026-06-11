# bridge-builder-toolkit

A self-contained Python CLI App that produces **validated bridge _specifications_** — a Final Bundle that seeds a bridge-app spec via `/speckit.specify` — from any **pile** (a file-based deposit of extracted source data) plus any **target schema** (a relational database). One installation manages many projects, each pairing a pile with a target. It is **not** a running bridge: the dbt project, materialized output, and oracle round-trip are validation evidence, and the target DB stays read-only except for the transactional oracle probe.

The toolkit wraps prior-art tools (`ydata-profiling`, `eralchemy2`, `dbt`/`dbt-duckdb`, Valentine/Magneto-style matchers) in an LLM-analyst layer, surfaced through copy-out-a-prompt HTML playgrounds. It has no knowledge of any particular pile producer or target application.

See [`specs/004-bridge-builder-toolkit/`](../specs/004-bridge-builder-toolkit/) for the spec and plan; `quickstart.md` there walks one concrete example pairing end-to-end.

## Stages (one CLI subcommand each)

`project` → `analyze` → `synthesize` → (`oracle`) → `iterate` → `review` → `accept-bundle`

Run `bridge_builder --help` for the full command surface.

## Prerequisites

- **Python 3.12+**
- **GraphViz** — required by `eralchemy2` for target ER diagrams (`analyze target`); the `dot` binary must be on PATH.
- **A disposable relational target** — the integration tests connect to whatever DSN `BRIDGE_TEST_TARGET_DSN` points at (any local Postgres, e.g. via Docker) and skip when it is unset.
- **Anthropic API key** — set `ANTHROPIC_API_KEY` (see `.env.example`) for the LLM-analyst layer.

## Install

```bash
cd bridge-builder-toolkit
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e .
bridge_builder --help
```

## Movability

This App is self-contained (FR-001/003): the whole `bridge-builder-toolkit/` directory can be moved to a separate repo without affecting either side. Per-project runtime state lives under `projects/` (gitignored); paths in `project.yml` are relative or env-referenced, and credentials are referenced by env-var name only — never stored.
