# Phase 1 Data Model: bridge-builder-toolkit

**Date**: 2026-06-08 · **Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

The toolkit is filesystem-backed (no toolkit-owned DB). This document maps the spec's [Key Entities](spec.md#key-entities) to concrete on-disk structures. Everything below lives **inside a project folder**, so the App stays movable (FR-003/SC-015).

---

## On-disk layout (per project)

```text
bridge-builder-toolkit/projects/<project-name>/
├── project.yml                         # Bridge Project config + validation status
├── .lock                               # per-project PID lockfile (FR-110); absent when idle
├── truth-baseline/
│   ├── baseline.tsv                    # Truth Baseline (human-editable; FR-157)
│   └── baseline.edit-history.jsonl     # append-only edit history sidecar (FR-155)
├── iterations/
│   ├── iteration-1/
│   │   ├── iteration.yml               # Iteration metadata (origin, oracle status, parent)
│   │   ├── pile.ydata-profile.html     # raw ydata (FR-021)            — Stage 2
│   │   ├── pile.enhanced.html          # enhanced playground (FR-022)  — Stage 2
│   │   ├── target.ydata-profile.html   # raw ydata
│   │   ├── target.er-diagram.svg       # raw eralchemy2 (relational only; FR-027)
│   │   ├── target.enhanced.html        # enhanced playground
│   │   ├── mapping.yml                 # Mapping Proposal (incl. AI-Inferred designation)
│   │   ├── bridge.dbt-project/         # raw stock-runnable dbt-duckdb project (FR-041)
│   │   ├── bridge.duckdb               # local staging+transform engine (gitignored)
│   │   ├── bridge.output.tsv           # materialized full output (FR-048)
│   │   ├── bridge.enhanced.html        # enhanced bridge playground (FR-042)
│   │   ├── oracle.result.json          # Validation Result (FR-070) — absent if skipped
│   │   ├── feedback.in.txt             # feedback payload that DROVE this iteration
│   │   ├── feedback.synthesized.txt    # auto feedback this iteration EMITTED (oracle fail)
│   │   └── review/                     # Review Sessions against this iteration (US6)
│   │       └── session-<ts>.summary.json
│   └── iteration-2/ ...                # mixed automatic + manual, chronological (FR-082)
└── final-bundle/                       # materialized by accept-bundle (FR-090); absent until then
```

---

## Entities

### Bridge Project — `project.yml`
```yaml
name: "IG post scrape to Travelogue"
created_at: "2026-06-08T14:00:00+0000"
pile:
  path: "../../pile-app/pile/posts.ourearthsandwich.local.tsv"   # operator-supplied (FR-005)
  kind: "tsv"                          # tsv | relational (future)
  sample: { strategy: "head+random", size: 200 }                  # FR-028/FR-029
target:
  kind: "relational"                   # v1: relational only (FR-005 v1 scope)
  connection_env: "BRIDGE_TARGET_DSN"  # env-var NAME, never the secret (FR-012)
validation:                            # Connection Validation Result (FR-007)
  pile_readable: true
  target_reachable: true
  target_read: true
  target_insert: true                  # drives oracle run vs skip (FR-070/075)
  target_delete: true
  validated_at: "2026-06-08T14:00:12+0000"
  notes: ""                            # e.g. "oracle loop will be skipped — no insert perm"
```
- **Identity**: `name` (unique per installation; `--force` to overwrite, FR-011).
- **Validation rules**: `project create` aborts cleanly (no folder) if `pile_readable` or `target_reachable` is false (FR-008). `target_insert && target_delete` gates the oracle loop.

### Connection Validation Result
The `validation:` block above. Per-endpoint booleans + timestamp + reason. Recorded at creation (FR-007); re-checked at each iteration's oracle/validation step and re-surfaced if credentials changed (Edge Case).

### Iteration — `iteration.yml`
```yaml
index: 2
origin: "manual"                       # automatic (oracle feedback) | manual (operator)
parent_index: 1
oracle_status: "validated"             # validated | failed | skipped
consecutive_auto_failures: 0           # the 5-fail counter (FR-073); reset rules apply
created_at: "..."
artifacts:                             # relative filenames present in this folder
  raw: [pile.ydata-profile.html, target.ydata-profile.html, target.er-diagram.svg, bridge.dbt-project]
  enhanced: [pile.enhanced.html, target.enhanced.html, bridge.enhanced.html]
  output: bridge.output.tsv
```
- **State transitions**: `synthesized → oracle(running) → {validated | failed→re-synth (auto) | skipped} → operator-review`. The 5-fail counter resets on an oracle pass OR a manual iteration (FR-073/078).

### Mapping Proposal — `mapping.yml`
```yaml
matcher_lineage: ["Valentine", "Magneto (VLDB'25)"]   # cited style (FR-045/FR-103)
tables:
  - target_table: "stops"
    columns:
      - target_column: "name"
        source: { pile_column: "location" }
        kind: "direct"                 # direct | deterministic | ai_inferred
      - target_column: "latitude"
        source: { pile_column: "lat" }
        kind: "deterministic"          # e.g. cast/parse
        transform: "cast(lat as double)"
      - target_column: "region_code"
        source: { pile_columns: ["caption", "location", "media_url"] }
        kind: "ai_inferred"            # FR-047 toolkit-side LLM step; FR-153 designation
        inference:
          prompt_ref: "infer_region"   # role-named (no model name; Rule #3)
          preserved_inputs: ["caption", "location", "media_url"]   # Principle V / Rule #4
comments: []                           # operator comments captured via the playground (FR-042)
```
- **AI-Inferred-Field Designation**: the `kind: ai_inferred` columns. Mirrored into the dbt project's `schema.yml` column meta (FR-153) so the review playground reads it (FR-021 of US6).
- **Inference-input preservation (Constitution V)**: every `ai_inferred` column MUST list `preserved_inputs`; those input values are written alongside the inferred value in `bridge.output.tsv` (below).

### Materialized output — `bridge.output.tsv` (FR-048)
One row per pile record (keyed by the pile's dedup id, e.g. `shortcode`). Columns:
- the target columns the mapping produces (deterministic + AI-inferred), **plus**
- for each `ai_inferred` target column `X`: a companion `X__inputs` column carrying the JSON of the preserved inference inputs, and `X__rationale` (role-named) — so any inference can be re-run/audited with a different model (Principle V). Companion columns are suffixed, never embedded with model names.

### Validation Result — `oracle.result.json` (FR-070)
```json
{
  "ran": true,
  "sampled_keys": ["BkLm…", "Cd9…", "Ef2…"],
  "selection": "constraint-stressing (max empty-fields, max length) + 1 random",
  "rows": [
    {"key": "BkLm…", "outcome": "success"},
    {"key": "Cd9…", "outcome": "schema_violation", "error": "null value in column \"region_code\" violates not-null constraint", "transformed_record": {…}}
  ],
  "passed": false,
  "failure_class": "schema_violation",   // schema_violation | transient | none
  "mechanism": "insert+delete in a rolled-back transaction"
}
```
- `ran: false` + a `reason` when skipped for missing insert/delete permission (FR-075).
- Transient failures retried with backoff before counting toward the 5-fail ceiling (FR-072).

### dbt Project Artifact — `bridge.dbt-project/`
Stock-runnable `dbt-duckdb` project: `dbt_project.yml`, `profiles.yml` (DuckDB pointing at `../bridge.duckdb`), `models/sources.yml` (the staged pile), `models/*.sql` (deterministic mappings only — NOT the AI inference, FR-047), `models/schema.yml` (column tests + the `ai_inferred` meta flags), and `target/` with generated `dbt docs`. Preserved byte-for-byte (FR-021/SC-005).

### ydata-Profile / ER-Diagram / Enhanced Playground Artifacts
Raw artifacts are the prior-art tools' untouched output (FR-021). Each **Enhanced Playground** is a single self-contained HTML file whose every section carries a label ∈ {`ydata-profiling baseline`, `ER-diagram baseline`, `dbt baseline`, `LLM-extended`, `toolkit-novel`} (FR-022/044), reflected in its copy-out-a-prompt payload (FR-052/053). ER artifact absent (not fabricated) for non-relational sides (FR-027).

### Truth Baseline — `truth-baseline/baseline.tsv` + edit-history sidecar
- `baseline.tsv`: human-readable, keyed by the review join key (e.g. `shortcode`); columns are the operator-believed-correct values, focused on AI-inferred fields. Hand-editable (FR-157). May start empty (FR-161 bootstrap).
- `baseline.edit-history.jsonl`: append-only; one JSON line per `bridge-improved` edit: `{key, column, prior_value, new_value, session_id, timestamp, editor, rationale?}` (FR-155). No edit loss (SC-020).

### Review Session — `iterations/iteration-N/review/session-<ts>.summary.json` (FR-159)
```json
{
  "session_id": "2026-06-08T18:00Z",
  "iterations": [2],                    // or [2, 3] in three-way mode (FR-158)
  "join_key": "shortcode",
  "ai_inferred_columns": ["region_code","name"],
  "bucket_counts": {"exact-match": 210, "bridge-improved": 14, "bridge-regressed": 6, "truly-different": 9, "only-truth": 0, "only-bridge": 3},
  "verdicts": [ {"key":"BkLm…","column":"region_code","verdict":"bridge-improved"} ],
  "baseline_edits": [ {"key":"BkLm…","column":"region_code","prior":"MEX","new":"NLU"} ]
}
```
- **Verdict** ∈ {`exact-match`, `bridge-improved`, `bridge-regressed`, `truly-different`} (FR-154). Only `bridge-improved` mutates the baseline (FR-155/156). The summary is acceptable as an `iterate` feedback payload (FR-160).

### Final Bundle — `final-bundle/` (FR-090)
Materialized by `accept-bundle`: a manifest (`bundle.yml`) plus copies/links of all iteration artifacts (raw + enhanced × stage), the final `mapping.yml`, `bridge.output.tsv`, the full iteration history, captured prompt payloads, and the two verbatim **003 US3 carry-forward items** (FR-092). Self-contained and directly usable as `/speckit.specify` input — it is the toolkit's deliverable (a validated bridge *specification*, not a running bridge).

### Synthesized Feedback Prompt — `feedback.synthesized.txt`
Natural-language payload auto-generated from an oracle failure (DB error + transformed record) that seeds the next automatic iteration (FR-071). Distinct from operator `feedback.in.txt`.

---

## Cross-cutting invariants
- **Inference inputs preserved** (Constitution V / Rule #4): enforced by the `preserved_inputs` field (mapping.yml) + the `*__inputs`/`*__rationale` companion columns (output.tsv) + captured prompt payloads in the bundle.
- **Role-based naming** (Rule #3): `ai_inferred`, `inference.prompt_ref`, `rationale`, `analyst_layer` — no `claude_*` / model names anywhere in config, output, or code.
- **Movability** (FR-003): all paths inside a project folder are relative or env-referenced; nothing absolute leaks into committed artifacts.
