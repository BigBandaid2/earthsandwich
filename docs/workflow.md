# SDLC Workflow Guide

> Source of truth for how this team uses Spec Kit, JIRA (OCS), and Claude Code together. Read before your first commit. Re-read whenever the workflow surprises you.

**Status**: Living document. Edit via PR; do not silently rewrite.

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

## The two cadences: per-feature and weekly

### Per-feature (full ceremony)

Use for new product surfaces, breaking architectural changes, anything warranting stakeholder review.

1. `/speckit.specify "<description>"` — creates `specs/00N-feature/spec.md` and a feature branch.
2. `/speckit.clarify` — interactive ambiguity scan, up to 5 questions.
3. `/speckit.plan` — produces `plan.md`.
4. `/speckit.tasks` — generates `tasks.md`.
5. `/speckit.implement` — Claude executes tasks, flipping `[ ]` → `[~]` → `[x]`.
6. `/speckit.jira.specstoissues 00N-feature` — creates Epic + Stories + active-phase Subtasks in OCS.
7. PR to default branch — review, merge, delete branch.
8. `/speckit.jira.sync-status 00N-feature` — flip JIRA tickets to Done.

### Weekly (the realistic default)

Claude Code is fast enough that small changes don't need full ceremony. Catch up the bookkeeping in batch every Monday morning (~30 min):

1. **Reconcile** — drift scan against last Monday → HEAD (see [§Reconciliation](#reconciliation-claudespec-drift-scan)).
2. **Append new phases** to relevant `tasks.md` for shipped work.
3. **Push to JIRA** — new phases become new Stories in OCS, placed in the current sprint for velocity attribution.
4. **Plan the week in JIRA's UI** — drag stories into the sprint, assign owners, set story points, write the Sprint goal.
5. **Knowledge refresh** — git-log digest + `/speckit.onboard.quiz` (~5 min per dev; see [§Knowledge refresh](#knowledge-refresh-monday-quiz)).
6. **Diagrams** — `/speckit.learn.review` to refresh component diagrams.

The weekly cadence is the contract. Per-feature ceremony is the optional discipline for serious architectural work.

---

## Reconciliation: Claude/spec drift scan

Between Monday meetings, Claude makes small changes that don't always make it into `tasks.md`. The drift scan catches them.

Ask Claude: *"Run a spec drift scan from `<last_known_good_commit>` to `HEAD`. For each commit touching `src/`, `public/`, or `package.json`, list whether it has a corresponding line in any `tasks.md`. Flag everything that doesn't, grouped by spec."*

Claude enumerates changed files per commit, buckets them by spec, greps `tasks.md` for matches, and outputs the unmatched commits as a proposed Phase N+1 task list.

| Trigger | What runs |
|---|---|
| Per commit | Nothing automated. Use whatever interface (VS Code, CLI). |
| Per push to default | Lightweight `tasks.md` drift check via `after_implement` hook (see [§Hook customization](#hook-customization)). |
| Weekly Monday | Full drift scan. Append misses as new phases. |

Per-commit is too noisy. Per-push and weekly catch-up is the right cadence.

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
- Append a `## Changelog` entry for each meaningful update.
- If the workflow surprises you, the doc is wrong — fix the doc, then fix the workflow.
