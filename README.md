# Earth Sandwich Travelogue

A web-app travelogue for a round-the-world itinerary, with a public-facing map view, a backend that holds the trip/stop schema, and a self-contained ingestion pipeline that pulls content from upstream sources (Instagram, planned Substack) into a local "data pile" — eventually bridged into the production schema by a future hand-crafted ETL App, and much later by an automated Data Unification App.

The project's Apps are catalogued in [`docs/roadmap.md`](docs/roadmap.md): **pile-app → bridge-app → useful-app → bridge-builder-app**. Today the codebase realizes three of them as three loosely-coupled parts:

- **useful-app — frontend** (`frontend/`) — Vite + React. Read-only map experience with itinerary stops, city drilldown, and detail panels. Reads from the backend API.
  Spec: [`specs/001-world-travelogue/spec.md`](specs/001-world-travelogue/spec.md)
- **useful-app — backend** (`backend/`) — FastAPI service with the trip/stop/post schema and REST read endpoints. Containerized via `docker-compose.yml`.
  Spec: [`specs/002-database-backend/spec.md`](specs/002-database-backend/spec.md)
- **pile-app** (currently `scripts/instagram-fetch-latest/`; relocating into a self-contained App root per the spec) — segregated pipeline services that produce a local pile of TSVs + media files. Physically self-contained and portable to a separate repo. Not directly read by the rest of the project; the future bridge-app will be the intermediary.
  Spec: [`specs/003-ingestion-pipeline/spec.md`](specs/003-ingestion-pipeline/spec.md)

## Project layout

```
specs/         Spec Kit specs (the project's "what + why")
docs/          Vision (roadmap.md), workflow (workflow.md), planning artifacts
frontend/     Front-end app (001)
backend/      FastAPI backend (002)
scripts/instagram-fetch-latest/   pile-app (003) — pending relocation to a self-contained App root
docker-compose.yml   Backend + DB stack
CLAUDE.md     Claude Code project instructions
ONBOARDING.md Setup checklist for new collaborators
```

## Run locally

### Front-end
```bash
cd frontend
npm install
npm run dev
```
`npm run build` and `npm run preview` produce the static build.

### Backend
```bash
docker compose up
```
See `backend/` for the FastAPI app and Alembic migrations.

### pile-app (003)
Standalone Python CLI under `scripts/instagram-fetch-latest/`. See `load_posts_tsv.py --help` for usage; features anti-throttle rate presets, multi-target scraping, streaming + crash recovery, and dual-path geocoding via an LLM. The script writes per-target TSV files and media into the working directory's pile.

## See also

- [`docs/roadmap.md`](docs/roadmap.md) — project vision and roadmap.
- [`docs/workflow.md`](docs/workflow.md) — working-process conventions (Cardinal Rules, weekly cadence, JIRA sync).
- [`ONBOARDING.md`](ONBOARDING.md) — onboarding setup for new collaborators.
