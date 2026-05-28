<!-- SPECKIT START -->
Three active specs:

**`001-world-travelogue`** — the front-end Travelogue App (Vite + React). Read-only map UX with itinerary stops, city drilldown, and detail panels. Reads from 002's REST API.
- Spec: `specs/001-world-travelogue/spec.md`
- Plan: `specs/001-world-travelogue/plan.md`
- Data model: `specs/001-world-travelogue/data-model.md`
- Tasks: `specs/001-world-travelogue/tasks.md`

**`002-database-backend`** — schema, REST read API, trip management, security, containerization. The Travelogue's persistence layer.
- Spec: `specs/002-database-backend/spec.md`
- Plan: `specs/002-database-backend/plan.md`
- Data model: `specs/002-database-backend/data-model.md`
- Research: `specs/002-database-backend/research.md`
- API contract: `specs/002-database-backend/contracts/api.md`
- Quickstart: `specs/002-database-backend/quickstart.md`
- Tasks: `specs/002-database-backend/tasks.md`

**`003-ingestion-pipeline`** — the current **pile-app**. A physically self-contained collection of segregated pipeline services (Instagram, future Substack, future others) that extract content from upstream sources and deposit it in a local "pile" of TSVs + media files. The pile is the App's sole downstream surface; no other App reads it directly. Re-authored from scratch on 2026-05-27 to reflect the App-shaped scope that emerged after the original 002→002+003 split.
- Spec: `specs/003-ingestion-pipeline/spec.md`
- Tasks: `specs/003-ingestion-pipeline/tasks.md` (historical phases preserved per Cardinal Rule #1; new phases pending `/speckit.plan`)
- Specify-prompt draft: `specs/003-ingestion-pipeline/specify-prompt-draft.md`
- Plan / data-model / research / quickstart: pending regeneration via `/speckit.plan` (old versions removed on 2026-05-27 since they referenced the dropped scope)

**Apps and architectural relationships** (see [`docs/roadmap.md`](docs/roadmap.md) for the canonical Apps catalogue):
- The project's Apps are **pile-app**, **bridge-app**, **useful-app**, **bridge-builder-app**. Specs do NOT map 1:1 to Apps.
- 003 is the current **pile-app**. 001 + 002 + future MCP/user-input spec are **useful-app**.
- **bridge-app** is planned (no spec yet) — the hand-crafted ETL/EDM that consumes 003's pile and writes into 002's schema via the backend's write paths. Owns stop linkage, normalization, cross-source mapping. Required before ingested content can flow into the Travelogue.
- **bridge-builder-app** is the far-future Data Unification ambition. *Not* a bridge — software whose job is to *produce* bridges automatically from a pile + target schema. Validated against our hand-crafted bridge-app once it exists.
- 001 reads from 002's REST API; 002 owns the production Travelogue schema. 002 does NOT receive direct writes from 003 — the bridge-app is the eventual intermediary.
- 003 is fully decoupled — no shared tables, no shared file paths. Per FR-110 / FR-111 / SC-010 / SC-011 in 003's spec, the App's root directory is meant to be movable to a separate repo without affecting either side.
<!-- SPECKIT END -->
