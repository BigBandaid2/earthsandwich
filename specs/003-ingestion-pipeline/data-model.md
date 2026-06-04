# Data Model: Ingestion Pipeline App

**Phase 1 output of `/speckit.plan`.** Documents the entities the App owns + the schemas of the pile artifacts the App produces. Producer-side only — the bridge-app's downstream interpretation is out of scope (and intentionally so per Roadmap Principle V "messy pile").

The pile is the only data surface that crosses the App boundary. Everything else in this document is internal to `pile-app/`.

---

## Entity overview

| Entity | Kind | Owner | Persistence |
|---|---|---|---|
| **Instagram Pile Record** | Pile artifact (per-target row) | `instagram/pipeline.py` | `pile-app/pile/posts.<target>.local.tsv` (one TSV per target) |
| **Instagram Media File** | Pile artifact (binary) | `instagram/pipeline.py` | `pile-app/pile/media/instagram/<target>_<shortcode>.<ext>` |
| **Substack Pile Record** | Pile artifact (per-publication row) | `substack/pipeline.py` | `pile-app/pile/articles.<publication>.local.tsv` (one TSV per publication) |
| **Crawler Session** | Internal state | `instagram/instagrapi_client.py` | `pile-app/instagrapi_session.json` |
| **Run Log** | Internal observability | `common/run_logging.py` | `pile-app/logs/scrape-<service>-<target>-<YYYYMMDD-HHMMSS>.log` |
| **Service Schedule Config** | Configuration | `common/scheduler.py` | `pile-app/config.yml` |
| **Rate Preset** | Configuration enum | `common/anti_throttle.py` | code constant |
| **Truth Baseline TSV** | Validation scaffolding (informal) | Instagram service maintainer (hand-curated) | `pile-app/instagram/validation/posts.local.tsv` |
| **Scrape Diff Report** | Validation scaffolding (informal) | Ad-hoc diff tooling vs. truth baseline | `pile-app/instagram/validation/scrape-diff*.txt` |

---

## Pile artifact: Instagram TSV

**Path**: `pile-app/pile/posts.<target>.local.tsv` (UTF-8, no BOM, LF newlines). One TSV per target account.

**Spec references**: FR-006 (per-target TSV), FR-018 (column set), FR-019 (tagged path canonicalization), FR-020 (inferred path), FR-022 (dedup: shortcode canonical, instagram_id retained), FR-105 (inference inputs preserved), FR-106 (upstream-deletion tombstone).

### Columns (in TSV order)

| # | Column | Type | Required | Source | Notes |
|---|---|---|---|---|---|
| 1 | `id` | int | yes | post-pass `sort+reid` | Local sequential 1..N after final sort by `timestamp ASC`. Not stable across runs; re-numbered after every incremental run. |
| 2 | `instagram_id` | string (numeric) | yes | instagrapi `Media.pk` | Instagram's primary key. Retained for traceability per FR-022 even though `shortcode` is the canonical dedup key. |
| 3 | `shortcode` | string | yes | instagrapi `Media.code` | **Canonical dedup key** per 2026-05-29 clarification. Maps to the public URL slug (`instagram.com/p/<shortcode>/`). |
| 4 | `tag_verbatim` | string | optional | instagrapi `Media.location.name` | Original Instagram-reported geo-tag name, preserved per FR-019 + FR-105. Empty if the post had no tag. |
| 5 | `lat_verbatim` | decimal string | optional | instagrapi `Media.location.lat` | **Original instagrapi-reported latitude for the tag**. Preserved per FR-105 / Cardinal Rule #4 as an input to the canonicalization LLM call (FR-019). Empty if the post had no tag. In v1 the canonicalization call does not modify lat/lng, so this matches the `lat` column for tagged-path rows; the dedicated column makes the principle explicit and forward-compatible if the canonicalizer later snaps lat/lng to a venue centroid. |
| 6 | `lng_verbatim` | decimal string | optional | instagrapi `Media.location.lng` | Original instagrapi-reported longitude for the tag. Same rationale as `lat_verbatim`. Empty if no tag. |
| 7 | `media_url` | string (relative path) | yes | local filesystem | POSIX-style relative path to the corresponding media file under `pile-app/pile/media/instagram/`. Example: `pile/media/instagram/ourearthsandwich_ABC123.jpg`. |
| 8 | `caption` | string | optional | instagrapi `Media.caption_text` | Original post caption, verbatim. Tab → space replacement applied on write to preserve TSV structure. Preserved per FR-105 (inference input for the inferred-path call). |
| 9 | `timestamp` | ISO 8601 UTC | yes | instagrapi `Media.taken_at` | Example: `2024-08-12T14:32:00Z`. Used as the sort key in the post-pass. |
| 10 | `location` | string | optional | LLM canonicalization (FR-019) or inference (FR-020) | Canonical `Venue, City, Country` form. Empty if neither path resolved a location and the fallback didn't fire. |
| 11 | `lat` | decimal string | optional | tagged path → instagrapi (currently equals `lat_verbatim`); inferred path → LLM JSON; fallback → inherited from prior row | Empty when no location resolved. |
| 12 | `lng` | decimal string | optional | as `lat` | Empty when no location resolved. |
| 13 | `region` | string (3-letter) | optional | LLM canonicalization or inference (IATA region code) | Empty when no location resolved. |
| 14 | `reasoning` | string | optional | LLM prose preamble + fallback annotations | Audit column. Holds the LLM's prose before its JSON (FR-020 evolution), plus any fallback notes like `fallback: inherited from prior post timestamp <ts>`. Preserved per FR-105. Tab → space replacement applied. |
| 15 | `deleted_upstream` | boolean (`true`/`""`) | optional | FR-106 incidental detection | Empty when never observed deleted. `true` if a later run encountered the post's absence in a fetched page whose timestamp range should have included it. |
| 16 | `deleted_upstream_at` | ISO 8601 UTC | optional | FR-106 detection timestamp | Set the first time the tombstone is applied; never overwritten on subsequent re-detections. Empty when `deleted_upstream` is empty. |

### Header row

```text
id<TAB>instagram_id<TAB>shortcode<TAB>tag_verbatim<TAB>lat_verbatim<TAB>lng_verbatim<TAB>media_url<TAB>caption<TAB>timestamp<TAB>location<TAB>lat<TAB>lng<TAB>region<TAB>reasoning<TAB>deleted_upstream<TAB>deleted_upstream_at
```

### Verbatim-input columns: which inference inputs are preserved where

Per Cardinal Rule #4 (inference inputs preserved) and FR-105, each LLM call's inputs MUST be recoverable from the TSV row alone. The mapping per path:

| Path | LLM inputs | Where the inputs live in the row |
|---|---|---|
| **Tagged (FR-019 canonicalization)** | `tag_verbatim`, `lat_verbatim`, `lng_verbatim` | columns 4, 5, 6 |
| **Inferred (FR-020 vision+text)** | `caption`, `media_url` (the file the model saw) | columns 8, 7 |
| **Fallback (no inference)** | prior row's `location` city + `lat` / `lng` / `region` | implicit (rationale recorded in `reasoning`) |

The `reasoning` column captures the LLM's own narration (prose preamble before its JSON) — the model's "input to its output" rather than the call's input. Both are kept because future audits may want to replay the call or critique the reasoning, and dropping either would violate the principle.

### Validation / invariants

- `shortcode` is the dedup key: at most one row per `(target, shortcode)` pair in a given TSV (per FR-022).
- `instagram_id` MUST also be unique per TSV (instagrapi guarantees pk uniqueness; we trust this).
- `id` is re-numbered 1..N after every post-pass `sort+reid`; consumers MUST NOT treat `id` as stable.
- `timestamp` MUST parse as ISO 8601 UTC; the post-pass relies on it for sorting.
- Caption and reasoning columns MUST escape embedded tabs (`\t` → single space on write).
- If `tag_verbatim` is non-empty, `lat_verbatim` and `lng_verbatim` MUST also be non-empty (instagrapi always returns lat/lng with the location object). The inverse holds too: empty tag ⇒ empty lat/lng verbatim.
- A row MAY have empty `location` / `lat` / `lng` / `region` (no resolution achieved); it MUST NOT be dropped.
- A row MAY have `deleted_upstream` = `true` AND non-empty location data: the tombstone is additive, not destructive (per FR-105 — preserve inference inputs).

### State transitions

A row has these observable states across runs:

1. **Created** — first incremental run that encounters the post writes the row with location/inference data and empty deletion fields.
2. **Refreshed in place** — subsequent runs that re-encounter the same `shortcode` MAY update mutable fields (caption edits, location data if previously empty) but MUST NOT touch `instagram_id` or `shortcode`. The default-shipping behaviour today is no-op skip on re-encounter, which is acceptable.
3. **Tombstoned** — a run that fetches a page whose timestamp range covers an existing pile row's `timestamp`, where the row's `shortcode` is absent from the fetched page, sets `deleted_upstream` = `true` and `deleted_upstream_at` = `<now>`. The row is otherwise preserved.

State 2-→1 (un-deletion) is not supported in v1; once tombstoned, always tombstoned. If the post reappears upstream the operator handles this manually.

---

## Pile artifact: Instagram Media File

**Path**: `pile-app/pile/media/instagram/<target>_<shortcode>.<ext>`

**Spec references**: FR-007 (media download), FR-006 (path stored in TSV), FR-022 (sort+reid renaming).

### File-name convention

- **Prefix**: `<target>_` — the target account's handle, lowercase, no `@`.
- **Identifier**: `<shortcode>` — the same `shortcode` that appears in the TSV row's `shortcode` column. Aligning the on-disk name with the canonical dedup key (per the 2026-05-29 clarification) means the post-pass `sort+reid` no longer needs to rename media files. Today's implementation uses local `<id>`; updating to `<shortcode>` is a migration item in `tasks.md`.
- **Extension**: derived from media type:
  - Photo (instagrapi `media_type == 1`) → `.jpg`
  - Video (instagrapi `media_type == 2`) → `.mp4`
  - Album (instagrapi `media_type == 8`) → use the first child's extension; one file per album (album-as-album persistence is a deferred enhancement, not in v1).

### Orphan sweep

After the post-pass completes, the service deletes any file in `pile-app/pile/media/instagram/` matching `<target>_*` whose `<shortcode>` portion is not referenced by any surviving TSV row. Per FR-022 this prevents orphan media files accumulating after re-runs.

---

## Pile artifact: Substack TSV

**Path**: `pile-app/pile/articles.<publication>.local.tsv` (UTF-8, LF). One TSV per Substack publication slug (e.g., `articles.welalive.local.tsv`).

**Spec references**: FR-023 (per-publication TSV), FR-024 (dedup: `<guid>` canonical, `<link>` retained), FR-106 (upstream-deletion tombstone).

### Columns (in TSV order)

| # | Column | Type | Required | Source | Notes |
|---|---|---|---|---|---|
| 1 | `id` | int | yes | post-pass `sort+reid` | Local sequential 1..N after sort by `published_at ASC`. |
| 2 | `substack_id` | string | yes | RSS `<guid>` | **Canonical dedup key** per 2026-05-29 clarification. |
| 3 | `link` | string (URL) | yes | RSS `<link>` | Public URL of the article. Retained per FR-024. |
| 4 | `title` | string | yes | RSS `<title>` | |
| 5 | `subtitle` | string | optional | RSS `<description>` | RSS convention treats `<description>` as the article's deck. |
| 6 | `body` | string (HTML) | yes | RSS `<content:encoded>` | Tab → space on write to preserve TSV structure. |
| 7 | `published_at` | ISO 8601 UTC | yes | RSS `<pubDate>` parsed | Sort key. |
| 8 | `deleted_upstream` | boolean | optional | FR-106 detection | As per Instagram. |
| 9 | `deleted_upstream_at` | ISO 8601 UTC | optional | FR-106 detection | As per Instagram. |

### Header row

```text
id<TAB>substack_id<TAB>link<TAB>title<TAB>subtitle<TAB>body<TAB>published_at<TAB>deleted_upstream<TAB>deleted_upstream_at
```

### Validation / invariants

Same shape as Instagram: `substack_id` uniqueness per TSV; `id` re-numbered each run; body MUST escape tabs.

Substack v1 has no LLM inference step, so the verbatim-input columns from the Instagram schema have no Substack equivalent. If a future Substack enhancement extracts locations from article bodies via LLM, that spec amendment MUST add verbatim columns for the inputs it relies on, per Cardinal Rule #4.

### Substack-specific notes

- Substack RSS feeds are typically capped at the most-recent ~20 entries; the App MUST NOT assume the feed covers the full publication history. A first-time pull captures only what RSS exposes; older posts are out of scope for v1.
- The first article body in the RSS often includes a `<![CDATA[...]]>` wrapper; the `feedparser` library strips this automatically.
- No media file artifact for Substack v1: article images stay as `<img>` tags in the HTML body. A future enhancement may extract them, but the bridge-app can render the HTML directly without that step.

---

## Internal: Crawler Session

**Path**: `pile-app/instagrapi_session.json` (gitignored).

**Spec references**: FR-001 (instagrapi authentication), FR-052 (challenge detection).

### Shape

JSON object produced by `instagrapi.Client.dump_settings()`. Opaque to this App; we store and reload it via `load_settings()` / `dump_settings()`. Contains:

- Device + UUID fingerprints (one-time generated; stable across sessions to look like the same device)
- Cookies + access tokens
- User-Agent metadata

### Lifecycle

1. **Bootstrap** (first run only) — `instagrapi.Client.login(username, password)` performs a fresh login using the burner crawler credentials from `.env`, then `dump_settings()` writes the session.
2. **Resume** (subsequent runs) — `load_settings()` then `login()` reuses the session without a fresh credential exchange. `login()` is a no-op when the session is still valid.
3. **Hard-block** — a challenge / checkpoint error during `login()` or any `user_medias_paginated_v1` call causes the service to halt (FR-052). The session file is NOT deleted; operator MUST resolve the challenge in a browser using the same account, then re-run.

---

## Internal: Run Log

**Path**: `pile-app/logs/scrape-<service>-<target>-<YYYYMMDD-HHMMSS>.log`

**Spec references**: FR-070 (per-run log), FR-072 (sweep retains 5 most recent per target).

### Format

Plaintext, line-oriented, UTC timestamped. One log line per event. No structured logging requirement in v1.

Example:

```text
2026-05-29T14:32:00Z [INFO] scrape start target=ourearthsandwich rate=normal
2026-05-29T14:32:03Z [INFO] user lookup: 323 media reported by instagrapi
2026-05-29T14:32:03Z [INFO] ETA: ~64 min (323 posts @ ~300 posts/hr normal preset)
2026-05-29T14:32:08Z [INFO] page 1/14 fetched (24 posts)
2026-05-29T14:32:11Z [INFO] page 1 written (24 rows, 0 skipped, 24 media files)
2026-05-29T14:32:11Z [INFO] inter-page sleep: 47.2s
2026-05-29T14:32:58Z [INFO] page 2/14 fetched (24 posts)
...
2026-05-29T15:36:01Z [INFO] post-pass: sort+reid complete (323 rows)
2026-05-29T15:36:02Z [INFO] orphan sweep: 0 files removed
2026-05-29T15:36:02Z [INFO] scrape end target=ourearthsandwich elapsed=01:04:02
```

### Sweep policy

After each run, the service enumerates `pile-app/logs/scrape-<service>-<target>-*.log`, sorts by mtime descending, and deletes files beyond the 5 most recent. Per FR-072. Sweep runs in the success path AND the hard-block path; the current run's log is always one of the 5 retained.

---

## Internal: Service Schedule Config

**Path**: `pile-app/config.yml` (YAML, version-controlled).

**Spec references**: FR-017 (per-service schedules), FR-074 (operator-tunable cadence), FR-107 (concurrency model).

### Shape

```yaml
schedules:
  instagram:
    enabled: true
    cadence: "interval:hours=1"      # APScheduler trigger spec
    rate_preset: "normal"
    targets:
      - "ourearthsandwich"
      - "welawen"
  substack:
    enabled: true
    cadence: "cron:hour=6,minute=0"  # daily 06:00 local
    rate_preset: "aggressive"
    publications:
      - "welalive"
```

### Validation

- `enabled` MUST be boolean.
- `cadence` MUST parse as either `interval:<kwargs>` or `cron:<kwargs>` where kwargs are valid APScheduler arguments.
- `rate_preset` MUST be one of `aggressive` / `normal` / `gentle`.
- `targets` / `publications` MUST be non-empty when `enabled: true`.

---

## Internal: Rate Preset (enum)

**Spec references**: FR-051 (anti-throttle), Research's `aggressive` / `normal` / `gentle` decision.

Implemented as a `dataclass` constant lookup in `common/anti_throttle.py`. Three named presets, each defines:

- `page_size: int` — max posts per page fetched from instagrapi
- `inter_page_jitter: tuple[float, float]` — `(min_seconds, max_seconds)` for the random sleep between pages
- `long_rest_every_n_pages: int` — periodic deeper sleep cadence
- `long_rest_jitter: tuple[float, float]` — random sleep range for the deeper rest
- `per_post_jitter: tuple[float, float]` — random sleep range between individual post processings

No runtime mutation; presets are constants. The `--rate` CLI flag selects which preset's values flow through the run.

---

## Informal: Instagram validation scaffolding

**Path**: `pile-app/instagram/validation/`

These artefacts support the iterative scraper-improvement loop ("produce pile → diff against truth → tweak scraper → re-produce → diff again"). They are NOT pile artefacts and are NOT consumed by the bridge-app. They live under the Instagram service so they travel with the App per FR-110/FR-111.

| File | Kind | Notes |
|---|---|---|
| `posts.local.tsv` | Truth baseline | Hand-curated TSV with the same shape as the Instagram pile TSV. Locations were entered by the operator from memory + photos and treated as ground truth when iterating the canonicalization + inference logic. Schema may drift from the producer's current TSV columns; that's tolerated until the comparison process is formalized. |
| `scrape-diff.txt`, `scrape-diff-v3.txt`, `scrape-diff-v4.txt` | Diff reports | Output from ad-hoc tooling that compared a fresh scrape against `posts.local.tsv`. Bucketed by failure mode (e.g., `old_appends_country`, `truly_different`). Preserved as a history of scraper-improvement deltas; not regenerated automatically. |

A future spec amendment will formalize the truth-baseline + diff workflow (likely with a `python -m pile_app validate instagram <target>` subcommand and a structured-diff format). Until that lands, these files are an informal but tracked-in-git scaffold.

---

## Notes on what's NOT in the data model

These are deliberately absent so the bridge-app gets a clean producer-side contract:

- **No `trip_id` / `region_metadata` / `editorial_status`** columns. The producer doesn't know about trips, doesn't curate, doesn't moderate. The bridge-app adds those when it writes into 002's schema.
- **No `source_app` column.** The TSV file's name (`posts.<target>.local.tsv` vs `articles.<publication>.local.tsv`) encodes the source.
- **No JSON columns.** Everything in the pile is flat strings. Per Principle V — the pile is intentionally messy and easy to grep.
- **No relational links between Instagram and Substack TSVs.** Each pile artifact stands alone; correlation across services is a bridge-app concern.
