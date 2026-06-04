# /speckit.specify input prompt — 004 bridge-builder-toolkit (DRAFT)

> Edit the **Vision** section freely. The **Context** section is intended for
> /speckit.specify to read as background; you can trim it but it shouldn't
> grow much. After you're satisfied, paste the whole document as input to
> `/speckit.specify`.

---

## Context — where bridge-builder sits today

CLAUDE.md describes the project's Apps as **pile-app**, **bridge-app**, **useful-app**, and **bridge-builder-app**:

- **pile-app** (currently 003) deposits content from upstream sources (Instagram, future Substack) into a "pile" of TSVs + media files. The pile is the App's only downstream surface; no other App reads it directly.
- **useful-app** (001 + 002 + future MCP/user-input spec) is the Travelogue: a Postgres schema + REST read API + React front-end.
- **bridge-app** is planned but unspec'd. Its intended job: hand-craft an ETL/EDM that consumes 003's pile and writes into 002's schema via the backend's write paths. Owns stop linkage, normalization, cross-source mapping.
- **bridge-builder-app** is the "far-future Data Unification ambition" per CLAUDE.md — software whose job is to *produce* bridges automatically from a pile + a target schema. CLAUDE.md's current ordering says: hand-craft bridge-app first, then validate bridge-builder against it.

**This spec intentionally inverts that ordering.** Building a prototype bridge-builder toolkit first means that we will take an intentional detuour before building the IG-pile→Travelogue bridge itself. This prototype bridge-builder toolkit will not directly build the IG-pile→Travelogue bridge, but will assist in producing the analysis and specification prompts that will help me in hand-crafting the first IG-pile→Travelogue bridge. Rationale: analysis and mapping of the pile and useful-target data models is a necessary pre-requisite of hand crafting the bridge. A re-usable tool kit and generalizable workflow is more useful than one-off analysis. At a later stage, this toolkit can also serve as a starting point for the real bridge-builder App. CLAUDE.md's roadmap will need updating to reflect this inversion.

What exists today that this spec can lean on:

- The pile-app surface: per-target TSV files (e.g. `posts.ourearthsandwich.local.tsv`, 16 columns including `id`, `instagram_id`, `shortcode`, `media_url`, `caption`, `timestamp`, `location`, `lat`, `lng`, `region`, `reasoning`) and a `public/media/` directory of associated media files. Schema is documented in `specs/003-ingestion-pipeline/contracts/pile-artifact-instagram.md`.
- The useful-app target: Postgres schema in `specs/002-database-backend/data-model.md`, REST API contract in `specs/002-database-backend/contracts/api.md`, and a live local stack via `docker compose up` (see `specs/002-database-backend/quickstart.md`).
- No bridge of any kind exists yet.

---

## Vision — what the new bridge-builder-toolkit spec should cover

> _Rewrite this section freely. The bullets below are a first-pass starting
> point; trim, add, reframe at will._

The new spec should describe **bridge-builder-toolkit** as a workflow-oriented analysis tool: given (a) a pile and (b) a target data model, it guides a human + AI through three stages — pile analysis, target analysis, mapping synthesis — and emits a versioned, spec-ready bundle of artifacts that a downstream consumer can use to build an actual ETL ("a bridge"). bridge-builder-toolkit is **NOT** itself an ETL runtime. Its first execution against the 003 IG pile + 002 Travelogue schema must produce a collection of analysis files and prompts which can be used together with `/speckit.specify` to create the IG→Travelogue bridge spec, which then eventually becomes the bridge-app.

The toolkit is also the foundational predecessor of the eventual **bridge-builder-app** (the productized "Data Unification" ambition from CLAUDE.md). What's spec'd here is the human-driven, AI-assisted workflow and the artifacts it produces; the eventual bridge-builder-app would automate the orchestrator end and broaden the workflow to general pile/target pairs. The toolkit/app distinction matters because it bounds the current scope: build the foundational artifacts and conventions now, leave automation for later.

### Self-contained application

bridge-builder-toolkit is a **physically self-contained App** at the project root, modeled on the pile-app pattern from 003:

- Lives in `bridge-builder-toolkit/` at the repo root, alongside `pile-app/`, `backend/`, `frontend/`.
- Owns its own `venv/`, `.env`, `pyproject.toml`/`requirements.txt`, CLI entry point (e.g. `bridge-builder-toolkit/cli.py`), tests, run logs, and iteration-history directory.
- Shares **no code** with pile-app or the backend. Interaction with the outside world happens only through well-defined operator-supplied surfaces: a path to a pile (file or directory), a target schema definition (file or URL), and optional target API/DB credentials for the insertion-validation step.
- Movable to a separate repo without breaking either side. The pile-app and useful-app both keep working if bridge-builder-toolkit is excised; bridge-builder-toolkit keeps working if pointed at any other pile + target. This is the same FR-110/FR-111 portability constraint pile-app respects.

The toolkit's CLI is the orchestrator's user surface: invoke `cli.py analyze pile --path ...`, `cli.py analyze target --schema ...`, `cli.py iterate ...`, etc. The exact subcommand shape is an implementation choice at plan time, but the principle is firm: one CLI per stage / orchestration step, mirrored after pile-app's `run instagram` subcommand pattern.

### In scope

**Stage 1 — Pile analysis (outsider perspective).** The workflow ingests a chosen pile surface (TSV file + linked media directory today; future piles may be DB-backed) and produces an interactive HTML report. The analysis must assume zero foreknowledge of how the pile was created and derive everything from the surface itself. The report covers at minimum:

- Columns likely to be IDs; the recommended canonical ID with justification.
- What kind of object the rows describe (entity classification, inferred from the data).
- Component-property clusters (e.g. `location` / `lat` / `lng` likely belong together).
- Likely pipeline-metadata fields (`createdAt`, `tombstoned`, `reasoning`, etc.) vs. likely original-source fields.
- Likely derived/inferred fields, with reasoning.
- Evidence of an AI workflow — which fields appear AI-generated and why.
- Categorical fields suitable for slicing the data (e.g. Instagram `media_type`).
- Per-column statistical summaries — numeric (mean/median/min/max), categorical (value distribution + frequencies) — plus interpretive notes on what the distributions imply about the data.
- Public-knowledge enrichment — surfacing publicly-documented data dictionaries that describe known fields (e.g. official Instagram Graph API field docs), cited.
- Sampled inspection of linked/joined objects (e.g. media files) — what samples share with each other, and what they share with the rows referencing them.
- Anything else the analyst surfaces as relevant; this list is a floor, not a ceiling.

Choice of pile and *part* of pile (which target's TSV, which date range, which subset) is a workflow input, not a hard-coded assumption.

**Stage 2 — Target-model analysis (outsider perspective).** Same outsider posture, applied to the target. Inputs the workflow may have access to (any subset, depending on the target): a schema definition, a snapshot of live data, an API surface, direct DB access. The interactive HTML report covers the same axes as the pile report, plus:

- Schema visualization (tables, columns, relationships, constraints).
- Which target tables are *candidates* to be populated from the pile, with reasoning for each candidate.

**Stage 3 — Bridge synthesis (interactive mapping).** The workflow produces a side-by-side HTML report showing the pile and target together, with recommended table-level and field-level mappings drawn between them. The HTML must let the user:

- Adjust mappings (add, remove, edit).
- Leave comments on any mapping, on either side's fields, or on the bridge as a whole.
- Export captured edits + comments as a prompt-friendly artifact that can be fed back into the loop.

**Iteration loop.**

- Each iteration re-runs Stage 3 — and may extend Stages 1 and 2 with newly-surfaced properties — until the user accepts the bridge configuration.
- Every iteration's pile report, target report, and bridge report — together with the AI-or-user-generated feedback that produced the next iteration — must be persisted (versioned).
- If the workflow has access to the target's DB or write API AND the access includes **BOTH insert and delete**, each iteration must attempt to insert a single dummy record (mocked from a real pile row, transformed per the current proposed bridge), then delete it. Insertion success is required for the iteration to be "validated."
- A failed insertion triggers another iteration. After **5 consecutive failed-insertion iterations**, the loop halts with an operator-intervention surface.
- If insert+delete access isn't available, the insertion-validation step is skipped (with a recorded note in the iteration's metadata) and acceptance falls back to user judgement alone.
- Insertion validation **cannot run inside the playground itself.** Playgrounds are closed-world, no-network HTML artifacts (a hard constraint inherited from the `playground:playground` plugin) and have no way to reach a database or write API. The validation step lives in the **orchestrator** that runs the iteration loop — outside the playground — and writes its result into the next iteration's playground as embedded data (last attempt's outcome, dummy record, error message if any). The playground displays the validation result; it does not perform it.

**Output deliverables (per iteration, and a final accepted bundle).**

- Each interactive HTML report is implemented as a Claude Code **playground** (the `playground:playground` skill published by Anthropic in the official plugins repo). Playgrounds are single-file, self-contained HTML — vanilla HTML/CSS/JS, no external dependencies, no remote assets, data embedded inline.
- The playground's canonical **"copy out a prompt"** output — a natural-language artifact synthesized from the shared `state` object via a clipboard button — serves as the **AI-consumable companion form** that downstream spec-authoring steps consume. No separate JSON sidecar is required; the generated prompt itself is the structured payload that crosses between stages and iterations.
- Embedded-data limits are real. The pile-analysis playground must work with a **sampled / summarized representation** of the pile (e.g. column dictionary + per-column summary statistics + N sample rows + a handful of linked-media samples), not the entire pile contents. Sampling strategy is an implementation detail to be settled at plan time.
- The three stages are **three separate playgrounds**, not a multi-page experience. Each is self-contained and opens in isolation. Operators navigate between stages by opening different HTML files. Iteration history is persisted as a directory of `iteration-N/{pile,target,bridge}.html` plus the captured prompt outputs that fed the next iteration.
- The final accepted bundle is a directory of files — reports, mappings, sample-record validation results, iteration history, captured prompt outputs — intended to be passed directly as input to `/speckit.specify` (or equivalent) for authoring the concrete bridge spec.

### Prior art, what's retread, and what's genuinely new

The toolkit must lean on existing schema-mapping and data-profiling tooling rather than reinventing it. Each of the three stages overlaps an established field; the toolkit should integrate with or wrap the canonical tool for each stage wherever doing so doesn't compromise the playground UX or the outsider posture. Mapping vocabulary, profile-output shapes, and validation idioms should follow established conventions — operators coming from those tools should find the toolkit immediately legible.

**Stage 1 — Pile analysis** overlaps the data-profiling field. The canonical tool is **ydata-profiling** (formerly pandas-profiling): point it at a CSV or DataFrame and get an HTML report covering distributions, types, correlations, missing-value patterns. **Great Expectations** and **Soda** are adjacent but expectation-shaped (assume the schema is known and you want to assert against it) — wrong posture for outsider analysis. The toolkit's pile-analysis playground should either embed a ydata-profiling-style summary as its raw input or borrow ydata-profiling's section structure for the same axes; what's novel is the **LLM-as-outsider-analyst** layer that turns the raw profile into entity-classification, AI-evidence detection, and component-property clustering claims.

**Stage 2 — Target analysis** overlaps schema-introspection tooling. For relational targets, **SQLAlchemy reflection** + standard ER-diagram libraries (e.g. `eralchemy`, `schemaspy`) handle the schema-visualization piece for free. The toolkit should use these rather than re-implementing relationship-graph rendering. What's novel is the **candidate-table reasoning** layer that ranks target tables by likelihood of being populated from the pile, again using LLM analysis over the introspected schema.

**Stage 3 — Bridge synthesis** is the most heavily-overlapped stage and the most novel in combination.
- **Mapping output format**: declarative mapping idioms exist (dbt models, RML/R2RML for RDF, JSONata transforms, Singer/Meltano tap-target configs). No single idiom dominates cross-domain in 2026 — the field is fragmented along SQL-warehouse (dbt), tap/target (Singer/Meltano), and semantic-web (RML) lines. The bundle's mapping output should pick **one canonical declarative format** for the IG→Travelogue case (likely dbt-style YAML over the Postgres target) and document why; future bridges may carry different formats.
- **Automated schema matching**: a real research field. **Valentine** (Koutras et al., VLDB 2021) is the benchmark + library bundling COMA, Cupid, SimilarityFlooding. LLM-based matchers from 2023–2025 (e.g. Magneto, Jellyfish, "Schema Matching with LLMs" arXiv papers) are research-stage. Tools like **Tamr** and **OpenRefine** carry the human-in-the-loop spirit but are entity-resolution focused or pre-LLM. The toolkit's mapping-proposal step **retreads this ground** — and should explicitly cite which matcher's algorithmic style it borrows for its initial proposals. What's novel is the **playground-UX-driven iteration loop** layered on top.
- **Mapping validation via round-trip insertion**: insert a sample, observe success/failure, delete. As far as the survey could tell, this isn't a named pattern in existing tools. Closest analogs are dbt unit tests, Great Expectations pre-flight assertions, and standard ETL staging-table conventions — but elevating *transactional insertion-with-rollback into the live target* as the primary acceptance oracle for a mapping appears genuinely novel. This is the toolkit's most defensible contribution.

**Summary** — bridge-builder-toolkit's spec should plant flags at: (a) which existing tool's output format / API the toolkit consumes or emits per stage, (b) which research direction its automated-proposal layer borrows from, and (c) where it claims novelty. The novel combination is **LLM-as-outsider-analyst** + **single-page playground iteration substrate** + **insertion-into-target-DB-with-rollback as acceptance oracle** — no surveyed tool combines all three.

> _Caveat: the prior-art survey above was assembled from training knowledge and not live-verified. At plan time, run a fresh web search on "LLM schema matching 2025–2026" and "dbt Copilot mapping" to confirm current tooling and add anything the model missed._

### Out of scope (defer to other specs)

- The bridge runtime itself: the ETL job, scheduling, observability, retries, idempotency, backfill. bridge-builder-toolkit produces the *spec* for a bridge; bridge-app is what implements one.
- Generic schema-to-schema migration tooling unrelated to pile→useful-app flows.
- Auto-deployment of accepted bridges into a runtime.
- Schema modifications to the target. The target schema is read-only input.
- Bidirectional sync. Pile → target is one-way.

### Additional notes and clarifications

- The HTML deliverables are produced via the Anthropic-published Claude Code **playground** plugin (`playground:playground` skill, source at https://github.com/anthropics/claude-plugins-official/tree/main/plugins/playground). The plugin's "copy out a prompt" pattern is exactly the prompt-friendly output Stage 3 needs for capturing user-adjusted mappings and comments, and its `data-explorer`, `concept-map`, and `diff-review` templates are reasonable starting points for Stages 1, 2, and 3 respectively. Constraints inherited from the plugin and binding on this spec: single-file self-contained HTML; no external dependencies or remote assets; data embedded inline; single-screen layout (controls + live preview + prompt); dark theme; system font for UI chrome, monospace for data.
- Playground prompts must be actionable standalone — readable by an AI consumer that has not seen the playground UI. This is a documented playground convention ("common mistakes" list) and is non-negotiable here because the prompt outputs are the handoff mechanism between iterations.
- "Outsider perspective" in Stages 1 and 2 is a firm constraint, not a posture. The workflow must not be permitted to use foreknowledge of the pile-app's internal pipeline or the useful-app's internal logic. This is what makes bridge-builder-toolkit generalizable beyond the IG→Travelogue case.
- The first concrete execution of bridge-builder-toolkit must run on the **003 IG pile + 002 Travelogue schema**, and that run's output is the input spec for bridge-app. A spec that can't be cleanly applied to this real-world pair is not done.

### Key Vision Points — These Should Overrule Any Other Contradicting Statements

- **bridge-builder-toolkit produces specs, not runtimes.** The deliverable of running it is a bundle of files suitable as input to the bridge-spec authoring step. If the spec finds itself describing scheduling, retries, observability, or write-path semantics, it has drifted into bridge-app territory and should pull back.
- **Outsider posture is non-negotiable.** No leaking foreknowledge from how the pile or target was built. The whole value of bridge-builder-toolkit rests on the discipline of treating both sides as black boxes that must be characterized from their surfaces.
- **Insertion validation, when access permits, is part of acceptance** — not an optional nice-to-have. The 5-iteration ceiling exists to bound runaway loops, not to make validation skippable.
- **Every iteration's reports plus feedback are versioned and retained.** This provenance is what gives the final bundle its credibility as a spec input.
- **The IG-pile→Travelogue-schema bridge is the first product.** The spec is generic, but its first invocation is concrete, and that invocation must succeed.
- **Each stage's report is a self-contained playground.** No linked multi-page experience, no remote dependencies, no separate machine-readable sidecar. The "copy out a prompt" output is the canonical handoff mechanism between stages and between iterations, and the playground convention rules wherever they apply.
- **The orchestrator is a real component of bridge-builder-toolkit, separate from the playgrounds.** Playgrounds are closed-world artifacts; anything requiring network access, file IO, or database writes — most notably the insertion-validation step — happens in the orchestrator and is fed back into the next iteration's playground as embedded data. If the spec finds itself trying to give a playground side effects, it's wrong.
- **bridge-builder-toolkit is a self-contained App** with the same physical structure as pile-app: own directory at the project root, own venv, own `.env`, own CLI, own tests, own iteration-history dir. No shared code with pile-app or the backend. Movable to a separate repo without breaking either side — operator-supplied paths/URLs are the only coupling.
- **Stand on existing shoulders.** The toolkit retreads three established fields (data profiling, schema introspection + matching, declarative mapping). For each stage the spec must name the canonical tool/idiom it borrows from and explain what novel layer is added on top. If a stage's design diverges from established conventions without justification, that's a flag — operators familiar with `ydata-profiling`, `Valentine`, `dbt`, etc. should find the toolkit's outputs immediately legible.
- **bridge-builder-toolkit is the foundational predecessor of bridge-builder-app.** This spec is intentionally scoped to the human-driven workflow + the artifacts it produces. The automation/productization layer (CLAUDE.md's "Data Unification ambition") is a later spec that will build on the conventions, formats, and mapping vocabulary locked in here. Don't spec the future App; do leave clean seams it can grow into.
