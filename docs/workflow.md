# SDLC Workflow Guide

> Source of truth for how this team uses Spec Kit, JIRA (OCS), and Claude Code together. Read this before your first commit. Re-read whenever the workflow surprises you.

**Status**: Living document. Edit via PR; do not silently rewrite.

---

## TL;DR — what each system owns

| System | Owns |
|---|---|
| **Spec Kit** (`specs/00N-feature/`) | Specifications, acceptance criteria, user stories, requirements, plans, tasks. The *what* and the *why*. |
| **Code repo** (`src/`, `public/`, etc.) | Implementation. The *how*. |
| **JIRA** (project `OCS`) | Project management state: priority, owner, sprint, story points, status, dependencies. The *who*, *when*, *in what order*. |
| **Git** (branches, PRs, history) | Reviewable change events. Audit trail. |
| **Memory / `MEMORY.md`** | Durable preferences and feedback that should persist across Claude sessions. |

If you're ever unsure which system to update, ask yourself which question your change answers and refer to the table above.

---

## Cardinal rules

1. **`tasks.md` is a historical record.** New work goes in **new phases** appended to the bottom. Never restructure or rewrite past phases. Status flips (`[ ]` ↔ `[x]` ↔ `[~]`) are fine — those *are* progress.
2. **Spec Kit drives spec content. JIRA drives schedule and assignment.** Don't put owners or sprints into `spec.md`. Don't put requirements into JIRA descriptions.
3. **One Spec Kit feature = one JIRA Epic. One Phase = one JIRA Story.** Subtasks exist in JIRA only for genuinely active phases. Completed phases get represented at the Story level only.
4. **Default branch is the source of truth for shipped work.** Anything that hasn't merged isn't shipped, regardless of how good the demo was.
5. **One-way sync: Spec Kit → JIRA, never the reverse.** PM fields (sprint, owner, priority, points) are author-time inputs in JIRA's UI. Don't try to mirror them into the repo.
6. **Synced artifacts carry identity, not state.** Files that the `spec-kit-jira` commands read or write — primarily `specs/<spec>/jira-mapping.json` — must not record sprint, owner, status, story points, or priority for any issue. They store only durable identity: key, summary, URL, the parent/child structure, and the local task id. PM state lives exclusively in JIRA. The reasoning: when a synced file mirrors a field that JIRA's UI also writes, you have two writers and one reader, and drift is guaranteed. Narrative artifacts that humans read but tools don't sync — `docs/planning/YYYY-WW.md`, this `workflow.md`, ad-hoc design notes — are exempt and may reference sprint/status/owners freely as historical record. The test: "If both this file and JIRA's UI can write this field, can they disagree?" If yes, the field doesn't belong in this file.

---

## The two cadences: per-feature and weekly

Two rhythms, not one.

### Per-feature cadence (when you're starting genuinely new scope)

This is the full Spec Kit ceremony. Follow it for any change that needs deliberate scoping — new product surfaces, breaking architectural decisions, anything that warrants stakeholder review.

1. `/speckit.specify "<concise feature description>"` — creates `specs/00N-feature/spec.md` and a feature branch.
2. `/speckit.clarify` — ambiguity scan. Resolve up to 5 questions interactively.
3. `/speckit.plan` — produces `plan.md` with the technology stack and architectural choices.
4. `/speckit.tasks` — generates `tasks.md` with phased task breakdown.
5. `/speckit.implement` — Claude executes tasks one at a time, updating `[ ]` → `[~]` → `[x]`.
6. **First sync to JIRA**: `/speckit.jira.specstoissues 00N-feature` — creates Epic + Stories + (optionally) Subtasks for active phases.
7. **PR to default branch** — review, merge, delete branch.
8. After merge: `/speckit.jira.sync-status 00N-feature` to flip JIRA tickets to Done.

### Weekly cadence (the realistic default)

Most days, Claude Code is fast enough that going through the full ceremony for every small change is friction. The weekly cadence exists to catch up the bookkeeping in batch.

**Every Monday morning (~30 minutes):**

1. **Reconcile**: run the spec-drift scan (see [§Reconciliation](#reconciliation-claudespec-drift-scan)) to find code changes that aren't reflected in `tasks.md` or `spec.md`.
2. **Append new phases** for the past week's shipped work to the relevant `tasks.md`. Never rewrite old phases — even if the original plan was wrong.
3. **Push to JIRA**: any new phase becomes a new Story in OCS, placed in the **current sprint** (so it counts toward this week's velocity, even though the work was completed earlier).
4. **Plan the week**: in JIRA's UI, drag stories into the active sprint, assign owners, set story points. Capture week-level goals in the Sprint goal field (see [§Sprint goals](#sprint-goals)).
5. **Knowledge refresh**: run `/speckit.onboard.review` (see [§Knowledge refresh](#knowledge-refresh-5-min-monday-quiz)) — 5-minute digest of what changed last week.
6. **Diagrams**: run `/speckit.learn.review` to refresh component diagrams and any other visual artifacts in `specs/`.

The weekly cadence is the contract. Per-feature ceremony is the optional discipline you reach for when you're doing serious architectural work.

---

## Reconciliation: Claude/spec drift scan

The realistic problem: between Monday meetings, you'll let Claude make many small changes without updating `spec.md` or `tasks.md`. The drift scan catches that.

### How to run it

In Claude Code, ask:

> "Run a spec drift scan against the default branch from `<last_known_good_commit>` to `HEAD`. For each commit in `src/`, `public/`, or `package.json`, list whether it has a corresponding line in any `tasks.md`. Flag everything that doesn't, grouped by spec."

I (Claude) will:
1. `git log <last>..HEAD --name-only` to enumerate changed files per commit.
2. Bucket commits by which `specs/00N-feature/` they most plausibly belong to (heuristic: file path, commit message keywords, recency).
3. For each spec, grep `tasks.md` for matching task descriptions.
4. Output a list of commits *without* a corresponding task — this becomes the proposed Phase N+1 task list.

### Frequency

| Trigger | What runs |
|---|---|
| **Per commit** | Nothing automated. You commit through whatever interface you prefer (VS Code, CLI). |
| **Per push to default** | The `after_implement` hook should run a lightweight tasks.md drift check (see [§Hook customization](#hook-customization)). |
| **Weekly Monday** | Full drift scan as above. Append any missed work as new phases. |

You probably don't want this on every commit — too noisy. Per-push to `master` and weekly catch-up is the right cadence.

---

## Git branches and PRs

### Branch model

- One branch per Spec Kit feature, named for the spec dir: `001-world-travelogue`, `002-instagram-automation`, etc. Created automatically by `/speckit.specify`.
- A long-running branch can host many phases — phases append to `tasks.md` as you go.
- The default branch is the integration point. Nothing exists "officially" until it's merged there.

### Pull requests

- One PR per merge to default. The PR description should reference the Epic and any Stories it closes (`Closes OCS-49, OCS-50`).
- Use `Draft` for in-progress feature branches that haven't reached a coherent merge candidate.
- PRs are the right place for stakeholder review of the shipped diff. They're not the right place for spec review — that happens in the spec PR earlier in the cycle.

### Abandoning a feature

Sometimes a whole feature gets imagined, prototyped, and then judged unsuitable. Goal: don't pollute `tasks.md` or JIRA with abandoned exploratory work.

**Procedure:**

1. **If the spec was never merged to default** (still on its feature branch): just delete the branch. The feature was never real. JIRA Epic and Stories should be transitioned to status **"Won't Do"** (not deleted — preserves the audit trail showing the team considered and rejected this direction). Add a one-paragraph postmortem to the Epic comments explaining the rejection.
2. **If parts of the spec did merge but the larger initiative is being abandoned**: append a final phase to `tasks.md` titled `Phase N: Abandonment — <reason>` explaining what was reverted, what was kept, and why. The corresponding JIRA Epic stays open at status "Won't Do" with the relevant Stories marked Done (for code that landed) or Won't Do (for code that didn't).
3. **Never delete past phases** even when abandoning. The historical record stays.

The rule of thumb: **abandonment is itself a phase**. Ship it as part of `tasks.md` history.

---

## Sprint goals

Capture the week's intent in two places: JIRA Sprint goal (one sentence) and the planning meeting notes.

### JIRA Sprint goal

Set in the Sprint configuration (Project → Boards → OCS → Sprint settings → Sprint goal).

Write it as a single sentence describing the *outcome* the team is committing to. Not a list, not a wishlist. Examples:

- **Good**: "Ship the scheduled Instagram pull and a draft SDLC workflow guide; explore the legacy comment-bot integration."
- **Bad**: "Do all the things from the planning meeting."

### Planning meeting notes

Each Monday's planning meeting produces a short markdown document in `docs/planning/YYYY-WW.md` (where `WW` is the ISO week number). Format:

```markdown
# Sprint planning — Week of YYYY-MM-DD

**Sprint**: OCS Sprint N
**Goal**: <one sentence, matches JIRA Sprint goal>

## Goals

1. **<Goal name>** — <one paragraph>. Tracking: OCS-XX (Epic).
2. **<Goal name>** — <one paragraph>. Tracking: OCS-YY.
3. **<Goal name>** — <one paragraph>. Tracking: OCS-ZZ.

## Out of scope this week

- <Things explicitly deferred>

## Dependencies / blockers

- <External dependencies, decisions still needed>
```

Each goal becomes (or maps to) an OCS Epic. If the goal needs spec work, that means a `/speckit.specify` invocation creating a new `specs/00N-...` directory; the Epic is created automatically when you run `/speckit.jira.specstoissues`.

For the *current* week's three goals (instagram automation, SDLC guide, JIRA bot integration), the planning doc would look like:

```markdown
# Sprint planning — Week of 2026-05-04

**Sprint**: OCS Sprint 1
**Goal**: Land the spec-kit/JIRA workflow, automate the Instagram pull, and explore the comment-bot integration.

## Goals

1. **Automate scheduled Instagram pull** — Replace the manual `posts.local.tsv` workflow with a daily/weekly pull that lands new posts as Instagram-typed stops in `src/data/earth-sandwich-2015.ts`. Tracking: new spec to be created via `/speckit.specify`.
2. **Draft SDLC workflow guide** — This document. Tracking: in `docs/workflow.md`. (Not a feature spec; a process artifact.)
3. **Explore JIRA comment-bot orchestration integration** — Investigate tying the legacy comment-bot service into this project. Outcome: feasibility doc and a go/no-go recommendation. Tracking: investigation; spec only if go.
```

---

## Hook customization

Spec Kit's extensions hook into per-command lifecycle events. We can wire team-wide checks into them.

### git extension (`auto_commit`)

The `git.commit` extension currently has every hook disabled (`enabled: false` in `.specify/extensions/git/git-config.yml`). Recommended team-wide settings:

```yaml
auto_commit:
  default: false
  after_specify:
    enabled: true
    message: "[Spec Kit] Add specification"
  after_clarify:
    enabled: true
    message: "[Spec Kit] Apply clarifications"
  after_plan:
    enabled: true
    message: "[Spec Kit] Add implementation plan"
  after_tasks:
    enabled: true
    message: "[Spec Kit] Add task breakdown"
  # Leave after_implement disabled — implementations should be human-reviewed PRs.
  before_implement:
    enabled: true
    message: "[Spec Kit] Save progress before implementation"
```

This auto-commits the spec/clarify/plan/tasks artifacts (which are themselves PR-reviewable text) but keeps human-driven commits for the implementation diffs.

### Custom checks before commit

We can extend the `git.commit` script with team-specific pre-commit checks. Proposed additions to a future `.specify/extensions/git/scripts/powershell/precheck.ps1`:

1. **Spec-drift scan** — for every changed file under `src/`, look for a corresponding `[x]` or `[~]` marker in some `tasks.md`. Warn (don't block) if missing.
2. **Diagram freshness** — if `src/components/*.tsx` changed, suggest running `/speckit.learn.review` to refresh `component-diagram.md`.
3. **JIRA reference** — if the commit message doesn't include an `OCS-NNN` token, prompt for one. Warn (don't block).

These are *advisory* checks — they print a warning but never fail the commit. Hard blocks belong in CI, not in the commit hook.

### Why use the `git.commit` agent at all (vs. VS Code's git UI)

The `git.commit` agent runs the same checks every time, formats messages consistently, and ties the commit to the Spec Kit lifecycle event (`after_specify`, etc.). VS Code's git UI is fine for raw commits, but it doesn't know which Spec Kit event it's being called from, so it can't run the lifecycle-specific checks. **Use VS Code for ad-hoc commits during a session; let the Spec Kit hooks fire `git.commit` for the lifecycle events.**

---

## learn extension: keeping diagrams fresh

The `learn` extension produces visual artifacts that explain the structure and reasoning behind the code. Targets:

- `specs/00N-feature/component-diagram.md` — component graph
- `specs/00N-feature/system-design.md` — overall architecture
- `specs/00N-feature/software-architecture.md` — class/module relationships

These rot the moment code changes without a refresh. Two patterns to keep them fresh:

### Pattern 1: weekly batch refresh (recommended)

In the Monday cadence (step 6), run `/speckit.learn.review` after the drift scan and any new-phase appends. This regenerates diagrams once per week using the latest code state.

### Pattern 2: hook into `after_implement`

If diagrams are critical and stale-by-a-week is too long, enable a `learn` hook on `after_implement` so diagrams refresh after every implementation pass:

```yaml
hooks:
  after_implement:
    - extension: learn
      command: speckit.learn.review
      enabled: true
      optional: false
```

**Trade-off**: this adds non-trivial latency to every `/speckit.implement` invocation. Use sparingly — typically only on the architecturally-sensitive specs (the first few features), then drop back to weekly.

---

## Knowledge refresh: 5-min Monday quiz

Goal: keep team-wide understanding sharp without a daily standup.

The `onboard` extension is designed for new joiners but generalizes nicely.

### Setup

Add to `.specify/extensions.yml` (note: `onboard` is already installed):

```yaml
hooks:
  before_implement:
    - extension: onboard
      command: speckit.onboard.before-implement
      enabled: true
      optional: true
      prompt: "Skim recent project changes before implementing?"
```

This is already enabled. It catches new code you'll touch before you touch it.

### Weekly quiz format

In the Monday cadence (step 5), each developer runs:

```
/speckit.onboard.review --since=last-monday
```

The output is a 5-minute digest:

1. **What shipped** — bullet list of merged PRs and the spec phases they map to.
2. **What's active** — Stories in the current sprint with owners.
3. **What's blocked** — Stories with no movement in 7+ days.
4. **Quiz** — 3 short multiple-choice questions about recent architectural choices, e.g.:
   > "Phase 10 introduced abandoned stops. Which of the following is correct?
   > (a) Abandoned stops still appear in the route polyline.
   > (b) The classification is based on UTC date.
   > (c) Stored status values include `abandoned`."
   >
   > Answer: (b). FR-028 specifies UTC; FR-030 says abandoned regions are skipped from the polyline; FR-028 also says the stored value remains `planned`.

Each developer answers via free-form text (or just reads the answer key). The point is recall, not testing — five minutes once a week is enough to keep the team mental model aligned.

This produces no enforcement, no scoring, no surveillance — just a structured nudge for context refresh. If a quiz question reveals confusion, that's a signal to update the spec or the docs.

---

## Putting it together: a typical week

```
Monday  09:00 — Planning meeting (30 min)
Monday  09:30 — Run /speckit.onboard.review --since=last-monday (5 min, each dev)
Monday  09:35 — Run drift scan; append last week's shipped work as new phases (15 min, lead)
Monday  09:50 — Run /speckit.jira.specstoissues for any new specs; place new Stories in current sprint (10 min)
Monday  10:00 — Sprint plan in JIRA UI: drag stories, assign owners, set story points (20 min)
Monday  10:20 — Run /speckit.learn.review to refresh diagrams (5 min, lead)
Monday          Goals captured in docs/planning/YYYY-WW.md and JIRA Sprint goal field.

Tue–Fri        — Implementation. Use /speckit.implement for major work; ad-hoc Claude
                 sessions for small changes. Update [x] in tasks.md as you ship.
                 Run /speckit.jira.sync-status as needed (or batch on Friday).

Friday  16:00 — Optional: pre-Monday triage. Skim what's still [ ] vs. shipped.
                 Make a note of anything that should be a "new phase" Monday.
```

The weekly cadence is the rhythm. The per-feature ceremony is the optional discipline.

---

## Common questions

**Q: I made a small change. Do I need to update `tasks.md`?**
Not immediately. Wait for Monday's reconciliation pass and append a new phase covering the week's small changes as a single bundle. If the change is architecturally meaningful, do create the phase now.

**Q: A change I shipped doesn't fit any existing spec. What do I do?**
You probably needed a new spec. If the change is small, append a phase to the *closest* spec and move on. If it's substantial enough to warrant its own JIRA Epic, run `/speckit.specify` after the fact and refer back to the merged commits as historical.

**Q: I want to abandon a feature but I've already pushed an Epic and Stories to JIRA.**
Transition the Epic and all Stories to **"Won't Do"** (not Delete). Append a final phase to `tasks.md` titled `Phase N: Abandonment — <reason>` describing what was reverted. Keep the Spec Kit directory. The historical record matters even when the work doesn't ship.

**Q: My VS Code git UI is faster than `git.commit` for ad-hoc commits.**
Keep using it. The Spec Kit `git.commit` agent's value is at lifecycle moments (after_specify, after_plan), not at every save. VS Code is fine for everything else.

**Q: Do I need to push every shipped task to JIRA as a Subtask?**
No. The convention is: completed phases are represented at the Story level only. Per-task Subtasks exist only for the active phase, where they help you triage owners and points. Going retroactive on shipped work creates noise without benefit.

**Q: Story Points missing on a Story — does that block sprint planning?**
No, you can still slot it into a sprint. But velocity charts will be inaccurate until points are set. Set them during planning meeting.

---

## Maintenance

This document is itself part of the workflow it describes. Treat it like any spec:

- Material changes → PR review.
- Append a `## Changelog` entry at the bottom for each meaningful update.
- If the workflow surprises you, the doc is wrong — fix the doc, then fix the workflow.
