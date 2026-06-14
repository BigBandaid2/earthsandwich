# Quickstart: bridge-builder-toolkit (IG → Travelogue first run)

**Date**: 2026-06-08 · **Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

The canonical first execution (FR-091): build a **validated bridge specification** for mapping the 003 Instagram pile into the 002 Travelogue schema. The output is a Final Bundle that seeds `/speckit.specify` for the bridge-app — *not* a running bridge.

## 0. Prerequisites

- Python 3.12+, Docker, an Anthropic API key, and **GraphViz** installed (for the ER diagram — `eralchemy2` needs it).
- The 002 Travelogue stack running locally (`docker compose up -d` from repo root) so the target Postgres is reachable.
- A 003 pile TSV on disk (e.g. `pile-app/pile/posts.ourearthsandwich.local.tsv`).

## 1. Install the toolkit

```pwsh
# From bridge-builder-toolkit/
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e .

copy .env.example .env
# Edit .env: ANTHROPIC_API_KEY=...
```

## 2. Create the project + validate connections (US1)

```pwsh
bridge_builder project create "IG pile → travelogue" `
    --data-dir ../pile-app/pile --media-dir ../pile-app/pile/media `
    --pile-files "posts.ourearthsandwich.local.tsv,posts.welawen.local.tsv" `
    --engine postgresql --host localhost --port 5432 `
    --database earthsandwich --user earthsandwich
    # target password read from a hidden prompt (never a plaintext flag);
    # stored only in projects/<slug>/.secrets
```
The name derives a unique **slug** (`ig-pile-to-travelogue`) = the folder name; freeing a taken slug requires an explicit `project delete` (no `--force`/overwrite). A file pile is **one or more `--data-dir` / `--media-dir` directories** (media is catalogued, not per-file-selected), with data files frozen by `--pile-files` (`all` or a comma-separated list). The target connection is entered as discrete fields; the password is prompted and the assembled DSN is written to gitignored `projects/<slug>/.secrets` — **never to `project.yml`** (FR-012).

**Endpoint symmetry**: pile and target are each `file` or `relational`. The IG→Travelogue first run is the common file-pile → relational-target shape above. To flip either side, set `--pile-kind`/`--target-kind` and supply that side's inputs — a relational pile takes `--pile-engine/--pile-host/--pile-port/--pile-database/--pile-user` (+ hidden prompt); a file target takes `--target-path`. File-based relational engines (`sqlite`, `duckdb`) need only `--database` (the file path) and prompt for no password.
Expect a validation report: pile **readable**, target **reachable + read + insert + delete** (the 002 stack grants all → the oracle loop will run). **SC-001: under 5 minutes.**

```pwsh
bridge_builder project list      # confirms slug, pile, target, validation status
```

### 2.5 …or use the Web UI (US7)

```pwsh
bridge_builder ui                # guided local UI at http://127.0.0.1:8765
```
The guided form walks Identity (name → slug, description & intent) → Pile sources (add data/media directories, "list & validate files", frozen selection, sample spec) → Target (discrete DB connection + **Test connection**) → gated Create. Edit / delete on Project details; each dashboard shows collapsed Pile/Target-valid status, stage progress across both loops, and the suggested next CLI command. The stages themselves still run via the CLI commands in steps 3–7.

## 3. Profile both sides (US2)

```pwsh
bridge_builder analyze pile   --project "ig-pile-to-travelogue"
bridge_builder analyze target --project "ig-pile-to-travelogue"
```
Produces in `data-profiling/iteration-1/`:
- `pile.ydata-profile.html` (canonical ydata — recognizable; SC-003), `pile.enhanced.html` (no ER — non-relational pile, FR-027).
- `target.ydata-profile.html`, `target.er-diagram.svg` (canonical eralchemy2; SC-004), `target.enhanced.html` (ranked candidate tables to populate — `stops` is the obvious one).

Open the enhanced playgrounds: every section is labeled **ydata baseline / ER-diagram baseline / LLM-extended / toolkit-novel** (SC-006).

## 4. Synthesize the bridge mapping (US3 → auto oracle US4)

```pwsh
bridge_builder synthesize bridge --project "ig-pile-to-travelogue"
```
- Emits `mapping.yml` (Magneto-style matcher, cited), a stock-runnable `bridge.dbt-project/` (try `dbt parse` / `dbt docs serve` — SC-005), and materializes `bridge.output.tsv` (the full local transform; the target is NOT bulk-loaded).
- AI-inferred columns (e.g. `region_code` from caption+location) come from the toolkit-side LLM step (FR-047); each ships with its preserved inputs.
- Because insert+delete permissions exist, the **oracle loop runs automatically**: it transforms a 3–5 row constraint-stressing sample and round-trips each into Postgres in a rolled-back transaction. You see the *final* state — an oracle-validated bridge, or a 5-fail halt banner — not the intermediate auto-iterations (FR-046/077).

Open `bridge.enhanced.html`: pile ↔ target side-by-side, proposed mappings, comment + adjust controls, **copy out a prompt**.

## 5. Refine manually (US5)

In `bridge.enhanced.html`, fix a semantic mis-map the oracle can't catch (right type, wrong column), leave comments, click **copy out a prompt**, then:

```pwsh
bridge_builder iterate --project "ig-pile-to-travelogue" --feedback feedback.txt
```
A new `iteration-2/` is produced (re-synthesized, re-oracled). Prior iterations stay readable for side-by-side compare.

## 6. Review AI-inference quality vs. a truth baseline (US6)

```pwsh
bridge_builder review --project "ig-pile-to-travelogue" `
    --baseline truth-baseline/baseline.tsv --join-key shortcode
```
Walk paired (truth, bridge) rows with AI-inferred columns emphasized; tag each `exact-match` / `bridge-improved` / `bridge-regressed` / `truly-different`. `bridge-improved` tags update the baseline (with edit-history); a session summary is saved and can be fed back to `iterate` (FR-160). **SC-019: a 300-row pass under 90 minutes.** Use `--vs-iteration` for three-way compare of two iterations.

## 7. Accept → the Final Bundle (the deliverable)

```pwsh
bridge_builder accept-bundle --project "ig-pile-to-travelogue"
```
Materializes `final-bundle/` — all artifacts, final mapping, output, full iteration history, captured prompts, and the verbatim 003-US3 carry-forward items (FR-092). Hand this bundle to `/speckit.specify` to author the **bridge-app** spec (SC-011). The functioning bridge is built later, from that spec.

## Validation shortcuts (tie-back to Success Criteria)
- `dbt parse bridge.dbt-project/` → SC-005. Open raw artifacts → SC-003/004.
- Break a mapping deliberately, re-synthesize → oracle flags it (SC-008); ≤3 auto-iterations to converge (SC-007).
- `mv bridge-builder-toolkit/ /elsewhere/` and re-run a project → SC-015 (movability).
