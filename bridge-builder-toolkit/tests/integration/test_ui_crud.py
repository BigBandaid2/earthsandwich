"""T050 — US7 acceptance: full UI CRUD pass against a real relational target.

Same generic skip-pattern as test_project_create.py: point
``BRIDGE_TEST_TARGET_DSN`` at any disposable relational database.
"""
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from typer.testing import CliRunner

import cli
from ui.server import create_app

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
TEST_DSN = os.environ.get("BRIDGE_TEST_TARGET_DSN", "")


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
    reason="set BRIDGE_TEST_TARGET_DSN to a reachable, disposable relational DSN to run the US7 acceptance suite",
)


def _parts(dsn: str) -> dict:
    u = urlparse(dsn)
    return {
        "engine": u.scheme.split("+")[0], "host": u.hostname or "", "port": str(u.port or 5432),
        "database": (u.path or "/").lstrip("/"), "user": u.username or "", "password": u.password or "",
    }


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("BRIDGE_PROJECTS_DIR", str(tmp_path / "projects"))
    projects = tmp_path / "projects"
    client = TestClient(create_app(projects_dir=projects))
    return client, projects


def test_full_ui_crud_pass_and_cli_parity(ctx):
    client, projects = ctx
    p = _parts(TEST_DSN)
    sources = [{"path": str(FIXTURES_DIR), "kind": "data", "files": ["pile.sample.tsv", "pile.sample2.tsv"]}]
    form = {
        "name": "ui-crud", "description": "", "sample": "head+random:200",
        "pile_kind": "file", "sources_json": json.dumps(sources),
        "target_kind": "relational", "engine": p["engine"], "host": p["host"], "port": p["port"],
        "database": p["database"], "user": p["user"], "password": p["password"],
    }

    # Create via UI → dashboard confirms
    response = client.post("/projects", data=form, follow_redirects=True)
    assert response.status_code == 200, response.text
    assert "Pile valid" in response.text and "Target valid" in response.text

    # SC-026: identical inputs via CLI → identical project.yml (modulo timestamps + slug)
    runner = CliRunner()
    result = runner.invoke(cli.app, [
        "project", "create", "cli-twin",
        "--data-dir", str(FIXTURES_DIR), "--pile-files", "pile.sample.tsv,pile.sample2.tsv",
        "--engine", p["engine"], "--host", p["host"], "--port", p["port"],
        "--database", p["database"], "--user", p["user"],
    ], input=p["password"] + "\n")
    assert result.exit_code == 0, result.output

    def _normalize(slug: str) -> str:
        text_ = (projects / slug / "project.yml").read_text(encoding="utf-8")
        lines = [
            line for line in text_.splitlines()
            if not line.strip().startswith(("created_at:", "validated_at:"))
        ]
        return "\n".join(lines).replace(slug, "<NAME>")

    assert _normalize("ui-crud") == _normalize("cli-twin")          # SC-026
    # neither project.yml carries a password key (FR-012)
    for slug in ("ui-crud", "cli-twin"):
        assert "password:" not in (projects / slug / "project.yml").read_text(encoding="utf-8")

    # Dashboard under the SC-025 render bound with a seeded iteration tree
    project_dir = projects / "ui-crud"
    for index in range(1, 6):
        it = project_dir / "data-profiling" / f"iteration-{index}"
        it.mkdir(parents=True)
        (it / "pile.ydata-profile.html").write_text("x", encoding="utf-8")
        (it / "target.ydata-profile.html").write_text("x", encoding="utf-8")
    for index in range(1, 6):
        it = project_dir / "bridge-mapping" / f"iteration-{index}"
        it.mkdir(parents=True)
        (it / "mapping-iteration.yml").write_text(f"index: {index}\noracle_status: validated\n", encoding="utf-8")
    start = time.monotonic()
    response = client.get("/projects/ui-crud")
    elapsed = time.monotonic() - start
    assert response.status_code == 200 and elapsed < 2.0            # SC-025
    assert "review" in response.text                                # validated → review primary

    # Update via UI (re-validates against the live target, reusing the stored DSN)
    response = client.post("/projects/ui-crud/update", data={"sample": "head+random:100"}, follow_redirects=True)
    assert response.status_code == 200
    assert "size: 100" in (project_dir / "project.yml").read_text(encoding="utf-8")

    # Delete via UI (typed-slug confirm)
    response = client.post("/projects/ui-crud/delete", data={"confirm_name": "ui-crud"}, follow_redirects=False)
    assert response.status_code == 303
    assert not project_dir.exists()
