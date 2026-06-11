"""US1 create/validation path exercised end-to-end against a SQLite target.

The Postgres acceptance run lives in tests/integration/test_project_create.py;
this file proves the same code path (probes, gates, abort-clean, multi-file
pile selection) with no external services, so it always runs.
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
def sqlite_env(tmp_path, monkeypatch):
    dsn = f"sqlite:///{(tmp_path / 'target.db').as_posix()}"
    monkeypatch.setenv("BRIDGE_TEST_DSN", dsn)
    monkeypatch.setenv("BRIDGE_PROJECTS_DIR", str(tmp_path / "projects"))
    return tmp_path


def test_create_validates_and_materializes(sqlite_env):
    project, project_dir = create_project(
        "unit-proj",
        pile=str(FIXTURES_DIR),
        pile_files="pile.sample.tsv",
        target="sqlite://local",
        target_cred_env="BRIDGE_TEST_DSN",
    )
    assert (project_dir / "project.yml").exists()
    assert project.pile.files == ["pile.sample.tsv"]
    v = project.validation
    assert v.pile_readable and v.target_reachable and v.target_read
    assert v.target_insert and v.target_delete and v.oracle_can_run


def test_all_selection_expands_and_freezes(sqlite_env):
    project, project_dir = create_project(
        "all-proj", pile=str(FIXTURES_DIR), pile_files="all",
        target="sqlite://local", target_cred_env="BRIDGE_TEST_DSN",
    )
    assert ".gitkeep" not in project.pile.files
    assert [f for f in project.pile.files if f.endswith(".tsv")] == ALL_FIXTURE_FILES
    persisted = (project_dir / "project.yml").read_text(encoding="utf-8")
    assert "pile.sample2.tsv" in persisted           # frozen EXPLICIT list, not "all"
    assert "files: all" not in persisted


def test_named_missing_file_aborts_with_no_folder(sqlite_env):
    with pytest.raises(OperatorError, match="not found"):
        create_project(
            "missing-file", pile=str(FIXTURES_DIR), pile_files="nope.tsv",
            target="sqlite://local", target_cred_env="BRIDGE_TEST_DSN",
        )
    assert not (sqlite_env / "projects" / "missing-file").exists()


def test_missing_pile_directory_aborts_with_no_folder(sqlite_env):
    with pytest.raises(OperatorError, match="pile directory"):
        create_project(
            "no-pile", pile=str(sqlite_env / "nodir"),
            target="sqlite://local", target_cred_env="BRIDGE_TEST_DSN",
        )
    assert not (sqlite_env / "projects" / "no-pile").exists()      # FR-008


def test_unset_cred_env_aborts_with_no_folder(sqlite_env, monkeypatch):
    monkeypatch.delenv("BRIDGE_TEST_DSN")
    with pytest.raises(OperatorError, match="is not set"):
        create_project(
            "no-env", pile=str(FIXTURES_DIR),
            target="sqlite://local", target_cred_env="BRIDGE_TEST_DSN",
        )
    assert not (sqlite_env / "projects" / "no-env").exists()


def test_non_relational_target_deferred(sqlite_env):
    with pytest.raises(OperatorError, match="deferred"):
        create_project(
            "non-rel", pile=str(FIXTURES_DIR),
            target="https://example.com/schema.json", target_cred_env="BRIDGE_TEST_DSN",
        )


def test_existing_project_needs_force(sqlite_env):
    kwargs = dict(pile=str(FIXTURES_DIR), target="sqlite://local", target_cred_env="BRIDGE_TEST_DSN")
    create_project("dup", **kwargs)
    with pytest.raises(OperatorError, match="--force"):
        create_project("dup", **kwargs)
    create_project("dup", force=True, **kwargs)                     # FR-011


def test_cli_create_and_list(sqlite_env):
    result = runner.invoke(cli.app, [
        "project", "create", "cli-proj",
        "--pile", str(FIXTURES_DIR),
        "--pile-files", "pile.sample.tsv,pile.sample2.tsv",
        "--target", "sqlite://local",
        "--target-cred-env", "BRIDGE_TEST_DSN",
    ])
    assert result.exit_code == 0, result.output
    assert "oracle loop:      will run" in result.output
    assert "2 files" in result.output

    listed = runner.invoke(cli.app, ["project", "list"])
    assert listed.exit_code == 0
    assert "cli-proj" in listed.output and "(2 files)" in listed.output


def test_cli_create_error_is_clean_exit_1(sqlite_env):
    result = runner.invoke(cli.app, [
        "project", "create", "bad",
        "--pile", str(sqlite_env / "nodir"),
        "--target", "sqlite://local",
        "--target-cred-env", "BRIDGE_TEST_DSN",
    ])
    assert result.exit_code == 1
    assert "Traceback" not in result.output                         # SC-017 clean error
    assert "pile directory" in result.output
