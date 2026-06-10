# bridge-builder-toolkit

A self-contained Python CLI App that produces **validated bridge _specifications_** — a Final Bundle that seeds a bridge-app spec via `/speckit.specify` — from a **pile** (003 ingestion output) plus a **target schema** (002's Travelogue Postgres). It is **not** a running bridge: the dbt project, materialized output, and oracle round-trip are validation evidence, and the target DB stays read-only except for the transactional oracle probe.

The toolkit wraps prior-art tools (`ydata-profiling`, `eralchemy2`, `dbt`/`dbt-duckdb`, Valentine/Magneto-style matchers) in an LLM-analyst layer, surfaced through copy-out-a-prompt HTML playgrounds.

See [`specs/004-bridge-builder-toolkit/`](../specs/004-bridge-builder-toolkit/) for the spec, plan, and the IG→Travelogue walkthrough (`quickstart.md`).

## Stages (one CLI subcommand each)

`project` → `analyze` → `synthesize` → (`oracle`) → `iterate` → `review` → `accept-bundle`

Run `bridge_builder --help` for the full command surface.

## Prerequisites

- **Python 3.12+**
- **GraphViz** — required by `eralchemy2` for target ER diagrams (`analyze target`); the `dot` binary must be on PATH.
- **Docker** — integration tests and the IG→Travelogue walkthrough run against the 002 backend's Docker Postgres.
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
