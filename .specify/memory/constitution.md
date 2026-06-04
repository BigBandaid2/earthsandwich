# Earth Sandwich Project Constitution

> Cross-cutting principles, the catalogue of project-level planning documents,
> and the few project-wide rules that survive any single spec's lifecycle.
> **Lean on references over duplication**: where another doc owns a topic,
> this constitution points at it rather than restating it.

## Core Principles

### I. Evolutionary Development, Not Dogmatic
Development is evolutionary, not dogmatic. Specs sometimes guide the project forward and sometimes catch up to capture what already emerged from working code. We rigorously question what's actually helping, prefer documenting emergent practice over enforcing pristine workflows, and treat [`docs/workflow.md`](../../docs/workflow.md) as the living account of how this project actually operates. When practice drifts from a spec, the spec is re-authored (see the 003 re-author on 2026-05-27 for the worked example).

### II. Apps Are the Architectural Unit
The project is composed of **Apps** — self-contained pieces of the system with well-defined interfaces between them. Apps are defined in [`docs/roadmap.md`](../../docs/roadmap.md). The App is the *architectural* unit; specs are *project-management* units and do **not** map 1:1 to Apps. A complex App may span multiple specs over time, and a spec may live entirely inside one App. Cross-App communication happens through explicit contracts (REST APIs, "piles", future ETL layers), never through shared code or shared filesystem reach-arounds.

### III. Project Purposes Are Authoritative
All work serves one or more of the three Purposes catalogued in [`docs/roadmap.md`](../../docs/roadmap.md). Features that don't serve a Purpose are deferred or declined.

### IV. AI-Driven Development as First-Class
Claude Code is a primary collaborator and this project is a learning sandbox for driving it well. Durable artefacts (memory entries, well-shaped prompts, repeatable workflows captured in [`docs/workflow.md`](../../docs/workflow.md)) are preferred over ad-hoc hacks. Identifiers in code and data avoid model-specific names so the model layer can be swapped without churning the data model.

### V. Inference Steps Preserve Their Inputs
Generalized from 003 FR-105. Any step in any App that calls a model to infer something MUST persist the original input alongside the output, so the inference can be re-evaluated, audited, or re-run with a different model without re-fetching the source. This is the cross-App expression of "the model is replaceable; the data is not."

## Cardinal Rules

Non-negotiable conventions that apply across all Apps. Stated here as the authoritative one-liners; the *why* and the worked examples live in [`docs/workflow.md`](../../docs/workflow.md) and the memory entries under [`.specify/memory/`](.).

1. **`tasks.md` is a historical record for completed and in-progress work.** New work appends new phases to the bottom; never restructure or rewrite phases whose tasks are completed or in progress. Stories and tasks that were envisioned but **never started** MAY be discarded during a spec overhaul or split — only what was actually worked on is sacred.
2. **No sprint / owner / status state in JIRA-synced artefacts.** PM state belongs in narrative docs (`docs/planning/`), not in `jira-mapping.json` or other synced files.
3. **No model-specific names in code or data model.** Identifiers describe the *role* (`infer_post_location`, `reasoning`), not the model (`get_location_via_claude`, `claude_reasoning`).
4. **Inference inputs are preserved** (Principle V above, stated procedurally here so it's enforceable in code review).
5. **Lean on references over duplication.** Where one project-level doc owns a topic, other docs reference it rather than restating its content. Reduces drift between docs that contradict each other and reduces edit cost when a topic moves. Authoritative homes for cross-cutting topics are catalogued in the Project-Level Planning Documents table below.

## Foundational Technology

Durable choices that are unlikely to change without a constitutional amendment:

**TypeScript · Python · PostgreSQL · Docker · Spec Kit · JIRA · GitHub**

Everything else (frameworks, libraries, model providers, scrapers, IDE extensions, …) is App-local and owned by that App's spec/plan. The list above is the *floor*; new Apps may add to it, but removing one of these requires an amendment.

## Project-Level Planning Documents

The authoritative catalogue. Each row states the document's **Purpose** and **Boundary** so future contributors know which file owns which topic and don't create overlap.

| Document | Purpose | Boundary |
|---|---|---|
| `.specify/memory/constitution.md` | This file. Cross-App principles, Cardinal Rules, foundational tech, the documents catalogue itself. | Doesn't enumerate Apps, sprint plans, or workflow steps — those have dedicated homes below. |
| `docs/roadmap.md` | Vision (the three Purposes), App definitions, current and planned spec list, boundary rules between Apps, explicit non-goals. | Doesn't dictate workflow or restate principles. Doesn't catalogue non-vision docs. |
| `docs/workflow.md` | How we actually work: weekly cadence (Before / During / After), JIRA sync conventions, sprint planning, time logging, emergent process notes. | Doesn't define what we're building (that's roadmap + specs). Doesn't enumerate principles (those are constitutional). |
| `CLAUDE.md` | Active-spec status + cross-App relationships, surfaced to Claude Code as on-load context every session. Updated as specs come and go. | Carries no policy. Reads as a directory pointer for Claude sessions, not as an authority. |
| `README.md` | Public-facing entry point: what the project is, how to run each part locally, where to look next. | No architecture or policy. |
| `docs/planning/YYYY-WNN.md` | Per-sprint plans (one per ISO week) — goals, attestation, retros. | Per-sprint, not project-level. Don't accumulate workflow rules here. |
| `docs/planning/time-log.tsv` | Append-only daily time log per person. | Per-sprint admin. |
| `.specify/memory/MEMORY.md` and `feedback_*.md` / `project_*.md` siblings | Auto-loaded memory entries for AI sessions: user preferences, validated feedback rules, project state captures. | Don't duplicate constitutional or workflow content — reference them. Operational signal, not authority. |
| `specs/<spec>/spec.md`, `plan.md`, `tasks.md`, etc. | Per-spec deliverables. Constitution-bound for cross-cutting rules; otherwise free to define their own internals. | Spec-local: their contents don't bind other specs or set project-wide policy. |

## Governance

This constitution amends through normal PR review when a principle materially changes; the version line below tracks the history. Spec-local decisions do NOT require a constitutional amendment — they're captured in the spec's own clarifications log.

The constitution's job is to reduce the cost of revisiting the same architectural decisions and to make the project's evolved scope legible to new collaborators (human or AI). When two documents disagree on a cross-cutting point, this one wins until amended.

**Version**: 2.1.0 | **Ratified**: 2026-04-22 | **Last Amended**: 2026-05-28
<!-- v1.0.x (2026-04-22 → 2026-04-24) framed the project as a "Static First / Vanilla JS" web app. v2.0.0 (2026-05-28) replaces that framing entirely to reflect the actual evolved architecture (front-end + backend + ingestion App + planned bridge / bridge-builder Apps), the App-segregation principle, and the AI-driven-dev framing. v2.1.0 (2026-05-28) adds Cardinal Rule #5 ("Lean on references over duplication"). -->
