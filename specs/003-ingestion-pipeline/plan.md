# Implementation Plan: Ingestion Pipeline App (pile-app)

**Branch**: `003-ingestion-pipeline` | **Date**: 2026-05-29 | **Spec**: [`spec.md`](spec.md)
**Input**: Feature specification from `specs/003-ingestion-pipeline/spec.md`

## Summary

Build an **Ingestion Pipeline App** (stub name `pile-app` per [`docs/roadmap.md`](../../docs/roadmap.md)) composed of segregated source-specific pipeline services that deposit raw artifacts into a local **pile** (TSV files + media directory + future DB tables). The Instagram service is largely shipped in `scripts/instagram-fetch-latest/`; this plan formalises that work, adds the Substack service, migrates the codebase into a self-contained App root (`pile-app/`) per FR-110/FR-111, and wires an in-process scheduler so services can run on per-service schedules.

The pile is the App's sole downstream surface; the future **bridge-app** is its only consumer. No code in this plan writes into `backend/`'s schema, the front-end's data, or any path outside `pile-app/`.

## Technical Context

**Language/Version**: Python 3.14 (matches the active venv at `scripts/instagram-fetch-latest/venv/`).
**Primary Dependencies**: `instagrapi` (Instagram session-based fetcher); `anthropic` SDK (LLM inference for FR-019/FR-020); `requests` (Instagram CDN media download); `python-dotenv` (env config); `feedparser` (Substack RSS — new for this plan); an in-process scheduler library (`APScheduler` candidate, decided in Phase 0).
**Storage**: Filesystem-only for v1: per-target TSV files (`pile-app/pile/posts.<target>.local.tsv`, `pile-app/pile/articles.<publication>.local.tsv`), shared media directory (`pile-app/pile/media/<service>/`), per-run log files (`pile-app/logs/`). No database in v1; FR-104 reserves the option.
**Testing**: `pytest` with the existing unit-test split (`tests/test_process_media.py`, `tests/test_location_helpers.py`, `tests/test_resort_helper.py`) and integration test (`tests/test_instagram_pull.py`). Total 79 unit tests at plan time.
**Target Platform**: Cross-platform Python CLI. Operator runs on Windows 11 today; macOS/Linux supported. No OS-specific dependencies.
**Project Type**: Self-contained Python CLI App. Per FR-110/FR-111 the entire App lives under one root directory (`pile-app/`) that's movable to a separate repo without affecting either side. SC-010/SC-011 are the portability gates.
**Performance Goals**: Anti-detection longevity SC-004 (≥100 consecutive scheduled runs without hard block); idempotency SC-002 (zero duplicates on re-runs); resilience SC-003 (interrupt loses ≤1 in-flight artefact); ETA accuracy SC-008 (±30% for ≥80% of runs).
**Constraints**: Physical segregation (FR-110/FR-111); anti-throttle pre-set rate-limiting (FR-051); hard-block detection without retry (FR-052); inference inputs preserved (FR-105); upstream-deletion tombstone (FR-106); cross-service concurrent + within-service sequential (FR-107); operator-driven (no auto-prune, no auto-notify).
**Scale/Scope**: Personal-scale travelogue. Expected at steady state: 2–10 target Instagram accounts per crawler, ≤2000 posts/target on first-scrape, 0–20 new posts per incremental hourly run. 1–3 Substack publications. ≤5 concurrent pipeline services at any time. No multi-tenant or commercial-scale concerns.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

Referencing [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) v2.1.0:

| Principle / Cardinal Rule | This plan's posture | Status |
|---|---|---|
| **I. Evolutionary Development, Not Dogmatic** | Spec was re-authored 2026-05-27 to match reality; this plan documents the migration path, not a green-field build. | ✅ Pass |
| **II. Apps Are the Architectural Unit** | Plan creates a dedicated `pile-app/` root directory; FR-110/FR-111 portability is a first-class constraint. | ✅ Pass |
| **III. Project Purposes Are Authoritative** | Serves data-unification-purpose; the App is the toy-scale pile producer per the roadmap. | ✅ Pass |
| **IV. AI-Driven Development as First-Class** | Identifiers avoid model names (`reasoning`, `infer_post_location`); LLM SDK is a swappable dependency. | ✅ Pass |
| **V. Cross-App Communication Through Explicit Interfaces** | Pile is the only output; bridge-app is the only consumer; zero writes into `backend/` or other Apps. | ✅ Pass |
| **Cardinal Rule #1 — `tasks.md` is historical** | Existing `tasks.md` phases preserved; new phases append. | ✅ Pass |
| **Cardinal Rule #2 — no PM state in synced artefacts** | `jira-mapping.json` preserved as-is; no sprint/owner/status fields added. | ✅ Pass |
| **Cardinal Rule #3 — no model-specific names in code/data** | Recent renames already enforce this. | ✅ Pass |
| **Cardinal Rule #4 — inference inputs preserved** | FR-105 enforced; new `tag_verbatim` + `lat_verbatim` + `lng_verbatim` columns on Instagram (tagged-path inputs) + caption/media-path retention (inferred-path inputs). | ✅ Pass |
| **Cardinal Rule #5 — lean on references over duplication** | Plan links to spec / constitution / roadmap rather than restating. | ✅ Pass |

No violations; Complexity Tracking table unused.

## Project Structure

### Documentation (this feature)

```text
specs/003-ingestion-pipeline/
├── spec.md                  # /speckit.specify + /speckit.clarify output
├── plan.md                  # This file
├── research.md              # Phase 0 output
├── data-model.md            # Phase 1 output
├── quickstart.md            # Phase 1 output
├── contracts/               # Phase 1 output
│   ├── pile-artifact-instagram.md
│   ├── pile-artifact-substack.md
│   └── cli.md
├── tasks.md                 # Historical record; new phases via /speckit.tasks
├── jira-mapping.json        # Preserved from re-author
├── specify-prompt-draft.md  # 2026-05-27 prompt artefact (paste-and-discard input; retained for history)
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
pile-app/                              # The Ingestion Pipeline App root (migration target)
├── instagram/                         # Instagram pipeline service
│   ├── __init__.py
│   ├── pipeline.py                    # Service orchestrator (run, schedule, halt)
│   ├── instagrapi_client.py           # Crawler auth + session resume
│   ├── tagged_location.py             # FR-019: canonicalize verbatim tag + IATA
│   ├── inferred_location.py           # FR-020: caption+media inference
│   ├── deletion_detection.py          # FR-106: tombstone on naturally-encountered absence
│   ├── validation/                    # Hand-curated truth baseline + scrape diffs
│   │   ├── posts.local.tsv            # Truth baseline (hand-curated locations)
│   │   ├── scrape-diff.txt            # Earliest diff output (preserved for history)
│   │   ├── scrape-diff-v3.txt
│   │   └── scrape-diff-v4.txt
│   └── README.md
├── substack/                          # Substack pipeline service (new)
│   ├── __init__.py
│   ├── pipeline.py
│   ├── rss_client.py                  # feedparser-based polling
│   ├── deletion_detection.py
│   └── README.md
├── common/                            # Shared infrastructure (service-agnostic)
│   ├── __init__.py
│   ├── pile.py                        # TSV read/write, media download, sort+reid, sweep
│   ├── inference.py                   # LLM SDK wrapper + JSON-and-prose extraction
│   ├── anti_throttle.py               # Rate presets, jittered sleep, challenge detection
│   ├── scheduler.py                   # In-process scheduler (FR-017, FR-074, FR-107)
│   └── run_logging.py                 # Per-run log files + retention sweep (FR-070, FR-072)
├── tests/                             # All tests live here, mirroring source structure
│   ├── instagram/
│   ├── substack/
│   ├── common/
│   └── integration/                   # Cross-service / end-to-end tests
├── pile/                              # Pile output (gitignored; created at runtime)
│   ├── posts.<target>.local.tsv
│   ├── articles.<publication>.local.tsv
│   └── media/
│       ├── instagram/
│       │   └── <target>_<shortcode>.<ext>
│       └── substack/
│           └── <publication>_<post-id>.<ext>
├── logs/                              # Per-run logs (gitignored; auto-pruned)
│   └── scrape-<service>-<target>-<YYYYMMDD-HHMMSS>.log
├── cli.py                             # Top-level CLI entry (`python -m pile_app ...`)
├── config.yml                         # Per-service schedule + rate-preset config
├── requirements.txt
├── pyproject.toml                     # Packaging metadata + entry point
├── .env.example                       # Documented credentials template
├── .gitignore                         # pile/, logs/, .env, session files
└── README.md                          # App-level overview + run instructions
```

**Structure Decision**: Single self-contained Python CLI App at `pile-app/` (repo root). Per-service modules (`instagram/`, `substack/`) under that root; shared infrastructure in `common/`. Pile output and run logs are gitignored runtime data inside the App root (FR-110: nothing written outside). The App is movable to a fresh repo as a unit (FR-111, SC-010).

**Migration path** from the current `scripts/instagram-fetch-latest/` layout into `pile-app/` is detailed in [`research.md`](research.md) under Decision: Migration strategy.

## Complexity Tracking

*Unused — Constitution Check passed without violations.*
