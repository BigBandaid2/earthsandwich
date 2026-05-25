# Quickstart: Ingestion Pipeline

**Branch**: `003-ingestion-pipeline` | **Plan**: [plan.md](plan.md)

> Assumes the `002-database-backend` quickstart has been completed: backend container running, database seeded, frontend reachable. This guide adds the ingestion-specific setup on top.

## 1. Add ingestion env vars to `.env`

In addition to the variables required by 002, set these:

```env
INSTA_USERNAME=<instagram username>
INSTA_PASSWORD=<instagram password>
INSTAGRAPI_SESSION_FILE=./instagrapi_session.json
SUBSTACK_RSS_URL=<substack rss url>

# Optional — schedule overrides (defaults shown)
INSTAGRAM_POLL_INTERVAL_MINUTES=60
SUBSTACK_POLL_INTERVAL_MINUTES=60

# Optional — SMTP for session-error notification email
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
```

`ANTHROPIC_API_KEY` is also required (already present in 002 for general backend use).

---

## 2. Instagram Login (one-time setup)

Before the ingestion scheduler can run, the instagrapi session must be initialized:

```bash
docker compose exec backend python -m app.cli.manage login
```

This prompts interactively for Instagram credentials and writes the session file to the path configured by `INSTAGRAPI_SESSION_FILE`. Normal scheduled ingestion reuses this session without re-authenticating.

If the session expires (Instagram challenge, 2FA, etc.), a notification email is sent to `automation@datacommlab.com` and the job exits cleanly. Re-run the login command above to refresh the session.

---

## 3. Trigger Ingestion Manually

Instagram ingestion (bypasses the schedule, runs immediately):
```bash
docker compose exec backend python -m app.ingestion.instagram
```

Substack ingestion:
```bash
docker compose exec backend python -m app.ingestion.substack
```

---

## 4. Verify Ingested Data

After a successful Instagram ingestion run, new rows should appear in `stops` and `instagram_posts`. Quick check via the 002 read API:

```bash
# Look up the most recent stops
curl "http://localhost:8000/stops?after=2026-05-01"

# Or fetch a specific stop's post directly
curl "http://localhost:8000/instagram-posts?stop_id=<stop_id>"
```

Substack runs populate `substack_posts` with `stop_id=NULL`. These rows are intentionally excluded from the public read API until manually assigned.
