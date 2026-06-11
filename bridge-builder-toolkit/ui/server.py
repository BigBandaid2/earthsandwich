"""FastAPI server for the guided Web UI (T046, FR-170–179).

Routes per contracts/web-ui.md. Every operation calls the same ``project/``
core modules the CLI uses (FR-171); mutations take the per-project lock for the
request only (FR-177); credential values never appear in any page (FR-178);
the artifact route is containment-checked (FR-175).
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from common.config import PROJECT_FILE, load_project
from project.create import OperatorError, create_project, default_projects_dir
from project.delete import delete_project
from project.registry import list_projects
from project.status import stage_status, suggest_next_step
from project.update import update_project
from ui import pages

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def create_app(projects_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="bridge_builder ui", docs_url=None, redoc_url=None, openapi_url=None)
    root = Path(projects_dir) if projects_dir else default_projects_dir()

    def _load(name: str):
        project_dir = root / name
        if not (project_dir / PROJECT_FILE).is_file():
            return None, None
        return load_project(project_dir), project_dir

    def _dashboard(name: str, *, flash: str | None = None, error: str | None = None):
        project, project_dir = _load(name)
        if project is None:
            return HTMLResponse(
                pages.render_message("not found", f"no project named {name!r} — it may have been deleted on disk", error=True),
                status_code=404,
            )
        status = stage_status(project_dir)
        validation_ok = project.validation.pile_readable and project.validation.target_reachable
        primary, alternates = suggest_next_step(name, status, validation_ok=validation_ok)
        return HTMLResponse(pages.render_dashboard(project, status, primary, alternates, flash=flash, error=error))

    @app.get("/")
    def index():
        return RedirectResponse("/projects", status_code=303)

    @app.get("/projects")
    def projects_list():
        return HTMLResponse(pages.render_project_list(list_projects(root)))

    @app.get("/projects/new")
    def project_new_form():
        return HTMLResponse(pages.render_create_form())

    @app.post("/projects")
    def project_create_submit(
        name: str = Form(...),
        pile: str = Form(...),
        target: str = Form(...),
        target_cred_env: str = Form(...),
        pile_sample: str = Form("head+random:200"),
        force: str = Form(""),
    ):
        values = {"name": name, "pile": pile, "target": target,
                  "target_cred_env": target_cred_env, "pile_sample": pile_sample}
        try:
            create_project(
                name.strip(), pile=pile.strip(), target=target.strip(),
                target_cred_env=target_cred_env.strip(), pile_sample=pile_sample.strip(),
                force=bool(force), projects_dir=root,
            )
        except OperatorError as exc:
            return HTMLResponse(pages.render_create_form(error=str(exc), values=values), status_code=400)
        return RedirectResponse(pages.project_url(name.strip()) + "?created=1", status_code=303)

    @app.get("/projects/{name}")
    def project_dashboard(name: str, created: str = "", updated: str = ""):
        flash = None
        if created:
            flash = "project created — validation report below"
        elif updated:
            flash = "project updated — re-validated report below"
        return _dashboard(name, flash=flash)

    @app.get("/projects/{name}/edit")
    def project_edit_form(name: str):
        project, _ = _load(name)
        if project is None:
            return HTMLResponse(pages.render_message("not found", f"no project named {name!r}", error=True), status_code=404)
        return HTMLResponse(pages.render_edit_form(project))

    @app.post("/projects/{name}/update")
    def project_update_submit(
        name: str,
        pile: str = Form(""),
        pile_sample: str = Form(""),
        target_cred_env: str = Form(""),
    ):
        project, _ = _load(name)
        if project is None:
            return HTMLResponse(pages.render_message("not found", f"no project named {name!r}", error=True), status_code=404)
        try:
            update_project(
                name,
                pile=pile.strip() or None,
                pile_sample=pile_sample.strip() or None,
                target_cred_env=target_cred_env.strip() or None,
                projects_dir=root,
            )
        except OperatorError as exc:
            return HTMLResponse(pages.render_edit_form(project, error=str(exc)), status_code=400)
        return RedirectResponse(pages.project_url(name) + "?updated=1", status_code=303)

    @app.post("/projects/{name}/delete")
    def project_delete_submit(name: str, confirm_name: str = Form("")):
        if confirm_name.strip() != name:
            return _dashboard(name, error="deletion refused: typed name does not match the project name")
        try:
            delete_project(name, projects_dir=root)
        except OperatorError as exc:
            return _dashboard(name, error=str(exc))
        return RedirectResponse("/projects", status_code=303)

    @app.get("/projects/{name}/artifacts/{relpath:path}")
    def project_artifact(name: str, relpath: str = ""):
        _, project_dir = _load(name)
        if project_dir is None:
            return HTMLResponse(pages.render_message("not found", f"no project named {name!r}", error=True), status_code=404)
        base = project_dir.resolve()
        candidate = (base / relpath).resolve() if relpath else base
        if candidate != base and base not in candidate.parents:
            return HTMLResponse(
                pages.render_message("refused", "path resolves outside the project folder (FR-175)", error=True),
                status_code=403,
            )
        if candidate.is_dir():
            entries = sorted(
                ((entry.name, entry.is_dir()) for entry in candidate.iterdir()),
                key=lambda item: (not item[1], item[0].lower()),
            )
            return HTMLResponse(pages.render_artifact_listing(name, relpath, entries))
        if candidate.is_file():
            return FileResponse(candidate)
        return HTMLResponse(pages.render_message("not found", f"no such artifact: {relpath}", error=True), status_code=404)

    return app


def run(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """Launch uvicorn; port-in-use surfaces as a clean operator error (FR-170)."""
    import uvicorn

    try:
        uvicorn.run(create_app(), host=host, port=port, log_level="info")
    except (OSError, SystemExit) as exc:
        if isinstance(exc, SystemExit) and not str(exc):
            return
        raise OperatorError(
            f"could not bind {host}:{port} ({exc}) — is the port in use? Try --port <other>"
        ) from exc
