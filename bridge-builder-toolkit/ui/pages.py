"""Server-rendered HTML layer for the guided Web UI (T045, FR-179).

Echoes the enhanced-playground dark idiom (own CSS constants — playground.py is
NOT imported; it builds standalone artifact files). Vanilla HTML via
``html.escape``; no template engine, no external assets.
"""
from __future__ import annotations

import html
from urllib.parse import quote

from common.config import BridgeProject
from project.status import ProjectStageStatus

_STYLE = """<style>
:root { color-scheme: dark; }
body { margin:0; font:14px/1.5 system-ui,sans-serif; background:#0f1115; color:#e6e8eb; }
header { padding:14px 20px; border-bottom:1px solid #232732; display:flex; align-items:baseline; gap:14px; }
header h1 { font-size:17px; margin:0; }
header a, header span.crumb { color:#9fb3d8; font-size:13px; text-decoration:none; }
main { padding:20px; display:flex; flex-direction:column; gap:16px; max-width:980px; }
.card { background:#161922; border:1px solid #232732; border-radius:8px; overflow:hidden; }
.card-head { display:flex; align-items:center; justify-content:space-between; padding:10px 14px; border-bottom:1px solid #232732; }
.card-head h2 { font-size:14px; margin:0; }
.card-body { padding:14px; }
table { width:100%; border-collapse:collapse; font-size:13px; }
th, td { text-align:left; padding:7px 10px; border-bottom:1px solid #20242f; }
a { color:#7fb0ff; }
pre { background:#0b0d12; border:1px solid #232732; border-radius:6px; padding:10px; overflow-x:auto; font:12px/1.5 ui-monospace,monospace; }
.badge { font-size:11px; padding:2px 8px; border-radius:999px; background:#2a3346; color:#9fb3d8; }
.badge.ok { background:#173527; color:#7fdc9c; }
.badge.warn { background:#3a2c17; color:#e7b96d; }
.badge.bad { background:#3a1c20; color:#f08a93; }
.error { background:#3a1c20; border:1px solid #5d2a31; color:#f0b6bc; border-radius:6px; padding:10px 12px; }
.flash { background:#173527; border:1px solid #28543a; color:#a9e4bd; border-radius:6px; padding:10px 12px; }
form.stack { display:flex; flex-direction:column; gap:10px; max-width:560px; }
label { font-size:12px; color:#9fb3d8; display:flex; flex-direction:column; gap:4px; }
input[type=text], input[type=number] { background:#0b0d12; color:#e6e8eb; border:1px solid #232732; border-radius:6px; padding:8px; font:13px ui-monospace,monospace; }
button { align-self:flex-start; padding:8px 16px; background:#3b82f6; color:#fff; border:0; border-radius:6px; cursor:pointer; }
button.danger { background:#b03a45; }
.chips { display:flex; gap:8px; flex-wrap:wrap; }
.chip { font-size:12px; padding:4px 10px; border-radius:6px; background:#1c2130; border:1px solid #232732; color:#9fb3d8; }
.chip.done { background:#173527; border-color:#28543a; color:#7fdc9c; }
.copy-row { display:flex; gap:8px; align-items:center; }
.copy-row pre { flex:1; margin:0; }
small.note { color:#7d8696; }
</style>
"""

_COPY_JS = """<script>
document.querySelectorAll('[data-copy]').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var pre = document.getElementById(btn.getAttribute('data-copy'));
    var text = pre.textContent;
    function fallback() { var r = document.createRange(); r.selectNodeContents(pre); var s = getSelection(); s.removeAllRanges(); s.addRange(r); btn.textContent = 'select+copy'; }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { btn.textContent = 'copied'; }, fallback);
    } else { fallback(); }
  });
});
</script>
"""


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def project_url(name: str, *suffix: str) -> str:
    path = "/projects/" + quote(name, safe="")
    if suffix:
        path += "/" + "/".join(suffix)
    return path


def layout(title: str, body: str, *, autorefresh: bool = False) -> str:
    refresh = (
        "<script>setTimeout(function(){location.reload();}, 5000);</script>" if autorefresh else ""
    )
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_e(title)}</title>\n{_STYLE}</head>\n<body>\n"
        f'<header><h1>bridge_builder</h1><a href="/projects">projects</a>'
        f'<span class="crumb">{_e(title)}</span></header>\n<main>\n'
        + body
        + "\n</main>\n"
        + _COPY_JS
        + refresh
        + "</body>\n</html>\n"
    )


def _validation_badge(project: BridgeProject) -> str:
    v = project.validation
    if not (v.pile_readable and v.target_reachable):
        return '<span class="badge bad">invalid</span>'
    if v.oracle_can_run:
        return '<span class="badge ok">valid (oracle: run)</span>'
    return '<span class="badge warn">valid (oracle: skip)</span>'


def render_project_list(projects: list[BridgeProject]) -> str:
    if projects:
        rows = "".join(
            f'<tr><td><a href="{project_url(p.name)}">{_e(p.name)}</a></td>'
            f"<td>{_e(p.pile.dir)} ({len(p.pile.files)} files)</td><td><code>{_e(p.target.connection_env)}</code></td>"
            f"<td>{_validation_badge(p)}</td></tr>"
            for p in projects
        )
        table = f"<table><tr><th>project</th><th>pile</th><th>target env</th><th>status</th></tr>{rows}</table>"
    else:
        table = "<p>(no projects yet)</p>"
    body = (
        '<section class="card"><div class="card-head"><h2>Bridge projects</h2>'
        '<a href="/projects/new">+ New project</a></div>'
        f'<div class="card-body">{table}</div></section>'
    )
    return layout("projects", body)


def _form_field(label: str, name: str, value: str = "", placeholder: str = "") -> str:
    return (
        f"<label>{_e(label)}"
        f'<input type="text" name="{_e(name)}" value="{_e(value)}" placeholder="{_e(placeholder)}"></label>'
    )


def _file_selection_html(file_choices: list[tuple[str, bool]] | None, *, list_label: str) -> str:
    """Checkbox block for the pile-file selection (FR-172), plus the list/re-list action."""
    list_button = f'<button type="submit" name="action" value="list_files">{_e(list_label)}</button>'
    if file_choices is None:
        return (
            list_button
            + '<small class="note">No file selection made yet - creating now selects ALL files '
            "currently in the directory (frozen to an explicit list).</small>"
        )
    boxes = "".join(
        f'<label><span><input type="checkbox" name="files" value="{_e(fname)}"{" checked" if checked else ""}> '
        f"{_e(fname)}</span></label>"
        for fname, checked in file_choices
    )
    return (
        '<input type="hidden" name="files_listed" value="1">'
        f'<div class="card-body" style="padding:0">{boxes or "<p>(directory has no files)</p>"}</div>'
        + list_button
    )


def render_create_form(
    error: str | None = None,
    values: dict[str, str] | None = None,
    file_choices: list[tuple[str, bool]] | None = None,
) -> str:
    v = values or {}
    err = f'<div class="error">{_e(error)}</div>' if error else ""
    body = (
        err
        + '<section class="card"><div class="card-head"><h2>New bridge project</h2></div><div class="card-body">'
        '<form class="stack" method="post" action="/projects">'
        + _form_field("Project name", "name", v.get("name", ""))
        + _form_field("Pile DIRECTORY (deposit of extracted source files)", "pile", v.get("pile", ""))
        + _file_selection_html(file_choices, list_label="List files in this directory")
        + _form_field("Target descriptor (relational DSN shape; never persisted)", "target", v.get("target", ""), "postgresql://host/db")
        + _form_field("Credential env-var NAME holding the target DSN (FR-012)", "target_cred_env", v.get("target_cred_env", ""), "MY_PROJECT_TARGET_DSN")
        + _form_field("Pile sample spec", "pile_sample", v.get("pile_sample", "head+random:200"))
        + '<label><span><input type="checkbox" name="force" value="1"> overwrite an existing project (--force)</span></label>'
        + '<button type="submit" name="action" value="create">Create + validate</button>'
        + '<small class="note">The credential VALUE is read from the named env var in the server\'s environment - it is never entered here, rendered, or persisted.</small>'
        + "</form></div></section>"
    )
    return layout("new project", body)


def render_edit_form(
    project: BridgeProject,
    error: str | None = None,
    file_choices: list[tuple[str, bool]] | None = None,
) -> str:
    err = f'<div class="error">{_e(error)}</div>' if error else ""
    name = project.name
    body = (
        err
        + f'<section class="card"><div class="card-head"><h2>Edit: {_e(name)}</h2>'
        f'<span class="badge">name is immutable</span></div><div class="card-body">'
        f'<form class="stack" method="post" action="{project_url(name, "update")}">'
        + _form_field("Pile DIRECTORY", "pile", project.pile.dir)
        + _file_selection_html(file_choices, list_label="Re-list files (after changing the directory)")
        + _form_field("Pile sample spec", "pile_sample", f"{project.pile.sample.strategy}:{project.pile.sample.size}")
        + _form_field("Credential env-var NAME", "target_cred_env", project.target.connection_env)
        + '<button type="submit" name="action" value="save">Re-validate + save</button>'
        + '<small class="note">Validation re-runs against these inputs BEFORE anything persists; on failure the prior config is untouched.</small>'
        + "</form></div></section>"
    )
    return layout(f"edit {name}", body)


def render_dashboard(
    project: BridgeProject,
    status: ProjectStageStatus,
    primary: str,
    alternates: list[str],
    *,
    flash: str | None = None,
    error: str | None = None,
) -> str:
    name = project.name
    v = project.validation
    yn = lambda b: "yes" if b else "NO"  # noqa: E731

    notice = ""
    if flash:
        notice += f'<div class="flash">{_e(flash)}</div>'
    if error:
        notice += f'<div class="error">{_e(error)}</div>'

    lock_banner = ""
    if status.lock_live_owner is not None:
        lock_banner = (
            f'<div class="error">operation in progress (lock held by live PID {status.lock_live_owner}) - '
            "dashboard is read-only and refreshing every 5 s; update/delete are disabled until it finishes</div>"
        )

    validation_html = (
        f"<pre>pile readable:    {yn(v.pile_readable)}  ({_e(project.pile.describe())})\n"
        f"target reachable: {yn(v.target_reachable)}  (env: {_e(project.target.connection_env)})\n"
        f"target read:      {yn(v.target_read)}\n"
        f"target insert:    {yn(v.target_insert)}\n"
        f"target delete:    {yn(v.target_delete)}\n"
        f"oracle loop:      {'will run' if v.oracle_can_run else 'will be skipped'}\n"
        f"validated at:     {_e(v.validated_at or '-')}</pre>"
    )

    def chip(label: str, done: bool) -> str:
        return f'<span class="chip{" done" if done else ""}">{_e(label)}</span>'

    stages_html = (
        '<div class="chips">'
        + chip("create", True)
        + chip(f"analyze pile ({'done' if status.pile_profiled else 'not run'})", status.pile_profiled)
        + chip(f"analyze target ({'done' if status.target_profiled else 'not run'})", status.target_profiled)
        + chip(f"synthesize ({status.mapping_iterations} iter)", status.mapping_iterations > 0)
        + chip(f"oracle: {status.latest_oracle_status or '-'}", status.latest_oracle_status == "validated")
        + chip(f"review ({status.review_sessions} sessions)", status.review_sessions > 0)
        + chip("final bundle", status.bundle_present)
        + "</div>"
        + f'<p><small class="note">data-profiling iterations: {status.profiling_iterations} - '
        f"bridge-mapping iterations: {status.mapping_iterations}</small></p>"
    )

    alt_html = ""
    if alternates:
        alt_items = "".join(f"<li><code>{_e(a)}</code></li>" for a in alternates)
        alt_html = f'<p><small class="note">also available:</small></p><ul>{alt_items}</ul>'
    next_html = (
        '<div class="copy-row">'
        f'<pre id="next-cmd">{_e(primary)}</pre>'
        '<button type="button" data-copy="next-cmd">copy</button></div>' + alt_html
    )

    mutations_disabled = status.lock_live_owner is not None
    edit_link = "" if mutations_disabled else f'<a href="{project_url(name, "edit")}">edit</a>'
    delete_form = (
        ""
        if mutations_disabled
        else (
            f'<form class="stack" method="post" action="{project_url(name, "delete")}">'
            f'<label>Type the project name to confirm deletion (irreversible - iteration histories, truth baseline and bundle are removed)'
            f'<input type="text" name="confirm_name" placeholder="{_e(name)}"></label>'
            '<button type="submit" class="danger">Delete project</button></form>'
        )
    )

    body = (
        notice
        + lock_banner
        + f'<section class="card"><div class="card-head"><h2>{_e(name)}</h2>'
        f"{_validation_badge(project)}</div><div class=\"card-body\">{validation_html}</div></section>"
        + f'<section class="card"><div class="card-head"><h2>Stage flow</h2>{edit_link}</div>'
        f'<div class="card-body">{stages_html}</div></section>'
        + f'<section class="card"><div class="card-head"><h2>Suggested next step</h2></div>'
        f'<div class="card-body">{next_html}'
        '<p><small class="note">Stages run via the CLI - the UI guides, it does not launch them.</small></p></div></section>'
        + f'<section class="card"><div class="card-head"><h2>Artifacts</h2></div><div class="card-body">'
        f'<p><a href="{project_url(name, "artifacts") + "/"}">browse the project folder</a></p></div></section>'
        + f'<section class="card"><div class="card-head"><h2>Danger zone</h2></div><div class="card-body">{delete_form or "<p>locked - mutations disabled</p>"}</div></section>'
    )
    return layout(name, body, autorefresh=status.lock_live_owner is not None)


def render_artifact_listing(name: str, relpath: str, entries: list[tuple[str, bool]]) -> str:
    base = project_url(name, "artifacts")
    rel = relpath.strip("/")
    items = "".join(
        f'<li><a href="{base}/{quote(rel + "/" + entry if rel else entry, safe="/")}">'
        f"{_e(entry)}{'/' if is_dir else ''}</a></li>"
        for entry, is_dir in entries
    )
    up = f'<p><a href="{base}/{quote("/".join(rel.split("/")[:-1]), safe="/")}">..</a></p>' if rel else ""
    body = (
        f'<section class="card"><div class="card-head"><h2>{_e(name)} / {_e(rel or ".")}</h2>'
        f'<a href="{project_url(name)}">dashboard</a></div>'
        f'<div class="card-body">{up}<ul>{items or "<li>(empty)</li>"}</ul></div></section>'
    )
    return layout(f"artifacts - {name}", body)


def render_message(title: str, message: str, *, error: bool = False) -> str:
    klass = "error" if error else "flash"
    body = f'<div class="{klass}">{_e(message)}</div><p><a href="/projects">back to projects</a></p>'
    return layout(title, body)
