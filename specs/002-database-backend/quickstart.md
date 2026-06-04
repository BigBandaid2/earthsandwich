# Quickstart: Database & Backend

**Branch**: `002-database-backend` | **Plan**: [plan.md](plan.md)

> Ingestion-specific setup (`instagrapi` login, manual Instagram/Substack triggers) lives in [`003-ingestion-pipeline/quickstart.md`](../003-ingestion-pipeline/quickstart.md).

## Prerequisites

- Docker Desktop (Mac/Windows) or Docker Engine + Compose plugin (Linux)
- Node 18+ with npm (for the TypeScript seed export only)
- Python 3.12 (for running scripts outside Docker; optional if you use Docker for everything)

---

## 1. Environment Setup

```bash
cp .env.example .env
```

Fill in the values required by this spec in `.env`. At minimum for local dev:

```env
DATABASE_URL=postgresql+asyncpg://earthsandwich:earthsandwich@localhost:5432/earthsandwich
API_SECRET_KEY=<generate a random string>
FRONTEND_ORIGIN=http://localhost:5173
ENVIRONMENT=development
```

Ingestion variables (Instagram credentials, Substack RSS URL, SMTP, etc.) are required only when working on `003-ingestion-pipeline`; see that spec's quickstart for the full list.

---

## 2. Start the Full Stack

```bash
docker compose up
```

On first start, the database container automatically applies `scripts/seed-dump.sql` (if the volume is empty), pre-populating all trips, stops, and posts without any manual import step.

Services:
- **Backend API**: `http://localhost:8000`
- **Frontend**: `http://localhost:5173` (or the port configured in `docker-compose.yml`)
- **PostgreSQL**: `localhost:5432`

---

## 3. Run the Seed Pipeline (first time only, or after TS data changes)

The seed pipeline is only needed when `scripts/seed-dump.sql` does not yet exist or when the TypeScript source data has changed.

**Step 1 — Export TypeScript data to JSON:**
```bash
npm install      # ensure tsx is available
npx tsx scripts/export-seed-data.ts
# Output: scripts/seed-data/{trips,stops,instagram_posts,substack_posts}.json
```

**Step 2 — Import JSON into PostgreSQL and generate the SQL dump:**
```bash
# With the database running (docker compose up -d db)
python scripts/seed.py
# Output: scripts/seed-dump.sql
```

The seed script is idempotent — re-running it will not create duplicate records.

After generating a new `seed-dump.sql`, commit it so new Docker environments pick it up automatically on first start.

---

## 4. Run Database Migrations

After any schema change, generate and apply an Alembic migration:

```bash
# Generate migration
docker compose exec backend alembic revision --autogenerate -m "describe the change"

# Apply migrations
docker compose exec backend alembic upgrade head
```

---

## 5. Run Tests

```bash
# Unit tests (no database required)
docker compose exec backend pytest tests/unit/

# Integration tests (requires running database)
docker compose exec backend pytest tests/integration/

# Contract tests (requires running backend)
docker compose exec backend pytest tests/contract/

# All tests
docker compose exec backend pytest
```

---

## 6. Verify the API

```bash
# List all trips
curl http://localhost:8000/trips

# Get a trip with all stops and posts
curl http://localhost:8000/trips/miscellaneous-adventures

# List visited stops in a region
curl "http://localhost:8000/stops?status=visited&region_code=OAX"

# Create a trip (auth required; id is auto-generated from title)
curl -X POST http://localhost:8000/trips \
  -H "Authorization: Bearer <API_SECRET_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Trip 2029","description":"desc","start_date":"2029-01-01","end_date":"2029-12-31"}'

# List all regions
curl http://localhost:8000/regions

# Health check
curl http://localhost:8000/health
```

Auto-generated API docs are available at `http://localhost:8000/docs` (Swagger UI).
