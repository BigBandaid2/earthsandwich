# Research: Ingestion Pipeline App

**Phase 0 output of `/speckit.plan`.** Resolves the Technical Context's "best practices" and "patterns" tasks by documenting the decisions already in the codebase plus the new ones this plan adds. No NEEDS CLARIFICATION items remain after the 2026-05-29 `/speckit.clarify` session.

Findings consolidated below. Each decision section follows:

- **Decision**: what was chosen
- **Rationale**: why
- **Alternatives considered**: what else was evaluated

---

## Decision: Instagram fetcher — `instagrapi`

**Decision**: Use `instagrapi` (Python, MIT-licensed) as the sole Instagram fetcher.

**Rationale**: Personal accounts have no Graph API surface that gives full media + tagged-location data; instagrapi authenticates as the crawler via the mobile-app session protocol and returns rich `Media` objects (pk, code/shortcode, taken_at, caption_text, location.{name,lat,lng}, video_url, thumbnail_url, resources for albums, media_type code 1/2/8). Session resume via `cl.load_settings()` + `cl.login()` works across runs. Already shipped + battle-tested through the @ourearthsandwich (323 posts) and @welawen (693 posts) scrapes.

**Alternatives considered**:
- **Instagram Graph API** — requires business/creator accounts; this project's targets are personal. Originally specced as a fallback (FR-043); retired 2026-05-25 since personal accounts can't use it and maintaining two code paths doubled the test surface for marginal gain.
- **Browser automation (Playwright/Selenium)** — heavier, slower, more brittle to Instagram UI changes, easier to detect.
- **Unofficial reverse-engineered APIs** — same fragility as instagrapi but without its community maintenance.

---

## Decision: LLM provider — Anthropic SDK (Claude family)

**Decision**: Use the official `anthropic` Python SDK with `claude-sonnet-4-6` as the working model for both FR-019 (canonicalization) and FR-020 (inference).

**Rationale**: Already shipped; vision-capable (FR-020 inferred path attaches the image as a base64 block); tool-style prompts produce reliable JSON when the prompt explicitly constrains format (the prose-preamble parser + length cap handle the residual cases). The Cardinal Rule #3 naming hygiene (no `claude_*` identifiers; column = `reasoning`) keeps the model swappable without churning data.

**Alternatives considered**:
- **OpenAI / GPT-4o** — comparable capability; would require porting the SDK call sites. Rejected for v1 to avoid switching costs; the parser layer (`common/inference.py`) is the swap-point if we want to revisit.
- **Open-weights local model (e.g. LLaVA)** — eliminates per-call cost; quality lower for the inferred-location task; operationally heavier. Reserved for a future cost-driven swap.

---

## Decision: Substack fetcher — `feedparser` (RSS only)

**Decision**: New dependency for v1: `feedparser` (Python, BSD-licensed) to consume Substack publication RSS feeds.

**Rationale**: Substack exposes a stable RSS feed per publication (`<slug>.substack.com/feed`). RSS gives `<guid>` (canonical dedup key per the 2026-05-29 clarification), `<link>`, `<title>`, `<description>` (mapped to `subtitle` per FR-024), `<content:encoded>` (mapped to `body`), and `<pubDate>`. No auth needed; no anti-detection concern at the scale of one feed poll per publication per day.

**Alternatives considered**:
- **Substack official API** — not publicly documented for content ingestion; would require partner status.
- **Headless browser scraping** — overkill for an RSS feed.

---

## Decision: In-process scheduler — `APScheduler` (background mode)

**Decision**: Use `APScheduler` (Apache 2.0, mature) in background-scheduler mode within the App. Each pipeline service registers itself as a job with its own interval / cron expression (FR-074). The scheduler runs alongside the CLI; the CLI top-level dispatcher can start the scheduler with `python -m pile_app schedule` or run one-off services with `python -m pile_app run instagram --target ourearthsandwich`.

**Rationale**: Mature, well-documented, supports both interval and cron triggers, and is widely used in Python services. Multi-thread mode satisfies FR-107 (cross-service parallel: each service runs in its own thread; within-service sequentiality is enforced by service-internal logic).

**Alternatives considered**:
- **External cron + one-off CLI runs** — explicitly listed as compatible in the Assumptions; the CLI supports it. APScheduler in-process is the v1 default because it removes the OS-cron prerequisite.
- **`schedule` package** — simpler API but single-threaded; would force serial cross-service runs in violation of FR-107.
- **Native `asyncio` + custom loop** — more flexibility, more code to maintain.

---

## Decision: Anti-throttle rate presets — `aggressive` / `normal` / `gentle`

**Decision**: Keep the three rate presets already shipped (`aggressive`, `normal`, `gentle`) and document them as a per-service-runtime configuration choice (FR-051). Default for scheduled Instagram runs: `normal`. Default for Substack: `aggressive` (RSS is not throttle-sensitive at our scale).

**Rationale**: The three presets cover the operational range we've actually used:
- `aggressive` — no delays (used only for fully-warmed sessions or non-throttle-sensitive sources like RSS).
- `normal` — 30–90s inter-page jitter + 90–180s long rests every 5 pages + 1–3s per-post jitter. Default; ~300 posts/hr; survives 100+ runs against the same target.
- `gentle` — 90–180s inter-page jitter + 180–300s long rests every 3 pages + 2–5s per-post jitter. Used when a crawler is already warm-but-on-thin-ice.

**Alternatives considered**:
- **Adaptive throttling** — measure latency / 429 rate, scale delays automatically. More code; v1 fixed presets are predictable and easier to reason about during operator-driven recovery.

---

## Decision: Pile artifact format — TSV (v1), with future-DB allowance

**Decision**: For v1, pile artifacts are tab-separated text files (UTF-8 + BOM-free), one per `(service, target)` pair. Media files live in a parallel `pile/media/<service>/` directory, named `<target>_<canonical-id>.<ext>`. FR-104 reserves the option to add database-backed artifacts for future services.

**Rationale**: TSV is human-greppable, version-controllable in principle, and natively supported by the existing Python `csv` module. Tabs handle the embedded commas in captions / location strings cleanly. Pile is intentionally messy (Principle V); the bridge-app will impose schema later, not the producer.

**Alternatives considered**:
- **JSON Lines (`.jsonl`)** — better for nested fields; not needed for the flat schemas we have. Could be revisited per-service if a future service has nested artefacts.
- **SQLite per service** — gives query power inside the pile but adds a join-step for the bridge-app and obscures the "messy file pile" framing.
- **Parquet / columnar** — overkill at toy scale.

---

## Decision: Migration strategy — `scripts/instagram-fetch-latest/` → `pile-app/`

**Decision**: Migrate in a single dedicated phase (forthcoming Phase 18 in `tasks.md`) using these steps:

1. Create `pile-app/` at repo root with the structure laid out in `plan.md`.
2. Split the existing `scripts/instagram-fetch-latest/load_posts_tsv.py` module into per-service + common files (`instagram/pipeline.py`, `instagram/instagrapi_client.py`, `instagram/tagged_location.py`, `instagram/inferred_location.py`, `common/pile.py`, `common/inference.py`, `common/anti_throttle.py`, `common/run_logging.py`).
3. Move existing pile artefacts to the new locations: `posts.<target>.local.tsv` → `pile-app/pile/posts.<target>.local.tsv`; `public/media/<target>_*.jpg` → `pile-app/pile/media/instagram/<target>_*.jpg`; existing log files → `pile-app/logs/`.
3a. Move Instagram-service validation artefacts (NOT pile artefacts — these are the historical scaffolding of the scraper-iteration loop):
    - `posts.local.tsv` (hand-curated truth baseline) → `pile-app/instagram/validation/posts.local.tsv`
    - `docs/planning/scrape-diff.txt`, `scrape-diff-v3.txt`, `scrape-diff-v4.txt` (diff outputs from successive scraper iterations) → `pile-app/instagram/validation/`
    These remain in version control (unlike the pile under `pile-app/pile/` which is gitignored). The "truth baseline + diff" workflow that produced them will be formalized in a later spec amendment; until then this directory is the canonical home for the artefacts so they travel with the App per FR-110/FR-111.
4. Update `.gitignore`: drop `instagrapi_session.json` from the project root; add `pile-app/.env`, `pile-app/pile/`, `pile-app/logs/`, `pile-app/instagrapi_session.json` patterns. The `pile-app/instagram/validation/` directory is NOT gitignored — its contents are tracked.
5. Update CLAUDE.md, README.md, and roadmap.md pointers to reference `pile-app/` instead of `scripts/instagram-fetch-latest/`.
6. Migrate the test suite: move `scripts/instagram-fetch-latest/tests/` → `pile-app/tests/` and update test-target imports.
7. Verify SC-010 (copy `pile-app/` to a fresh empty repo; tests pass; scrape runs).
8. Delete `scripts/instagram-fetch-latest/` once the migration is verified.

**Rationale**: Single big-bang migration is the cleanest cut. The current location is already well-isolated (no external modules import from it), which keeps the migration mechanical. Tests pin the behaviour, so any regression would surface immediately.

**Alternatives considered**:
- **Gradual migration with symlinks** — adds complexity, leaves the repo in an ambiguous state for an indeterminate time.
- **Move without restructure** — would satisfy FR-110/FR-111 but leave the monolithic `load_posts_tsv.py` untouched; the Substack service can't slot in cleanly without the `common/` layer.

---

## Decision: Concurrency implementation — thread per service via APScheduler

**Decision**: APScheduler's `ThreadPoolExecutor` (default) dispatches each service's scheduled invocation to its own thread; within a service, all work is single-threaded sequential. Pile writes use file-level append + flush; the per-target TSV files are written by exactly one service, so cross-service file-lock contention is structurally absent.

**Rationale**: Satisfies FR-107 (cross-service parallel, within-service sequential) with minimal code. The thread-per-service model also gives the in-process scheduler natural isolation: an Instagram run cannot block a Substack run.

**Alternatives considered**:
- **`multiprocessing`** — heavier, doesn't share the Python session cache used by instagrapi.
- **`asyncio`** — would require rewriting the instagrapi calls into an async wrapper; instagrapi itself is sync.

---

## Decision: Upstream-deletion detection (FR-106) — incidental, not exhaustive

**Decision**: Detection runs only when the pipeline service happens to fetch a source response that should have contained a previously-pile'd record. For Instagram: incremental runs fetch the newest N pages; if a pile record's `shortcode` is missing from a fetched page that timestamp-wise should have contained it, mark the pile record `deleted_upstream: true` + `deleted_upstream_at: <timestamp>`. For Substack: each incremental poll re-reads the full RSS feed (Substack RSS feeds are usually capped at the last ~20 entries); pile records whose `<guid>` falls within the feed's covered date range but isn't present get the same tombstone.

**Rationale**: Matches the 2026-05-29 clarification — "only if upstream deletion is encountered naturally." No separate audit pass. Predictable cost: the detection is a side-effect of normal pagination, not a new pass.

**Alternatives considered**:
- **Full audit on each run** — explicitly rejected per clarification.
- **No detection at all (Option D from the clarification)** — would have been operationally simpler but loses the tombstone signal that the bridge-app might want.

---

## Decision: Operator notification — log + stdout, no out-of-band signalling for v1

**Decision**: Hard-block events (FR-052, FR-106 detection, inference exhaustion) write to the per-run log file (FR-070) and to stdout. No email / SMS / desktop notification. The operator is expected to monitor logs out-of-band (cron-driven `tail -n 50 logs/*.log | grep -E 'challenge|exhausted'` is a documented pattern in `quickstart.md`).

**Rationale**: Matches the spec's operator-as-owner posture (Q2/Q3/Q4 clarifications). Adding notification adds an SMTP / webhook surface that's out of scope. The retired FR-044 (email notification on session error) is intentionally not resurrected.

**Alternatives considered**:
- **Webhook-on-block** — useful but operator-specific; deferred to a future enhancement, not v1.
- **OS notification (Windows toast / macOS Notification Center)** — platform-coupling; out of scope.

---

## Open items deferred to planning of follow-on specs

- **Pile-to-Travelogue data flow** — belongs in the planned bridge-app spec (see roadmap.md).
- **Target-account allow-list enforcement** — operator-authorised stance recorded as implicit (Q5 declined); could be promoted to an enforced allow-list in a future amendment if the scope changes.
- **Scaling beyond ~10 targets per crawler** — deliberately out of v1 scope; the current rate-preset settings are tuned for this scale.

All decisions above unblock Phase 1 (data-model, contracts, quickstart).
