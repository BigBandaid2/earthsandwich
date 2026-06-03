# SDLC Workflow Guide

> Source of truth for how this team uses Spec Kit, JIRA (OCS), and Claude Code together. Read before your first commit. Re-read whenever the workflow surprises you.

**Status**: Living document. Edit via PR; do not silently rewrite.

---

## Weekly Cadence

Two rhythms operate here. **Per User Story** (the "After Each User Story" sub-section below) fires whenever a Story finishes — could happen twice in a week, or zero times — and is the gate between "operator marked all tasks done" and the manual JIRA Done flip. **Weekly** (the three meeting-anchored sub-sections after it) is the team-meeting rhythm: drift scan, sync, attest, plan.

### After Each User Story

Triggered when an operator believes a User Story is complete (all its tasks `[x]`-marked). Required gate before flipping the JIRA Story to Done.

1. **Build the DoD review playground** at `specs/<spec>/reviews/phase-NN-usN.html` (see [§Definition of Done Review](#definition-of-done-review) for table contents, carry-forward handling, and the prompt-back convention).
2. **Schedule a peer-review walkthrough** with at least one other team member — never the builder alone. Peer is the knowledge-share + accountability check, not a rubber stamp.
3. **Reviewer fills disposition fields** in the playground: name, general comment, `DONE` / `Needs work`.
4. **Paste the playground's copy-out prompt into Claude.** Records the outcome: peer-review attestation in `tasks.md`, any peer-driven spec amendments, and (DONE only) the manual JIRA Story flip from In Progress → Done.

### Before Weekly Team Meeting

1. **Merge open feature branches into the default branch** — get all shipped work onto a coherent base so the drift scan + JIRA sync read from a single source.
2. **Reconcile Code to Tasks** — drift scan against previous drift reconciliation → HEAD (see [§Reconciliation](#reconciliation-claudespec-drift-scan)).
3. **New Phase/Story for Code Drift** — bundle detected changes as a new Phase appended to the relevant `tasks.md`.
4. **Sync Spec State to JIRA** — push new phases as Stories, advance Stories with any task progress to **In Progress** (never directly to Done), and check each newly-created Story for `Duplicate` relationships with existing Stories (overhauled predecessors, user tickets) — link them when found (see [§JIRA sync](#jira-sync)).
5. **Backfill sprint on Done items** — any Done Story missing a sprint goes into the currently-open sprint (see [§Sprint membership rule](#sprint-membership-rule)).
6. **Log estimated hours** — append daily rows to `docs/planning/time-log.tsv` and add a person/story hours summary to the current sprint plan (see [§Time logging](#time-logging)).
7. **Check Progress Against Previous Sprint Plan** — append sprint review notes.

### During Weekly Team Meeting

8. **Attest hours** — each team member confirms their estimated hours, adds meeting time, fills the `Hours Attested` column (see [§Time logging](#time-logging)).
9. **Plan the week in JIRA's UI** — drag stories into the sprint, assign owners, set story points, write the Sprint goal, start the next sprint.

### After Weekly Team Meeting

10. **Pull current-sprint Stories from JIRA** — JQL: `project = OCS AND sprint = openSprints()`. List everything the team committed to this week, with owner and status. This is the baseline for steps 11–17: the planning doc, the link sweep, and the post-meeting push all read off the same set.
11. **Link related tickets** — `Duplicate` for 1-to-1 parallels with a spec-kit Story, `Blocks` for prerequisite dependencies between tickets, `Relates` for everything else (see [§JIRA sync](#jira-sync)).
12. **Create New Sprint Plan** — author `docs/planning/YYYY-WW.md` from the step-10 pull, which is canonical: include only people and items it returned. Header: `**Sprint**` + `**Goal**` (verbatim from JIRA). Body: one `### <Person>` sub-section per owner.
13. **Push to JIRA** — any phases newly decided in the meeting become new Stories in OCS, placed in the current sprint for velocity attribution. (Drift-discovered phases were already synced + sprint-attributed in steps 4–5.)
14. **Update time-log artifacts with attested hours** — fold each attendee's step-8 attestation into `docs/planning/time-log.tsv` (fill empty `Hours Attested` cells, add dedicated rows for meeting time), regenerate `docs/planning/time-log.html` from the TSV so its embedded data matches, and update the sprint-review file's Hours section with attested totals.
15. **Merge master into your feature branch.** Project-level updates from steps 3–6 land on master; each team member merges master into their active feature branch so subsequent work reads off the current state.
16. **Knowledge refresh** — git-log digest + `/speckit.onboard.quiz` (~5 min per dev; see [§Knowledge refresh](#knowledge-refresh-monday-quiz)).
17. **Diagrams** — `/speckit.learn.review` to refresh component diagrams.

The weekly cadence is the contract. The per-feature ceremony (below) is the optional discipline for serious architectural work.

---

## TL;DR — what each system owns

| System | Owns |
|---|---|
| **Spec Kit** (`specs/00N-feature/`) | Specifications, acceptance criteria, requirements, plans, tasks. The *what* and *why*. |
| **Code repo** (`src/`, `public/`, etc.) | Implementation. The *how*. |
| **JIRA** (project `OCS`) | PM state: priority, owner, sprint, story points, status. The *who*, *when*, *in what order*. |
| **Git** | Reviewable change events. Audit trail. |
| **Memory** (`.claude/.../memory/`) | Durable preferences across Claude sessions. |

If unsure where a change belongs, match the question it answers to the table above.

---

## Spec Kit + JIRA conventions

The [constitution's Cardinal Rules](../.specify/memory/constitution.md#cardinal-rules) apply project-wide. The conventions below are workflow-specific — how Spec Kit and JIRA should interact:

1. **Spec Kit drives spec content. JIRA drives schedule and assignment.** Owners and sprints don't go into `spec.md`; requirements don't go into JIRA descriptions.
2. **One Spec Kit feature = one JIRA Epic. One Phase = one Story.** Subtasks exist only for genuinely active phases; completed phases live at the Story level.
3. **One-way sync: Spec Kit → JIRA, never the reverse.** PM fields live in JIRA's UI; they're not mirrored into the repo.

---

## New Specs and Spec Overhauls

For structural changes the weekly cadence can't absorb: carving a spec in two, re-authoring a spec from scratch, or starting a brand-new spec. [§Project-Level Doc Propagation](#project-level-doc-propagation) at the bottom is common to all three.

### Splitting features out of an existing spec

When a spec has grown beyond a single coherent concern.

1. **Decide the split.** Sketch which user stories, FRs, edge cases, success criteria, and assumptions go to each side before touching files.
2. **Create the new spec dir** at next available NNN: `mkdir -p specs/<NNN>-<slug>/checklists`. Either copy the original files and trim, or run `/speckit.specify` for the new side if scope warrants.
3. **Trim the original.** Replace each moved item with a one-line pointer: `> [Description] moved to specs/<NNN>-<slug>/spec.md on <date>.` Update inline FR/US/SC numbers.
4. **`tasks.md` on both sides.** Phases with completed-or-in-progress tasks stay on the original ([Cardinal Rule #1](../.specify/memory/constitution.md#cardinal-rules)); envisioned-but-not-started phases may be discarded or rewritten. Phase numbers carry across the split (if original was at Phase 16, both sides continue at Phase 17).
5. **Fresh `jira-mapping.json`** on the new spec. Existing JIRA tickets stay where their work actually shipped.
6. **`/speckit.plan`** for the new spec if you didn't author via `/speckit.specify`.
7. **Propagate** (see [§Project-Level Doc Propagation](#project-level-doc-propagation)).

Worked example: `002-data-ingestion` → `002-database-backend` + `003-ingestion-pipeline` on 2026-05-22.

### Overhauling an existing spec from scratch

When patches won't bridge the gap between the spec and reality.

1. **Draft a specify-prompt** at `specs/<NNN>-<slug>/specify-prompt-draft.md`: (a) original scope, (b) what's been built/decided since, (c) the new vision. Paste-and-discard input to `/speckit.specify`.
2. **Stash preserved files OUTSIDE `specs/`.** Move `tasks.md`, `jira-mapping.json`, etc. into `_<NNN>-keep/` at the repo root — otherwise the NNN scan allocates a new number instead of reusing the slot.
3. **Swap.** `rm -rf specs/<NNN>-<slug>/` → run `/speckit.specify` with the prompt → `mv _<NNN>-keep/* specs/<NNN>-<slug>/ && rmdir _<NNN>-keep`.
4. **Iterate on the new spec.** An overhaul is the cheapest moment to capture latent decisions explicitly.
5. **`/speckit.plan` and `/speckit.tasks` regeneration is OPTIONAL.** Phases with completed-or-in-progress tasks must stay at the top of `tasks.md` ([Cardinal Rule #1](../.specify/memory/constitution.md#cardinal-rules)); envisioned-but-not-started phases may be discarded. Merge by hand if needed.
6. **Sync to JIRA + mark overhauled.** Push new Stories via `/speckit.jira.specstoissues`; suffix pre-overhaul Stories' titles with `(overhauled)` (leave at `Done`); add `Duplicate` / `Relates` links per [§Issue-link reconciliation](#issue-link-reconciliation).
7. **Propagate** (see [§Project-Level Doc Propagation](#project-level-doc-propagation)).
8. **Update cross-references in sibling specs.** Other specs may reference this one's FRs or concepts by number or name. `grep -rn "<spec-slug>" specs/` to find them; update or remove references that now point to retired or renumbered FRs.

Worked example: `003-ingestion-pipeline` re-author on 2026-05-27 — the split-time spec assumed APScheduler-in-backend; reality was a standalone CLI App. Patches couldn't bridge that gap.

### Brand-new spec

Standard ceremony for a feature with no prior history:

1. `/speckit.specify "<description>"` (the `before_specify` hook handles the feature branch).
2. `/speckit.clarify` if needed.
3. `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`.
4. `/speckit.jira.specstoissues <slug>` — Epic + Stories + active-phase Subtasks.
5. PR to default branch — review, merge, delete branch.
6. `/speckit.jira.sync-status <slug>` — Subtasks flip to Done automatically; Stories advance to In Progress. Walk each Story's Independent Test and flip to Done manually in JIRA when verified.
7. **Propagate** (see [§Project-Level Doc Propagation](#project-level-doc-propagation)).

### Project-Level Doc Propagation

Sweep these after any flow above. The [constitution's Documents catalogue](../.specify/memory/constitution.md#project-level-planning-documents) is authoritative on what each doc owns; the table is the operational "which doc to touch, when":

| Doc | Update when |
|---|---|
| [`docs/roadmap.md`](roadmap.md) | **Always.** Add/remove the spec row, update the App row + boundary rules, add or edit the Spec Reference paragraph. |
| [`CLAUDE.md`](../CLAUDE.md) | **Always.** Keep the active-specs catalogue current (between `<!-- SPECKIT START -->` and `<!-- SPECKIT END -->`). |
| [`README.md`](../README.md) | When the spec corresponds to a user-visible part of the project layout. |
| [`.specify/memory/constitution.md`](../.specify/memory/constitution.md) | **Rarely.** Only when a cross-cutting principle, Cardinal Rule, or App-level assumption changes. |
| Sibling specs | When cross-references go stale (retired FRs, moved-out FRs, renamed concepts). |

Per [Cardinal Rule #5](../.specify/memory/constitution.md#cardinal-rules), prefer references over duplication.

---

## Reconciliation: Claude/spec drift scan

Between Monday meetings, Claude makes small changes that don't always make it into `tasks.md`. The drift scan catches them.

Ask Claude: *"Run a spec drift scan. For each commit touching `src/`, `public/`, or `package.json`, list whether it has a corresponding line in any `tasks.md`. Flag everything that doesn't, grouped by spec."*

**Starting point.** Claude derives `<last_known_good_commit>` itself — never pass a date. The most recent `## Phase N: Drift Reconciliation (YYYY-MM-DD …)` heading across all `specs/**/tasks.md` defines the baseline; scan `<that-commit>..HEAD`. Fall back to last Monday 00:00 if no such phase exists. Scans are idempotent across re-runs and consecutive weeks chain without overlap.

Claude enumerates changed files per commit, buckets them by spec, greps `tasks.md` for matches, and outputs unmatched commits as a proposed Phase N+1. Always *propose* — never append directly ([Cardinal Rule #1](../.specify/memory/constitution.md#cardinal-rules)).

Cadence: per-commit is too noisy; per-push (lightweight drift check via `after_implement` hook) and the weekly Monday scan together are the right catch-up rhythm.

---

## JIRA sync

Two commands keep JIRA aligned with the spec state:

- `/speckit.jira.specstoissues <spec>` — creates an Epic for the spec and a Story for each `## Phase N: ...` in its `tasks.md`. Existing Stories are left alone; only new phases are pushed. Subtasks are *not* created by default — sync at the Story level unless there's a clear reason to break out individual tasks (e.g. active forward-sprint work that needs triage in JIRA).
- `/speckit.jira.sync-status <spec>` — reads `[ ]` / `[~]` / `[x]` task flips in `tasks.md` and transitions the corresponding JIRA issues. **Subtasks** map straight through: `[ ]` → `To Do`, `[~]` → `In Progress`, `[x]` → `Done`. **Stories** advance only as far as `In Progress` (any `[~]` or `[x]` task → `In Progress`); the final flip to `Done` is **manual in JIRA** by the operator who has verified the Story's Independent Test passes. Sync never advances a Story to Done, even when all its tasks are `[x]`.

> **Why Stories don't auto-flip to Done.** Task-IDs in commit messages prove a commit *touched* the task, not that the *Story* is shippable. The Story's Independent Test (in its description) is the acceptance bar — and the sync agent has no way to run it. Manual Done flip = "I (a human) verified this Story actually works end-to-end." This rule was added 2026-06-01 after OCS-108 was auto-flipped Done off [T056]–[T062] commits while the frontend↔backend wiring wasn't actually live.

### Sprint membership rule

Any Story flipped to **Done** must belong to a sprint — default to the currently-open sprint unless the work demonstrably happened in a different one (in which case set that sprint explicitly). This keeps velocity attribution accurate at sprint-review time.

**Operationalised as step 5 of the weekly cadence.** After step 4's status-flip pass, query JIRA for Done-without-sprint Stories and assign each to the open sprint:

- JQL: `project = OCS AND status = Done AND sprint is EMPTY AND issuetype not in (Subtask, Epic)` — Subtasks inherit their parent's sprint and can't be set directly; Epics never belong to a sprint in JIRA Cloud's next-gen projects. The filter keeps the result list to items the rule can actually act on.
- For each result: set the `sprint` field to the currently-open sprint ID (via JIRA UI drag-into-sprint, or the MCP `editJiraIssue` with `customfield_10020` = sprint ID).
- Override the default only when the work demonstrably shipped in a prior sprint — e.g. a Story flipped Done late but the commits land in last sprint's window. In that case set the historical sprint explicitly.

In-progress stories are *not* automatically added to the current sprint. Add one case-by-case when partial work has shipped this sprint and the team wants velocity credit for it.

### Issue-link reconciliation

JIRA accumulates parallel issues that describe the same or related work — typically: (a) user-created tickets vs. spec-kit Stories, and (b) pre-overhaul spec-kit Stories vs. their post-overhaul replacements. When two issues describe the same work, the *current canonical* one (post-overhaul Story, or the spec-kit Story over a user ticket) is the record of truth and the older / informal one gets linked to it rather than left orphaned.

| Link | When | Direction (`inwardIssue` / `outwardIssue`) |
|---|---|---|
| `Duplicate` | Two issues describe the same work 1-to-1 (user ticket ↔ spec-kit Story; pre-overhaul Story ↔ post-overhaul Story) | canonical / duplicate |
| `Blocks` | One ticket must finish before another can start | blocker / blocked |
| `Relates` | Tangential or non-1-to-1 overlap — spike, follow-on, historical context, **or a pre-overhaul Story whose scope was split across multiple post-overhaul Stories** | either |

**Duplicate-check is step 4 of the weekly cadence** (`Sync Spec State to JIRA`). For each Story `/speckit.jira.specstoissues` just created, scan: (1) user-created tickets describing the same work; (2) pre-overhaul Stories the new one supersedes. Auto-link on a clean 1-to-1; use `Relates` when scope diverges. Surface candidates in the sprint review when judgement is needed.

Don't touch the Subtasks under spec-kit Stories — those are managed by the speckit-jira agents; link at the Story level only. Surface `Blocks` chains at planning. OCS has no `Blocked` status; the `Blocks` link IS the dependency record. True close-cascade requires Parent-Subtask conversion (out of scope) — manually close duplicates when the spec-kit Story closes.

### What never goes into the sync

Per [Cardinal Rule #2](../.specify/memory/constitution.md#cardinal-rules), `specs/<spec>/jira-mapping.json` must not record sprint, owner, status, story points, or priority — **including derived counters like `completed_stories` / `pending_stories` / `completed_tasks`** that summarize status. Those PM fields live in JIRA's UI; the mapping file carries only identity (key, summary, URL, parent/child structure) plus a `total_stories` / `total_tasks` count. Two writers (this file + JIRA's UI) on the same field guarantees drift. Narrative artefacts that humans read but tools don't sync (`docs/planning/YYYY-WW.md`, this guide) are exempt.

---

## Definition of Done Review

Each User Story closes with a peer-reviewed Definition-of-Done walkthrough — the [§After Each User Story](#after-each-user-story) gate referenced in the weekly cadence. Purpose: knowledge-share, sanity-check, gap-finding, capturing criteria that can't be fully satisfied, and accountability (the builder is not also their sole tester and judge).

### The playground

Each Story gets a single-file HTML playground at `specs/<spec>/reviews/phase-NN-usN.html`. Hand-curated for now; the template will likely evolve before it's worth scripting. Layout follows the `playground:playground` conventions: single file, vanilla HTML/CSS/JS, no external deps, dark theme, live state, copy-out-a-prompt.

The playground's table aggregates the Story's Definition of Done from `spec.md` and `tasks.md`:

| Source | Rows |
|---|---|
| spec.md User Story `Independent Test` | one per sub-clause (a, b, ...) |
| spec.md User Story `Acceptance Scenarios` | one per AS |
| tasks.md phase `Checkpoint` | one row |
| spec.md `Success Criteria` tied to the Story | one per SC |

Each row carries: builder's pre-review AI assessment (`satisfied` / `partial` / `forward` / `needs review`), supporting evidence (commits, test names, file paths), an editable peer-comment textarea, and a satisfied checkbox. The reviewer can add new rows for criteria the spec missed, delete rows for criteria deemed irrelevant, and edit existing item text — all of which the prompt records as spec amendments.

### Carry-forward items

Items that can only be tested in another App (typical case: contracts the consuming App must honour but which the producing App cannot self-verify) get a `forward` assessment in the playground. The peer-review walkthrough is responsible for **routing the forward item to the spec that will test it** — leaving forward items in the playground alone is not enough.

Two-step protocol per forward item:

1. **Mark the playground row's evidence** with `carried forward to specs/<spec>/...` so the trail is visible at review time.
2. **Open the receiving spec and capture the constraint there.** Bridge-app-side contracts go into spec 004 (`bridge-builder-toolkit`), which relays them into the bridge-app spec via its Final Bundle. Other downstream destinations work the same way: file the constraint in the spec that owns the verification, and reference the originating Story.

Worked example: 003 Phase 22 / US3 has two bridge-app-side Acceptance Scenarios (AS#1, AS#2) that can't be verified until bridge-app exists. They live as `forward` in `specs/003-ingestion-pipeline/reviews/phase-22-us3.html` and as relayed constraints in `specs/004-bridge-builder-toolkit/spec.md`'s carry-forward block (FR-092).

### Disposition + prompt

The reviewer's binary `DONE` / `Needs work` disposition drives the copy-out prompt's tail. DONE-path lists 5 follow-up actions (Checkpoint attestation in `tasks.md`, spec amendments if any, JIRA Story flip In Progress → Done, commit + push). Needs-work-path lists 4 different ones (address unsatisfied items, amend spec if any, schedule second pass, Story stays In Progress).

Without the peer-review prompt being executed, no Story → Done. The In-Progress-only sync rule (see [§JIRA sync](#jira-sync)) presumes peer review is the final hop.

---

## Time logging

`docs/planning/time-log.tsv` is an append-only daily ledger of estimated and attested hours. One row per day per person per Story (or per `Overhead` category). It exists to make velocity attribution honest at sprint review and to build a calibration loop: the gap between *estimated* and *attested* hours tells you whether your future estimates need adjustment.

### Columns

| Column | Notes |
|---|---|
| Date | YYYY-MM-DD |
| DOW | Day of week |
| Sprint | `OCS Sprint N` (the sprint the work calendar-attributes to) |
| Story | JIRA key (`OCS-NN`). Use `Overhead` for non-Story work (sprint planning, workflow doc updates, JIRA sync, spec restructures). |
| Person | Full name matching git author / JIRA assignee |
| Commits | Commit hash + brief description. Include qualitative notes that explain the estimate (e.g. "AI-assisted burst, 8 commits in 24 min"). |
| Time Span | Calendar span of commits that day (`HH:MM-HH:MM`). Reference only — not the same as active work time. |
| Hours Estimated | Single decimal. Filled before the weekly team meeting from commit history + judgment. |
| Hours Attested | Filled by the team member after the meeting. Includes meeting time on top of work time. Empty until attested. |

### Before the weekly team meeting

After the drift scan and JIRA sync, the team lead enumerates commits since the last sync, groups them by Story + person + day, and writes one row each with `Hours Estimated`. Add a person/story summary block at the bottom of `docs/planning/YYYY-WW.md` so the meeting has a quick read of where effort went.

### After the weekly team meeting (attestation)

Each team member reviews their rows and fills `Hours Attested`:

- **Add meeting time on top of work time.** The weekly meeting itself counts — add it to one of your existing rows for that day, or create a dedicated `Overhead — meeting` row.
- **Adjust the number** if your actual time differed significantly from the estimate. The gap is feedback for tuning future estimates; don't silently re-baseline.
- Leave a note in the Commits column if context is important (e.g. "deeper than estimated — blocked 2h on instagrapi challenge").

Attested numbers are the source of truth for sprint velocity. Estimated numbers stay in place for the calibration history.

---

## Git branches and PRs

**Branches**: one per Spec Kit feature, named for the spec dir (`001-world-travelogue`). Created automatically by `/speckit.specify`. A long-running branch can host many phases — phases append to `tasks.md` as you go. The default branch is the integration point.

**Pull requests**: one PR per merge to default. PR description references the Epic and any Stories it closes (`Closes OCS-49, OCS-50`). Use `Draft` for in-progress branches that haven't reached a coherent merge candidate. PRs review the shipped diff; spec review happens in the spec PR earlier in the cycle.

### Abandoning a feature

Goal: don't pollute `tasks.md` or JIRA with abandoned exploratory work, but also don't erase the historical record.

1. **Spec never merged** (still on its feature branch): delete the branch. Transition the JIRA Epic and Stories to **"Won't Do"** (preserves audit trail). Add a one-paragraph postmortem to the Epic.
2. **Spec partially merged**: append a final phase to `tasks.md` titled `Phase N: Abandonment — <reason>` describing what was reverted, what was kept, and why. Epic stays open at "Won't Do"; Stories marked Done (for code that landed) or Won't Do (for code that didn't).
3. **Never delete past phases.** Abandonment is itself a phase.

---

## Sprint goals

Capture the week's intent in two places: the JIRA Sprint goal (one sentence) and the planning meeting notes.

**JIRA Sprint goal**: set in Project → Boards → OCS → Sprint settings. Write a single sentence describing the *outcome* the team commits to. Not a list, not a wishlist.

> Good: "Ship the scheduled Instagram pull and a draft SDLC workflow guide; explore the legacy comment-bot integration."
> Bad: "Do all the things from the planning meeting."

**Planning notes**: each Monday produces `docs/planning/YYYY-WW.md` (ISO week number). Header: `**Sprint**` (`OCS Sprint N` + date range) and `**Goal**` (matches the JIRA Sprint goal). Body: one `### <Person>` sub-section per team member, each listing that person's stories for the sprint.

---

## learn extension: keeping diagrams fresh

Targets in `specs/00N-feature/`: `component-diagram.md`, `system-design.md`, `software-architecture.md`. They rot the moment code changes without a refresh.

**Recommended**: weekly batch. Run `/speckit.learn.review` as the Monday cadence **Diagrams** step.

**Optional, for architecturally-sensitive work**: hook into `after_implement` so diagrams refresh after every implementation pass:

```yaml
hooks:
  after_implement:
    - extension: learn
      command: speckit.learn.review
      enabled: true
```

This adds latency to every `/speckit.implement`. Use sparingly.

---

## Knowledge refresh: Monday quiz

Goal: keep team-wide understanding sharp without a daily standup. The `onboard` extension is designed for new joiners but generalizes to weekly recall.

The `before_implement` onboard hook is already enabled in `.specify/extensions.yml` (`speckit.onboard.before-implement`) — it nudges you to skim recent project changes before touching code.

**Weekly review** (Monday cadence **Knowledge refresh** step) — two parts, ~5 min per developer:

1. **Digest** — ask Claude: *"Give me a weekly review since last Monday — what shipped, what's active, what's blocked."* Claude composes a `git log` summary plus an Atlassian MCP query for active sprint state. Three sections expected: shipped commits mapped to phases, active sprint issues with owners, items with no movement in 7+ days.
2. **Quiz** — run `/speckit.onboard.quiz`. Generates 5 questions calibrated to your profile level (`junior` / `mid` / `senior`), grounded in real project artifacts, and persisted in `.onboard/profiles/<name>.json` so questions never repeat.

No enforcement, no scoring, no surveillance — just a structured nudge for context refresh. If a quiz reveals confusion, that's a signal to update the spec or the docs.

---

## Maintenance

This document is itself part of the workflow it describes:

- Material changes → PR review.
- If the workflow surprises you, the doc is wrong — fix the doc, then fix the workflow.
