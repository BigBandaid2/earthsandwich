# Contract: bridge-builder-toolkit CLI

**Date**: 2026-06-08 · **Spec**: [../spec.md](../spec.md) · **Plan**: [../plan.md](../plan.md)

The toolkit exposes two operator surfaces over one shared core (FR-004): this CLI — the automation/scripting surface and the only surface that launches stages — and the guided local Web UI ([web-ui.md](web-ui.md), FR-170–179). The CLI has one subcommand per stage, mirroring the pile-app pattern. Entry point: `bridge_builder` (after `pip install -e .`) or `python cli.py` (dev). Every *stage* command operates on a named project under `bridge-builder-toolkit/projects/<name>/`, acquires the per-project lock (FR-110) for the duration, and writes a per-run log; `project list` and `ui` are exceptions — `ui` locks per mutating request only (FR-177).

**Global conventions**
- Project selected by `--project <name>` (or positional `<name>` where natural).
- Exit `0` success; `1` operator-correctable error (bad path, unreachable target, lock held) with a clear message; `2` prior-art tool hard-failure (FR-105). No stack traces on the `1`/`2` paths.
- Credentials are NEVER passed on the command line — only env-var names in `project.yml` (FR-012).
- Stdout is the human log; machine artifacts go to the project folder.

---

## `project create`

```
bridge_builder project create <name> \
    --pile <dir> \
    [--pile-files <a.tsv,b.tsv | all>] \
    --target <dsn-or-schema-file-or-url> \
    --target-cred-env <ENV_VAR_NAME> \
    [--pile-sample head+random:200] [--force]
```
- **US1 / FR-005–008, FR-011–012.** `--pile` is the pile DIRECTORY; `--pile-files` selects one, multiple (comma-separated), or `all` of its files (default `all`). The selection is **frozen to an explicit file list** at creation — later-arriving files join only via `project update`. Creates `projects/<name>/`, writes `project.yml`, runs the **connection-validation step** (every selected pile file readable; target reachable + read/insert/delete probes) and records per-endpoint status.
- v1 rejects a non-relational `--target` with a "deferred to a future version" message (FR-005 v1 scope).
- Aborts cleanly with **no folder** if pile unreadable or target unreachable (FR-008). Refuses to overwrite an existing project without `--force` (FR-011).
- **Output**: `project.yml` + a printed validation report (per-endpoint yes/no; whether the oracle loop will run or be skipped).

## `project list`
```
bridge_builder project list
```
- **US1 / FR-010.** Prints each project's name, pile path, target endpoint, and current validation status.

## `project update`
```
bridge_builder project update <name> [--pile <dir>] [--pile-files <a.tsv,b.tsv | all>] [--pile-sample <spec>] [--target-cred-env <ENV_VAR_NAME>]
```
- **US7 / FR-172, FR-176.** Applies the supplied edits (`--pile-files all` re-expands against the directory's CURRENT contents and freezes the new list) and re-runs connection validation against the edited inputs BEFORE persisting; on failure the prior config is untouched. Acquires the project lock for the operation.

## `project delete`
```
bridge_builder project delete <name> [--yes]
```
- **US7 / FR-176, FR-177.** Interactive confirmation unless `--yes`. Refuses (exit 1) while the project's lock is held by a live process; otherwise removes the project folder.

## `ui`
```
bridge_builder ui [--host 127.0.0.1] [--port 8765]
```
- **US7 / FR-170–179.** Launches the guided local Web UI — see [web-ui.md](web-ui.md) for the route contract. Localhost-bound by default; port-in-use is a clear exit-1 operator error. Holds no standing project lock (FR-177).

## `analyze pile`
```
bridge_builder analyze pile --project <name>
```
- **US2 / FR-020–024, FR-028–029, FR-100, FR-105.** In the project's current iteration folder, produces `pile.ydata-profile.html` (raw ydata) and `pile.enhanced.html` (LLM-analyst playground over a sampled pile). ER diagram skipped for a non-relational pile (FR-027). Hard-errors (exit 2) if ydata fails (FR-105) — never fabricates the baseline.

## `analyze target`
```
bridge_builder analyze target --project <name>
```
- **US2 / FR-020–022, FR-025–026, FR-100–101, FR-105.** Reflects the target schema (SQLAlchemy), produces `target.ydata-profile.html`, `target.er-diagram.svg` (raw eralchemy2), and `target.enhanced.html` (candidate-table ranking + reasoning). Requires GraphViz; missing-GraphViz is an exit-1 operator error with install guidance.

## `synthesize bridge`
```
bridge_builder synthesize bridge --project <name>
```
- **US3 / FR-040–048, FR-102–104.** Requires pile+target analyses present. Produces the **Mapping Proposal** (`mapping.yml`, Magneto-style matcher, cited), the stock-runnable `bridge.dbt-project/`, runs the **hybrid transform** (dbt-duckdb deterministic mappings + toolkit-side LLM inference for `ai_inferred` columns) materializing `bridge.output.tsv` (FR-048), and the `bridge.enhanced.html` playground.
- If the project has insert+delete permissions, control passes automatically to the **oracle loop** (US4) before returning — intermediate failed auto-iterations are NOT shown live (FR-046/077). Without permissions, returns the bridge directly for manual review.
- **Output**: a new (or current) iteration folder fully populated; oracle result embedded when applicable.

## `iterate`
```
bridge_builder iterate --project <name> --feedback <path-or-->
```
- **US5 / FR-080–082.** Takes a feedback payload (a bridge-playground copy-out prompt, or a US6 review-session summary, FR-160) and produces a **new iteration** incorporating it: re-runs synthesis (and re-enters the oracle loop if permissions allow), re-running profile analyses only if the feedback surfaces an uncovered property (FR-081). Prior iterations remain readable (FR-082).

## `accept-bundle`
```
bridge_builder accept-bundle --project <name> [--iteration <N>]
```
- **US5 / FR-083, FR-090–092.** Marks the chosen iteration final and materializes `final-bundle/` — all artifacts, final mapping, output, full history, captured prompts, and the two verbatim 003-US3 carry-forward items (FR-092). The bundle is the toolkit's deliverable: a validated bridge **specification**, usable as `/speckit.specify` input without structural hand-editing (SC-011).

## `review`
```
bridge_builder review --project <name> \
    --baseline <truth-baseline.tsv> --join-key <col> \
    [--iteration <N> [--vs-iteration <M>]] \
    [--ai-columns col1,col2]
```
- **US6 / FR-150–161.** Joins `bridge.output.tsv` against the truth baseline on `--join-key`, buckets `shared`/`only-truth`/`only-bridge`, emphasizes AI-inferred columns, and opens the review playground for per-pair verdict tagging. On save: `bridge-improved` tags write back to the baseline + edit-history sidecar (FR-155); a `session-<ts>.summary.json` is persisted (FR-159); the summary is acceptable as an `iterate` feedback payload (FR-160).
- `--vs-iteration` enables three-way mode (truth + N + M), scoped to AI-inferred columns (FR-158).
- Refuses to run (exit 1) if the join key is absent from either side (Edge Case / FR-151). Bootstraps an empty baseline (FR-161).

---

## Playground UI contract (all enhanced + review playgrounds)
- Single self-contained HTML file; vanilla HTML/CSS/JS; no remote assets; data embedded inline (FR-050/051).
- A **"copy out a prompt"** button producing a standalone, AI-actionable payload (FR-052/053), degrading to a selectable textarea where the clipboard API is unavailable (FR-054).
- Per-section provenance labels (`…baseline` / `LLM-extended` / `toolkit-novel`) visible in the UI and present in the copy-out payload (FR-022/044).
