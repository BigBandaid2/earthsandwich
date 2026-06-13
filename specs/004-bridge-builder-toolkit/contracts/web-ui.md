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

Conventions: POST-redirect-GET on success; on failure the form is re-rendered with an inline error (`OperatorError` text — no stack traces). The relational-endpoint **password is write-only** — its value never appears in any rendered page, log, or `project.yml`; it is stored only in `.secrets` (FR-012 / FR-178).

| Route | Behavior |
|---|---|
| `GET /` | Redirect to `/projects`. |
| `GET /projects` | Project list: slug, pile (directories + file count), target endpoint, validation status; link to the create form and each dashboard (FR-172 list). Routes below key on the **slug**. |
| `GET /projects/new` | Four-part create form (FR-172): **Identity** (name → live slug + uniqueness, description & intent + char counter); **Pile sources** (add data/media directories, "List & validate files", per-file row×col/format/reject + Select-all, frozen selection, editable sample spec); **Target** (engine/host/port/database/user/password + Test connection); **Create** (gated). |
| `POST /projects/list-files` | Lists + table-validates the files in the submitted data directories (row×col, format, reject reasons) and catalogues media directories; re-renders the form with the file checkboxes — no state created. |
| `POST /projects/test-connection` | Assembles the submitted discrete connection into a DSN and probes reachability + read/insert/delete WITHOUT persisting (FR-183); returns the per-permission result inline. Opens/closes the Create gate. |
| `POST /projects` | `action=create`: gated (slug free + ≥1 valid data-file + connection tested), then the same core flow as `project create` (validate-then-materialize, FR-008 parity) — writes the DSN to `.secrets`, `project.yml` password-free. Success → redirect to the dashboard with the FR-007 report inline. Failure (slug taken, invalid/unreadable file, unreachable target) → form re-rendered with the inline error; no state created. |
| `GET /projects/{slug}` | **Dashboard** (FR-173/174/185): collapsed Pile-valid/Target-valid (detail → Project details); stage-flow + iteration counts for both loops; latest oracle status; final-bundle presence; artifact links; suggested-next-step tracker (one primary + alternates). No delete here. Auto-polls (~5 s) while the lock is held; static otherwise. Missing slug → clear not-found page. |
| `GET /projects/{slug}/edit` | **Project details** = the create form mirrored, name read-only, current values pre-filled (data-file selection pre-checked, connection shown as "tested/stored" without the password), plus a collapsed **Delete project** (typed-slug confirm). |
| `POST /projects/{slug}/update` | Re-validate-then-persist (FR-172); prior config + `.secrets` untouched on failure; a re-entered password re-writes `.secrets`; refused while the lock is live-held (FR-177). |
| `POST /projects/{slug}/delete` | Requires a confirmation field equal to the **slug** (typed-confirm — irreversible); refused while the lock is live-held (FR-177); on success removes the project folder (incl. `.secrets`) and redirects to `/projects`. |
| `GET /projects/{slug}/artifacts/{relpath}` | Serves a file from **inside the owning project's folder only** — containment checked after resolution; escapes refused (FR-175). A directory path renders a minimal listing; missing path → 404. |

## Rendering contract

- Fully offline: vanilla HTML/CSS/JS, no external assets or CDNs (FR-179); persistent **left-rail app-shell** (FR-184) — workspace nav + per-project nav, consistent across in-project views.
- UI pages are server-rendered documents — explicitly **not** bound by FR-050's single-file rule, which remains scoped to the Stage 1–3 / US6 artifact playgrounds.
- The **password field is write-only** (FR-178): never rendered back (the form shows a tested/stored state), never logged, never written to `project.yml` — the DSN lives only in `.secrets`.
- The dashboard derives everything from the on-disk structures in [data-model.md](../data-model.md) (`project.yml`, `data-profiling/iteration-*/`, `bridge-mapping/iteration-*/`, `final-bundle/`, `.lock`); the UI maintains no parallel state (FR-173).
