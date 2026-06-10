# Feature Specification: Ingestion Pipeline App

**Feature Branch**: `003-ingestion-pipeline`
**Created**: 2026-05-27
**Status**: Draft
**Input**: Re-authored from scratch on 2026-05-27 to reflect the App-shaped scope that emerged over the two weeks following the 2026-05-22 split. Previous spec versions are preserved in git history; this document supersedes them. Completed phases in `tasks.md` are retained as a historical record per project Cardinal Rule #1.

## Overview

This spec defines the **Ingestion Pipeline App** — a self-contained collection of segregated pipeline services that extract content from disparate upstream sources (Instagram, Substack, future others) and deposit the results into a single conceptual **pile**.

The App is **physically self-contained**: all of its code, tests, configuration, run artifacts, and pile contents live within a single root directory at the project level. The App's directory is movable as a unit to a different project or repository without requiring changes to either the App or to the source project's other code. Only the speckit working-process artifacts (this spec, JIRA mapping, planning docs) remain at the parent project's root since they're part of the cross-App PM scaffolding.

The pile is the App's sole downstream surface. Other Apps in the project **never read the pile directly**. A future **bridge-app** (see [roadmap.md](../../docs/roadmap.md)) sits between the pile and any consumer (the Travelogue DB, the front-end, future consumers); the bridge-app is responsible for cleaning, normalization, and mapping pile artifacts into consumer-ready shapes. The pile-to-bridge handoff is the only contract this App exposes; what happens downstream of that is out of scope.

The pile is intentionally messy — it represents the kind of artifact a real organization gets when it "centralizes" disparate sources into a common vicinity (data lake / warehouse / Snowflake repository). Each pipeline service is treated as an opaque external workflow from the perspective of downstream consumers; the App is the toy-scale stand-in for the Data Unification project's App 1 (Raw Data Pile) in the project roadmap.

## Clarifications

### Session 2026-05-29

- Q: What's the canonical dedup identity per source for pile artifacts? → A: Per Option A with Instagram canonical = `shortcode`. Instagram pile records carry both `shortcode` (canonical, used for dedup + downstream lookups) and `instagram_id` (the numeric Instagram pk, retained alongside for traceability). Substack pile records carry both `<guid>` (canonical, used for dedup) and `<link>` (retained alongside).
- Q: Do pile artifacts have a retention policy or do they persist indefinitely? → A: Indefinite. Pile artifacts are not auto-pruned. The operator handles manual pruning if storage becomes an issue. Matches the App's role as a raw data pile producer — the bridge-app and the eventual bridge-builder-app's value depend on full historical content being available.
- Q: What happens when an upstream post is deleted after the pile already has it? → A: Option B with light-touch detection only. When the pipeline service naturally encounters source-side absence during normal operation (a previously-stored post is missing from a source response that should have contained it), it marks the pile record with a tombstone field (e.g., `deleted_upstream: true` plus the date detected). The service does NOT run a separate audit pass to proactively check older records — detection is incidental, not exhaustive. Pile records are never physically removed by the service.
- Q: What's the concurrency model when schedules fire at overlapping times? → A: Option C — each source type IS its own pipeline service, fully independent and indifferent of other pipeline services; they may run concurrently when their schedules coincide. **Within** a single pipeline service, work is sequential by default (one target, one page, one record at a time) unless a specific run is justified to deviate. Anti-detection constraints live entirely within a single service.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scrape a target Instagram account into the pile (Priority: P1)

The operator configures one or more public Instagram target accounts and runs the Instagram pipeline service. The service authenticates as a separate crawler account (never as a target), paginates each target's feed, downloads media, geo-locates each post, and writes a record per post to the pile. Re-running the service against the same target is idempotent.

**Why this priority**: This is the App's primary use case at v1 and exercises the bulk of the pipeline behavior (auth, pagination, media handling, geo-location, idempotency).

**Independent Test**: Configure crawler credentials and a public target. Run the Instagram pipeline service. Verify the pile contains one record per post with media, location, and inference reasoning preserved. Re-run the service; verify zero new records.

**Acceptance Scenarios**:

1. **Given** valid crawler credentials and a public target, **When** the Instagram pipeline service runs from a fresh state, **Then** every public post from that target is represented in the pile in chronological order, with media downloaded and a location resolved.
2. **Given** the pile already contains records for a target up to a known timestamp, **When** the pipeline service runs again, **Then** only posts newer than that timestamp are fetched and appended; existing records are unchanged.
3. **Given** a post with an explicit Instagram geo-tag, **When** the service processes it, **Then** the pile retains the verbatim tag, the canonical location form, and the original lat/lng/region.
4. **Given** a post with no geo-tag, **When** the service processes it, **Then** an inference call produces a location from the post's caption and media, the inference rationale is recorded alongside the result, and the original inputs to the inference (caption + media reference) are preserved.
5. **Given** an inference call produces no usable location, **When** a chronologically-prior pile record exists, **Then** the service falls back to that prior record's city (not its exact venue) and inherits its lat/lng/region; the fallback is identifiable in the pile.

---

### User Story 2 - Pipeline service survives upstream throttling (Priority: P1)

Instagram (and other social sources) aggressively detect automated access. The Instagram pipeline service must space requests, back off on transient errors, distinguish hard blocks from transient errors, and preserve partial progress when interrupted. Mid-scrape failures must not lose work already persisted to the pile.

**Why this priority**: Without this, the P1 scrape use case cannot reach completion for any source with non-trivial history. This is the gating reliability property.

**Independent Test**: Inject a transient error mid-pagination; verify the service backs off and resumes. Inject a hard-block error (challenge / checkpoint); verify the service halts cleanly, surfaces an operator-readable signal, and preserves all artifacts already written. Re-run after operator action; verify resumption from the last persisted record.

**Acceptance Scenarios**:

1. **Given** a transient upstream error during pagination, **When** the pipeline service encounters it, **Then** the service backs off for a randomized delay and retries once; subsequent successful pages proceed normally.
2. **Given** a hard-block challenge / checkpoint from the upstream source, **When** the pipeline service detects it, **Then** the service does NOT retry, halts pagination, surfaces an operator-facing prompt explaining the required manual verification, and preserves all artifacts already written to the pile.
3. **Given** a pipeline service is interrupted mid-page (process killed, network drop), **When** the operator re-invokes the service, **Then** the next run resumes from the most recent pile artifact and re-fetches only the missing tail.
4. **Given** an inference call fails (rate-limited, credits exhausted, service unavailable), **When** the pipeline service encounters it, **Then** the failure is treated as a hard block — processing halts, the operator is notified, and pile artifacts already written are preserved.

---

### User Story 3 - The pile is consumed only via a bridge-app, never directly (Priority: P2)

The pile is produced by this App and is read by exactly one consumer: a future bridge-app. The bridge-app handles cleaning, normalization, and mapping pile artifacts to consumer-ready data for downstream Apps (Travelogue DB, front-end, etc.). The bridge-app is out of scope here; what matters in this spec is that the pile's structure is the App's contract with the bridge-app, and that no other consumer reaches into the pile.

The App itself is also **physically self-contained**: code, tests, run artifacts, and pile contents all live in a single root directory that's movable to a separate project or repo without affecting either side.

**Why this priority**: This validates the App-as-black-box property and the physical-segregation property that together let this App be developed, tested, deployed, and even relocated independently of the rest of the project.

**Independent Test**: Two halves — (a) Confirm no project source outside the App's root directory contains a path reference reaching INTO the App's pile (grep across the rest of the project for the pile directory name returns zero hits in non-spec code). (b) Copy the App's root directory to an empty fresh project; verify it runs end-to-end (an Instagram scrape against a public target completes; all tests pass).

**Acceptance Scenarios**:

1. **Given** the pile contains artifacts from multiple pipeline services, **When** the bridge-app reads from the pile, **Then** it accesses artifacts through pile-level conventions (file paths, table names) without referring to any pipeline service's code or names.
2. **Given** a pipeline service is replaced with a different implementation (same pile output contract), **When** the bridge-app reads the pile, **Then** it observes no difference.
3. **Given** the App's root directory is copied to a fresh project, **When** the test suite is run inside the new copy, **Then** all tests pass.
4. **Given** any non-spec file in the parent project, **When** searched for references reaching into the App's pile, **Then** zero matches are found (the project's other code never points into the App's data).

---

### User Story 4 - Scrape a Substack publication into the pile (Priority: P2)

The operator configures one or more Substack RSS feed URLs and runs the Substack pipeline service. The service polls each feed, persists each new article's title, subtitle, body, and publication date to the pile, and is idempotent across re-runs.

**Why this priority**: The Substack source proves the App's "multiple disparate pipelines" property and provides the long-form narrative layer of the travelogue. It's the second source built after Instagram.

**Independent Test**: Configure an RSS URL. Run the Substack pipeline service. Verify new articles appear in the pile. Re-run; verify no duplicates.

**Acceptance Scenarios**:

1. **Given** a configured RSS feed URL, **When** the Substack pipeline service runs, **Then** every entry not already in the pile is persisted with title, subtitle, body, and publication date.
2. **Given** an RSS feed entry already in the pile, **When** the service runs again, **Then** no duplicate is created.
3. **Given** an RSS feed URL is unreachable, **When** the service runs, **Then** the service logs the error, exits cleanly, and leaves existing pile artifacts unchanged.

---

### User Story 5 - Pipeline services run on a recurring schedule (Priority: P3)

Each pipeline service can be configured to run on a recurring schedule (e.g., Instagram approximately hourly, Substack approximately daily). Schedules are configured per-service. The operator does not need to manually invoke a service for each run.

**Why this priority**: Recurring scheduling is how the App stays current without operator effort. For v1 it can be deferred to an external scheduler, but the App is expected to support an in-process scheduler.

**Independent Test**: Configure a recurring schedule for the Instagram pipeline service at a short interval. Leave the App running. Verify a run executes at the next interval boundary and produces the expected pile artifacts.

**Acceptance Scenarios**:

1. **Given** a recurring schedule configured for a pipeline service, **When** the schedule fires, **Then** the service runs and persists any new pile artifacts.
2. **Given** two pipeline services have different schedules, **When** their schedules fire, **Then** each service runs independently without coordinating with the other.

---

### User Story 6 - A new pipeline service is added for a new source (Priority: P3)

The operator extends the App with a new pipeline service for a new upstream source (a different social platform, a blog RSS, an export file format). Existing pipeline services are untouched. The new service follows the same App-level conventions (writes to the pile, preserves inference inputs, etc.) but is otherwise free to choose its own techniques.

**Why this priority**: This validates the segregation / extensibility property. The App's architecture should make the marginal cost of adding a new source roughly proportional to that source's complexity, not to the existing service count.

**Independent Test**: Add a new pipeline service module that writes a single test artifact to the pile (a fake source). Verify the existing Instagram and Substack services still work unchanged. Verify the new service's artifact is readable through the pile's conventions.

**Acceptance Scenarios**:

1. **Given** an existing App with Instagram and Substack services, **When** the operator adds a new pipeline service, **Then** no existing service file or configuration requires modification.
2. **Given** a new pipeline service writes to the pile, **When** a downstream consumer reads the pile, **Then** the new artifacts are visible through the same pile conventions as existing artifacts.

---

### Edge Cases

- What happens when the crawler account is hit by an Instagram challenge / checkpoint? *(Pipeline service halts, surfaces operator-facing prompt explaining the required manual verification, preserves all artifacts already written. Next run resumes from the last persisted record.)*
- What happens when the inference service is rate-limited or out of credits mid-run? *(Treated as a hard block — same handling as an upstream challenge. Pipeline halts, partial pile artifacts preserved, operator notified.)*
- What happens when a media download fails for one post (CDN error, 404)? *(The pile record is still created with an empty media reference; the failure is logged; other posts in the run continue.)*
- What happens when an upstream feed (RSS, etc.) is unreachable entirely? *(Service exits cleanly with an error log; existing pile artifacts unchanged; next run retries the feed.)*
- What happens when a pipeline service is interrupted mid-write (process killed)? *(At most the in-flight artifact is lost or partial; subsequent run resumes from the most recent fully-written artifact.)*
- What happens when an inference call returns prose without parseable JSON, or prose embedded in a JSON field? *(The output is rejected, the raw response is preserved in an audit field, and the service applies the same empty-inference fallback used when no result was returned.)*
- What happens when the chronological-neighbor fallback is invoked but no prior pile artifact exists (e.g., the very first record in a fresh scrape with no usable inference)? *(The record is persisted with empty location fields; downstream consumers see the gap.)*
- What happens when a target Instagram account becomes private or is deleted between runs? *(Service halts on the auth/visibility error, logs the cause, preserves prior artifacts. Operator decides whether to remove the target from configuration.)*
- What happens when two pipeline services are configured to write to artifacts with overlapping namespaces? *(Each service is expected to own its own namespace within the pile; collisions are a configuration error, surfaced at service startup.)*
- What happens when the crawler account itself is suspended? *(Service halts on auth failure across all targets; operator must provision a replacement crawler.)*
- What happens when a previously-stored pile record is no longer present in the upstream source (the original post was deleted)? *(Per FR-106, the service marks the pile record with a tombstone field if it naturally encounters the absence during a normal run. The record is never physically removed. No proactive deletion-audit pass is performed.)*

## Requirements *(mandatory)*

### Key Principles

These principles overrule any contradicting requirement detail below:

1. **The App is physically self-contained.** All code, tests, configuration, run artifacts, and pile contents reside within a single root directory. The directory is movable to a different project or repository as a unit without affecting either the App or the source project's other code. Speckit / working-process artifacts (this spec, JIRA mapping, planning docs) live at the parent project's root and are NOT part of the App.
2. **The pile is the App's sole surface.** Downstream consumers see only the pile, and only through a future bridge-app — no consumer reads the pile directly. No service-level details (which pipeline service ran when, internal data structures, etc.) leak to consumers.
3. **Pipeline services are segregated and opaque.** Each service is a self-contained workflow. From the downstream perspective they are "unknown and mysterious" — like an unrelated upstream organization.
4. **Inference steps preserve their inputs.** Any step that calls a model to infer something MUST persist the original inputs alongside the output, so the inference can be re-run, audited, or replaced with a different model without re-fetching the source.
5. **The pile is intentionally messy.** Heterogeneous artifact types (TSV files, media files, relational tables, blob stores) coexist. The mess is the point — it simulates the result of "centralizing" disparate sources without enforcing a unified schema.

### Functional Requirements

> FR numbering continues the convention from the prior 003 spec where the requirement is preserved or amended; new FRs start at FR-050. Retired FRs are listed at the bottom so historical `tasks.md` cross-references remain interpretable.

#### App-Level (Pile + Service Segregation)

- **FR-100**: The App MUST consist of one or more segregated pipeline services, each responsible for exactly one upstream source.
- **FR-101**: Each pipeline service MUST be runnable independently of the others. Adding, modifying, disabling, or removing one service MUST NOT require changes to other services' code or configuration.
- **FR-102**: All pipeline services MUST write into a single conceptual pile — a collection of file folders and/or databases that constitutes the App's sole downstream surface.
- **FR-103**: Downstream Apps MUST NOT read the pile directly. Pile access is mediated by a future bridge-app — separate from this spec — which is the only consumer of the pile and the only producer of consumer-ready data for downstream Apps (Travelogue DB, front-end, etc.).
- **FR-104**: The pile MAY contain heterogeneous artifact types — a single pile may be backed by TSV files, image/video files, relational databases, blob stores, or any combination. Each pipeline service feeds exactly one pile; one pile MAY be fed by one or more pipeline services.
- **FR-105**: Any pipeline service that performs an inference step (LLM call, ML model invocation, heuristic resolution, etc.) MUST persist the original inputs to that inference alongside the output, so the inference can be re-evaluated, audited, or re-run with a different model without re-fetching from the upstream source.
- **FR-106**: When a pipeline service naturally encounters source-side absence during normal operation (a previously-stored pile record is missing from a source response that should have contained it), the service MUST mark that pile record with a tombstone field (e.g., `deleted_upstream` boolean + detection timestamp) but MUST NOT physically delete the record. The service MUST NOT run a separate audit pass to proactively check for upstream deletions — detection is incidental, not exhaustive.
- **FR-107**: Pipeline services MAY run concurrently with each other; the App MUST NOT serialize one service's runs behind another's. Anti-detection and rate-limiting concerns are scoped to a single pipeline service, not coordinated across the App. Within a single pipeline service, work MUST be sequential by default (one target at a time, one page at a time, one record at a time); any deviation requires explicit justification in that service's design.

#### App Boundary (Physical Segregation)

- **FR-110**: All of the App's code, tests, configuration, run artifacts (per-run logs, sessions, scratch files), and pile contents (TSV files, media files, databases, blob stores) MUST reside within a single root directory at the project level. The App MUST NOT write any runtime artifact to a project-shared directory (e.g., a frontend's `public/`, a backend's data directory, the project root). The App MUST NOT read any runtime artifact from outside its own root directory.
- **FR-111**: The App's root directory MUST be movable as a self-contained unit to a different project or repository. The move MUST NOT require modifying any file outside the App's directory and MUST NOT require modifying any file inside the App's directory beyond what's needed to run it in the new location (e.g., wiring up Python environment, secrets).
- **FR-112**: Speckit / working-process artifacts — this spec, `tasks.md`, `jira-mapping.json`, `specify-prompt-draft.md`, planning notes, the cross-project roadmap — MAY remain at the parent project's root since they're part of the cross-App PM scaffolding, not the App itself. The App MUST be moveable independently of these artifacts (e.g., a future repo containing only the App will be a working, runnable codebase, even without any speckit metadata).
- **FR-113**: Downstream Apps in the same project access pile data ONLY through the future bridge-app (see FR-103). The bridge-app is the hand-crafted ETL/EDM between the messy pile and consumer-ready data; it is out of scope for this spec but is the assumed consumer of the pile.

#### Instagram Pipeline Service

- **FR-016**: The Instagram pipeline service MUST authenticate as a separate crawler account distinct from the accounts being scraped. The crawler account's credentials and the list of target accounts are separately configurable.
- **FR-017**: The service MUST support a recurring-schedule mode (e.g., approximately hourly by default) AND a one-off CLI invocation mode. Schedule frequency MUST be configurable per service.
- **FR-018**: Each run MUST be incremental — the service determines the most recent pile artifact for each target and fetches only posts newer than that point.
- **FR-019**: For each post with an explicit geo-tag, the service MUST persist BOTH the verbatim tag string AND a canonical "Venue, City, Country" form, plus the original lat/lng and an IATA region code. The verbatim tag preservation satisfies the inference-input-preservation principle (FR-105) when the canonical form is derived by inference.
- **FR-020**: For each post without a geo-tag, the service MUST invoke an inference step using the post's caption and media as inputs, producing a location, lat/lng, region, and an audit-able reasoning record. The caption and media path (the inference inputs) MUST be preserved in the pile (FR-105).
- **FR-021**: Each post MUST have its media (image or video) downloaded into the pile. A media download failure MUST log a warning, leave the media reference empty for that record, and NOT abort processing of remaining posts.
- **FR-022**: The service MUST be idempotent — re-running on a stable pile state MUST NOT create duplicate records. Dedup is keyed on the canonical Instagram post identifier (`shortcode`); the numeric `instagram_id` (Instagram pk) MUST be retained alongside in each pile record for traceability.
- **FR-050**: The service MUST support scraping multiple target accounts in a single invocation. Target accounts are independent — failure to fetch one MUST NOT prevent processing of the others.
- **FR-051**: The service MUST apply anti-detection behaviors when paginating the upstream feed: randomized inter-request delays, smaller page sizes than the upstream API's max, periodic longer rests at configurable intervals, and a configurable rate-preset that bundles these settings.
- **FR-052**: The service MUST distinguish between transient errors (network blip, 5xx, connection reset) and hard-block errors (Instagram challenge / checkpoint flows, account suspension). Transient errors trigger a single retry after randomized backoff; hard blocks trigger immediate halt without retry, with an operator-facing prompt explaining the required manual verification.
- **FR-053**: Each post MUST be persisted to the pile (record written, media downloaded) BEFORE the next page is fetched, so a mid-scrape interruption preserves partial progress. Subsequent runs resume from the most recent persisted record.
- **FR-054**: When the inference step (FR-020) returns no usable location AND a chronologically-prior pile record for the same target exists, the service MUST fall back to copying that prior record's CITY (not its exact venue), inheriting lat/lng/region from the prior record. Fallback records MUST be identifiable in the pile as such (e.g., a fallback marker in the audit field).
- **FR-055**: The crawler account credentials (FR-016) and target account list MUST come from separate configuration sources (environment variables or distinct config keys), and the service MUST never use a target account's credentials as the crawler.

#### Substack Pipeline Service

- **FR-023**: The Substack pipeline service MUST poll one or more configured RSS feed URLs on a recurring schedule or via one-off CLI invocation.
- **FR-024**: For each RSS entry not already represented in the pile, the service MUST persist a record containing title, subtitle, body, and publication date. Dedup is keyed on the canonical Substack post identifier (`<guid>`); `<link>` MUST be retained alongside in each pile record for traceability.
- **FR-025**: The service MUST be idempotent — re-running on a stable pile state MUST NOT create duplicate records.
- **FR-026**: If an RSS feed URL is unreachable or returns an invalid feed, the service MUST log the error and exit cleanly for that feed without affecting existing pile artifacts or other configured feeds.
- **FR-028**: The Substack service MUST support a **full-archive backfill** mode that enumerates ALL of a publication's posts via the publication's archive API (offset/limit pagination), not only the most-recent subset the RSS feed exposes. This is an explicit operator-invoked mode that lifts the RSS-window cap (data-model.md § "Substack-specific notes"); the default RSS path remains the cheap incremental poll.
- **FR-029**: For each archived post, the backfill MUST fetch the full HTML body (the archive listing returns metadata only) and persist the same pile-record shape as the RSS path, keyed on the same canonical post identifier (the archive `canonical_url`, which equals the RSS `<guid>`), so backfilled records dedup against RSS-pulled records.
- **FR-030**: Backfill MUST be idempotent and mergeable with the RSS path — running a backfill after an RSS pull (or re-running a backfill) MUST NOT create duplicate records (dedup keyed on `substack_id`).
- **FR-031**: Backfill MUST be polite to the upstream (a bounded inter-request rate) and resilient to a single post-body fetch failure (log and skip that post, continue the run); on a wholesale archive-API failure it MUST log the error and exit cleanly with existing pile artifacts intact, like the RSS path (FR-026).

#### Operations & Observability

- **FR-070**: Each pipeline service run MUST emit a per-run log file in a known location, capturing progress, timing, inference call results, and errors.
- **FR-071**: At the start of each run, the pipeline service MUST surface an estimated runtime (derived from the upstream's known item count if available, plus the active rate-preset settings) so the operator knows whether to wait synchronously or schedule a check-back.
- **FR-072**: Old per-run log files MUST be auto-pruned to a fixed retention (default: 5 most recent runs per service).
- **FR-073**: Each pipeline service MUST be invokable via CLI with at least: target selection, rate-preset selection, and the ability to override pile artifact paths.
- **FR-074**: Each pipeline service MUST be schedulable independently of the others, with per-service schedule configuration that the operator can change without affecting other services.

#### Retired / Out-of-Scope

The following FR numbers are reserved and intentionally retired so historical `tasks.md` cross-references remain interpretable:

- **FR-027**: ~~Substack post → stop linkage~~ — Moved to the future raw-pile-to-Travelogue-DB integration spec. The pile holds Substack records with no stop reference; downstream consumers assign linkage.
- **FR-040**: ~~Trip auto-assignment by date range~~ — Moved to the future raw-pile-to-Travelogue-DB integration spec. The pile holds posts without trip assignment.
- **FR-041**: ~~CLI login command for instagrapi session~~ — Operator manages session credentials manually; no in-app CLI wrapper required for v1.
- **FR-043**: ~~Graph API fallback~~ — Retired 2026-05-25; the App does not depend on any upstream API surface beyond the one each service is built for.
- **FR-044**: ~~Email notification on session error~~ — Replaced by operator-facing stdout prompts (FR-052).

### Key Entities

- **Pile**: The App's downstream surface. A collection of file folders and/or databases located **within the App's root directory** at well-known relative paths. Heterogeneous in artifact type. The sole interface between this App and the future bridge-app; never read directly by Travelogue or other downstream consumers.
- **App Root Directory**: The single physical directory at the parent project's root that contains all of this App's code, tests, configuration, run artifacts, and pile contents. Movable as a unit (FR-110, FR-111).
- **Bridge App** (out of scope, referenced): A separate future App that consumes the pile and produces consumer-ready data for downstream Apps. Hand-crafted ETL/EDM; see [`docs/roadmap.md`](../../docs/roadmap.md) for the Apps catalogue and the distinction from the much-later **bridge-builder-app** (Data Unification itself).
- **Pipeline Service**: A self-contained workflow that extracts content from one upstream source and writes artifacts to the pile. Independently runnable. Opaque to downstream consumers.
- **Pile Artifact**: A single record (TSV row, file, DB row) produced by a pipeline service. The atomic unit downstream consumers read.
- **Inference Step**: Any step within a pipeline service that calls a model (LLM, ML model, heuristic) to derive output from raw inputs. Subject to FR-105: original inputs preserved.
- **Crawler Account**: A separate account (credentials) used by a pipeline service to access the upstream source. Distinct from any target account being scraped. May be a burner account.
- **Target**: A specific upstream identifier (account handle, RSS URL, etc.) that the pipeline service scrapes data from.
- **Rate Preset**: A named bundle of anti-detection settings (inter-request delays, page sizes, rest cadence) selected at run time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A from-scratch run of the Instagram pipeline service against a public target with N posts produces N pile records (completeness).
- **SC-002**: Re-running any pipeline service on a stable pile state produces zero new pile artifacts (idempotency).
- **SC-003**: Interrupting a pipeline service mid-run loses at most one in-flight artifact; subsequent runs resume from the last persisted artifact (resilience).
- **SC-004**: A pipeline service runs continuously against the same upstream source for at least 100 consecutive scheduled runs without triggering an unrecoverable upstream block (anti-detection longevity).
- **SC-005**: Adding a new pipeline service to the App requires zero code or configuration changes to existing pipeline services (segregation).
- **SC-006**: Any inference output in the pile can be reproduced by re-running the same recorded inputs through the same inference logic (input preservation).
- **SC-007**: A downstream consumer can read the pile and produce a complete output without referencing any pipeline service by name or importing any service-internal module (decoupling).
- **SC-008**: At the start of each pipeline service run, an estimated runtime is surfaced; the actual runtime falls within ±30% of the estimate for at least 80% of runs (observability accuracy).
- **SC-009**: Per-service log retention is enforced at 5 most recent runs; older logs are auto-removed (log hygiene).
- **SC-010**: Copying the App's root directory to a fresh empty project (no speckit artifacts, no other App code) produces a working, runnable codebase. All tests pass; an Instagram scrape against a public target completes successfully (physical-segregation portability).
- **SC-011**: A grep across the App's root directory finds zero file-system references to paths outside the App (no `../`, no absolute paths into the parent project's other directories) other than (a) standard system locations like `/tmp` or `os.path.expanduser`, and (b) network endpoints. (Self-containment property.)
- **SC-012**: A full-archive backfill of a Substack publication with M posts (M may far exceed the ~20-entry RSS window) produces M pile records — including every post older than the RSS window — deduped against any records a prior RSS pull already wrote (archive completeness, FR-028/FR-029).
- **SC-013**: Running a backfill after an RSS pull, or re-running a backfill, yields the union of articles with zero duplicates (cross-mode idempotency, FR-030).

## Assumptions

- Each pipeline service manages its own authentication, sessions, and resilience independently — there is no shared auth or session layer at the App level.
- Crawler accounts for each pipeline service are separate from any production user accounts and are operated as burners; their suspension is a recoverable operational event, not an outage.
- "Anti-detection longevity" (SC-004) is measured per source-account pair, not in absolute calendar time. Different upstream sources have different thresholds; the App's rate-preset settings are tuned per service.
- The pile's specific artifact types are an implementation choice per pipeline service. For v1, Instagram and Substack both write TSV files plus a shared media directory; future services may use other formats.
- Recurring scheduling for v1 is implemented in-process via an embedded scheduler within the App, not via external cron. External cron remains compatible (each service supports one-off CLI invocation).
- Inference is currently performed by an LLM, but FR-105 (input preservation) is intentionally model-agnostic — other inference types in future services follow the same rule.
- Operators have access to the crawler accounts on a separate device (e.g., phone) to complete verification challenges when FR-052 surfaces an operator prompt.
- The pile is read-only from the downstream perspective; downstream consumers must not mutate pile artifacts. Mutations are the producing pipeline service's exclusive responsibility.
- Pile artifact retention is indefinite. The App does not auto-prune; the operator handles any pruning manually if storage becomes an issue. The pile's value is its completeness — full historical content underwrites both the bridge-app's accuracy and the eventual bridge-builder-app's training surface.
- The handoff from the pile to downstream consumers (the Travelogue DB, the front-end, future Apps) passes through a bridge-app, defined in a separate future spec / Epic. The bridge-app is the only consumer of this App's output; this spec defines the pile as the producer's contract; what the bridge-app does with it (cleaning, normalization, mapping to downstream schemas, conflict resolution between pipelines, etc.) is out of scope.
- The current codebase has some artifacts that pre-date the FR-110 / FR-111 segregation rule (the pipeline code lives in `scripts/instagram-fetch-latest/`, pile data lives at the project root and in `public/media/`). Migrating those into a single App root directory is a planned implementation task under this spec; once complete, the App will satisfy FR-110 / FR-111. Until that task lands, the spec is the source of truth for the target state.
