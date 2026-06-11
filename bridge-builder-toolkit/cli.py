"""bridge-builder-toolkit CLI — one subcommand per stage (FR-004).

Entry point: ``bridge_builder`` (after ``pip install -e .``) or ``python cli.py``
(dev). Stage commands are registered here as stubs; each is fleshed out and wired
in its own user-story phase. See ``specs/004-bridge-builder-toolkit/contracts/cli.md``.
"""
from __future__ import annotations

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


@project_app.command("create")
def project_create(
    name: str = typer.Argument(..., help="Project name (unique per installation)."),
    pile: str = typer.Option(..., "--pile", help="Path to the pile (a local file-based data deposit, e.g. a TSV)."),
    target: str = typer.Option(..., "--target", help="Target endpoint descriptor (relational DSN shape; never persisted)."),
    target_cred_env: str = typer.Option(..., "--target-cred-env", help="ENV VAR NAME holding the target DSN (FR-012)."),
    pile_sample: str = typer.Option("head+random:200", "--pile-sample", help="Pile sampling spec '<strategy>:<size>'."),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing project (FR-011)."),
) -> None:
    """Create a named project and validate its pile + target connections (US1)."""
    from project.create import OperatorError, create_project, format_validation_report

    try:
        project, project_dir = create_project(
            name, pile=pile, target=target, target_cred_env=target_cred_env,
            pile_sample=pile_sample, force=force,
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


@analyze_app.command("pile")
def analyze_pile() -> None:
    """Profile the pile: ydata baseline + enhanced playground (US2)."""
    _stub("analyze pile")


@analyze_app.command("target")
def analyze_target() -> None:
    """Profile the target: ydata + ER diagram + enhanced playground (US2)."""
    _stub("analyze target")


@synthesize_app.command("bridge")
def synthesize_bridge() -> None:
    """Synthesize the pile-to-target mapping + dbt project + output (US3)."""
    _stub("synthesize bridge")


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
