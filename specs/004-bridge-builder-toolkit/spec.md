# Feature Specification: bridge-builder-toolkit

**Feature Branch**: `004-bridge-builder-toolkit`
**Created**: 2026-06-01
**Status**: Draft
**Input**: See [specify-prompt-draft.md](specify-prompt-draft.md) for the full natural-language prompt this spec is derived from.

## Clarifications

### Session 2026-06-08

- Q: How does the bridge produce AI-inferred target columns relative to the dbt artifact? → A: Hybrid — dbt expresses the deterministic mappings; a separate toolkit-side LLM step (in the orchestrator, not inside dbt) produces the AI-inferred columns; dbt's `schema.yml` marks which columns are AI-inferred but does not execute the inference.
- Q: Which target types does the initial implementation support? → A: Relational DB only (Postgres via SQLAlchemy / dbt-postgres) for v1. FR-005's schema-file and API-URL forms remain the eventual surface but are deferred; the toolkit may reject non-DB targets at project creation.
- Q: Where do the "transformed records" that US6 reviews come from, given the oracle only round-trips single rows? → A: The bridge materializes its full transformed output to a LOCAL artifact in the iteration folder (keyed by the pile's dedup id); US6 review and accept-bundle read that file. The target DB is read-only except the transient oracle round-trip — no bulk load into the target.
- Q: Does the oracle validate one pile row or a sample? → A: A small sample (3–5) of real pile rows, deterministically chosen to include constraint-stressing rows (most empty/null fields, longest values); the oracle passes only if ALL sampled rows insert+delete cleanly.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Create a new bridge project and validate connections (Priority: P1)

A repository operator opens the toolkit, names a new bridge project (e.g. "IG post scrape to Travelogue"), enters the location of the pile (a filesystem path), enters the location of the useful-target (a schema file, an API URL, or DB connection details), and supplies any credentials the target needs. The toolkit creates a project folder, verifies that the pile is reachable and readable, verifies that the target is reachable (and reports whether read access, insert access, and delete access are each present), and saves the project configuration. The operator now has a named, isolated workspace where all subsequent analysis artifacts for this bridge will live.

**Why this priority**: This is the MVP gate. Nothing downstream is testable without a project to scope it to: no analysis without a pile path, no insertion validation without target credentials, no iteration history without a project folder. Multi-bridge support — the toolkit handling multiple distinct bridge projects (IG→Travelogue first; future Substack→Travelogue, etc.) — also depends on this structure. Finally, validating connections up-front catches credential/path mistakes before the operator burns LLM time on analysis.

**Independent Test**: An operator clones the project, installs `bridge-builder-toolkit/`, runs the project-creation CLI with valid inputs for the 003 IG pile + 002 Travelogue stack, and observes (a) a new project folder created on disk, (b) a config file recording the inputs, and (c) a validation report showing both endpoints reachable. They re-run with deliberately-wrong inputs and observe clear error reporting before any project state is mutated.

**Acceptance Scenarios**:

1. **Given** the operator runs project-creation with name "IG post scrape to Travelogue", pile path `pile-app/pile/posts.ourearthsandwich.local.tsv`, and target URL `postgresql://earthsandwich:earthsandwich@localhost:5432/earthsandwich`, **When** the toolkit checks connectivity, **Then** the toolkit creates the project folder, writes a config file naming all inputs, runs a reachability check on each endpoint, and reports per-endpoint status (pile: readable yes/no, target: reachable + read access + insert access + delete access).
2. **Given** a project with the same name already exists, **When** the operator runs project-creation again, **Then** the toolkit refuses to overwrite without an explicit `--force` flag and lists the existing project's path.
3. **Given** the pile path is unreadable, **When** project-creation runs validation, **Then** no project folder is finalized (or partial state is rolled back), and the toolkit reports the specific failure.
4. **Given** the target is reachable for reads but lacks insert+delete permissions, **When** project-creation runs validation, **Then** the project IS created but the validation report records that the automatic oracle loop (User Story 4) will be skipped for this project.
5. **Given** multiple bridge projects exist on disk, **When** the operator runs `cli project list`, **Then** the toolkit prints each project's name, pile path, target endpoint, and current validation status.

---

### User Story 2 — Pile and target data-profile analysis (Priority: P2)

For a validated project, the operator runs the data-profile analysis stages: pile profiling and target profiling. For EACH side, the toolkit produces multiple artifacts side by side:

- A **raw `ydata-profiling` HTML report** (the canonical prior-art data-profiling tool's untouched output) — preserved in the project folder as a baseline that an operator already familiar with ydata-profiling can immediately read.
- When the side is a **relational database** (the target in the IG→Travelogue case; future DB-backed piles), a **raw ER diagram artifact** produced by an established schema-visualization tool (canonical references: `eralchemy`, `schemaspy`) — also preserved untouched as a baseline.
- An **enhanced toolkit-analyst playground** (single-file HTML, playground-shaped) that consumes the prior-art artifacts as input and adds an LLM-driven outsider-analyst layer on top.

The enhanced playground MUST label, per section, whether the content originated from a prior-art baseline (ydata-profiling, eralchemy/schemaspy), was extended by the LLM-analyst layer, or is entirely novel to the toolkit. The labeling is visible in the playground UI and reflected in the copy-out-a-prompt payload.

**Why this priority**: The pile and target profile analyses are the toolkit's contribution to the "outsider perspective" discipline — and the discipline only works if operators can see, transparently, what comes from prior art versus what the toolkit added on top. P2 because the profile analyses are independently valuable artifacts even before bridge synthesis happens. They are also the longest-running of the stages (LLM-heavy), so getting them right and replayable is operationally important.

**Independent Test**: After completing User Story 1, the operator invokes the analyze-pile and analyze-target CLI subcommands against the validated IG→Travelogue project, and ends up with artifacts in `iteration-1/`: `pile.ydata-profile.html`, `pile.enhanced.html`, `target.ydata-profile.html`, `target.er-diagram.svg` (since the target is relational), `target.enhanced.html`. The ydata reports look like canonical ydata output. The ER diagram looks like canonical eralchemy/schemaspy output. The enhanced playgrounds visibly label which sections are prior-art-derived vs. LLM-extended vs. toolkit-novel.

**Acceptance Scenarios**:

1. **Given** a validated project, **When** the operator invokes the pile-analysis CLI, **Then** the toolkit (a) runs `ydata-profiling` against the pile and writes its untouched HTML output to `pile.ydata-profile.html`, AND (b) if the pile is a relational DB, runs an ER-diagram tool and writes its untouched output to `pile.er-diagram.svg` (skipped for non-relational piles like the IG TSV), AND (c) produces an enhanced toolkit playground `pile.enhanced.html` that builds on the available baselines, adding ID-candidate justification, entity-classification, component-property clusters, AI-evidence detection, pipeline-metadata vs. original-source categorization, public-knowledge enrichment with citations, and a sampled inspection of linked media files.
2. **Given** a validated project with a relational target, **When** the operator invokes the target-analysis CLI, **Then** the toolkit (a) runs `ydata-profiling` against the target's introspected schema and any available snapshot data, writing the result to `target.ydata-profile.html`, AND (b) runs an ER-diagram tool against the schema and writes its untouched output to `target.er-diagram.svg`, AND (c) produces an enhanced toolkit playground `target.enhanced.html` that builds on the ydata + ER baselines, adding interpretive entity classification, candidate-table ranking with reasoning, and other LLM-extended/toolkit-novel claims.
3. **Given** the enhanced playgrounds are open, **When** the operator inspects any analysis section, **Then** each section is explicitly labeled as one of: **"ydata-profiling baseline"** / **"ER-diagram baseline"** (content extracted unchanged from the prior-art tool), **"LLM-extended"** (toolkit's LLM-analyst layer adds interpretation on top of a prior-art baseline), or **"toolkit-novel"** (no equivalent in the prior-art tools).
4. **Given** an enhanced playground is open, **When** the operator clicks "copy out a prompt", **Then** a natural-language payload describing the analysis state — including which claims are from prior-art baseline(s) vs. LLM-extended vs. toolkit-novel — lands on the clipboard and is by itself sufficient for an AI consumer to act on without seeing the playground UI.
5. **Given** an operator already familiar with `ydata-profiling`, **When** they open `pile.ydata-profile.html` first, **Then** they see canonical ydata output (no toolkit chrome, no modifications) and immediately recognize the tool.
6. **Given** an operator already familiar with `eralchemy` or `schemaspy`, **When** they open `target.er-diagram.svg`, **Then** they see canonical ER-diagram output (no toolkit chrome) and immediately recognize the tool.

---

### User Story 3 — Bridge synthesis (Priority: P3)

For a project with both pile and target profile analyses produced, the operator runs the bridge synthesis stage. As with Stage 2, the toolkit produces multiple artifacts side by side:

- A **raw `dbt` project artifact** (the canonical prior-art declarative-transformation tool's untouched output for the mapping case) — a small dbt project containing `sources.yml`, model SQL files, `schema.yml`, `dbt_project.yml`, and the generated `dbt docs` HTML site. Preserved in the project folder as a baseline an operator already familiar with dbt can immediately read and run with stock dbt tooling.
- An **enhanced toolkit-synthesis playground** (single-file HTML, playground-shaped) that consumes the dbt project artifact as input and adds the LLM-driven layer on top: side-by-side pile/target visualization, schema-matching proposals with algorithmic-style citations, interactive controls to adjust mappings and leave comments, and the "copy out a prompt" affordance for feedback capture.

The enhanced bridge playground MUST label, per section, whether the content originated from the dbt baseline, was extended by the LLM-analyst layer, or is entirely novel to the toolkit — the same discipline as Stage 2's enhanced playgrounds.

This stage produces the **initial** bridge proposal. When the target is a relational database and the project has insert+delete permissions, control automatically passes to User Story 4 (the automatic oracle-driven refinement loop) before the result is presented to the operator. Otherwise control passes directly to User Story 5 (manual operator refinement).

**Why this priority**: Bridge synthesis is the joinder where pile and target analyses become a single mapping artifact. P3 because it depends on P2 having run at least once. Same prior-art-as-artifact discipline as P2: explicit dbt baseline + clearly-labeled toolkit value-add.

**Independent Test**: After completing User Stories 1 and 2, the operator invokes the bridge-synthesis CLI for the project and observes two artifacts in `iteration-1/`: a `bridge.dbt-project/` directory containing a valid stock-dbt-runnable project (sources, models, schema, docs) and a `bridge.enhanced.html` playground showing pile and target side-by-side with proposed mappings. The dbt project files are recognizable to a dbt user; the playground labels which sections are dbt-baseline vs. LLM-extended vs. toolkit-novel. With insert+delete permissions present, the oracle loop (Story 4) fires automatically before the bridge is exposed to the operator for review. Without those permissions, the operator sees the bridge directly.

**Acceptance Scenarios**:

1. **Given** a project's pile and target enhanced playgrounds exist, **When** the operator invokes the bridge-synthesis CLI, **Then** the toolkit produces (a) `bridge.dbt-project/` — a stock-dbt-runnable project for the IG→Travelogue mapping case (sources.yml describing the pile, models/*.sql with the proposed transforms, schema.yml with column tests, plus dbt-generated docs HTML), preserved untouched as the canonical prior-art artifact, AND (b) `bridge.enhanced.html` — a self-contained playground showing pile and target side-by-side with the same recommended mappings, plus interactive controls to adjust and comment.
2. **Given** the enhanced bridge playground is open, **When** the operator inspects any section, **Then** each section is explicitly labeled as one of: **"dbt baseline"** (content equivalent to what the dbt project artifact expresses — source declarations, model SQL, column tests), **"LLM-extended"** (toolkit's LLM-analyst layer adds interpretation on top of the dbt baseline — e.g. natural-language rationale for a mapping), or **"toolkit-novel"** (no equivalent in dbt — e.g. interactive comment threads, the copy-out-a-prompt feedback payload, the pile-side schema-matcher visualization).
3. **Given** the bridge playground is open, **When** the operator adds, removes, or edits a mapping, **Then** the change is reflected in the live preview and in the prompt-output payload.
4. **Given** the bridge playground is open, **When** the operator leaves a comment on a mapping or a field, **Then** the comment is reflected in the prompt-output payload alongside the mapping it annotates.
5. **Given** the bridge playground is open, **When** the operator clicks "copy out a prompt", **Then** a natural-language payload representing the current mapping state (proposals + adjustments + comments + labeling claims) lands on the clipboard and is by itself sufficient for an AI consumer to act on without seeing the playground UI.
6. **Given** the bridge proposal layer uses a schema-matching algorithm, **When** the operator inspects the bridge playground's proposal section, **Then** the playground explicitly cites which matcher's algorithmic style it borrows from (canonical references: `Valentine` library matchers, LLM-based matchers like `Magneto` / `Jellyfish`).
7. **Given** an operator already familiar with `dbt`, **When** they open the `bridge.dbt-project/` directory, **Then** they recognize a canonical dbt project layout, can `dbt parse` / `dbt compile` it with stock dbt tooling, and can read the generated docs HTML as a normal dbt-docs site.
8. **Given** the project has insert+delete permissions on the target (per User Story 1's validation), **When** bridge synthesis completes, **Then** control automatically passes to the oracle loop (User Story 4) — the operator does NOT see the bridge for review until the oracle loop terminates (passed or 5-failed).

---

### User Story 4 — Automatic oracle-driven refinement (Priority: P4)

When a project has insert+delete permissions on a relational target, every bridge synthesis triggers an automatic acceptance check: the orchestrator transforms a small sample (3–5) of real pile rows — deterministically chosen to include constraint-stressing rows — per the current mapping, attempts to insert each into the target, and (on success) deletes them; the check passes only if all sampled rows round-trip cleanly. The outcome drives an automatic feedback loop — on failure, the toolkit synthesizes a feedback prompt from the database error and the broken record(s), re-runs bridge synthesis with that prompt, and tries the oracle again. The loop iterates until the oracle passes or 5 consecutive failures, at which point control hands off to the operator (User Story 5).

Critically, this is an **automatic** loop: the operator does NOT see intermediate failed iterations during the loop's execution. They see the final state — either an oracle-validated bridge or a halt banner naming the persistent failure — when control returns.

**Why this priority**: Round-trip insertion validation as an automatic acceptance oracle is the toolkit's most defensible novelty over existing schema-mapping tools. Running the oracle BEFORE presenting the bridge to the operator means the operator's manual refinement effort (User Story 5) is spent only on bridges that already work mechanically — they can focus on semantic correctness rather than schema-level wiring. P4 because it depends on P3 producing a proposal, and on P1's validation having detected the relevant permissions.

**Independent Test**: Operator's project uses the 002 Travelogue Docker stack as the target (full read/write/delete). Operator runs bridge synthesis (User Story 3) with a deliberately-broken proposal scaffolding. The oracle loop fires automatically, produces a series of automatic iterations in the iteration-history directory, and either converges to an oracle pass or halts at iteration-5-failed. The operator never has to manually intervene during the loop. After the loop terminates, the operator can inspect each intermediate iteration in the history.

**Acceptance Scenarios**:

1. **Given** bridge synthesis completes for a project with insert+delete permissions, **When** the orchestrator runs the oracle check, **Then** it selects a small sample (3–5) of real pile rows (including constraint-stressing rows), transforms each per the mapping, inserts them into the target, deletes them on success — passing only if all sampled rows round-trip cleanly — and records the outcome (success, schema-violation failure, or transient failure) in the iteration's metadata.
2. **Given** an oracle check fails because the mapping produced an invalid record, **When** the orchestrator processes the failure, **Then** it automatically synthesizes a feedback prompt incorporating the database error message and the transformed dummy record, feeds that prompt into a new bridge synthesis run, increments the iteration counter, and re-runs the oracle check — all without operator intervention.
3. **Given** the automatic loop is iterating, **When** the operator inspects the project folder, **Then** each automatic iteration is persisted in the iteration history (raw dbt + enhanced playground + oracle result + synthesized feedback) — operators can review the full trail after the loop terminates.
4. **Given** the oracle passes on automatic iteration N, **When** the orchestrator records the success, **Then** the loop exits, the iteration is marked "oracle-validated", and control passes to the operator (User Story 5) with the validated bridge presented for review.
5. **Given** 5 consecutive automatic iterations have failed the oracle, **When** the 5th failure is recorded, **Then** the loop halts and surfaces an operator-intervention banner naming the persistent failure mode (e.g., recurring NOT-NULL violation on column X). The 5-fail counter MUST track ONLY consecutive automatic iterations; a successful oracle pass or a subsequent manual user iteration (User Story 5) resets it.
6. **Given** the 5-fail halt has fired, **When** the operator fixes the underlying problem and resumes, **Then** the loop picks up from the next iteration number, NOT from iteration 1 — the prior automatic iterations remain in the history for reference.
7. **Given** the project does not have insert+delete permissions, **When** bridge synthesis completes, **Then** the oracle loop is skipped entirely, the iteration's metadata records this fact with the reason from User Story 1's validation report, and control passes directly to the operator (User Story 5) without an "oracle-validated" mark.

---

### User Story 5 — Manual iterative refinement with feedback capture (Priority: P5)

After bridge synthesis (and the automatic oracle loop, if applicable) terminates, the operator inspects the current bridge in the enhanced playground. They want to revise — the mapping placed `caption` against the wrong target column despite passing the oracle, missed a region mapping entirely, etc. They use the bridge playground's controls to adjust mappings and leave comments, copy out the resulting prompt, and feed it back into the toolkit's iterate command to produce a new iteration. The new iteration re-runs bridge synthesis (and re-enters the oracle loop if applicable) with the operator's feedback incorporated. Multiple manual iterations are persisted side by side in the project; the operator can compare iteration N against iteration N-1 by opening the side-by-side reports.

**Why this priority**: A single oracle-passed bridge is rarely semantically correct. The oracle catches schema-level wiring problems (type mismatches, NOT-NULLs, foreign-key violations) but cannot detect semantic mis-mappings (right type, wrong column). Manual refinement is what gets the bridge to semantic correctness, and it depends on the oracle loop having already eliminated the mechanical errors. P5 because the toolkit is still mechanically useful at P4 (it produces an oracle-validated bridge), but full value requires the operator's semantic judgement.

**Independent Test**: After completing User Story 4 (or User Story 3 directly if no oracle permissions), the operator opens the bridge playground, adjusts a mapping, leaves a comment, copies the prompt, runs the iterate CLI with the prompt payload as input, and observes that a new iteration is created. If the project has oracle permissions, the new iteration automatically re-enters the oracle loop before becoming visible. The operator can inspect prior iterations indefinitely; both remain readable.

**Acceptance Scenarios**:

1. **Given** a project has a current bridge (oracle-validated or non-oracle), **When** the operator opens the bridge playground, adjusts mappings, leaves comments, copies the prompt, and runs the iterate CLI with the prompt as input, **Then** a new iteration is produced inside the project folder with a new bridge playground (and new raw dbt project artifact) that incorporate the feedback into the mapping proposal.
2. **Given** the project has insert+delete permissions, **When** a manual iteration is produced, **Then** it automatically re-enters the oracle loop (User Story 4) before being presented to the operator for the next round of manual refinement.
3. **Given** feedback in a manual iteration surfaces a property the pile- or target-analysis report didn't cover, **When** the iteration runs, **Then** the upstream profile analyses for that iteration are re-run and extended to cover the new property (both raw prior-art baselines and enhanced playground refreshed if needed).
4. **Given** any iteration (automatic or manual) has completed, **When** the operator inspects the project folder, **Then** every iteration's artifacts plus the feedback payload that drove the next iteration are present and readable.
5. **Given** an iteration is mid-flight, **When** the orchestrator process is killed, **Then** the project's iteration-history directory remains in a consistent state and the next invocation can start a fresh iteration cleanly.
6. **Given** the operator decides the current bridge is final, **When** they invoke the toolkit's accept-bundle command, **Then** a final-bundle directory is materialized inside the project — suitable as input to `/speckit.specify` for authoring the downstream bridge spec.

---

### User Story 6 — Truth-baseline review of bridge output (Priority: P6)

After one or more iterations have produced transformed records, the operator wants to evaluate output quality — particularly the AI-inferred columns whose value depends on the model's judgment rather than a deterministic rule. They open a review playground that joins each bridge output row against a hand-curated **truth baseline** for the same record (via a stable identifier like `shortcode`), focuses visually on the AI-inferred columns, and walks them pair by pair. For each pair they tag a verdict: `exact-match` / `bridge-improved` / `bridge-regressed` / `truly-different`. Pairs tagged `bridge-improved` immediately update the truth-baseline file (with the prior value preserved in a timestamped edit history); other tags are recorded in the session summary without touching the baseline. The summary lists per-bucket counts, per-pair verdicts, and which AI-inferred columns drove the disagreements — and can be fed back as a payload to the `iterate` CLI (User Story 5) to drive a fresh bridge iteration informed by the inference-quality observations.

The baseline is **deliberately editable**, not frozen, for two reasons: (a) the baseline itself may be stale or wrong, and discovering this through review is part of how the baseline matures; (b) different AI-inference iterations of the same bridge produce different outputs against the same baseline — the baseline must record *what the operator currently believes is correct*, learning over time. Three-way mode lets the operator compare two bridge iterations against the same baseline simultaneously, scoped to AI-inferred columns, to see which iteration's inference improved.

**Why this priority**: The auto oracle (Story 4) catches schema-level wiring problems; manual refinement (Story 5) catches semantic mapping errors at the proposal level. Neither catches the case where a mapping is correctly wired and the proposal is semantically sound but the AI inference inside the bridge produced the wrong value. Truth-baseline review is the operator's tool for measuring AI-inference quality across iterations and converging it toward correctness. P6 because it depends on the bridge having produced output (Stories 3–5) — it's a post-hoc quality control overlay, not part of the build-the-bridge sequence.

**Independent Test**: Operator has run the bridge for the IG→Travelogue project at least once and has transformed records in the target. They invoke the review CLI with a truth-baseline path (e.g. a TSV of hand-curated locations keyed by `shortcode`) and the join key. The toolkit opens a review playground with paired rows, AI-inferred columns visually emphasized; the operator works through pairs tagging verdicts and confirming baseline edits. On session save: (a) `bridge-improved` tags overwrite the corresponding baseline values, with prior-value + timestamp + rationale captured in a sidecar edit history; (b) a session summary report is persisted in the iteration folder; (c) the summary can be passed as a payload to the `iterate` CLI to drive a new iteration.

**Acceptance Scenarios**:

1. **Given** a bridge has produced N output records and a truth-baseline file exists for the same domain, **When** the operator invokes the review CLI with the truth-baseline path and a stable join key, **Then** the toolkit produces a review playground showing paired rows joined on that key, surfaces unmatched-on-either-side cases as separate buckets (`only-truth` / `only-bridge`), and visually emphasizes the AI-inferred columns of the target schema.
2. **Given** the operator is inspecting a pair in the playground, **When** they tag it `bridge-improved`, **Then** the toolkit captures the edit; on session save the truth-baseline file on disk is updated to the bridge's value, with the prior value, the editor identity, a timestamp, and the (optional) operator rationale preserved in a baseline edit-history sidecar.
3. **Given** the operator tags a pair `bridge-regressed` or `truly-different`, **When** they save the session, **Then** the verdict is recorded in the session summary, the pair is included in the follow-up list, and the baseline is NOT modified.
4. **Given** the operator tags a pair `exact-match`, **When** they save the session, **Then** the verdict is recorded in the per-bucket count; the baseline is not modified.
5. **Given** any review session has completed, **When** the operator inspects the iteration folder, **Then** the session summary (per-bucket counts, per-pair verdicts, baseline edits made, AI-inferred-column focus list, session timestamp) is persisted alongside the iteration's other artifacts.
6. **Given** a review session summary exists, **When** the operator decides to act on it, **Then** they can pass the summary as a feedback payload to the `iterate` CLI (User Story 5) to drive a new bridge iteration informed by the inference-quality observations.
7. **Given** the bridge mapping designates certain target columns as AI-inferred and others as direct copies or deterministic transforms, **When** the review playground renders, **Then** AI-inferred columns are visually distinguished (texture or border emphasis) and the operator can filter the pair list to "AI-inferred only" / "direct-copy only" / "all."
8. **Given** the operator wants to compare two different bridge iterations against the same truth baseline, **When** they invoke the review CLI naming both iterations, **Then** the playground shows a three-way comparison (truth + iteration N + iteration M) scoped to AI-inferred columns, with per-iteration verdict columns so the operator can capture independent judgments per iteration.

---

### Edge Cases

- **Empty or malformed pile**: The toolkit must produce a meaningful Stage 1 report even with zero rows or some malformed rows. ydata-profiling has its own degraded-mode output for these; the enhanced playground must surface them readably rather than crash.
- **No plausible mapping candidates**: Stage 2's candidate-table reasoning may conclude no target tables can be populated from the pile. Stage 3 must handle "zero proposed mappings" gracefully. The dbt project artifact for this case still exists but contains zero models; the oracle loop has nothing to validate and is skipped with a "no mappings" reason recorded.
- **Empty truth baseline at first review**: A brand-new domain may have no truth baseline yet. The toolkit MUST allow bootstrapping: the first review session starts with an empty baseline, every pair is treated as `only-bridge`, and the operator's `bridge-improved` tags become the seed entries of the baseline. Subsequent sessions compare against the growing baseline normally.
- **Join key absent from one side**: If the supplied join key is missing from the bridge output schema or the truth-baseline schema, the review CLI MUST refuse to run with a clear error naming the missing side.
- **Bridge produces surrogate keys not present in the baseline**: The operator can supply a deterministic key-translation function or a join-key lookup table; the toolkit applies it before pairing.
- **Insertion validation succeeds for the wrong reason**: A mapping that inserts NULLs into nullable columns may "succeed" without being semantically correct. The oracle is necessary but not sufficient; that's why User Story 5 exists.
- **Playground embedded-data limits**: If the pile is large enough that a fair sample plus per-column statistics push the playground HTML past ~5 MB, the orchestrator must sample more aggressively or summarize further. The raw ydata/ER/dbt artifacts are unaffected — they're separate files with their own size profiles.
- **Non-relational pile**: ER-diagram generation is skipped on the pile side; the pile-analysis playground gets only the ydata baseline as prior art. The enhanced playground's per-section labels MUST still distinguish "ydata baseline" vs. "LLM-extended" vs. "toolkit-novel"; "ER-diagram baseline" is absent rather than fabricated.
- **dbt unable to model the case cleanly**: dbt was designed for warehouse-to-warehouse transformations, not raw-TSV-to-Postgres. The toolkit MUST still produce a meaningful dbt project artifact and surface the limitation in the enhanced playground's "dbt baseline" labeling.
- **Oracle loop hits a transient (non-mapping) failure**: A network outage or temporary target unavailability is NOT a mapping problem. The orchestrator MUST distinguish transient-failure from schema-violation-failure when classifying oracle results; transient failures retry with backoff before counting toward the 5-fail ceiling.
- **Operator-intervention exit from oracle loop (5-fail ceiling)**: Reversible — the operator fixes the problem and resumes the loop rather than starting from iteration 1. The 5-fail counter resets on the next successful oracle pass OR on the next manual user iteration.
- **Concurrent toolkit runs against the same project**: The orchestrator locks the project directory for the duration of a run.
- **Browser without clipboard API**: The "copy out a prompt" button must degrade to a selectable textarea so the prompt is always extractable.
- **Prior-art tool unavailable or errors** (ydata-profiling, eralchemy/schemaspy, dbt): If a pinned prior-art tool fails to run, the toolkit MUST surface that as a hard error and refuse to produce a "fake" enhanced playground for the affected stage.
- **Credentials change between runs**: If the target's credentials change between iterations, the next iteration's validation/oracle step must detect this and surface it.

## Requirements *(mandatory)*

### Functional Requirements

**Self-contained application**

- **FR-001**: Toolkit MUST be a physically self-contained App at the repository root in `bridge-builder-toolkit/`, with its own venv, `.env`, `pyproject.toml`/`requirements.txt`, CLI entry point, tests, run logs, and a top-level projects directory.
- **FR-002**: Toolkit MUST share no source code with `pile-app`, `backend`, or `frontend`. The only coupling to other Apps is via operator-supplied paths/URLs at invocation time.
- **FR-003**: Toolkit MUST be movable to a separate Git repository without breaking either side.
- **FR-004**: Toolkit MUST expose a CLI surface mirrored on the pile-app pattern: one subcommand per stage / orchestration step (e.g. `project create`, `project list`, `analyze pile`, `analyze target`, `synthesize bridge`, `iterate`, `accept-bundle`).

**Project lifecycle (User Story 1)**

- **FR-005**: Toolkit MUST support creating a named bridge project via the CLI. Project creation accepts: a project name, a pile path, a target endpoint (schema file path OR API URL OR database connection string), and target credentials (or a reference to where credentials live, e.g., env var name). **v1 scope**: the initial implementation MUST support a **relational database** target (Postgres via SQLAlchemy / `dbt-postgres`) only; the schema-file and API-URL forms are the eventual surface but are deferred. The toolkit MAY reject a non-DB target at project creation with a "deferred to a future version" message. Everything downstream (ER diagram, dbt artifact, the FR-070 oracle round-trip, SQLAlchemy reflection) assumes the relational-DB target in v1.
- **FR-006**: Project creation MUST persist the project's configuration to a per-project config file (e.g. `bridge-builder-toolkit/projects/<name>/project.yml`) so subsequent CLI invocations can act on the project by name.
- **FR-007**: Project creation MUST run a **connection-validation step** before the project folder is finalized: the toolkit attempts to read the pile, reach the target, and probe target permissions (read access, insert access, delete access). Each probe's result MUST be recorded in the project's config or validation report.
- **FR-008**: If any required check fails (pile unreadable, target unreachable), project creation MUST abort cleanly — no partially-created folder, clear error reporting.
- **FR-009**: Toolkit MUST support multiple concurrent bridge projects in the same installation; each project has an isolated folder.
- **FR-010**: Toolkit MUST support listing all projects with their current validation status.
- **FR-011**: Toolkit MUST refuse to overwrite an existing project's config without an explicit `--force` flag.
- **FR-012**: Credentials in the project config MUST be referenced indirectly (e.g., env var names) rather than embedded as plaintext.

**Pile and target profile analysis (User Story 2)**

- **FR-020**: For each profile-analysis side (pile, target), the toolkit MUST produce three artifact kinds per iteration: a raw `ydata-profiling` HTML report, a raw ER-diagram artifact when the side is a relational database (using `eralchemy`, `schemaspy`, or equivalent), and an enhanced toolkit playground that consumes the available baselines and adds the LLM-analyst layer.
- **FR-021**: The raw prior-art artifacts (ydata report, ER diagram) MUST be the official tools' output with no toolkit modifications.
- **FR-022**: The enhanced playground MUST label every analysis section as one of: **"ydata-profiling baseline"**, **"ER-diagram baseline"**, **"LLM-extended"**, or **"toolkit-novel"**. The labels are visible in the playground UI and reflected in the copy-out-a-prompt payload.
- **FR-023**: The pile-analysis stage MUST assume zero foreknowledge of how the pile was created and MUST derive its claims only from the pile's surface artifacts.
- **FR-024**: The pile-analysis enhanced playground MUST cover at minimum (in addition to what the prior-art baselines contribute): ID-candidate columns with justification; entity-classification claim; component-property clusters; pipeline-metadata vs. original-source field categorization; likely-derived/inferred fields with reasoning; AI-workflow evidence per-field; categorical-slicing candidates beyond the ydata baseline; public-knowledge enrichment with citations; sampled inspection of linked/joined objects.
- **FR-025**: The target-analysis stage MUST assume zero foreknowledge of the target's internal logic and MUST derive its claims only from the introspected schema and any provided data.
- **FR-026**: The target-analysis enhanced playground MUST cover at minimum (in addition to what the prior-art baselines contribute): a ranked list of target tables that are candidates to be populated from the pile, with reasoning per candidate. Schema visualization for relational targets is delivered via the raw ER-diagram artifact (FR-020); the enhanced playground may reference and annotate that artifact but MUST NOT re-implement relationship-graph rendering.
- **FR-027**: When the pile or target side is NOT a relational database, the ER-diagram artifact MUST be skipped (not fabricated). The enhanced playground's per-section labels MUST reflect the absence.
- **FR-028**: The pile-analysis enhanced playground MUST work with a sampled or summarized representation of the pile rather than the entire contents, to respect playground embedded-data limits.
- **FR-029**: The choice of which pile and which subset of that pile MUST be a project-config input — not a hard-coded toolkit assumption.

**Bridge synthesis (User Story 3)**

- **FR-040**: For the bridge synthesis stage, the toolkit MUST produce TWO artifact kinds per iteration: a raw `dbt` project artifact and an enhanced toolkit playground that consumes the dbt project and adds the LLM-analyst layer.
- **FR-041**: The raw dbt project artifact MUST be a valid stock-dbt-runnable project: a `bridge.dbt-project/` directory containing at minimum `sources.yml`, model SQL files (`models/*.sql`), `schema.yml` with column tests, a `dbt_project.yml`, and a `target/` subdirectory with the generated `dbt docs` HTML site. An operator with stock dbt installed MUST be able to `dbt parse` / `dbt compile` / `dbt docs serve` it without modification.
- **FR-042**: The enhanced bridge playground MUST be a self-contained playground showing pile and target side-by-side with recommended mappings, plus interactive controls to adjust mappings (add/remove/edit) and leave comments on any mapping, on either side's fields, or on the bridge as a whole.
- **FR-043**: The enhanced bridge playground MUST export captured edits and comments as a prompt-friendly artifact via a "copy out a prompt" affordance.
- **FR-044**: The enhanced bridge playground MUST label every section as one of: **"dbt baseline"**, **"LLM-extended"**, or **"toolkit-novel"**. The labels are visible in the playground UI and reflected in the copy-out-a-prompt payload.
- **FR-045**: The enhanced bridge playground MUST cite which schema-matching algorithmic style its mapping proposals borrow from (canonical references: `Valentine` library matchers, LLM-based matchers like `Magneto` / `Jellyfish`).
- **FR-046**: When the project has insert+delete permissions on the target (per FR-007's recorded status), bridge synthesis MUST automatically pass control to the oracle loop (FR-070) before exposing the bridge to the operator. When permissions are absent, control passes directly to the manual refinement path (User Story 5).
- **FR-047**: The bridge transform is a **hybrid**: deterministic field/table mappings are expressed in the dbt project artifact (FR-041), while AI-inferred target columns are produced by a separate toolkit-side LLM inference step that runs in the orchestrator (NOT inside dbt). The dbt project's `schema.yml` MUST mark which columns are AI-inferred (the designation FR-153 reads), but the dbt SQL itself MUST NOT execute the inference. Re-running the bridge MAY therefore yield different AI-inferred values across iterations even with an unchanged deterministic dbt artifact — this is the basis for the inference-quality review in User Story 6.
- **FR-048**: Bridge synthesis MUST **materialize the full transformed output** of the current mapping (deterministic dbt mappings + the FR-047 toolkit-side inference) over the pile to a **local artifact** in the iteration folder (e.g. `bridge.output.tsv`/`.json`, keyed by the pile's dedup id). This local output is what the User Story 6 review (FR-151) and `accept-bundle` (FR-090) read. The target database MUST remain read-only except for the transient single-row oracle round-trip (FR-070); the bridge MUST NOT bulk-load its full output into the target.

**Playground contract (binding on Stages 1–3 enhanced playgrounds)**

- **FR-050**: Each enhanced playground MUST be a self-contained playground — single HTML file, vanilla HTML/CSS/JS, no external dependencies, no remote assets, all data embedded inline.
- **FR-051**: The pile, target, and bridge enhanced playgrounds MUST be three separate files, not a multi-page experience. The raw prior-art artifacts are additional separate files/directories, not embedded in the enhanced playgrounds.
- **FR-052**: Each enhanced playground MUST expose a "copy out a prompt" affordance that synthesizes a natural-language payload from the playground's state.
- **FR-053**: The "copy out a prompt" payload MUST be actionable standalone — readable by an AI consumer that has not seen the playground UI.
- **FR-054**: Playgrounds MUST gracefully degrade clipboard access (fall back to a selectable textarea).

**Automatic oracle-driven refinement loop (User Story 4)**

- **FR-070**: When the project's recorded validation status indicates both insert and delete permissions on the target, the toolkit MUST automatically run an oracle check after each bridge synthesis (FR-046): transform a small sample (3–5) of real pile rows per the current mapping — deterministically chosen to include constraint-stressing rows (most empty/null fields, longest values) — attempt to insert each into the target, delete each on success, and record the outcome (success, schema-violation failure, or transient failure) in the iteration's metadata. The oracle check PASSES only if ALL sampled rows round-trip cleanly; any sampled row's schema-violation failure fails the check.
- **FR-071**: When the oracle check fails with a schema-violation failure (mapping is the problem), the toolkit MUST automatically synthesize a feedback prompt incorporating the database error message and the transformed dummy record, feed that prompt into a new bridge synthesis run, increment the iteration counter, and re-run the oracle — without operator intervention.
- **FR-072**: When the oracle check fails with a transient failure (network outage, target temporarily unavailable), the orchestrator MUST retry with backoff before classifying the iteration as a "consecutive failure" against the 5-fail ceiling.
- **FR-073**: After 5 consecutive automatic schema-violation failures, the loop MUST halt and surface an operator-intervention banner naming the persistent failure mode. The 5-fail counter MUST track ONLY consecutive automatic oracle failures; a successful oracle pass OR a subsequent manual user iteration MUST reset it.
- **FR-074**: When the oracle passes on automatic iteration N, the iteration MUST be marked "oracle-validated" in its metadata and control MUST pass to the operator (User Story 5) for manual review.
- **FR-075**: When the project lacks insert+delete permissions, the oracle loop MUST be skipped, the iteration's metadata MUST record this fact with the reason from FR-007's recorded status, and control MUST pass directly to manual refinement (User Story 5).
- **FR-076**: Every automatic iteration MUST be persisted in the iteration history (raw dbt + enhanced playground + oracle result + synthesized feedback) — operators can review the full automatic trail after the loop terminates.
- **FR-077**: Oracle execution MUST run in the orchestrator process, NOT inside any playground. The oracle's result MUST be embedded as displayed data in the next iteration's bridge playground when control returns to the operator.
- **FR-078**: The 5-fail halt MUST be reversible: after the operator fixes the underlying problem, resuming the loop MUST pick up at the next available iteration number, NOT iteration 1.

**Manual iterative refinement (User Story 5)**

- **FR-080**: The operator MUST be able to take the bridge playground's prompt output, run an `iterate` CLI command with that payload as input, and produce a new iteration that incorporates the feedback.
- **FR-081**: A manual iteration MUST re-run bridge synthesis (producing fresh dbt project and enhanced playground); MAY re-run pile and target profile analyses if the feedback surfaces a property a prior iteration didn't cover; and MUST re-enter the oracle loop (FR-046) if the project has insert+delete permissions.
- **FR-082**: Every manual iteration MUST be persisted on disk inside the project folder alongside automatic iterations. The on-disk layout MUST allow an operator to inspect any prior iteration without re-running the toolkit.
- **FR-083**: The operator MUST be able to mark the current bridge as final via an `accept-bundle` CLI command, which materializes a final-bundle directory inside the project — suitable as input to `/speckit.specify` for authoring the downstream bridge spec.

**Truth-baseline review (User Story 6)**

- **FR-150**: Toolkit MUST provide a `review` CLI subcommand accepting: one or more iteration identifiers, a truth-baseline file path, a join-key column name, and (optionally) an explicit list of AI-inferred columns when the bridge mapping does not already mark them.
- **FR-151**: The review playground MUST present pairs joined on the supplied key, partitioned into buckets: `shared` (present on both sides), `only-truth` (in baseline, not in bridge output), `only-bridge` (in bridge output, not in baseline).
- **FR-152**: For shared pairs, the review playground MUST default-focus on the AI-inferred columns (per FR-153) and visually distinguish them from direct-copy / deterministic-transform columns (texture, shading, or border accent).
- **FR-153**: The bridge mapping (the dbt project's `schema.yml` column metadata or an equivalent toolkit-side metadata layer) MUST mark which target columns are AI-inferred. The review playground reads this designation and renders the inferred-column emphasis automatically.
- **FR-154**: The playground MUST let the operator tag each pair with one of: `exact-match`, `bridge-improved` (truth should be updated to the bridge's value), `bridge-regressed` (truth is right, bridge is wrong), `truly-different` (independent semantic disagreement — flag for follow-up research). Tags are operator-driven and per-pair.
- **FR-155**: When the operator tags a pair `bridge-improved` and saves the session, the toolkit MUST write the bridge value back to the on-disk truth-baseline file AND append an entry to a baseline edit-history sidecar capturing: prior value, new value, session id, timestamp, optional operator rationale.
- **FR-156**: When the operator tags a pair `bridge-regressed`, `truly-different`, or `exact-match`, the truth-baseline file MUST NOT be modified.
- **FR-157**: The truth-baseline file MUST be a human-readable text format (TSV, CSV, or JSON) so it can be hand-edited outside the toolkit. The baseline edit-history sidecar MUST live alongside the baseline file and MUST itself be human-readable.
- **FR-158**: The review playground MUST support a three-way comparison mode showing one truth baseline against two (or more) bridge iterations side-by-side, scoped to the AI-inferred columns. The operator MUST be able to capture independent per-iteration verdicts in the three-way mode.
- **FR-159**: Each review session MUST produce a persisted session summary inside the iteration folder containing: per-bucket counts (`exact-match` / `bridge-improved` / `bridge-regressed` / `truly-different` / `only-truth` / `only-bridge`), per-pair verdicts, baseline edits captured, AI-inferred-column focus list, and session timestamp.
- **FR-160**: A review-session summary MUST be acceptable as a feedback payload to the `iterate` CLI (FR-080), so the operator can drive a fresh bridge iteration informed by the review's findings.
- **FR-161**: A brand-new domain MUST be allowed to start with an empty truth baseline. The first review session bootstraps the baseline: every pair appears as `only-bridge`; `bridge-improved` tags become the baseline's seed entries.

**Outputs**

- **FR-090**: The final accepted bundle MUST be a directory of files inside the project — all iteration artifacts (raw ydata + raw ER + raw dbt + enhanced playgrounds), the final mappings, sample-record validation results, full iteration history (automatic and manual), and captured prompt payloads — suitable for direct use as input to `/speckit.specify` (or equivalent spec-authoring step).
- **FR-091**: The toolkit's first concrete execution MUST run as a project named for the IG→Travelogue case, against the 003 IG pile + 002 Travelogue schema, and MUST produce a bundle usable as input for the bridge-app spec without further hand-editing of the bundle's structure.
- **FR-092**: For the IG→Travelogue first-run case (per FR-091), the Final Bundle MUST include the following two items, verbatim, so the bridge-app spec the bundle seeds carries them forward where they can finally be tested by the consuming App:
  - `003 US3 AS#1` — "bridge-app reads pile via file-level conventions, no service-internal names"
  - `003 US3 AS#2` — "swapping a pipeline-service implementation is invisible to bridge-app (same pile output contract)"

  This is an editorial inclusion specific to the 003→bridge-app handoff — captured here on 2026-06-03 during the Phase 22 DoD peer-review of OCS-99 — NOT a systemic mechanism for cross-spec inheritance. Pile-app exposes only the pile to other Apps; spec 004 simply remembers these two bridge-app-side constraints from spec 003 so the toolkit doesn't drop them when producing the bundle. Future bridge cases would establish their own such items independently if relevant.

**Standing on existing shoulders**

- **FR-100**: Stage 2 MUST use `ydata-profiling` as the canonical data-profiling prior art (per FR-020) and MUST preserve its raw output as a project artifact (per FR-021).
- **FR-101**: Stage 2 MUST use an established ER-diagram tool (canonical references: `eralchemy`, `schemaspy`) as the canonical schema-visualization prior art for relational sides (per FR-020) and MUST preserve its raw output as a project artifact.
- **FR-102**: Stage 3 MUST use `dbt` as the canonical declarative-transformation prior art (per FR-040) and MUST preserve a stock-runnable dbt project as an artifact (per FR-041).
- **FR-103**: Stage 3 mapping-proposal layer MUST explicitly cite which schema-matching algorithm or research direction it borrows from for its initial proposals (per FR-045).
- **FR-104**: All enhanced playgrounds MUST surface prior-art-vs.-toolkit distinctions via the per-section labeling discipline (FR-022 for Stage 2 playgrounds, FR-044 for the bridge playground).
- **FR-105**: If any pinned prior-art tool (`ydata-profiling`, the ER tool, `dbt`) fails to run, the toolkit MUST refuse to produce a "synthesized" enhanced playground for the affected stage and instead surface the prior-art failure as a hard error.

**Concurrency and crash safety**

- **FR-110**: The toolkit MUST lock a project's folder for the duration of an in-progress run so concurrent runs against the same project cannot corrupt state. If a process is killed mid-run, the lock MUST be safely reclaimable on the next invocation.

### Key Entities

- **Bridge Project**: A named workspace for one bridge effort (e.g. "IG post scrape to Travelogue"). Owns: a config file recording pile location, target endpoint, credential references, and creation-time validation status; an iteration-history directory; a final-bundle directory after acceptance. Multiple bridge projects coexist isolatedly in `bridge-builder-toolkit/projects/`.
- **Pile**: Operator-supplied input source referenced from a project's config. Filesystem-accessible at run time.
- **Target Model**: Operator-supplied input destination referenced from a project's config. May be a schema file, snapshot, API surface, or direct DB access. Treated as read-only.
- **Connection Validation Result**: The recorded outcome of probing a project's endpoints at creation time. Per-endpoint: reachable/readable yes-no, plus for the target: insert/delete access yes-no. Drives whether the oracle loop runs (FR-070) or is skipped (FR-075).
- **ydata-Profile Artifact**: A raw, untouched `ydata-profiling` HTML report produced per side per iteration. Canonical Stage-2 data-profiling baseline.
- **ER-Diagram Artifact**: A raw, untouched ER-diagram produced per side per iteration WHEN the side is a relational database. Canonical Stage-2 schema-visualization baseline. Absent for non-relational sides.
- **dbt Project Artifact**: A stock-dbt-runnable project produced by the bridge-synthesis stage. Canonical Stage-3 declarative-transformation baseline.
- **Enhanced Playground**: A single-file HTML playground produced per stage per iteration. Consumes its stage's prior-art artifact(s) and adds the LLM-analyst layer. Per-section labeled "prior-art baseline / LLM-extended / toolkit-novel" (FR-022 / FR-044).
- **Iteration**: One pass through bridge synthesis within a project. Has an integer index, an origin (automatic — from oracle feedback; or manual — from operator feedback), and an oracle-validation status (validated / failed / skipped). Owns: all per-iteration artifacts (raw + enhanced × stage), the materialized bridge output artifact (FR-048), the feedback payload that drove it, and the oracle Validation Result.
- **Iteration History**: An on-disk versioned record of all iterations for a project, mixing automatic and manual iterations chronologically. Movable as part of the final bundle.
- **Mapping Proposal**: The set of table- and field-level mappings between pile and target at a given iteration. Serialized as the dbt project artifact's models + schema.yml, plus comments captured via the enhanced bridge playground.
- **Validation Result**: The outcome of one insert+delete round trip against the target during an iteration — success, schema-violation failure, transient failure (retried), or "skipped" — with the transformed dummy record and any error message.
- **Synthesized Feedback Prompt**: A natural-language payload generated automatically from an oracle failure, used to seed the next automatic iteration's bridge synthesis. Distinct from operator-generated feedback in that it requires no user intervention.
- **Final Bundle**: The directory of files produced when the operator runs `accept-bundle` on a project. Suitable as direct input to `/speckit.specify`.
- **Truth Baseline**: A hand-curated reference dataset for a bridge domain — the operator-believed-correct values for each record. Stored as a human-readable TSV/CSV/JSON file inside the project folder. Editable through review sessions; deliberately NOT frozen. Every edit preserved with prior value, timestamp, and rationale in an edit-history sidecar. Refines over time as the operator's understanding sharpens or the bridge surfaces baseline errors.
- **AI-Inferred-Field Designation**: Metadata on the bridge mapping naming which target columns are produced by AI inference (as opposed to direct copies or deterministic transforms). Drives review-playground emphasis and the three-way comparison's scope.
- **Review Session**: One operator pass through paired (truth, bridge) records for one or more iterations. Owns: the iteration(s) under review, the truth-baseline snapshot at session start, per-pair verdicts, baseline edits captured, persisted session summary. Lives in the iteration folder.
- **Verdict**: The operator's per-pair tag from a review session — one of `exact-match`, `bridge-improved`, `bridge-regressed`, `truly-different`. The mechanism by which operator judgment enters the iteration record.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator unfamiliar with the toolkit can complete project creation + connection validation for the IG→Travelogue case (User Story 1) in **under 5 minutes**.
- **SC-002**: An operator with a validated project can complete one full pile + target profile-analysis pass (User Story 2, both sides, raw + enhanced artifacts including ER diagram for the relational target) in **under 30 minutes** of human time (excluding LLM-call wall-clock).
- **SC-003**: An operator already familiar with `ydata-profiling` recognizes the raw ydata artifact as canonical ydata output **in 100% of cases**.
- **SC-004**: An operator already familiar with `eralchemy` or `schemaspy` recognizes the raw ER-diagram artifact as canonical output of that tool **in 100% of cases**.
- **SC-005**: An operator already familiar with `dbt` recognizes the raw dbt project artifact as a canonical stock-dbt-runnable project **in 100% of cases**, and can `dbt parse` / `dbt compile` it without modification.
- **SC-006**: An operator inspecting any enhanced playground can correctly identify, for every section, whether the content is **prior-art baseline / LLM-extended / toolkit-novel** by reading the playground alone, in at least **95%** of test sections — driven by the FR-022 / FR-044 labeling.
- **SC-007**: When target DB access is available, the automatic oracle-driven refinement loop (User Story 4) **converges to an oracle-validated bridge within 3 automatic iterations** for at least **80%** of synthetic test cases starting from a typical initial broken mapping.
- **SC-008**: When target DB access is available, the oracle correctly **flags a deliberately-broken mapping as failed** in at least **95%** of synthetic test cases (mapping breakages: type mismatch, NOT-NULL violation, foreign-key violation).
- **SC-009**: The 5-fail ceiling on the automatic oracle loop halts the loop within **one iteration** of the 5th consecutive schema-violation failure (no runaway loops, no silent overruns).
- **SC-010**: Transient failures during the oracle loop (network outage, target temporarily unavailable) are correctly distinguished from schema-violation failures and do NOT count toward the 5-fail ceiling, in at least **95%** of test cases.
- **SC-011**: The final bundle for the IG→Travelogue case is **acceptable as input to `/speckit.specify` without further hand-editing of the bundle's structure** in at least **90%** of test runs by independent operators.
- **SC-012**: A second-time operator (someone who has used the toolkit at least once before) completes a fresh project+analysis+synthesis run in **under half the human time** their first run took.
- **SC-013**: The toolkit can be run against a **non-IG pile** and a **non-Travelogue target** without source-code changes — only via the project-creation CLI with different paths/URLs — and produces a bundle whose contents an operator unfamiliar with that pile+target finds legible.
- **SC-014**: All three enhanced playgrounds for any one iteration **open and render fully in a stock browser within 3 seconds** on a typical operator machine, with embedded data of representative size.
- **SC-015**: The toolkit's directory **can be moved to a fresh repository** by `mv bridge-builder-toolkit/ /elsewhere/` and run there against existing projects with the same results — validates FR-003.
- **SC-016**: Multiple bridge projects coexist in one installation **without state corruption** across **at least 5 concurrent projects**.
- **SC-017**: Connection-validation at project creation correctly **identifies a misconfigured endpoint** (wrong path, wrong credentials, unreachable host) in **100%** of test cases.
- **SC-018**: If any pinned prior-art tool (`ydata-profiling`, ER tool, `dbt`) fails at runtime, the toolkit **never** produces an enhanced playground that fabricates the affected baseline — the failure surfaces to the operator in **100%** of test cases (FR-105 honored).
- **SC-019**: For a 300-row bridge output reviewed against an existing truth baseline (the calibration anchor here is the IG→Travelogue 2026-06-03 manual walkthrough of 322 shared shortcodes), an operator can complete one review pass — including baseline edits — in **under 90 minutes**.
- **SC-020**: Every truth-baseline edit made through a review session is retrievable from the edit-history sidecar with its prior value, new value, session id, timestamp, and (when supplied) rationale in **100%** of cases — no edit loss, no edit untraceability.
- **SC-021**: The review playground correctly identifies AI-inferred columns vs direct-copy / deterministic-transform columns from the bridge mapping in **100%** of test cases (FR-153 honored).
- **SC-022**: In three-way mode (truth + iteration N + iteration M), an operator can identify which iteration's AI inference improved overall (more `bridge-improved` tags, fewer `bridge-regressed`) for the AI-inferred column subset in **under 5 minutes** for representative test cases.
- **SC-023**: A review-session summary, passed as a feedback payload to the `iterate` CLI (FR-160), drives a new bridge iteration whose AI-inference outputs measurably improve on the prior iteration's `bridge-regressed` tags in at least **70%** of test cases (early-loop refinement metric).

## Assumptions

- The operator has Python 3.12+, Docker, and an Anthropic LLM API key available at run time (matches the rest of the project's environment).
- `ydata-profiling`, an ER-diagram tool (`eralchemy` or `schemaspy`), and `dbt-core` (with the relevant adapter for the IG→Travelogue case, e.g. `dbt-postgres`) are installable in the toolkit's venv.
- The pile is filesystem-accessible to the toolkit process. Remote piles are out of scope for the initial implementation.
- The target's schema is introspectable. For the IG→Travelogue first execution, this means a live Postgres database (via the existing `docker compose up` stack) or a static schema file. For future targets, SQLAlchemy reflection is the assumed mechanism.
- For the automatic oracle loop (User Story 4), the operator can supply credentials with both insert and delete permissions on the target — but the toolkit DOES NOT require this; projects without those permissions skip the oracle loop and rely on manual refinement (User Story 5) alone.
- Project credentials are supplied via env-var references rather than embedded as plaintext (enforced by FR-012).
- Playground HTML is opened in a modern browser with JavaScript and clipboard API access; older browsers fall back per FR-054.
- LLM analysis at each stage is the canonical Anthropic Claude API; provider-specific implementation details are an open choice at plan time.
- The prior-art and existing-shoulder references in this spec (`ydata-profiling`, `eralchemy`/`schemaspy`, `dbt`, `Valentine`, `Magneto`/`Jellyfish`) were assembled from training knowledge at draft time; a live web-search verification pass is expected during planning to confirm currency and identify any tools the model missed.
- One operator runs the toolkit at a time against a given project. Concurrent runs against the same project are blocked by per-project locking (FR-110). Runs against *different* projects in the same installation can proceed concurrently.
- The toolkit produces spec input but does NOT itself author or commit downstream spec files. Handoff to `/speckit.specify` (or equivalent) is the operator's responsibility.
- The toolkit is the foundational predecessor of a future `bridge-builder-app` spec. Automation of the orchestrator end and generalization to arbitrary pile+target pairs is explicitly deferred to that future spec.
