# Contract: bridge-builder-toolkit Web UI

**Date**: 2026-06-10 · **Spec**: [../spec.md](../spec.md) (User Story 7, FR-170–179) · **CLI contract**: [cli.md](cli.md)

The guided local Web UI is the toolkit's second operator surface (FR-004b): project lifecycle CRUD plus a guided per-project dashboard. It executes exclusively through the same `project/` core modules the CLI uses (FR-171) — no UI-only lifecycle logic. **Stage launching is out of scope** for this story: the dashboard guides the operator to the right CLI command (FR-174).

## `ui` CLI command

```
bridge_builder ui [--host 127.0.0.1] [--port 8765]
```
- **FR-170.** Binds localhost by default; never exposed beyond the operator's machine by default. Port already in use → clear operator error, exit 1.
- The `ui` command does **NOT** take a project lock for its lifetime (carve-out from cli.md's global conventions): mutating requests acquire the per-project lock for the request duration only (FR-177).
- Requests are logged to stdout; exit 0 on clean shutdown.

## Routes (server-rendered HTML)

Conventions: POST-redirect-GET on success; on failure the form is re-rendered with an inline error (`OperatorError` text — no stack traces). Credential env-var **names** only; values never appear in any request, page, or log (FR-178).

| Route | Behavior |
|---|---|
| `GET /` | Redirect to `/projects`. |
| `GET /projects` | Project list: name, pile path, target env-var name, validation status; link to the create form and each dashboard (FR-172 list). |
| `GET /projects/new` | Create form: name, pile path, target descriptor, target-cred-env, pile-sample, force checkbox — mirroring `project create` inputs. |
| `POST /projects` | Same core flow as `project create` (validate-then-materialize, FR-008 parity). Success → redirect to the dashboard with the FR-007 validation report rendered inline. Failure (missing env var, unreadable pile, unreachable target, duplicate name) → form re-rendered with the inline error; no state created. |
| `GET /projects/{name}` | **Dashboard** (FR-173/174): validation block; stage-flow progress for both loops; iteration counts; latest oracle status; final-bundle presence; artifact links; lock indicator; suggested-next-step panel (one primary command + labeled alternates). While the lock is held the page auto-polls (~5 s, vanilla-JS refresh of the same snapshot); static otherwise. Missing project → clear not-found page. |
| `GET /projects/{name}/edit` | Update form: pile path, pile-sample, target-cred-env. |
| `POST /projects/{name}/update` | Re-validate-then-persist (FR-172); prior config untouched on failure; refused with a clear message while the lock is live-held (FR-177). |
| `POST /projects/{name}/delete` | Requires a confirmation field whose value MUST equal the project name (typed-name confirm — deletion is irreversible); refused while the lock is live-held (FR-177); on success removes the project folder and redirects to `/projects`. |
| `GET /projects/{name}/artifacts/{relpath}` | Serves a file from **inside the owning project's folder only** — containment is checked after path resolution; anything escaping the folder is refused (FR-175). A directory path renders a minimal listing of its entries as links (same containment rule), so multi-file artifacts (dbt project, dbt docs site) are browsable. Missing path → 404. |

## Rendering contract

- Fully offline: vanilla HTML/CSS/JS, no external assets or CDNs (FR-179); visual idiom shared with the enhanced playgrounds (dark theme).
- UI pages are server-rendered documents — explicitly **not** bound by FR-050's single-file rule, which remains scoped to the Stage 1–3 / US6 artifact playgrounds.
- The dashboard derives everything from the on-disk structures in [data-model.md](../data-model.md) (`project.yml`, `data-profiling/iteration-*/`, `bridge-mapping/iteration-*/`, `final-bundle/`, `.lock`); the UI maintains no parallel state (FR-173).
