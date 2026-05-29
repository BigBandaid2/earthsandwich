# Earth Sandwich — Vision & Roadmap

> Addressed to a product-manager reader with personal experience of the **pile → bridge → useful** problem (data lake → ETL+EDM → production app). Frames vision from product, architecture, market, and business angles; technical detail lives in specs. Not a spec, workflow guide, or constitution — see the [constitution](../.specify/memory/constitution.md) for the full doc catalogue.

---

## Vision

ETLs and EDMs exist to turn raw sources into shaped, trusted, useful data models. In practice they fall short in two ways. First, the data store they produce isn't fit for direct production consumption — downstream apps still need bespoke read layers tuned to their use cases. Second, they take months of esoteric configuration and teams of people to operate. **Our goal for Data Unification** is to use AI to collapse both costs by 100x, and to build an architecture native to a future dominated by MCPs and agentic workflows.

We believe in a future dominated by headless enterprise apps that are essentially a database + MCP + agents. In such a world, a premium will be placed on flexible responsive data modeling that can quickly adapt to new use cases, while keeping data trustworthiness always at the fore.

To serve these high velocity needs, there can be no more people writing JavaScript, C#, and YAML rules and configurations for months— demanding esoteric knowledge of a cumbersome EDM/ETL framework for implementation. Instead, a non-expert user with primary knowledge in their business domain will be able to define a use case and rely on an AI orchestrator and an LLM to shape the target model, look at the raw data pile, and build the pipe in days.

In the future there will also be no more data-quality operators clearing an endless queue of daily exception tickets and fixing individual data points. Instead, issues will be detected instantly, checked against a source of truth, fixes applied at the global root cause, and presented to data managers as permanent solutions already pre-tested at scale and ready for push-button deployment.

This project is the first attempt to approach the problem at toy scale and probe the feasibility of this vision — and the capabilities of frontier AI at developing and operating such a solution.

To that end, the project serves three distinct purposes:

### travelogue-purpose — A visual travelogue for our trips

A useful and fun web app for friends and family to follow where we went on our last earth-sandwich trip and where we intend to go on the next big round-the-world trip. This provides a context to ingest and clean several sources messy data, while not being so boring that you want to kill yourself.

### ai-learning-purpose — A hands-on experiment in AI-driven development

A learning sandbox for AI-assisted software development, with **Spec Kit** chosen as the starting framework. We are using this project to learn how to drive Claude Code productively, compensate for its limitations, and project-manage well enough to actually ship useful features.

### data-unification-purpose — A toy case for the Data Unification project

A dedicated **Data Unification** project was started earlier and paused due to spiraling complexity. Earth Sandwich involves the same core problems at toy scale: data pipelines, raw data tables, normalization, and matching related records. Tackling them here lets us deliberately apply methods that would normally be overkill for a personal app, with the goal of generalizing those patterns back into the larger project later.

---

## Apps

The project is composed of self-contained **Apps**, ordered here by the data-flow story they tell: **pile-app → bridge-app → useful-app → bridge-builder-app**. The first three are concrete; the fourth (the bridge-builder, i.e. Data Unification itself) is the deep ambition behind data-unification-purpose and won't be attempted until the first three exist as a reference.

Apps are the architectural unit; specs are the project-management unit and do **not** map 1:1 to Apps. A complex App may grow across multiple specs over time. Per the [constitution](../.specify/memory/constitution.md) (Principle II), no App reaches into another App's source code or filesystem.

| App | What it is | Specs in scope |
|---|---|---|
| **pile-app** | The Ingestion Pipeline App. Segregated source-specific pipeline services (Instagram, future Substack, future others) that produce a local pile of raw artefacts (TSVs, media, possibly DBs). Physically self-contained — movable to a separate repo. | `003-ingestion-pipeline` (and likely future split specs as it grows) |
| **bridge-app** _(planned — next concrete spec)_ | The hand-crafted ETL/EDM that reads from the pile and produces consumer-ready data for the useful-app. Stop linkage, normalization, deduplication, cross-source mapping. Will eventually serve as the test reference for the bridge-builder-app. | none yet |
| **useful-app** | The Travelogue. Frontend (Vite + React map UX) reads from Backend (FastAPI + persistence + REST + planned MCP/user-input write paths) via REST. Owns trip management and all user-driven authoring. | `001-world-travelogue` (frontend), `002-database-backend` (backend), future MCP + user input spec |
| **bridge-builder-app** _(far-future)_ | Data Unification itself. Automated orchestrator that inspects a pile + target schema and aims to *produce a bridge-app by itself*, repeatably across projects. Built and validated against our hand-crafted bridge-app as reference. The deep goal of data-unification-purpose. | none yet |

The useful-app's Frontend + Backend together realize the DU framework's "App 4" (Target Useful Production App). They're separated as sub-areas within useful-app because their concerns (UI vs. persistence + write paths) and tech stacks are different enough to warrant a boundary; the DU framework treats them as one downstream client.

---

## Specs

Sorted by App. Italicized rows are planned (not yet formalized).

| Spec | Epic | App | Scope (summary) | Trigger | Reference |
|---|---|---|---|---|---|
| `001-world-travelogue` | [OCS-11](https://datacommlab.atlassian.net/browse/OCS-11) | useful-app | Front-end UX for read-only browsing of trip history and plans; wiring to the backend now in progress. | 2026-04 — initial build of a basic front-end-only demo app. | [↓](#001-world-travelogue) |
| `002-database-backend` | [OCS-73](https://datacommlab.atlassian.net/browse/OCS-73) | useful-app | Travelogue DB, REST read API, full-app containerization. (Write paths — MCP + user-editing interface + trip import — live in the MCP + user input spec below.) | 2026-05 — hardcoded scope outgrown; recurring Instagram ingestion made static JSON impractical. | [↓](#002-database-backend) |
| _MCP + user input interface_ | — | useful-app | All useful-app write paths: LLM CRUD via an MCP server (references [OCS-71](https://datacommlab.atlassian.net/browse/OCS-71)), a user-facing editing UI for trips/stops, and finalized-itinerary import from chat (the workflow that supersedes the dropped Festivals spec). | When LLM-based trip authoring or hands-on trip editing becomes a real need. | [↓](#mcp--user-input-interface) |
| `004-test-and-cicd` | — | (project-wide tooling) | Project-wide test suite + GitHub Actions (per-PR unit lane, nightly integration lane) + deployment / domain pipeline (TLS, secrets, log aggregation; references [OCS-69](https://datacommlab.atlassian.net/browse/OCS-69)). Kernel in `scripts/instagram-fetch-latest/tests/`. | Next sprint or two. | [↓](#004-test-and-cicd) |
| `003-ingestion-pipeline` | [OCS-74](https://datacommlab.atlassian.net/browse/OCS-74) | pile-app | The Ingestion Pipeline App: physically self-contained collection of segregated pipeline services (Instagram, future Substack) that produce a local pile of raw artefacts. Sole downstream surface is the pile; consumed only by the future bridge-app, never by other Apps directly. Re-authored 2026-05-27 to reflect App-shaped scope. | 2026-05 — split from 002 to isolate pile concerns from the Travelogue. | [↓](#003-ingestion-pipeline) |
| _Bridge App_ | — | bridge-app | The only consumer of the pile-app's pile and the only producer of consumer-ready data for the useful-app. Hand-crafted ETL/EDM: stop linkage, normalization, deduplication, cross-source mapping. Will eventually serve as the test reference for the bridge-builder-app. | When the Travelogue's hand-curated data is no longer enough — i.e. when we want ingested content to actually populate the production schema. | [↓](#bridge-app) |
| _Data Unification (DU)_ | — | bridge-builder-app | Automated orchestrator that aims to produce a bridge-app from a pile + target schema, repeatably across projects. The deep goal of data-unification-purpose, validated against our hand-crafted bridge-app. | Far future — only attempted after pile-app, bridge-app, and useful-app are all working. | [↓](#data-unification-du) |

A planned spec graduates by running `/speckit.specify <slug>` once its trigger fires; at that point its Epic is filled in and the Trigger column updates to a backward-looking date + justification.

### Boundary rules

- **useful-app — frontend (001)** owns the UI and the in-repo data shapes (`Stop`, `Trip`, `Region` types, regions list). It does *not* own persistence or fetching.
- **useful-app — backend (002)** owns persistence, the read API, and containerization. It does *not* own ingestion, the UI, or any write paths.
- **useful-app — write paths (MCP + user input, planned)** owns all useful-app write paths: LLM CRUD via MCP, user-facing trip/stop editor, finalized-itinerary import. Backed by the backend's persistence; orthogonal to the pile-app's ingestion. Trip creation and management live here.
- **pile-app (003)** owns automated content ingestion + the pile it produces. The pile is a collection of files (TSVs, downloaded media) and may include databases; it lives within the App's own root directory. The App does *not* expose HTTP endpoints, does *not* change the UI, and does *not* write into any other App's data. The pile is consumed only by the future bridge-app.
- **bridge-app (planned, hand-crafted)** is the only reader of the pile-app's pile and the only writer into the useful-app's backend schema (via the backend's own write paths). Owns stop linkage, normalization, deduplication, cross-source mapping. Does *not* own trip management (that lives in the useful-app).
- **bridge-builder-app (far-future)** is the bridge-*builder*, not the bridge. It does not itself touch the pile or the useful-app. Its job is to take a pile and a target schema as input and emit a working bridge-app as output — validated by comparing against our hand-crafted bridge-app. Nothing here is specced until pile-app + bridge-app + useful-app are all working.

When work is ambiguous between specs (e.g. a new stop type), default to whichever spec owns the *primary* surface area; document the cross-spec dependency in the spec that depends on it. Phase numbering preserves history across splits (see the 002 → 002+003 split on 2026-05-22).

---

## data-unification-purpose — Data Unification outline

> Transcription of `docs/images/data-unification-outline.jpeg` (handwritten notebook page).

### App 1 — Raw Data Pile (Input for Data Unification) — pile-app in this project

**Ingestion Pipelines**

- Sources
- Pull / Post Schedules
- Files / Locations / Credentials
- API params / API Keys
- Post Production Steps

**Data Warehouse**

- DB's (groups of directly join-able tables, roughly equivalent to Sources from Ingestion Pipeline)
- Tables
- Slices (groups of rows distinguished by categorical column(s))

**Earth Sandwich realization (spec `003-ingestion-pipeline`)**: each data source — Instagram, Substack, Google Location, etc. — gets its own self-contained pipeline service with no runtime dependencies on the others. The pile lives within the pile-app's own root directory (physically segregated from the useful-app's production schema) and is the App's sole downstream surface. The **bridge-app** (planned, see specs table) is the only consumer of the pile — useful-app and other downstream Apps never read it directly. Until the bridge-app is built, the Travelogue runs on hand-curated data; content from the pile does not flow into the Travelogue until the bridge-app exists. The bridge-app will eventually serve as the test reference for **bridge-builder-app** — the far-future Data Unification ambition behind data-unification-purpose.

### App 2 — Inventory, Dictionary, Mappings, Variances (Data Unification Itself) — bridge-builder-app in this project

**ORM Graph**

- DB's / Sources
- Cost of Acquisition
- Objects / Nodes
- Nodemaps and Hierarchies
- Fields / Aliases
- Row Slices

### App 3 — Normalized and Joined Data Model (Output of Data Unification) — bridge-app in this project

**Silvers**

- Pairs
- Join Keys
- Measures
- Variances (Common)
- Mappings
- Time Series

**Golds**

- Groups
- Selection Logic
- Violators
- Corrections

### App 4 — Target Useful Production App (Client of Data Unification) — useful-app in this project

This is the downstream app / operating user that we are meant to serve. The owner of this app outlines what they need and Data Unification (DU) is meant to help them extract it out of the dog pile, clean it up, and present it as a push data export or queryable end-point.

---

## Spec references

### 001-world-travelogue

_Placeholder — to be expanded._ useful-app (frontend). Originally a read-only front-end demo over hardcoded trip data; now evolving to consume the useful-app backend API in place of the in-repo `frontend/src/data/` shapes.

### 002-database-backend

_Placeholder — to be expanded._ useful-app (backend). Backend persistence + read API + full-app containerization. The frontend reads from it; the pile-app writes raw-pile rows into its own pile (not the backend's DB). All useful-app write paths — user editing, LLM CRUD, finalized-itinerary import from chat — live in the MCP + user input interface spec, not here.

### MCP + user input interface

_Placeholder — to be written when the spec is formalized._ useful-app. One spec covering all useful-app write paths so the backend stays read-only:

- **LLM CRUD via MCP** — an MCP server backed by the backend's read API (write side added here), letting Claude / other LLMs read and modify trips, stops, posts. References [OCS-71](https://datacommlab.atlassian.net/browse/OCS-71).
- **User-facing editor UI** — hands-on trip/stop editing surface in the front-end for non-LLM workflows.
- **Finalized-itinerary import** — trip research and planning happens outside Travelogue (chat, notes, other tools); the resulting multi-stop itinerary is imported into the Travelogue via this interface. Subsumes what was previously sketched as the "Festivals trip mode" spec.

### 004-test-and-cicd

_Placeholder — to be written when the spec is formalized._ Project-wide tooling under ai-learning-purpose. Project-wide test suite organization + CI/CD workflows. Also absorbs the production deployment pipeline (domain pointing, TLS, secrets, log aggregation — what was previously the "Deployment + domain" planned spec) since the same infrastructure / GitHub Actions surface owns both.

### 003-ingestion-pipeline

The Ingestion Pipeline App — data-unification-purpose, **pile-app**. Owns automated content ingestion from disparate upstream sources (Instagram, planned Substack, future others) and produces the raw pile that the bridge-app will eventually consume. Physically self-contained. See [`specs/003-ingestion-pipeline/spec.md`](../specs/003-ingestion-pipeline/spec.md) for scope, requirements, and acceptance criteria.

### Bridge App

_Planned — no spec yet._ data-unification-purpose, **bridge-app**. The hand-crafted ETL/EDM that reads from the pile-app's pile and writes into the useful-app's backend via its standard write paths. Responsible for stop linkage, normalization, deduplication, and any other cross-source operations that don't belong in any individual pipeline service. **Not** responsible for trip management — trips are user-created artefacts that live in the useful-app's planned MCP + user input spec.

Trigger: when the Travelogue's hand-curated data is no longer enough and we want ingested content to actually populate the production schema.

Later, the bridge-app will serve as the test reference for the bridge-builder-app.

### Data Unification (DU)

_Far-future — no spec yet, and won't be triggered until pile-app + bridge-app + useful-app are all working._ data-unification-purpose, **bridge-builder-app**. Realizes "App 2" of the DU framework: not a bridge itself, but software whose job is to *produce* bridges. Given a pile and a target schema (the Travelogue's), the bridge-builder-app should be able to emit a working bridge-app with minimal hand-tuning. Our hand-crafted bridge-app becomes the test reference against which the bridge-builder-app's outputs are graded.

This is the deep "why" of data-unification-purpose. Everything before it — pile-app, bridge-app, useful-app, the heterogeneous Apps, the deliberate messiness — is staged so the bridge-builder-app has interesting friction to chew on at toy scale.

---

## Deferred / explicit non-goals

- **Multi-tenant authoring.** This is a single-traveler-couple travelogue. No public user accounts.
- **Mobile-first UI.** Mobile responsiveness is expected; primary target is desktop/tablet.
- **Real-time / live-tracking features.** Ingestion is hourly-ish, not push.
- **Comment-bot orchestration.** Considered in W19 sprint planning; never explored. Off the table unless a clear need surfaces.

---

## Maintenance

- Update this doc when:
  - A new spec is opened (move it from Planned → Current).
  - An existing spec closes or splits (note the change inline, like the 2026-05-22 002 split).
  - A Planned entry's trigger fires (graduate it) or is abandoned (move it to Deferred).
  - The Vision changes — that's a big deal; flag it in the commit message.
- Material changes → PR review, same convention as [`docs/workflow.md`](workflow.md).
