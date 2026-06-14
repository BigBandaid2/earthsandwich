"""bridge-builder-toolkit CLI — one subcommand per stage (FR-004).

Entry point: ``bridge_builder`` (after ``pip install -e .``) or ``python cli.py``
(dev). Stage commands are registered here as stubs; each is fleshed out and wired
in its own user-story phase. See ``specs/004-bridge-builder-toolkit/contracts/cli.md``.
"""
from __future__ import annotations

from typing import List, Optional

import typer

app = typer.Typer(
    name="bridge_builder",
    help="Produce validated bridge specifications from a pile + target schema.",
    no_args_is_help=True,
    add_completion=False,
)

project_app = typer.Typer(help="Create and list bridge projects (US1).", no_args_is_help=True)
analyze_app = typer.Typer(help="Profile the pile and the target schema (US2).", no_args_is_help=True)
synthesize_app = typer.Typer(help="Synthesize the pile-to-target bridge mapping (US3).", no_args_is_help=True)

app.add_typer(project_app, name="project")
app.add_typer(analyze_app, name="analyze")
app.add_typer(synthesize_app, name="synthesize")

_NOT_IMPLEMENTED = "stage not yet implemented - wired in its user-story phase"


def _stub(stage: str) -> None:
    """Placeholder body for an unimplemented stage. Exit 1 = operator-correctable."""
    typer.echo(f"[bridge_builder] {stage}: {_NOT_IMPLEMENTED}")
    raise typer.Exit(code=1)


def _prompt_password(label: str, engine: str) -> str:
    """Hidden password prompt for a relational endpoint; file engines need none (FR-012)."""
    from project.create import FILE_ENGINES

    if engine in FILE_ENGINES:
        return ""
    return typer.prompt(label, hide_input=True, default="", show_default=False)


def _pile_spec_cli(pile_kind, data_dir, media_dir, pile_files, conn) -> dict:
    if pile_kind == "relational":
        return {"kind": "relational", **conn}
    directories = [(d, "data") for d in (data_dir or [])] + [(d, "media") for d in (media_dir or [])]
    selections = {d: pile_files for d in (data_dir or [])}
    return {"kind": "file", "directories": directories, "selections": selections}


@project_app.command("create")
def project_create(
    name: str = typer.Argument(..., help="Project name (its slug is the immutable identity, FR-180)."),
    description: str = typer.Option("", "--description", help="Markdown intent (≤4000 chars, FR-181)."),
    pile_kind: str = typer.Option("file", "--pile-kind", help="Pile endpoint kind: file | relational."),
    data_dir: List[str] = typer.Option([], "--data-dir", help="Pile data directory (repeatable; file pile)."),
    media_dir: List[str] = typer.Option([], "--media-dir", help="Pile media directory (repeatable; file pile)."),
    pile_files: str = typer.Option("all", "--pile-files", help="Data-file selection per data dir: names, or 'all' (frozen)."),
    pile_sample: str = typer.Option("head+random:200", "--pile-sample", help="Pile sampling spec '<strategy>:<size>'."),
    pile_engine: str = typer.Option("postgresql", "--pile-engine", help="Relational pile engine."),
    pile_host: str = typer.Option("", "--pile-host"),
    pile_port: int = typer.Option(5432, "--pile-port"),
    pile_database: str = typer.Option("", "--pile-database"),
    pile_user: str = typer.Option("", "--pile-user"),
    target_kind: str = typer.Option("relational", "--target-kind", help="Target endpoint kind: relational | file."),
    engine: str = typer.Option("postgresql", "--engine", help="Relational target engine."),
    host: str = typer.Option("", "--host"),
    port: int = typer.Option(5432, "--port"),
    database: str = typer.Option("", "--database"),
    user: str = typer.Option("", "--user"),
    target_path: str = typer.Option("", "--target-path", help="Output directory for a file target."),
) -> None:
    """Create a project and validate its pile + target endpoints (US1; either may be file or relational)."""
    from project.create import OperatorError, create_project, format_validation_report

    pile_conn = {"engine": pile_engine, "host": pile_host, "port": pile_port, "database": pile_database,
                 "user": pile_user, "password": _prompt_password("Pile database password", pile_engine) if pile_kind == "relational" else ""}
    pile = _pile_spec_cli(pile_kind, data_dir, media_dir, pile_files, pile_conn)
    if target_kind == "file":
        target = {"kind": "file", "path": target_path}
    else:
        target = {"kind": "relational", "engine": engine, "host": host, "port": port, "database": database,
                  "user": user, "password": _prompt_password("Target database password", engine)}
    try:
        project, project_dir = create_project(
            name, pile=pile, target=target, sample=pile_sample, description=description,
        )
    except OperatorError as exc:
        typer.echo(f"[bridge_builder] error: {exc}")
        raise typer.Exit(code=1)
    typer.echo(format_validation_report(project))
    typer.echo(f"created: {project_dir}")


@project_app.command("list")
def project_list() -> None:
    """List projects with their pile, target, and validation status (US1)."""
    from project.registry import format_project_lines, list_projects

    typer.echo(format_project_lines(list_projects()))


@project_app.command("update")
def project_update(
    slug: str = typer.Argument(..., help="Project slug to update (identity is immutable)."),
    description: Optional[str] = typer.Option(None, "--description", help="Replace the intent text."),
    pile_sample: Optional[str] = typer.Option(None, "--pile-sample", help="New sampling spec '<strategy>:<size>'."),
    pile_kind: Optional[str] = typer.Option(None, "--pile-kind", help="Switch/restate the pile kind: file | relational."),
    data_dir: List[str] = typer.Option([], "--data-dir", help="Replacement pile data directory (repeatable)."),
    media_dir: List[str] = typer.Option([], "--media-dir", help="Replacement pile media directory (repeatable)."),
    pile_files: str = typer.Option("all", "--pile-files", help="Data-file selection for the replacement dirs."),
    pile_engine: str = typer.Option("postgresql", "--pile-engine"),
    pile_host: str = typer.Option("", "--pile-host"),
    pile_port: int = typer.Option(5432, "--pile-port"),
    pile_database: str = typer.Option("", "--pile-database"),
    pile_user: str = typer.Option("", "--pile-user"),
    target_kind: Optional[str] = typer.Option(None, "--target-kind", help="Switch/restate the target kind: relational | file."),
    engine: str = typer.Option("postgresql", "--engine"),
    host: str = typer.Option("", "--host"),
    port: int = typer.Option(5432, "--port"),
    database: str = typer.Option("", "--database"),
    user: str = typer.Option("", "--user"),
    target_path: str = typer.Option("", "--target-path"),
) -> None:
    """Edit a project and re-validate before persisting (US7). Omitted endpoints are re-validated unchanged."""
    from project.create import OperatorError, format_validation_report
    from project.update import update_project

    pile = None
    if pile_kind is not None or data_dir or media_dir:
        kind = pile_kind or "file"
        conn = {"engine": pile_engine, "host": pile_host, "port": pile_port, "database": pile_database,
                "user": pile_user, "password": _prompt_password("Pile database password", pile_engine) if kind == "relational" else ""}
        pile = _pile_spec_cli(kind, data_dir, media_dir, pile_files, conn)
    target = None
    if target_kind is not None:
        if target_kind == "file":
            target = {"kind": "file", "path": target_path}
        else:
            target = {"kind": "relational", "engine": engine, "host": host, "port": port, "database": database,
                      "user": user, "password": _prompt_password("Target database password", engine)}
    try:
        project, _ = update_project(
            slug, description=description, pile=pile, target=target, pile_sample=pile_sample,
        )
    except OperatorError as exc:
        typer.echo(f"[bridge_builder] error: {exc}")
        raise typer.Exit(code=1)
    typer.echo(format_validation_report(project))
    typer.echo("updated.")


@project_app.command("delete")
def project_delete(
    name: str = typer.Argument(..., help="Project to delete (irreversible)."),
    yes: bool = typer.Option(False, "--yes", help="Skip the confirmation prompt."),
) -> None:
    """Delete a project folder entirely - irreversible (US7)."""
    from project.create import OperatorError
    from project.delete import delete_project

    if not yes:
        typer.confirm(
            f"Delete project {name!r} and ALL its history (iterations, truth baseline, bundle)?",
            abort=True,
        )
    try:
        removed = delete_project(name)
    except OperatorError as exc:
        typer.echo(f"[bridge_builder] error: {exc}")
        raise typer.Exit(code=1)
    typer.echo(f"deleted: {removed}")


def _run_analysis(project_name: str, side: str) -> None:
    """Shared lock-acquire + error-mapping shell for the analyze commands."""
    from analyze import PriorArtError
    from common.config import load_project
    from common.locking import LockHeldError, ProjectLock
    from project.create import OperatorError, default_projects_dir

    project_dir = default_projects_dir() / project_name
    if not (project_dir / "project.yml").is_file():
        typer.echo(f"[bridge_builder] error: no project named {project_name!r}")
        raise typer.Exit(code=1)
    try:
        with ProjectLock(project_dir):
            project = load_project(project_dir)
            if side == "pile":
                from analyze.pile import run_pile_analysis as run
            else:
                from analyze.target import run_target_analysis as run
            artifacts = run(project, project_dir)
    except LockHeldError as exc:
        typer.echo(f"[bridge_builder] error: {exc}")
        raise typer.Exit(code=1)
    except OperatorError as exc:
        typer.echo(f"[bridge_builder] error: {exc}")
        raise typer.Exit(code=1)
    except PriorArtError as exc:
        typer.echo(f"[bridge_builder] prior-art failure: {exc}")
        raise typer.Exit(code=2)
    typer.echo(f"analyze {side}: {artifacts['iteration']}")
    for key, path in artifacts.items():
        if key != "iteration":
            typer.echo(f"  {key}: {path.name}")


@analyze_app.command("pile")
def analyze_pile(
    project: str = typer.Option(..., "--project", help="Project name."),
) -> None:
    """Profile the pile: ydata baseline + enhanced playground (US2)."""
    _run_analysis(project, "pile")


@analyze_app.command("target")
def analyze_target(
    project: str = typer.Option(..., "--project", help="Project name."),
) -> None:
    """Profile the target: ydata + ER diagram + enhanced playground (US2)."""
    _run_analysis(project, "target")


@synthesize_app.command("bridge")
def synthesize_bridge() -> None:
    """Synthesize the pile-to-target mapping + dbt project + output (US3)."""
    _stub("synthesize bridge")


@app.command("ui")
def ui(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind address (localhost by default; FR-170)."),
    port: int = typer.Option(8765, "--port", help="Port for the local UI server."),
) -> None:
    """Launch the guided local Web UI for project CRUD + dashboards (US7)."""
    from project.create import OperatorError
    from ui.server import run

    typer.echo(f"[bridge_builder] ui: http://{host}:{port}  (Ctrl+C to stop)")
    try:
        run(host=host, port=port)
    except OperatorError as exc:
        typer.echo(f"[bridge_builder] error: {exc}")
        raise typer.Exit(code=1)


@app.command("iterate")
def iterate() -> None:
    """Apply a feedback payload and produce a new iteration (US5)."""
    _stub("iterate")


@app.command("accept-bundle")
def accept_bundle() -> None:
    """Materialize the Final Bundle from a chosen iteration (US5)."""
    _stub("accept-bundle")


@app.command("review")
def review() -> None:
    """Review bridge output against a truth baseline (US6)."""
    _stub("review")


if __name__ == "__main__":
    app()
