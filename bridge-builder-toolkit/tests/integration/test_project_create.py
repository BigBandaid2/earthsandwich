"""T013 — US1 acceptance against a real relational target (SC-001, SC-017).

Generic by design: the toolkit has no knowledge of any particular target.
Point ``BRIDGE_TEST_TARGET_DSN`` at any disposable relational database (e.g. a
local Dockerized Postgres) to run this suite; with the variable unset or the
target unreachable, the suite skips with the reason. Credentials are entered as
discrete connection fields + a hidden password prompt and stored in the
gitignored ``.secrets`` (never project.yml, FR-012).
"""
import os
from pathlib import Path
from urllib.parse import urlparse

import pytest
from sqlalchemy import create_engine, text
from typer.testing import CliRunner

import cli

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
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


def _parts(dsn: str) -> dict:
    u = urlparse(dsn)
    return {
        "engine": u.scheme.split("+")[0], "host": u.hostname or "", "port": str(u.port or 5432),
        "database": (u.path or "/").lstrip("/"), "user": u.username or "", "password": u.password or "",
    }


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("BRIDGE_PROJECTS_DIR", str(tmp_path / "projects"))
    return tmp_path


def _target_flags(p: dict) -> list[str]:
    return ["--engine", p["engine"], "--host", p["host"], "--port", p["port"],
            "--database", p["database"], "--user", p["user"]]


def test_valid_create_against_real_target(env):
    """US1 Independent Test, happy path: folder + config + validation report."""
    p = _parts(TEST_DSN)
    result = runner.invoke(cli.app, [
        "project", "create", "sample-pile-to-target",
        "--data-dir", str(FIXTURES_DIR), *_target_flags(p),
    ], input=p["password"] + "\n")
    assert result.exit_code == 0, result.output
    for line in ("pile readable:    yes", "target reachable: yes", "target read:      yes"):
        assert line in result.output                               # FR-007 report
    assert "oracle loop:      will" in result.output               # run-vs-skip recorded

    project_dir = env / "projects" / "sample-pile-to-target"
    persisted = (project_dir / "project.yml").read_text(encoding="utf-8")
    assert "secret_ref: target" in persisted                       # secret marker stored...
    assert "password:" not in persisted                            # ...never a password key (FR-012)
    secrets = (project_dir / ".secrets").read_text(encoding="utf-8")
    assert (project_dir / ".secrets").is_file() and "@" in secrets  # the credentialled DSN lives here, not in yml

    listed = runner.invoke(cli.app, ["project", "list"])
    assert "sample-pile-to-target" in listed.output                # FR-010


def test_wrong_inputs_abort_cleanly_no_state(env):
    """US1 Independent Test, failure path: clear errors, no project state (SC-017)."""
    p = _parts(TEST_DSN)
    # Missing named pile file (fails before the target probe)
    r1 = runner.invoke(cli.app, [
        "project", "create", "broken-pile",
        "--data-dir", str(FIXTURES_DIR), "--pile-files", "nope.tsv", *_target_flags(p),
    ], input=p["password"] + "\n")
    assert r1.exit_code == 1 and "not found" in r1.output

    # Unreachable target (dead port)
    r2 = runner.invoke(cli.app, [
        "project", "create", "broken-target",
        "--data-dir", str(FIXTURES_DIR),
        "--engine", "postgresql", "--host", "localhost", "--port", "59999",
        "--database", "nodb", "--user", "nobody",
    ], input="nope\n")
    assert r2.exit_code == 1 and "no project created" in r2.output

    projects_root = env / "projects"
    assert not (projects_root / "broken-pile").exists()            # FR-008
    assert not (projects_root / "broken-target").exists()
    for r in (r1, r2):
        assert "Traceback" not in r.output
