"""FastAPI server for the guided Web UI (b2-ledger redesign, FR-170–185).

Routes per contracts/web-ui.md. Every operation calls the same ``project/`` core
modules the CLI uses (FR-171); mutations take the per-project lock for the request
only (FR-177); credential values never appear in any page or JSON response
(FR-012/FR-178); the artifact route is containment-checked (FR-175). Identity is
the project **slug** (FR-180).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from common.config import PROJECT_FILE, TargetConnection, load_project
from project.create import (
    OperatorError,
    create_project,
    default_projects_dir,
    test_connection,
    writable_dir,
)
from project.delete import delete_project
from project.pile_scan import MEDIA_EXTS, catalogue_media_directory, scan_data_directory
from project.secrets import SECRETS_FILE
from project.registry import list_projects
from project.status import stage_status, suggest_next_step
from project.update import update_project
from ui import pages

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def _human_bytes(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def _media_view(catalogue: dict | None) -> dict:
    cat = catalogue or {}
    types = cat.get("types") or {}
    types_str = " · ".join(f"{ext} {n}" for ext, n in types.items()) or "—"
    return {
        "total": cat.get("count", 0),
        "types": types_str,
        "size": _human_bytes(cat.get("bytes", 0)),
        "ref": "to be matched at profile time",
    }


def _scan_to_dict(scan) -> dict:  # noqa: ANN001
    return {
        "name": scan.name, "valid": scan.valid, "fmt": scan.fmt,
        "rows": scan.rows, "cols": scan.cols, "reason": scan.reason,
    }


def _scan_sources(sources: list[dict]) -> list[dict]:
    """For each {path, kind}, return data file scans or a media catalogue view."""
    out = []
    for s in sources:
        path = (s.get("path") or "").strip()
        kind = s.get("kind") or "data"
        if kind == "media":
            out.append({"kind": "media", "path": path, "media": _media_view(catalogue_media_directory(path))})
        else:
            out.append({"kind": "data", "path": path, "files": [_scan_to_dict(f) for f in scan_data_directory(path)]})
    return out


def _edit_sources(project) -> list[dict]:  # noqa: ANN001
    """Initial form sources for the edit view: existing selection + best-effort dims."""
    out = []
    for d in project.pile.directories:
        if d.kind == "data":
            scans = {f.name: f for f in scan_data_directory(d.path)}
            files = []
            for name in d.files:
                f = scans.get(name)
                if f and f.valid:
                    files.append({"name": name, "valid": True, "fmt": f.fmt, "rows": f.rows, "cols": f.cols, "checked": True})
                else:
                    files.append({"name": name, "valid": True, "fmt": "", "rows": "—", "cols": "—", "checked": True})
            out.append({"path": d.path, "kind": "data", "files": files})
        else:
            out.append({"path": d.path, "kind": "media", "media": _media_view(d.catalogue)})
    return out


def _pile_spec(pile_kind: str, sources: list[dict], conn: dict) -> dict:
    """Build the pile endpoint spec for create/update from form inputs."""
    if pile_kind == "relational":
        return {"kind": "relational", **conn}
    directories, selections = _sources_to_create_args(sources)
    return {"kind": "file", "directories": directories, "selections": selections}


def _target_spec(target_kind: str, conn: dict, target_path: str) -> dict:
    """Build the target endpoint spec for create/update from form inputs."""
    if target_kind == "file":
        return {"kind": "file", "path": (target_path or "").strip()}
    return {"kind": "relational", **conn}


def _sources_to_create_args(sources: list[dict]) -> tuple[list[tuple[str, str]], dict[str, str]]:
    """Map parsed form sources → (directories, selections); drop unselected data dirs."""
    directories: list[tuple[str, str]] = []
    selections: dict[str, str] = {}
    for s in sources:
        path = (s.get("path") or "").strip()
        if not path:
            continue
        if s.get("kind") == "media":
            directories.append((path, "media"))
        else:
            files = [f for f in (s.get("files") or []) if f]
            if not files:
                continue
            directories.append((path, "data"))
            selections[path] = ",".join(files)
    return directories, selections


def create_app(projects_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="bridge_builder ui", docs_url=None, redoc_url=None, openapi_url=None)
    root = Path(projects_dir) if projects_dir else default_projects_dir()

    def _load(slug: str):
        project_dir = root / slug
        if not (project_dir / PROJECT_FILE).is_file():
            return None, None
        return load_project(project_dir), project_dir

    def _not_found(slug: str):
        return HTMLResponse(
            pages.render_message("not found", f"no project with slug {slug!r} — it may have been deleted on disk", error=True),
            status_code=404,
        )

    def _dashboard(slug: str, *, flash: str | None = None, error: str | None = None):
        project, project_dir = _load(slug)
        if project is None:
            return _not_found(slug)
        status = stage_status(project_dir)
        validation_ok = project.validation.pile_readable and project.validation.target_reachable
        primary, alternates = suggest_next_step(project.slug, status, validation_ok=validation_ok)
        return HTMLResponse(pages.render_dashboard(project, status, primary, alternates, flash=flash, error=error))

    @app.get("/")
    def index():
        return RedirectResponse("/projects", status_code=303)

    @app.get("/projects")
    def projects_list():
        return HTMLResponse(pages.render_project_list(list_projects(root)))

    @app.get("/projects/new")
    def project_new_form():
        return HTMLResponse(pages.render_create_form(existing_slugs=[p.slug for p in list_projects(root)]))

    @app.get("/fs")
    def fs_browse(path: str = ""):
        """Server-side directory browser for the pile-source picker (localhost-only UI).

        Returns subdirectories of ``path`` (with shallow data/media file counts) so
        the operator can pick a real on-disk directory; paths are returned relative
        to the server's working directory for movability (FR-110/FR-111).
        """
        cwd = Path.cwd()

        def to_rel(p: Path) -> str:
            try:
                return os.path.relpath(p, cwd).replace(os.sep, "/")
            except ValueError:                          # different drive on Windows
                return str(p).replace(os.sep, "/")

        try:
            target = Path(path).expanduser() if path else cwd
            if not target.is_absolute():
                target = cwd / target
            target = target.resolve()
            if not target.is_dir():
                target = cwd
        except (OSError, RuntimeError):
            target = cwd

        entries = []
        try:
            for child in sorted(target.iterdir(), key=lambda e: e.name.lower()):
                if not child.is_dir() or child.name.startswith("."):
                    continue
                data = media = 0
                try:
                    for f in child.iterdir():
                        if f.is_file() and not f.name.startswith("."):
                            if f.suffix.lower() in MEDIA_EXTS:
                                media += 1
                            else:
                                data += 1
                except OSError:
                    pass
                entries.append({
                    "name": child.name, "rel": to_rel(child),
                    "kind": "media" if media > data else "data", "data": data, "media": media,
                })
        except OSError:
            pass

        parent = target.parent if target.parent != target else None
        return JSONResponse({
            "abs": str(target).replace(os.sep, "/"),
            "rel": to_rel(target),
            "parentRel": to_rel(parent) if parent is not None else None,
            "entries": entries,
        })

    @app.post("/projects/list-files")
    def list_files(sources_json: str = Form("[]")):
        try:
            sources = json.loads(sources_json or "[]")
        except json.JSONDecodeError:
            return JSONResponse([], status_code=400)
        return JSONResponse(_scan_sources(sources))

    @app.post("/projects/test-connection")
    def test_conn(
        engine: str = Form("postgresql"),
        host: str = Form(""),
        port: str = Form("5432"),
        database: str = Form(""),
        user: str = Form(""),
        password: str = Form(""),
    ):
        try:
            connection = TargetConnection(
                engine=engine.strip(), host=host.strip(), port=int(port or 5432),
                database=database.strip(), user=user.strip(),
            )
            reachable, read, insert, delete, note, _dsn = test_connection(connection, password)
        except (OperatorError, ValueError) as exc:
            return JSONResponse({"reachable": False, "note": str(exc)})
        return JSONResponse({
            "reachable": reachable, "read": read, "insert": insert,
            "delete": delete, "oracle": insert and delete, "note": note,
        })

    @app.post("/projects/test-dir")
    def test_dir(path: str = Form("")):
        path = path.strip()
        if not path:
            return JSONResponse({"exists": False, "writable": False, "note": "enter a directory path"})
        exists, writable, note = writable_dir(path)
        return JSONResponse({"exists": exists, "writable": writable, "note": note})

    @app.post("/projects")
    def project_create_submit(
        name: str = Form(""),
        description: str = Form(""),
        sample: str = Form("head+random:200"),
        pile_kind: str = Form("file"),
        sources_json: str = Form("[]"),
        pile_engine: str = Form("postgresql"),
        pile_host: str = Form(""),
        pile_port: str = Form("5432"),
        pile_database: str = Form(""),
        pile_user: str = Form(""),
        pile_password: str = Form(""),
        target_kind: str = Form("relational"),
        engine: str = Form("postgresql"),
        host: str = Form(""),
        port: str = Form("5432"),
        database: str = Form(""),
        user: str = Form(""),
        password: str = Form(""),
        target_path: str = Form(""),
    ):
        values = {
            "name": name, "description": description, "pile_kind": pile_kind, "target_kind": target_kind,
            "pile_engine": pile_engine, "pile_host": pile_host, "pile_port": pile_port,
            "pile_database": pile_database, "pile_user": pile_user,
            "engine": engine, "host": host, "port": port, "database": database, "user": user,
            "target_path": target_path,
        }
        existing = [p.slug for p in list_projects(root)]
        try:
            sources = json.loads(sources_json or "[]")
        except json.JSONDecodeError:
            sources = []
        pile = _pile_spec(pile_kind, sources, {
            "engine": pile_engine.strip(), "host": pile_host.strip(), "port": pile_port.strip() or "5432",
            "database": pile_database.strip(), "user": pile_user.strip(), "password": pile_password,
        })
        target = _target_spec(target_kind, {
            "engine": engine.strip(), "host": host.strip(), "port": port.strip() or "5432",
            "database": database.strip(), "user": user.strip(), "password": password,
        }, target_path)
        try:
            create_project(
                name.strip(), pile=pile, target=target,
                sample=sample.strip() or "head+random:200", description=description, projects_dir=root,
            )
        except OperatorError as exc:
            return HTMLResponse(
                pages.render_create_form(existing_slugs=existing, error=str(exc), values=values, sources=sources),
                status_code=400,
            )
        from common.config import derive_slug
        return RedirectResponse(pages.project_url(derive_slug(name.strip())) + "?created=1", status_code=303)

    @app.get("/projects/{slug}")
    def project_dashboard(slug: str, created: str = "", updated: str = ""):
        flash = None
        if created:
            flash = "project created — validation report below"
        elif updated:
            flash = "project updated — re-validated against the new inputs"
        return _dashboard(slug, flash=flash)

    @app.get("/projects/{slug}/edit")
    def project_edit_form(slug: str):
        project, _ = _load(slug)
        if project is None:
            return _not_found(slug)
        return HTMLResponse(pages.render_edit_form(project, sources=_edit_sources(project)))

    @app.post("/projects/{slug}/update")
    def project_update_submit(
        slug: str,
        description: str = Form(""),
        sample: str = Form(""),
        pile_kind: str = Form("file"),
        sources_json: str = Form("[]"),
        pile_engine: str = Form(""),
        pile_host: str = Form(""),
        pile_port: str = Form(""),
        pile_database: str = Form(""),
        pile_user: str = Form(""),
        pile_password: str = Form(""),
        target_kind: str = Form("relational"),
        engine: str = Form(""),
        host: str = Form(""),
        port: str = Form(""),
        database: str = Form(""),
        user: str = Form(""),
        password: str = Form(""),
        target_path: str = Form(""),
    ):
        project, _ = _load(slug)
        if project is None:
            return _not_found(slug)
        try:
            sources = json.loads(sources_json or "[]")
        except json.JSONDecodeError:
            sources = []
        # Build an endpoint spec only when the form actually carries that endpoint's
        # inputs; otherwise pass None so update_project re-validates it unchanged.
        pile = None
        if pile_kind == "relational" and any(v.strip() for v in (pile_host, pile_database, pile_user, pile_password)):
            pile = _pile_spec("relational", sources, {
                "engine": pile_engine.strip(), "host": pile_host.strip(), "port": pile_port.strip() or None,
                "database": pile_database.strip(), "user": pile_user.strip(), "password": pile_password or None,
            })
        elif any((s.get("path") or "").strip() for s in sources):
            pile = _pile_spec("file", sources, {})
        target = None
        if target_kind == "file" and target_path.strip():
            target = _target_spec("file", {}, target_path)
        elif target_kind == "relational" and any(v.strip() for v in (host, database, user, password)):
            target = _target_spec("relational", {
                "engine": engine.strip(), "host": host.strip(), "port": port.strip() or None,
                "database": database.strip(), "user": user.strip(), "password": password or None,
            }, "")
        try:
            update_project(
                slug, description=description, pile=pile, target=target,
                pile_sample=sample.strip() or None, projects_dir=root,
            )
        except OperatorError as exc:
            project, _ = _load(slug)
            return HTMLResponse(
                pages.render_edit_form(project, sources=sources or _edit_sources(project), error=str(exc)),
                status_code=400,
            )
        return RedirectResponse(pages.project_url(slug) + "?updated=1", status_code=303)

    @app.post("/projects/{slug}/delete")
    def project_delete_submit(slug: str, confirm_name: str = Form("")):
        if confirm_name.strip() != slug:
            return _dashboard(slug, error="deletion refused: typed slug does not match the project slug")
        try:
            delete_project(slug, projects_dir=root)
        except OperatorError as exc:
            return _dashboard(slug, error=str(exc))
        return RedirectResponse("/projects", status_code=303)

    @app.get("/projects/{slug}/artifacts")
    @app.get("/projects/{slug}/artifacts/{relpath:path}")
    def project_artifact(slug: str, relpath: str = ""):
        project, project_dir = _load(slug)
        if project_dir is None:
            return _not_found(slug)
        base = project_dir.resolve()
        candidate = (base / relpath).resolve() if relpath else base
        if candidate != base and base not in candidate.parents:
            return HTMLResponse(
                pages.render_message("refused", "path resolves outside the project folder (FR-175)", error=True),
                status_code=403,
            )
        # The secrets file and other dotfiles are never listed nor served (FR-012/FR-178).
        if any(part.startswith(".") for part in candidate.relative_to(base).parts):
            return HTMLResponse(
                pages.render_message("refused", "credential and dotfiles are not browsable (FR-012/FR-178)", error=True),
                status_code=403,
            )
        if candidate.is_dir():
            entries = []
            for entry in sorted(candidate.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
                if entry.name.startswith(".") or entry.name == SECRETS_FILE:
                    continue
                try:
                    size = entry.stat().st_size if entry.is_file() else 0
                except OSError:
                    size = 0
                entries.append((entry.name, entry.is_dir(), size))
            return HTMLResponse(pages.render_artifact_listing(project, relpath, entries))
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
