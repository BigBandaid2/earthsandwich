# SDLC Workflow Guide

> Source of truth for how this team uses Spec Kit, JIRA (OCS), and Claude Code together. Read before your first commit. Re-read whenever the workflow surprises you.

**Status**: Living document. Edit via PR; do not silently rewrite.

---

## Weekly Cadence

Roughly once per week, the Team Lead is responsible for grasping the current state of the project, capturing all progress since the last sprint review, planning objectives for the sprint to come, and keeping the core spec readable and coherent. 

### Before Weekly Team Meeting

1. **Reconcile Code to Tasks** — drift scan against preview drift reconciliation → HEAD (see [§Reconciliation](#reconciliation-claudespec-drift-scan)).
2. **New Phase/Story for Code Drift** - bundle detected changes to a new Phase in appended to relevant `tasks.md` for shipped work.
3. **Sync Spec State to JIRA** — push new phases as Stories and flip completion statuses so the planning meeting reads off current JIRA state (see [§JIRA sync](#jira-sync)).
4. **Log estimated hours** — append daily rows to `docs/planning/time-log.tsv` and add a person/story hours summary to the current sprint plan (see [§Time logging](#time-logging)).
5. **Check Progress Against Previous Sprint Plan** - append sprint review notes.

### During Weekly Team Meeting

6. **Attest hours** — each team member confirms their estimated hours, adds meeting time, fills the `Hours Attested` column (see [§Time logging](#time-logging)).
7. **Plan the week in JIRA's UI** — drag stories into the sprint, assign owners, set story points, write the Sprint goal.

### After Weekly Team Meeting

8. **Link related tickets** — `Duplicate` for 1-to-1 parallels with a spec-kit Story, `Blocks` for prerequisite dependencies between tickets, `Relates` for everything else (see [§JIRA sync](#jira-sync)).
9. **Create New Sprint Plan** - Create new sprint plan via Jira tickets or directly
10. **Push to JIRA** — any phases newly decided in the meeting become new Stories in OCS, placed in the current sprint for velocity attribution. (Drift-discovered phases were already synced in step 3.)
11. **Knowledge refresh** — git-log digest + `/speckit.onboard.quiz` (~5 min per dev; see [§Knowledge refresh](#knowledge-refresh-monday-quiz)).
12. **Diagrams** — `/speckit.learn.review` to refresh component diagrams.

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

## Cardinal rules

1. **`tasks.md` is a historical record.** New work goes in **new phases** appended to the bottom. Never restructure or rewrite past phases. Status flips (`[ ]` ↔ `[x]` ↔ `[~]`) are progress, not rewrites.
2. **Spec Kit drives spec content. JIRA drives schedule and assignment.** Don't put owners or sprints into `spec.md`. Don't put requirements into JIRA descriptions.
3. **One Spec Kit feature = one JIRA Epic. One Phase = one Story.** Subtasks exist in JIRA only for genuinely active phases. Completed phases live at the Story level only.
4. **Default branch is the source of truth for shipped work.** Anything unmerged isn't shipped, regardless of how good the demo was.
5. **One-way sync: Spec Kit → JIRA, never the reverse.** PM fields are author-time inputs in JIRA's UI. Don't mirror them into the repo.
6. **Synced artifacts carry identity, not state.** Files that `spec-kit-jira` reads or writes — primarily `specs/<spec>/jira-mapping.json` — must not record sprint, owner, status, story points, or priority. They store only key, summary, URL, and parent/child structure. Two writers (this file + JIRA's UI) on the same field guarantees drift. Narrative artifacts that humans read but tools don't sync (`docs/planning/YYYY-WW.md`, this guide) are exempt.

---

## New Specs and Spec Overhauls

Use this section when a spec changes shape in a way the weekly cadence can't absorb: an existing spec needs to be carved in two, an existing spec needs to be re-authored from the ground up, or a brand-new spec is needed. The weekly cadence (top of doc) is the default for incremental work; reach for the ladders below only when the change is structural.

The **Project-Level Doc Propagation** sub-section at the bottom is common to all three flows.

### Splitting features out of an existing spec

When a spec has grown beyond a single coherent concern and needs to become two. Worked example: `002-data-ingestion` → `002-database-backend` + `003-ingestion-pipeline` on 2026-05-22.

1. **Decide the split.** Identify which user stories, FRs, edge cases, success criteria, and assumptions belong to each side. Sketch the list before touching files — it makes step 4 mechanical instead of judgmental.
2. **Reserve the new spec's NNN.** Next available three-digit prefix; pick a slug.
3. **Create the new spec dir.** `mkdir -p specs/<NNN>-<slug>/checklists`. Either:
   - **Copy approach**: copy the original spec files into the new dir and trim each side, OR
   - **Run `/speckit.specify`** for the new side if the carved-out scope is large enough to deserve a fresh prompt-driven authoring.
4. **Trim the original spec.** For each item moving to the new spec, replace the moved content with a one-line pointer of the form `> [Description] moved to specs/<NNN>-<slug>/spec.md on <date>.` Do **not** delete — pointers preserve cross-reference legibility. Update any FR/US/SC numbers that referenced the moved content.
5. **Handle `tasks.md` on both sides.** Preserve phases whose tasks are completed or in progress on the original (Cardinal Rule #1); start a fresh phase list on the new spec. **Phases of envisioned-but-not-started work MAY be discarded or rewritten** during the split — only what was actually worked on is sacred. **Phase numbers carry across the split** — if the original was at Phase 16, the next phase on either side is Phase 17, so reconciliation reports remain comparable.
6. **Create a fresh `jira-mapping.json`** for the new spec. Existing JIRA tickets stay associated with whichever spec their work actually shipped under; new tickets follow the new mapping.
7. **Run `/speckit.plan`** for the new spec if you didn't author via `/speckit.specify`. `/speckit.tasks` is optional at the split moment — historical phases in step 5 may already be the right starting point.
8. **Propagate to project-level docs** (see [§Project-Level Doc Propagation](#project-level-doc-propagation)).

### Overhauling an existing spec from scratch

When a spec has drifted so far from the actual codebase that patching it would produce an incoherent document, re-author from scratch rather than continuing to amend. Worked example: `003-ingestion-pipeline` on 2026-05-27 — the split-time spec (2026-05-22) had assumed an APScheduler-in-backend layout, but reality had become a standalone CLI App with multi-target, anti-throttle, streaming, dual-path geocoding, and physical self-containment. Patches couldn't bridge that gap.

1. **Draft a specify-prompt** at `specs/<NNN>-<slug>/specify-prompt-draft.md`. Structure: (a) original scope at the time of last authoring, (b) a numbered list of what's actually been built or decided since, (c) the vision section to be re-authored. Have Claude help draft from the existing spec + recent commits; you edit. The prompt is paste-and-discard input for `/speckit.specify` — you can delete the file after the run.
2. **Stash files to preserve OUTSIDE `specs/`.** Move `tasks.md`, `jira-mapping.json`, and any other files you want to keep into a temp dir at the repo root (`_<NNN>-keep/`). This matters because `/speckit.specify`'s NNN scan would otherwise see the existing dir and allocate the *next* number, not reuse the slot.
3. **Delete the old spec dir.** `rm -rf specs/<NNN>-<slug>/`. (Safety alternative: rename to a non-`NNN-` prefix so the NNN scan ignores it — easier to recover from if step 4 misbehaves.)
4. **Run `/speckit.specify`** with the prompt content pasted in. With the dir gone, sequential numbering reallocates the slot.
5. **Restore the stashed files** into the new spec dir. `mv _<NNN>-keep/* specs/<NNN>-<slug>/ && rmdir _<NNN>-keep`.
6. **Iterate on the new spec** based on your reading. Re-authoring is the moment to capture decisions that had been latent — make them explicit in clarifications / key principles / new FRs while the context is fresh.
7. **`/speckit.plan` / `/speckit.tasks` regeneration is OPTIONAL** at this stage. Phases whose tasks are completed or in progress are sacred (Cardinal Rule #1) and must be preserved at the top of `tasks.md` when you regenerate. Phases of envisioned-but-not-started work MAY be discarded — an overhaul is the cheapest moment to drop work that the new spec no longer wants. Merge by hand: completed-or-in-progress at the top, new phases append at the bottom.
8. **Propagate to project-level docs** (see [§Project-Level Doc Propagation](#project-level-doc-propagation)).
9. **Sync cross-referencing sibling specs.** Any sibling spec that points at the overhauled one likely has stale FR numbers, retired-FR references, or moved-FR attributions. `grep -rn "<spec-slug>" specs/` and clean up. Pay special attention to clarifications and assumption pointers that say "moved to <spec> on <date>."

### Brand-new spec

When adding a feature with no prior history.

1. `/speckit.specify "<description>"` — creates `specs/<NNN>-<slug>/spec.md`. The `before_specify` hook handles the feature branch.
2. `/speckit.clarify` — interactive ambiguity scan if needed.
3. `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`.
4. `/speckit.jira.specstoissues <slug>` — creates Epic + Stories + active-phase Subtasks in OCS.
5. PR to default branch — review, merge, delete branch.
6. `/speckit.jira.sync-status <slug>` — flip JIRA tickets to Done.
7. **Propagate to project-level docs** (see [§Project-Level Doc Propagation](#project-level-doc-propagation)).

### Project-Level Doc Propagation

After any of the three flows above, sweep the project-level docs that catalogue or cross-reference specs. The [constitution's Documents catalogue](../.specify/memory/constitution.md#project-level-planning-documents) is authoritative on what each doc owns; the table below is the operational "which doc to touch, when":

| Doc | Update when |
|---|---|
| [`docs/roadmap.md`](roadmap.md) | **Always.** Add/remove/update the spec row in the Specs table, update the affected App's row in the Apps table, update boundary rules, add or edit the Spec Reference paragraph. |
| [`CLAUDE.md`](../CLAUDE.md) | **Always.** Keep the active-specs catalogue (between `<!-- SPECKIT START -->` and `<!-- SPECKIT END -->`) current. |
| [`README.md`](../README.md) | When the spec corresponds to a user-visible part of the project layout (front-end, backend, ingestion service, etc.). |
| [`.specify/memory/constitution.md`](../.specify/memory/constitution.md) | **Rarely.** Only when a cross-cutting principle, Cardinal Rule, or App-level assumption changes. Spec-local decisions do NOT belong here. |
| Sibling specs | When cross-references go stale (retired FRs, moved-out FRs, renamed concepts, changed attributions). |

Per Cardinal Rule #5, prefer references over duplication: a sibling spec or project-level doc should point at the changed spec rather than restate its content. Linking is cheap; staying in sync after duplication is not.

---

## Reconciliation: Claude/spec drift scan

Between Monday meetings, Claude makes small changes that don't always make it into `tasks.md`. The drift scan catches them.

Ask Claude: *"Run a spec drift scan. For each commit touching `src/`, `public/`, or `package.json`, list whether it has a corresponding line in any `tasks.md`. Flag everything that doesn't, grouped by spec."*

**Determining the scan's starting point.** Claude derives the `<last_known_good_commit>` automatically — do not pass a date by hand. The rule:

1. Grep every `specs/**/tasks.md` for phase headings matching `## Phase N: Drift Reconciliation (YYYY-MM-DD …)`.
2. Take the **most recent date** across all matches (whichever spec it appears in).
3. Use the commit that introduced that heading as the baseline. Find it with `git log -S "Phase N: Drift Reconciliation" --pretty=format:"%h" -- specs/**/tasks.md` (or the equivalent diff scan), then scan `<that-commit>..HEAD`.
4. If no Drift Reconciliation phase exists anywhere, fall back to the last commit before last Monday 00:00 local time.

This means scans are idempotent across re-runs and consecutive weeks chain without overlap — the next scan starts exactly where the last one ended, regardless of how many weeks have passed.

Claude enumerates changed files per commit, buckets them by spec, greps `tasks.md` for matches, and outputs the unmatched commits as a proposed Phase N+1 task list. Always *propose* — never append to `tasks.md` directly. The user decides whether and how to record each item (Cardinal Rule #1).

| Trigger | What runs |
|---|---|
| Per commit | Nothing automated. Use whatever interface (VS Code, CLI). |
| Per push to default | Lightweight `tasks.md` drift check via `after_implement` hook (see [§Hook customization](#hook-customization)). |
| Weekly Monday | Full drift scan. Append misses as new phases. |

Per-commit is too noisy. Per-push and weekly catch-up is the right cadence.

---

## JIRA sync

Two commands keep JIRA aligned with the spec state:

- `/speckit.jira.specstoissues <spec>` — creates an Epic for the spec and a Story for each `## Phase N: ...` in its `tasks.md`. Existing Stories are left alone; only new phases are pushed. Subtasks are *not* created by default — sync at the Story level unless there's a clear reason to break out individual tasks (e.g. active forward-sprint work that needs triage in JIRA).
- `/speckit.jira.sync-status <spec>` — reads `[ ]` / `[~]` / `[x]` task flips in `tasks.md` and transitions the corresponding JIRA issues to `To Do` / `In Progress` / `Done`.

### Sprint membership rule

Any Story flipped to **Done** must belong to a sprint — default to the currently-open sprint unless the work demonstrably happened in a different one (in which case set that sprint explicitly). This keeps velocity attribution accurate at sprint-review time.

In-progress stories are *not* automatically added to the current sprint. Add one case-by-case when partial work has shipped this sprint and the team wants velocity credit for it.

### User-created tickets — reconciliation

JIRA accumulates two kinds of issues: those produced by `/speckit.jira.specstoissues` (labeled `spec-kit`) and those created ad-hoc in the JIRA UI (typically during weekly meetings or stakeholder discussions). When the two describe the same work, the spec-kit Story is the canonical record and the user ticket gets linked to it rather than left orphaned.

Convention:
- **`Duplicate`** link when the user ticket and spec-kit Story describe the same work 1-to-1. Direction: the user ticket *duplicates* the spec-kit Story (`outwardIssue` = user ticket, `inwardIssue` = spec-kit Story).
- **`Blocks`** link when one ticket must finish before another can start (cross-ticket dependency, in either direction — spec-kit ↔ user, spec-kit ↔ spec-kit, or user ↔ user). Direction: `inwardIssue` = the blocker, `outwardIssue` = the blocked ticket (so "A is blocked by B" → `inwardIssue: B, outwardIssue: A`). Surface these at planning so blocked work doesn't get committed before its prereq.
- **`Relates`** link when the connection is tangential — a spike whose outcome shaped another story, a follow-on idea, historical context (e.g. a webfetch-blocking spike whose outcome was the instagrapi pivot).
- **Don't touch the Subtasks attached to spec-kit Stories** — those are managed by the speckit-jira agents. Linking happens at the user-ticket / Story level only.

This OCS workflow has only `To Do` / `In Progress` / `Done` — no `Blocked` status. The `Blocks` link is the canonical record of a dependency; the blocked ticket stays in `To Do` (or `In Progress` if partial work has shipped) until the blocker clears.

True close-cascade requires a Parent-Subtask relationship, which would mean converting the user ticket's issue type. That's out of scope for the weekly cadence; manually close the duplicate when the spec-kit Story closes (or leave it for next-week reconciliation).

### What never goes into the sync

Per Cardinal Rule 6, `specs/<spec>/jira-mapping.json` must not record sprint, owner, status, story points, or priority. Those PM fields live in JIRA's UI; the mapping file carries only identity (key, summary, URL, parent/child structure).

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

**Planning notes**: each Monday produces `docs/planning/YYYY-WW.md` (ISO week number). Format:

```markdown
# Sprint planning — Week of YYYY-MM-DD

**Sprint**: OCS Sprint N
**Goal**: <one sentence, matches JIRA Sprint goal>

## Goals
1. **<Name>** — <one paragraph>. Tracking: OCS-XX (Epic).
2. **<Name>** — <one paragraph>. Tracking: OCS-YY.

## Out of scope this week
- <Things explicitly deferred>

## Dependencies / blockers
- <External dependencies, decisions still needed>
```

Each goal becomes (or maps to) an OCS Epic. Spec-needing goals run through `/speckit.specify`; the Epic appears when you run `/speckit.jira.specstoissues`.

---

## Hook customization

### git extension (`auto_commit`)

`.specify/extensions/git/git-config.yml` — recommended team-wide settings (currently active in this repo):

```yaml
auto_commit:
  default: false
  after_specify:    { enabled: true,  message: "[Spec Kit] Add specification" }
  after_clarify:    { enabled: true,  message: "[Spec Kit] Apply clarifications" }
  after_plan:       { enabled: true,  message: "[Spec Kit] Add implementation plan" }
  after_tasks:      { enabled: true,  message: "[Spec Kit] Add task breakdown" }
  before_implement: { enabled: true,  message: "[Spec Kit] Save progress before implementation" }
  # after_implement intentionally disabled — implementations should be human-reviewed PRs.
```

This auto-commits the spec/clarify/plan/tasks artifacts (themselves PR-reviewable text) but keeps human-driven commits for implementation diffs.

### Custom pre-commit checks (proposed)

`git.commit` can be extended with team-specific *advisory* checks (warn, never block — hard blocks belong in CI):

1. **Spec-drift scan** — for each changed `src/` file, look for a matching `[x]` / `[~]` task. Warn if missing.
2. **Diagram freshness** — if `src/components/*.tsx` changed, suggest `/speckit.learn.review`.
3. **JIRA reference** — if commit message lacks `OCS-NNN`, prompt for one.

### When to use `git.commit` vs. VS Code's git UI

`git.commit` runs lifecycle-specific checks and ties commits to Spec Kit events (`after_specify`, etc.). VS Code's UI is fine for ad-hoc commits but doesn't know which lifecycle event it's serving. **Use VS Code for ad-hoc; let Spec Kit hooks fire `git.commit` at lifecycle moments.**

---

## learn extension: keeping diagrams fresh

Targets in `specs/00N-feature/`: `component-diagram.md`, `system-design.md`, `software-architecture.md`. They rot the moment code changes without a refresh.

**Recommended**: weekly batch. Run `/speckit.learn.review` in the Monday cadence (step 6).

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

**Weekly review (Monday cadence step 5)** — two parts, ~5 min per developer:

1. **Digest** — ask Claude: *"Give me a weekly review since last Monday — what shipped, what's active, what's blocked."* Claude composes a `git log` summary plus an Atlassian MCP query for active sprint state. Three sections expected: shipped commits mapped to phases, active sprint issues with owners, items with no movement in 7+ days.
2. **Quiz** — run `/speckit.onboard.quiz`. Generates 5 questions calibrated to your profile level (`junior` / `mid` / `senior`), grounded in real project artifacts, and persisted in `.onboard/profiles/<name>.json` so questions never repeat.

No enforcement, no scoring, no surveillance — just a structured nudge for context refresh. If a quiz reveals confusion, that's a signal to update the spec or the docs.

---

## A typical week

```
Mon 09:00  Planning meeting (30 min)
Mon 09:30  Each dev: ask Claude for weekly digest, then /speckit.onboard.quiz (5 min)
Mon 09:35  Lead: drift scan, append new phases (15 min)
Mon 09:50  /speckit.jira.specstoissues for new specs; place Stories in current sprint (10 min)
Mon 10:00  Sprint plan in JIRA UI: drag stories, assign owners, set points (20 min)
Mon 10:20  /speckit.learn.review to refresh diagrams (5 min, lead)
Mon        Goals captured in docs/planning/YYYY-WW.md and JIRA Sprint goal field.

Tue–Fri    Implementation. /speckit.implement for major work; ad-hoc Claude
           sessions for small changes. Mark [x] in tasks.md as you ship.
           /speckit.jira.sync-status as needed (or batch on Friday).

Fri 16:00  Optional pre-Monday triage. Note anything that should become a new phase.
```

---

## Common questions

**Q: I made a small change. Update `tasks.md` now?**
Wait for Monday's reconciliation pass and append a new phase covering the week's small changes as a single bundle. Architecturally meaningful changes warrant a phase now.

**Q: A change doesn't fit any existing spec.**
You probably needed a new spec. Small change → append to the closest spec. Substantial → run `/speckit.specify` after the fact and reference the merged commits as historical context.

**Q: I want to abandon a feature already pushed to JIRA.**
Transition the Epic and Stories to **"Won't Do"** (not Delete). Append `Phase N: Abandonment` to `tasks.md`. Keep the Spec Kit directory.

**Q: My VS Code git UI is faster than `git.commit` for ad-hoc commits.**
Keep using it. `git.commit`'s value is at lifecycle moments (`after_specify`, etc.), not at every save.

**Q: Push every shipped task to JIRA as a Subtask?**
No. Completed phases live at the Story level only. Per-task Subtasks exist for the active phase, where they help triage owners and points.

**Q: Story Points missing — does that block sprint planning?**
No, but velocity charts will be inaccurate. Set them during planning meeting.

---

## Maintenance

This document is itself part of the workflow it describes:

- Material changes → PR review.
- If the workflow surprises you, the doc is wrong — fix the doc, then fix the workflow.
