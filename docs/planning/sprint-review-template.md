<!--
  Sprint planning + review template. Copy into docs/planning/YYYY-WW.md (ISO week of the sprint's
  opening Monday) and fill the <…> placeholders. One file per sprint, plan and review combined.

  Lifecycle — the same file is touched twice, a week apart:
    • PLAN-TIME — cadence step 12, after the meeting that OPENS this sprint. Fill: header, Goal
      (no marks yet), "## Sprint plan" with ⬜ items per owner. See workflow.md §Sprint goals.
    • REVIEW-TIME — cadence step 7, before the meeting that CLOSES this sprint. Add Goal marks,
      rename "## Sprint plan" → "## Sprint plan + review" and annotate each item against JIRA,
      fill the Hours table (step 6), and add Sprint takeaways. See workflow.md step 7.

  Narrative doc — humans read it, no tool syncs it (exempt from Cardinal Rule #2, so PM state is
  fine here). Keep it tight; lean toward half the length you first draft. A closed sprint is a
  record, not a worklist — do NOT keep an "open items" section; unresolved actionable items roll
  into the NEXT sprint's plan (the "Carry-overs" pointer at the bottom is the hand-off).
  Worked example: docs/planning/2026-W23.md.
-->

# Sprint planning — Week of <YYYY-MM-DD — sprint's opening Monday>

**Sprint**: OCS Sprint <N> (<YYYY-MM-DD> → <YYYY-MM-DD>)
**Goal** <!-- review marks added <YYYY-MM-DD> -->:
- <✅|🟡|🔁|⬜> <goal 1 — verbatim from the JIRA Sprint goal>
- <✅|🟡|🔁|⬜> <goal 2> *(optional one-line note when partial/superseded)*

> Legend: ✅ done · 🟡 partial · 🔁 superseded · ⬜ not started · ⚡ drift / unplanned

## Sprint plan + review
<!-- Heading is "## Sprint plan" at plan-time; rename to "+ review" when annotating. -->

> Reviewed against JIRA Sprint <N> on <YYYY-MM-DD>: **<X> of <Y> issues Done, <Z> To Do, <W> In Progress.**

### <Person>

<!-- PLAN-TIME: one ⬜ line per committed item — `⬜ **<title>** — OCS-NN. <one-line scope>.`
     REVIEW-TIME: set the icon to the issue's current JIRA status, then append the outcome —
     the key(s), Done/To Do, what actually shipped, and any supersession (🔁). Add a final
     `⚡` line per owner for unplanned work that landed this sprint. -->
1. <icon> **<item title>** — OCS-NN <status + outcome note>.
2. …
N. <icon> ⚡ **Unplanned** — <drift / unplanned work that shipped, with keys>.

### <Person>
1. …

---

## Hours (estimated)
<!-- Filled at step 6 (pre-meeting, estimated) from docs/planning/time-log.tsv. Re-titled
     "Hours (attested)" and refreshed at step 14 once Hours Attested is populated. -->

| Person | Story work | Overhead | Meetings | Total |
|---|---:|---:|---:|---:|
| <Person> | <h> | <h> | <h or —> | **<total>** |

<One paragraph: estimated-vs-attested basis, any sprint-boundary attribution caveat, and a one-line read on where the effort went.>

---

## Sprint takeaways
<!-- ~3 retrospective bullets. Observations, not a worklist. -->

- **<headline stat, e.g. "N of M issues Done">.** <which goals met / slipped>.
- **<the sprint's defining story>** — <what happened, with keys>.
- **<second notable thread + the velocity line>** Velocity est./att. **<h>**.

Carry-overs for W<next> planning: <unresolved actionable items — they land in the next sprint's plan, not here>.
