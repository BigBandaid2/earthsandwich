"""T013 — US1 acceptance against a real relational target (SC-001, SC-017).

Generic by design: the toolkit has no knowledge of any particular target.
Point ``BRIDGE_TEST_TARGET_DSN`` at any disposable relational database (e.g. a
local Dockerized Postgres) to run this suite; with the variable unset or the
target unreachable, the suite skips with the reason.
"""
import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from typer.testing import CliRunner

import cli

FIXTURE_PILE = Path(__file__).parent.parent / "fixtures" / "pile.sample.tsv"
TEST_DSN = os.environ.get("BRIDGE_TEST_TARGET_DSN", "")
runner = CliRunner()


def _reachable(dsn: str) -> bool:
    if not dsn:
        return False
    try:
        engine = create_engine(dsn)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _reachable(TEST_DSN),
    reason="set BRIDGE_TEST_TARGET_DSN to a reachable, disposable relational DSN to run the US1 acceptance suite",
)


def _descriptor(dsn: str) -> str:
    """Credential-free, relational-shaped --target descriptor from the test DSN."""
    scheme = dsn.split("://", 1)[0].split("+", 1)[0]
    return f"{scheme}://test-target"


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("SAMPLE_PROJECT_TARGET_DSN", TEST_DSN)
    monkeypatch.setenv("BRIDGE_PROJECTS_DIR", str(tmp_path / "projects"))
    return tmp_path


def test_valid_create_against_real_target(env):
    """US1 Independent Test, happy path: folder + config + validation report."""
    result = runner.invoke(cli.app, [
        "project", "create", "sample-pile-to-target",
        "--pile", str(FIXTURE_PILE),
        "--target", _descriptor(TEST_DSN),
        "--target-cred-env", "SAMPLE_PROJECT_TARGET_DSN",
    ])
    assert result.exit_code == 0, result.output
    for line in ("pile readable:    yes", "target reachable: yes", "target read:      yes"):
        assert line in result.output                               # FR-007 report
    assert "oracle loop:      will" in result.output               # run-vs-skip recorded

    project_dir = env / "projects" / "sample-pile-to-target"
    assert (project_dir / "project.yml").exists()
    persisted = (project_dir / "project.yml").read_text(encoding="utf-8")
    assert "SAMPLE_PROJECT_TARGET_DSN" in persisted                # env-var NAME stored...
    assert TEST_DSN not in persisted                               # ...never the secret (FR-012)

    listed = runner.invoke(cli.app, ["project", "list"])
    assert "sample-pile-to-target" in listed.output                # FR-010


def test_wrong_inputs_abort_cleanly_no_state(env, monkeypatch):
    """US1 Independent Test, failure path: clear errors, no project state (SC-017)."""
    # Unreadable pile
    r1 = runner.invoke(cli.app, [
        "project", "create", "broken-pile",
        "--pile", str(env / "nope.tsv"),
        "--target", _descriptor(TEST_DSN),
        "--target-cred-env", "SAMPLE_PROJECT_TARGET_DSN",
    ])
    assert r1.exit_code == 1 and "pile not readable" in r1.output

    # Unreachable target (dead port)
    monkeypatch.setenv("DEAD_TARGET_DSN", "postgresql+psycopg://nobody:nope@localhost:59999/nodb")
    r2 = runner.invoke(cli.app, [
        "project", "create", "broken-target",
        "--pile", str(FIXTURE_PILE),
        "--target", "postgresql://dead-target",
        "--target-cred-env", "DEAD_TARGET_DSN",
    ])
    assert r2.exit_code == 1 and "no project created" in r2.output

    projects_root = env / "projects"
    assert not (projects_root / "broken-pile").exists()            # FR-008
    assert not (projects_root / "broken-target").exists()
    for r in (r1, r2):
        assert "Traceback" not in r.output
