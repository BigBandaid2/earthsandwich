# Earth Sandwich — Vision & Roadmap

> **What this doc is**: the project-level "where we're going and why." Sits above any single spec. Specs (`specs/00N-feature/`) drive implementation; this doc captures the vision, the boundaries between specs, and what's *planned* but not yet formalized.
>
> **What this doc is not**: a spec. It doesn't get a JIRA Epic, drift scans, or any `/speckit.*` ceremony. Living document — edit via PR. Cardinal Rule 6 applies (narrative artifact, tools don't sync).

---

## Vision

The project serves three distinct purposes:

### 1. A visual travelogue for our trips

A web app for friends and family to follow where we went on our last earth-sandwich trip and where we intend to go on the next big round-the-world trip. It may also help us record more detailed trip plans in a structured way and display content for smaller upcoming trips (Montenegro, India) — but those are secondary objectives that exist mainly to enhance or test functionality built primarily for the round-the-world use case.

### 2. A hands-on experiment in AI-driven development

A learning sandbox for AI-assisted software development, with **Spec Kit** chosen as the starting framework. Ethan and Evan / Elena are using this project to learn how to drive Claude Code productively, compensate for its limitations, and project-manage well enough to actually ship useful features — instead of slipping into the easy defaults of producing more raw code and more useless documentation.

### 3. A toy case for the Data Unification project

The more serious **Data Unification** work was started and paused due to spiraling complexity. Earth Sandwich involves the same core problems at toy scale: data pipelines, raw data tables, normalization, and matching related records. Tackling them here lets us deliberately apply methods that would normally be overkill for a personal app, with the goal of generalizing those patterns back into the larger project later.

---

## Purpose 3 — Data Unification outline

> Transcription of `docs/images/data-unification-outline.jpeg` (handwritten notebook page). From data Unification perspective there are 4 distinct apps.

### App 1 - Raw Data Pile (Input for Data Unification)

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

**Earth Sandwich realization (spec `003-ingestion-pipeline`)**: each data source — Instagram, Substack, Google Location, etc. — gets its own self-contained pipeline with no runtime dependencies on the others. The DB that holds raw pipeline output is intentionally separate from the Travelogue app's production DB; that raw store is the "dog pile" that Data Unification (when DU exists) will digest into useful information for the downstream Travelogue app. Until DU is built, the Travelogue app reads from this raw pile directly via straightforward queries — DU is the future intermediary, not a current dependency.

### App 2 - Inventory, Dictionary, Mappings, Variances (Data Unification Itself)

**ORM Graph**

- DB's / Sources
- Cost of Acquisition
- Objects / Nodes
- Nodemaps and Hierarchies
- Fields / Aliases
- Row Slices

### App 3 - Normalized and Joined Data Model (Output of Data Unification)

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

### App 4 - Target Useful Production App (Client of Data Unification)

This is the downstream app / operating user that we are meant to serve. This owner of this app outlines what they need and Data Unification (DU) is meant to help them extract it out of the dog pile, clean it up, and present it as a push data export or queryable end-point.

In addition to a creating a clean, query-able data source. DU will also provide:

- **Cost Visibility and Allocation**, both for the consumer and provider of the data. Create an internal marketplace for data, and build the foundations for DU to evolve into a 3rd party marketplace and purveyor of data.
- **Data Quality Quantified** - Certain data sets will be marked as base truth for a particular slice/node of data. All other nodes will inherit a degree of credibility based on their variance and distance from these base truth nodes. Provide source trace for any delivered data point.
- **Searchable Data Dictionary** - AI assisted dataset curation, what do I want to do and what datasets might help me do it? Ideally both within the pile and beyond. Crawl data catalogues, inventories, contracts, internet. Guidance for new data acquisition and on-boarding.

---

## Specs

Sorted by Purpose, then logical sequence within each Purpose. Italicized rows are planned (not yet formalized).

| Spec | Epic | Purpose | Scope (summary) | Trigger | Reference |
|---|---|---|---|---|---|
| `001-world-travelogue` | [OCS-11](https://datacommlab.atlassian.net/browse/OCS-11) | 1 | Front-end UX for read-only browsing of trip history and plans; wiring to the 002 backend now in progress. | 2026-04 — initial build of a basic front-end-only demo app. | [↓](#001-world-travelogue) |
| `002-database-backend` | [OCS-73](https://datacommlab.atlassian.net/browse/OCS-73) | 1 | Relational DB, REST API, MCP, basic user-editing interface for trips/stops, full-app containerization. | 2026-05 — hardcoded scope outgrown; recurring Instagram ingestion made static JSON impractical. | [↓](#002-database-backend) |
| _Festivals trip mode_ | — | 1 | Trip variant where stops cluster around named events rather than chronology. | When a festivals-shaped use case starts feeling real. | [↓](#festivals-trip-mode) |
| _Deployment + domain_ | — | 1 | Domain pointing, TLS, secrets, log aggregation, deploy pipeline. References [OCS-69](https://datacommlab.atlassian.net/browse/OCS-69). | When the first prod-bound code lands. | [↓](#deployment--domain) |
| `004-test-and-cicd` | — | 2 | Project-wide test suite + GitHub Actions (per-PR unit lane, nightly integration lane). Kernel in `scripts/instagram-fetch-latest/tests/`. | Next sprint or two. | [↓](#004-test-and-cicd) |
| _MCP for trip / stop CRUD_ | — | 2 | LLM read + write of trips/stops via an MCP server backed by 002's API. References [OCS-71](https://datacommlab.atlassian.net/browse/OCS-71). Possibly subsumed by 002's MCP scope; revisit when LLM-authoring becomes a real need. | When LLM-based trip authoring becomes a real need. | [↓](#mcp-for-trip--stop-crud) |
| `003-ingestion-pipeline` | [OCS-74](https://datacommlab.atlassian.net/browse/OCS-74) | 3 (App 1) | Standalone, source-specific raw-data pipelines feeding the raw data pile. See reference for detail. | 2026-05 — split from 002 to isolate ingestion / pile concerns from the production app's DB. | [↑ App 1](#app-1---raw-data-pile-input-for-data-unification) |

A planned spec graduates by running `/speckit.specify <slug>` once its trigger fires; at that point its Epic is filled in and the Trigger column updates to a backward-looking date + justification.

### Boundary rules

- **001 owns the UI and the in-repo data shapes** (`Stop`, `Trip`, `Region` types, regions list). It does *not* own persistence or fetching.
- **002 owns persistence and the read/write API**. It does *not* own ingestion or UI.
- **003 owns automated content ingestion only** — writes rows into the raw-data DB (independent of the Travelogue app's production DB). It does *not* expose HTTP endpoints or change the UI.

When work is ambiguous between specs (e.g. a new stop type), default to whichever spec owns the *primary* surface area; document the cross-spec dependency in the spec that depends on it. Phase numbering preserves history across splits (see the 002 → 002+003 split on 2026-05-22).

---

## Spec references

### 001-world-travelogue

_Placeholder — to be expanded._ Purpose 1 (Travelogue). Originally a read-only front-end demo over hardcoded trip data; now evolving to consume the 002 backend API in place of the in-repo `frontend/src/data/` shapes.

### 002-database-backend

_Placeholder — to be expanded._ Purpose 1 (Travelogue). Backend + persistence + editing surface that 001 reads from. Includes containerization for full-app packaging.

### 004-test-and-cicd

_Placeholder — to be written when the spec is formalized._ Purpose 2 (AI-driven dev experiment). Project-wide test suite organization + CI/CD workflows.

### MCP for trip / stop CRUD

_Placeholder — to be written when the spec is formalized._ Purpose 2 (AI-driven dev experiment). LLM-targeted CRUD interface backed by 002's API.

### Festivals trip mode

_Placeholder — to be written when the spec is formalized._ Purpose 1 (Travelogue). Trip variant clustered around named events.

### Deployment + domain

_Placeholder — to be written when the spec is formalized._ Purpose 1 (Travelogue). Production deploy pipeline + domain pointing.

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
- Material changes → PR review, same convention as `docs/workflow.md`.
