<!-- SPECKIT START -->
Two active specs (split from `002-data-ingestion` on 2026-05-22):

**`002-database-backend`** — schema, REST API, trip management, security, containerization.
- Plan: `specs/002-database-backend/plan.md`
- Spec: `specs/002-database-backend/spec.md`
- Data model: `specs/002-database-backend/data-model.md`
- Research: `specs/002-database-backend/research.md`
- API contract: `specs/002-database-backend/contracts/api.md`
- Quickstart: `specs/002-database-backend/quickstart.md`
- Tasks: `specs/002-database-backend/tasks.md`

**`003-ingestion-pipeline`** — automated Instagram + Substack ingestion, scheduler, Claude-based geocoding.
- Plan: `specs/003-ingestion-pipeline/plan.md`
- Spec: `specs/003-ingestion-pipeline/spec.md`
- Data model: `specs/003-ingestion-pipeline/data-model.md`
- Research: `specs/003-ingestion-pipeline/research.md`
- Quickstart: `specs/003-ingestion-pipeline/quickstart.md`
- Tasks: `specs/003-ingestion-pipeline/tasks.md`

003 depends on 002's schema and FastAPI skeleton; it adds `backend/app/ingestion/` and `backend/app/cli/` but no new tables or HTTP endpoints.
<!-- SPECKIT END -->
