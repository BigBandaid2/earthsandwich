"""US1 create/validation path against a SQLite target — no external services.

SQLite is a file-based relational engine, so the full probe path (read + DML +
oracle gate) runs with no Postgres. The Postgres acceptance run lives in
tests/integration/test_project_create.py. Endpoint symmetry (file/relational on
either side) is exercised here too.
"""
from pathlib import Path

import pytest
from typer.testing import CliRunner

import cli
from project.create import OperatorError, create_project

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
ALL_FIXTURE_FILES = ["pile.sample.tsv", "pile.sample2.tsv"]
runner = CliRunner()


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("BRIDGE_PROJECTS_DIR", str(tmp_path / "projects"))
    return tmp_path


def _sqlite_target(tmp_path) -> dict:
    return {"kind": "relational", "engine": "sqlite",
            "database": (tmp_path / "target.db").as_posix()}


def _file_pile(selection="all") -> dict:
    return {"kind": "file", "directories": [(str(FIXTURES_DIR), "data")],
            "selections": {str(FIXTURES_DIR): selection}}


def test_create_validates_and_materializes(env):
    project, project_dir = create_project(
        "unit-proj", pile=_file_pile("pile.sample.tsv"), target=_sqlite_target(env),
    )
    assert (project_dir / "project.yml").exists()
    assert project.slug == "unit-proj"
    assert project.pile.directories[0].files == ["pile.sample.tsv"]
    v = project.validation
    assert v.pile_readable and v.target_reachable and v.target_read
    assert v.target_insert and v.target_delete and v.oracle_can_run
    # the DSN lives only in .secrets; project.yml records no password (FR-012)
    assert "password" not in (project_dir / "project.yml").read_text(encoding="utf-8")
    assert (project_dir / ".secrets").is_file()


def test_all_selection_expands_and_freezes(env):
    project, project_dir = create_project("all-proj", pile=_file_pile("all"), target=_sqlite_target(env))
    files = project.pile.directories[0].files
    assert ".gitkeep" not in files
    assert [f for f in files if f.endswith(".tsv")] == ALL_FIXTURE_FILES
    persisted = (project_dir / "project.yml").read_text(encoding="utf-8")
    assert "pile.sample2.tsv" in persisted           # frozen EXPLICIT list, not "all"
    assert "files: all" not in persisted


def test_named_missing_file_aborts_with_no_folder(env):
    with pytest.raises(OperatorError, match="not found"):
        create_project("missing-file", pile=_file_pile("nope.tsv"), target=_sqlite_target(env))
    assert not (env / "projects" / "missing-file").exists()


def test_missing_pile_directory_aborts_with_no_folder(env):
    bad = {"kind": "file", "directories": [(str(env / "nodir"), "data")], "selections": {}}
    with pytest.raises(OperatorError, match="data directory"):
        create_project("no-pile", pile=bad, target=_sqlite_target(env))
    assert not (env / "projects" / "no-pile").exists()      # FR-008


def test_no_selected_data_file_aborts(env):
    empty = {"kind": "file", "directories": [], "selections": {}}
    with pytest.raises(OperatorError, match="valid data file"):
        create_project("empty-pile", pile=empty, target=_sqlite_target(env))
    assert not (env / "projects" / "empty-pile").exists()


def test_unreachable_target_aborts_with_no_folder(env):
    dead = {"kind": "relational", "engine": "postgresql", "host": "localhost",
            "port": 59999, "database": "nodb", "user": "nobody", "password": "nope"}
    with pytest.raises(OperatorError, match="no project created"):
        create_project("dead-target", pile=_file_pile(), target=dead)
    assert not (env / "projects" / "dead-target").exists()


def test_slug_collision_refused_no_overwrite(env):
    create_project("dup", pile=_file_pile(), target=_sqlite_target(env))
    with pytest.raises(OperatorError, match="already exists"):       # FR-011/FR-180, no --force
        create_project("dup", pile=_file_pile(), target=_sqlite_target(env))


def test_file_target_validates_as_writable_dir(env):
    out = env / "bridge-out"
    project, project_dir = create_project(
        "file-target", pile=_file_pile(), target={"kind": "file", "path": str(out)},
    )
    assert out.is_dir() and project.target.kind == "file"
    assert project.validation.target_reachable and not project.validation.oracle_can_run
    assert not (project_dir / ".secrets").is_file()                  # no relational endpoint → no secret


def test_relational_pile_stores_pile_secret(env):
    project, project_dir = create_project(
        "db-pile", pile=_sqlite_target(env) | {"kind": "relational"},
        target={"kind": "file", "path": str(env / "out2")},
    )
    assert project.pile.kind == "relational"
    import yaml
    secrets = yaml.safe_load((project_dir / ".secrets").read_text(encoding="utf-8"))
    assert set(secrets) == {"pile"}                                  # pile DSN, no target


def test_cli_create_and_list(env):
    result = runner.invoke(cli.app, [
        "project", "create", "cli-proj",
        "--data-dir", str(FIXTURES_DIR), "--pile-files", "pile.sample.tsv,pile.sample2.tsv",
        "--engine", "sqlite", "--database", (env / "target.db").as_posix(),
    ])
    assert result.exit_code == 0, result.output
    assert "oracle loop:      will run" in result.output
    assert "2 data files" in result.output

    listed = runner.invoke(cli.app, ["project", "list"])
    assert listed.exit_code == 0
    assert "cli-proj" in listed.output and "2 data files" in listed.output


def test_cli_create_error_is_clean_exit_1(env):
    result = runner.invoke(cli.app, [
        "project", "create", "bad",
        "--data-dir", str(env / "nodir"),
        "--engine", "sqlite", "--database", (env / "target.db").as_posix(),
    ])
    assert result.exit_code == 1
    assert "Traceback" not in result.output                         # SC-017 clean error
    assert "data directory" in result.output
