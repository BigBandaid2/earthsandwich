# Research: Ingestion Pipeline

**Phase**: 0 | **Plan**: [plan.md](plan.md) | **Date**: 2026-05-22

> Decisions inherited from the original 002-data-ingestion research; copied here so 003 stands on its own.

## Decision 1: Instagram Ingestion Library

**Decision**: `instagrapi` (session-based) as the sole method. _Updated 2026-05-25 — Graph API fallback dropped per the amended FR-016._

**Rationale**: The travelers' account is a personal account — the Instagram Graph API requires a Business or Creator account and cannot access personal feeds, so a Graph API fallback never had a realistic surface area for the primary use case. `instagrapi` uses the private Instagram API with session-based authentication (no account type restriction) and provides structured location objects including country code, eliminating the need for a separate geocoding step when a tag exists. The 2026-05-25 amendment retired the Graph API fallback to avoid maintaining two ingestion code paths for marginal robustness gain.

**Alternatives considered**:
- Instagram Graph API only: ruled out — does not support personal accounts
- `instagram-private-api` (Python): less actively maintained than instagrapi; fewer post metadata fields
- Manual TSV scraping (current approach): does not support personal accounts either; Claude-based geocoding for every post is slow and costly

**Session management**: The `python -m app.cli.manage login` command (FR-041) handles initial authentication and persists the session file to `INSTAGRAPI_SESSION_FILE`. Normal ingestion reuses the persisted session without re-authenticating.

---

## Decision 2: In-Process Job Scheduling

**Decision**: APScheduler 3.x with `BackgroundScheduler`

**Rationale**: The 002 spec (Assumptions section) explicitly requires scheduling as background threads or APScheduler within the Python backend process — not an external cron. APScheduler satisfies this: it runs in the same process as FastAPI (started in the `lifespan` context manager), requires no external broker, and is trivially configurable via environment variable. The ingestion interval (default ~1 hour) is set via `INSTAGRAM_POLL_INTERVAL_MINUTES` and `SUBSTACK_POLL_INTERVAL_MINUTES`.

**Alternatives considered**:
- Celery + Redis/RabbitMQ: production-grade but requires a broker container and worker process — overkill for two scheduled jobs at low frequency
- External cron (host crontab): creates host-level dependency that conflicts with the Docker deployment model; also the current architecture we're replacing
- FastAPI BackgroundTasks: for one-off tasks, not recurring schedules

---

## Decision 3: IATA Region Code Determination

**Decision**: Claude AI exclusively (no external airport-lookup API)

**Rationale**: The 2026-05-15 spec update dropped the Airlabs IATA lookup in favor of having Claude infer the IATA code directly. This collapses two API calls into one when a location must be inferred, eliminates the need for an additional API key (`AIRPORT_API_KEY`), and consolidates location logic in a single LLM call. Prompt engineering is required to ensure the model returns valid IATA codes consistently; a low-confidence response is logged at WARNING level and `region_code` is left null.

**Alternatives considered**:
- Airlabs `GET /airports?lat=X&lng=Y` (original design): added a second external dependency and required a paid tier for country filtering at the request volume implied by ingestion growth
- OpenFlights static dataset: requires bundling a CSV file and implementing haversine distance sorting locally; more code, no maintenance path if airports change
- Google Places API: overkill and expensive for this narrow use case

---

## Decision 4: Email Notification for Session Errors

**Decision**: Python `smtplib` (stdlib) with environment-configured SMTP

**Rationale**: No external dependency needed; the notification is a one-shot fire-and-forget on session error. `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` are read from env. If SMTP is not configured, the email step is skipped and the error is logged only (per spec Assumptions).

**Alternatives considered**:
- SendGrid / Mailgun SDK: adds a third-party dependency for a low-frequency notification; overkill
- AWS SES: requires AWS credentials; not justified at this scale
