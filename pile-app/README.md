# pile-app — Ingestion Pipeline App

The Earth Sandwich project's **Ingestion Pipeline App**. A physically self-contained collection of segregated pipeline services that extract content from disparate upstream sources (Instagram via `instagrapi`, Substack via RSS, future others) and deposit the results into a single conceptual **pile** (TSV files + media directory).

The pile is this App's sole downstream surface. The future **bridge-app** is its only consumer; downstream consumers (the Travelogue front-end, the production DB) never read this App's pile directly.

## App boundary

Per FR-110 / FR-111 / SC-010 / SC-011 in the spec, this directory (`pile-app/`) is meant to be movable as a unit to a separate project or repository without affecting either side. Everything the App needs at runtime lives under this directory:

- Code (this folder's Python packages)
- Tests (`tests/`)
- Runtime data (`pile/`, `logs/`, `instagrapi_session.json`)
- Per-service validation scaffolding (`instagram/validation/`)
- Configuration (`config.yml`, `.env`)

Speckit working-process artifacts (spec, plan, tasks, JIRA mapping) live at the parent project's root (`../specs/003-ingestion-pipeline/`) and are NOT part of the App — see the spec at [`../specs/003-ingestion-pipeline/spec.md`](../specs/003-ingestion-pipeline/spec.md).

## Quickstart

Full operator guide at [`../specs/003-ingestion-pipeline/quickstart.md`](../specs/003-ingestion-pipeline/quickstart.md). The short version:

```pwsh
# From this directory (pile-app/):
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e .

copy .env.example .env
# Edit .env to fill in INSTA_USERNAME, INSTA_PASSWORD, ANTHROPIC_API_KEY

# Verify install
pile_app run instagram <target> --dry-run --max-pages 1
```

## Layout

```text
pile-app/
├── cli.py                  # Top-level CLI entry (`pile_app ...` via console_scripts)
├── instagram/              # Instagram pipeline service
│   └── validation/         # Hand-curated truth baseline + scrape diffs (informal)
├── substack/               # Substack pipeline service
├── common/                 # Shared infrastructure (pile I/O, LLM SDK wrapper, anti-throttle, scheduler)
├── tests/                  # All tests
├── pile/                   # Pile output (gitignored runtime data)
│   ├── posts.<target>.local.tsv
│   ├── articles.<publication>.local.tsv
│   └── media/instagram/
├── logs/                   # Per-run logs (gitignored, auto-pruned)
├── config.yml              # Per-service schedule + rate-preset config
├── pyproject.toml
├── requirements.txt
└── .env.example
```

## Architecture references

- **Spec**: [`../specs/003-ingestion-pipeline/spec.md`](../specs/003-ingestion-pipeline/spec.md)
- **Plan**: [`../specs/003-ingestion-pipeline/plan.md`](../specs/003-ingestion-pipeline/plan.md)
- **Data model**: [`../specs/003-ingestion-pipeline/data-model.md`](../specs/003-ingestion-pipeline/data-model.md)
- **Pile artifact contracts**: [`../specs/003-ingestion-pipeline/contracts/`](../specs/003-ingestion-pipeline/contracts/)
- **Project roadmap** (App catalogue, bridge-app context): [`../docs/roadmap.md`](../docs/roadmap.md)
