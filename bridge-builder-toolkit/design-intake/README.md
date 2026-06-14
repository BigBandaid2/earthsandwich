# Design-intake package — bridge-builder-toolkit UI + playground redesign

Prepared 2026-06-11 for a Claude Design session (claude.com/design). This folder is
deliberately untracked — zip/upload what you need, then delete or keep at will.

## What's here

```
brief/CONTEXT-BRIEF.md     paste-ready project context (the engineering contracts)
brief/TOKENS.md            current design tokens + component inventory, with semantics
screenshots/               current state, 1440px dark
  ui-project-list.png        Surface A: project list
  ui-create-form.png         Surface A: create form (incl. pile file selection)
  ui-dashboard.png           Surface A: dashboard (validation, stage chips, next step, danger zone)
  ui-edit-form.png           Surface A: edit form
  ui-artifact-browser.png    Surface A: artifact directory listing
  playground-pile-enhanced.png    Surface B: pile playground (provenance labels, copy-out)
  playground-target-enhanced.png  Surface B: target playground
  raw-ydata-report.png            what a RAW prior-art artifact looks like (not ours to restyle)
artifacts/                 working sample artifacts (NEUTRAL synthetic data - safe to upload)
  pile.enhanced.html         single-file playground, open in any browser
  target.enhanced.html       single-file playground
  target.er-diagram.svg      raw ER artifact (eralchemy2 + GraphViz)
  pile.ydata-profile.html    raw ydata artifact (reference only - raw artifacts stay stock)
  target.ydata-profile.html  raw ydata artifact
```

**Privacy note**: these samples were regenerated from neutral fixture data (field-station
theme). The real project's artifacts under `bridge-builder-toolkit/projects/` embed your
actual Instagram captions/locations — use them locally for fidelity checks, but the
neutral set is the upload-safe default. (The UI screenshots do reveal pile *file names*.)

## Session playbook

1. **One-time org setup**: in Claude Design, set up the design system — link the
   `earthsandwich` repo (it will read `bridge-builder-toolkit/ui/pages.py` and
   `common/playground.py`) AND upload `brief/TOKENS.md` (Design reads hex values but not
   their intent; TOKENS.md supplies the semantics).
2. **Create TWO projects** (different contracts, shared tokens):
   - *Toolkit UI* — attach: CONTEXT-BRIEF.md, the five `ui-*.png`, your new comps/moodboards.
   - *Profiling playgrounds* — attach: CONTEXT-BRIEF.md, the two `playground-*.png`,
     `artifacts/pile.enhanced.html` + `target.enhanced.html` (it can ingest the real
     single-file artifacts whole), `raw-ydata-report.png` (so it designs the enhanced
     playground to sit comfortably NEXT TO stock ydata output), your comps.
3. **First prompt — ask for variants in one shot** (Design has its own weekly usage
   budget; consolidated prompts beat dribbles):

   > Using the attached context brief, tokens, current-state screenshots, and my
   > reference comps: propose three visual directions for this surface — one evolution
   > of the current dark idiom, one minimal/editorial, one expressive — as working
   > prototypes. Honor every constraint in the brief (vanilla offline HTML/CSS/JS;
   > provenance labels and copy-out-a-prompt as first-class elements; server-rendered
   > multi-page for the UI / single-file for playgrounds). Keep the information
   > architecture; redesign the visual system.

4. **Iterate** with click-to-comment inline edits on the winner; pull in the best
   details from the runners-up.
5. **Export**: playgrounds → *standalone HTML*; UI → *Handoff to Claude Code* bundle
   (or standalone HTML if the bundle path assumes a Node target).
6. **Hand the exports to Claude Code** in the repo. Implementation lands as:
   `ui/pages.py` (`_STYLE` + renderers), `common/playground.py` (`_STYLE` + section
   markup), and the analyze-stage playground builders — then the existing test suites
   re-verify the contracts (labels, no-secret-rendered, lock states, render-time bounds).

## Redesign guardrails (for whoever implements)

- Raw prior-art artifacts (ydata reports, ER svg, dbt project) are byte-for-byte
  canonical — never restyled. The redesign scope is the UI pages + ENHANCED playgrounds.
- A pure visual redesign needs no spec change. New *interaction capabilities* (filters,
  navigation, widgets) need a small spec amendment first (FR-170–179 / FR-050–054 are
  the binding contracts).
