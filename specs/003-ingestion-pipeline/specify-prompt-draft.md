# /speckit.specify input prompt — 003 re-author (DRAFT)

> Edit the **Vision** section freely. The **Context** section is intended for
> /speckit.specify to read as background; you can trim it but it shouldn't
> grow much. After you're satisfied, paste the whole document as input to
> `/speckit.specify`.

---

## Context — original 003 scope (2026-05-22 split from 002)

When 003 was split off from 002 on 2026-05-22, the assumed scope was:

- Both Instagram (instagrapi + Graph API fallback) and Substack (RSS) ingestion live as **APScheduler jobs inside the backend FastAPI process** — there is no standalone CLI surface.
- The ingestion writes **directly into the production database** (`stops`, `instagram_posts`, `substack_posts` tables defined in 002's data-model).
- New stops get **auto-assigned to trips by date range**, with `miscellaneous-adventures` as the fallback trip.
- Geocoding via Claude in two paths: trust the verbatim Instagram geo-tag for FR-019, full image+caption inference for FR-020.
- Operator runs a one-time `python manage.py login` CLI to seed the instagrapi session; thereafter the scheduled jobs run unattended.
- On a session error: send an alert email to `automation@datacommlab.com` and exit; an external Instagram Graph API fallback existed as FR-043 (later retired 2026-05-25).

## Context — what's actually been built / decided since (as of 2026-05-27)

Reality has diverged substantially:

1. **The pipeline lives in `scripts/instagram-fetch-latest/load_posts_tsv.py`** as a standalone Python CLI — not as a backend module. No APScheduler integration exists; the operator invokes the script manually.
2. **Output is per-target TSV files** (`posts.<target>.local.tsv` in the project root) and media files (`public/media/<target>_<id>.<ext>`), **not database writes**. The TSV schema has 11 columns: `id, instagram_id, shortcode, media_url, caption, timestamp, location, lat, lng, region, reasoning`. This makes the pipeline a "raw data pile" producer (Roadmap data-unification-purpose / pile-app, see [docs/roadmap.md](../../docs/roadmap.md)), with the production Travelogue DB consuming from the raw pile through a future bridge-app, not directly.
3. **Crawler account is separate from target accounts.** `INSTA_USERNAME`/`INSTA_PASSWORD` authenticate a burner crawler; one or more targets are passed via `--targets ourearthsandwich,welawen` or `INSTAGRAM_TARGET_ACCOUNTS` env. Multi-target is first-class.
4. **Anti-throttle and resilience are built in.** `--rate {aggressive,normal,gentle}` presets bundle page-size, inter-page jitter, periodic long rests, and per-post jitter. Page-fetch errors are categorized into challenges (no retry; manual operator verification required) vs. transient (one retry with 60–180s backoff). Mid-pagination failure preserves partial progress.
5. **Streaming model.** Pages are processed one at a time — each page's rows are written + flushed before the next page is fetched. Page-level crash recovery. After streaming completes, a post-pass re-sorts the TSV by timestamp ASC, renumbers ids 1..N, renames media files via two-pass swap, and sweeps orphan media files matching the target's prefix.
6. **Tagged-path canonicalization (FR-019 evolution).** The LLM is called with the verbatim Instagram geo-tag + lat/lng and returns both a canonical "Venue, City, Country" name AND the IATA region in one JSON. The verbatim tag is no longer stored as-is — the canonical form is.
7. **Inferred-path reasoning is preserved (FR-020 evolution).** When the LLM writes prose before its JSON, the prose is captured in the `reasoning` column instead of being discarded. The JSON-extraction parser handles markdown fences AND prose preambles.
8. **No-inference fallback uses the prior post's city** (not its venue) and inherits lat/lng/region from that prior post. The fallback note goes in `reasoning`. Triggers only when inference returns empty AND a prior row exists.
9. **Observability.** Each scrape prints an upfront ETA (derived from `media_count` on the user lookup + the active rate preset), per-page completion timing, and an anti-throttle delay log. Per-target scrape log files are auto-swept on each run (keep the most recent 5).
10. **No backend integration exists yet.** No APScheduler jobs, no `python manage.py login` CLI, no SMTP email for session errors, no trip auto-assignment, no writes to 002's tables. All of those are deferred.
11. **Substack ingestion hasn't been built at all.** RSS poller is still vapor.

## Vision — what the new 003 spec should cover

> _Rewrite this section freely. The bullets below are a first-pass starting
> point; trim, add, reframe at will._

The new 003 spec should describe the **automated content-ingestion pipeline as a raw-data-pile producer** for the Earth Sandwich travelogue — distinct from the production Travelogue DB, which 002 owns and which consumes from the raw pile through a future integration path.

In scope:

- **Instagram ingestion via instagrapi** for one or more target accounts, authenticated as a separate crawler account. Multi-target is a first-class requirement, not an extension.
- **Anti-throttle behavior** appropriate for high-volume periodic scrapes from a single residential IP: spaced/jittered requests, smaller page sizes, long-rest pauses, retry-with-backoff for transient errors, hard stop with operator-facing surface on Instagram challenge / checkpoint flows.
- **Streaming + crash recovery** as a design property: partial progress survives mid-scrape interrupts; subsequent incremental runs resume from the most recent persisted row.
- **Dual-path geocoding** preserving the existing FR-019 (tagged) vs FR-020 (inferred) split, plus canonicalization for tagged tags and a city-level fallback when inference fails. The LLM's reasoning is preserved alongside its conclusions in an audit-able column.
- **Per-target TSV output + shared media directory** as the canonical raw-pile format. Schema includes `reasoning` for LLM rationale.
- **Substack ingestion via RSS** as a parallel pipeline, also writing to per-target TSV files (one TSV per Substack publication).
- **CLI surface** for one-off invocation, with rate preset and target list selectable per run. Recurring execution may be a wrapper concern (cron / Task Scheduler / backend hook) rather than baked into the script.

Out of scope (defer to other specs):

- Writing into 002's production tables (`stops`, `instagram_posts`, etc.). The handoff from raw pile → Travelogue DB is a separate spec / future work.
- Trip auto-assignment by date range (FR-040 original) — belongs in the raw-pile-to-Travelogue-DB layer.
- Email notifications for session errors (SMTP) — operator-facing stdout prompts are sufficient for v1.
- Object storage / S3 for media — local filesystem is fine.

Additional Notes and Clarifications:

- Backend APScheduler integration — scheduling is in-scope for this pipeline
- The canonical name (FR-019) should be stored alongside the verbatim tag. 
- For the no-inference fallback, the heuristic city extraction has a known limitation (US "City, State, Country" tags resolve to state). This should be ugraded to an LLM-based extractor ot translate place to city.
- There will be a seperate Epic to define how the production Travelogue DB will eventually pick up from the raw pile? It is out of scope for 003. 003 is meant to produce a "pile", another workflow will operate on this intentionally messy starting point.

The Instagram pipeline's success criteria should center on **completeness** (every public post from a target lands in the TSV), **idempotency** (incremental runs produce no duplicates), **resilience** (mid-scrape interrupts preserve work), and **anti-detection longevity** (the crawler account doesn't get suspended within N successful runs). Future pipelines such as Substack should generally adhere to the same goals, but with flexibility for the case in hand.

**Key Vision Points - These Should Overrule Any Other Contradicting Statements**

- In general, any inference step in a data pipeline should retain the original inputs for the inference.
- The products of this epic is meant to be treated as a self-contained "App". The final product of the ingestion workflow is the "pile" which consitutes of file folders and DB's which holds the final data of the various ingestion workflows (Instagram, Substack, etc.). This pile is the only thing that will surface to other Apps in this project.
- The purpose of the "pile" is to represent/simulate a messy data warehouse, data lake, snowflake repository, whatever you call the result of initiatives to "centralize" data by collecting things from disparate sources and dumping them in the same vicinity.
- Within this data ingestion "App", each of the individual pipelines that extract data from a source and put them in the pile should also be segregated. These are meant to represent various unrelated upstream workflows and should each be treated as thier own stand alone service. From the persepective of downstream processes in this project on the other side of the "pile", these services are unknown and mysterious.
- The disparate pipeline services can feed piles of different types, some may create tsv files, some may feed DB's. Each pipeline service feeds one pile. One pile may be fed by 1 or more pipeline services.