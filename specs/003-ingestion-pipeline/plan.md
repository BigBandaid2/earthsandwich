# Implementation Plan: Ingestion Pipeline

**Branch**: `003-ingestion-pipeline` | **Date**: 2026-05-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/003-ingestion-pipeline/spec.md`

## Summary

Automated content ingestion for the travelogue: Instagram posts pulled via `instagrapi` (with an Instagram Graph API fallback) and Substack articles pulled via RSS feed. Geocoding and IATA region-code determination are performed by Claude AI. Both jobs run on a recurring schedule within the FastAPI backend process via APScheduler. Records are written into the schema defined in `002-database-backend`.

## Relationship to 002-database-backend

This spec depends on `002-database-backend` and adds no new schema, new HTTP endpoints, or new containers. It introduces:
- `backend/app/ingestion/` — the ingestion modules (Instagram, Substack, location, scheduler)
- `backend/app/cli/manage.py` — interactive `instagrapi` login command
- New environment variables specific to ingestion (Instagram credentials, Substack feed URL, SMTP, Graph API token)
- Hook into 002's FastAPI `lifespan` to start/stop the APScheduler

## Technical Context

**Language/Version**: Python 3.12 (matches 002)
**Primary Dependencies**: `instagrapi`, `feedparser`, `anthropic` SDK, APScheduler 3.x, `smtplib` (stdlib)
**Storage**: PostgreSQL 16 via the schema in 002 (writes to `stops`, `instagram_posts`, `substack_posts`)
**Testing**: pytest, pytest-asyncio; unit tests for trip-assignment logic and location parsing; integration tests against a test PostgreSQL instance
**Target Platform**: Same Linux server / Docker container as the 002 backend
**Performance Goals**: New Instagram posts surface in the database within 2 hours of being posted (SC-002)
**Constraints**: No hardcoded secrets (`INSTA_USERNAME`, `INSTA_PASSWORD`, `ANTHROPIC_API_KEY`, `SUBSTACK_RSS_URL`, optional `INSTAGRAM_GRAPH_API_TOKEN`, optional `SMTP_*`); structured JSON logs only (FR-042 in 002); no external airport-lookup API
**Scale/Scope**: A few new posts per day expected; ingestion runs hourly per default

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Static First | ⚠ Justified violation | Automated ingestion is the entire point — cannot be done statically. Inherited justification from 002. |
| II. Responsive Design | N/A | Backend feature; no UI. |
| III. Accessibility | N/A | Backend feature; no UI. |
| IV. Performance | ✓ Pass | Hourly cadence; ingestion is async background work with no end-user latency impact. |
| V. Security | ✓ Pass | All credentials in env vars only; no secrets in logs; fail-fast on missing required env at startup. |
| Stack: Python | ✓ Justified | `instagrapi` is Python-only; ingestion must live in the Python backend. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| In-process scheduler (APScheduler vs. host cron) | Cron creates a host-level dependency that conflicts with the Docker deployment model in 002; APScheduler runs in the same process as FastAPI and starts/stops with the container | Host crontab works but ties scheduling to the host OS rather than the deployment artifact |
| Two ingestion code paths for Instagram (instagrapi + Graph API) | instagrapi is the primary because the account is personal (Graph API only supports business/creator); Graph API is the fallback per FR-043/FR-044 | Single-method ingestion would either lock out personal accounts (Graph only) or have no fallback if instagrapi sessions break |

## Project Structure

### Documentation (this feature)

```text
specs/003-ingestion-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0 — technology decisions (instagrapi, APScheduler, SMTP, Claude location)
├── data-model.md        # Phase 1 — schema deltas vs. 002 (none; references 002)
├── quickstart.md        # Phase 1 — ingestion-specific operator guide (login, manual triggers)
├── tasks.md             # Phase 2 output
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (additions to the 002 backend)

```text
backend/app/
├── ingestion/                # NEW — owned by this spec
│   ├── __init__.py
│   ├── instagram.py          # instagrapi primary + Graph API fallback + email alert
│   ├── substack.py           # feedparser RSS ingestion
│   ├── location.py           # Claude-only IATA determination and location inference
│   └── scheduler.py          # APScheduler BackgroundScheduler, job registration
└── cli/                      # NEW — owned by this spec
    ├── __init__.py
    └── manage.py             # `python -m app.cli.manage login` — interactive instagrapi login
```

The FastAPI `lifespan` hook in `backend/app/main.py` (owned by 002) is extended to start/stop the scheduler defined here.

**Structure Decision**: This spec adds two directories under `backend/app/`. No other backend layout changes. The `models/`, `schemas/`, `api/`, `database.py`, `config.py`, and `main.py` files remain owned by 002; this spec adds *new* config keys (validated in 002's `config.py`) and reads from 002's database layer.
