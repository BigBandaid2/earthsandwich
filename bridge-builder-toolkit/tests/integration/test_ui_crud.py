"""T050 — US7 acceptance: full UI CRUD pass against a real relational target.

Same generic skip-pattern as test_project_create.py: point
``BRIDGE_TEST_TARGET_DSN`` at any disposable relational database.
"""
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from typer.testing import CliRunner

import cli
from ui.server import create_app

FIXTURE_PILE = Path(__file__).parent.parent / "fixtures" / "pile.sample.tsv"
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


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("UI_CRUD_TARGET_DSN", TEST_DSN)
    monkeypatch.setenv("BRIDGE_PROJECTS_DIR", str(tmp_path / "projects"))
    client = TestClient(create_app(projects_dir=tmp_path / "projects"))
    return client, tmp_path / "projects"


def _descriptor(dsn: str) -> str:
    scheme = dsn.split("://", 1)[0].split("+", 1)[0]
    return f"{scheme}://test-target"


def test_full_ui_crud_pass_and_cli_parity(ctx):
    client, projects = ctx
    form = {
        "name": "ui-crud",
        "pile": str(FIXTURE_PILE),
        "target": _descriptor(TEST_DSN),
        "target_cred_env": "UI_CRUD_TARGET_DSN",
        "pile_sample": "head+random:200",
    }

    # Create via UI → inline validation report
    response = client.post("/projects", data=form, follow_redirects=True)
    assert response.status_code == 200
    assert "pile readable:    yes" in response.text
    assert "target reachable: yes" in response.text

    # SC-026: identical inputs via CLI → identical project.yml (modulo timestamps)
    runner = CliRunner()
    result = runner.invoke(cli.app, [
        "project", "create", "cli-twin",
        "--pile", form["pile"], "--target", form["target"],
        "--target-cred-env", form["target_cred_env"], "--pile-sample", form["pile_sample"],
    ])
    assert result.exit_code == 0, result.output

    def _normalize(name: str) -> str:
        text_ = (projects / name / "project.yml").read_text(encoding="utf-8")
        lines = [
            line for line in text_.splitlines()
            if not line.strip().startswith(("created_at:", "validated_at:"))
        ]
        return "\n".join(lines).replace(name, "<NAME>")

    assert _normalize("ui-crud") == _normalize("cli-twin")          # SC-026

    # Dashboard under the SC-025 render bound with a seeded 10-iteration tree
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

    # Update via UI (re-validates against the live target)
    response = client.post("/projects/ui-crud/update", data={"pile_sample": "head+random:100"}, follow_redirects=True)
    assert response.status_code == 200
    assert "size: 100" in (project_dir / "project.yml").read_text(encoding="utf-8")

    # Delete via UI (typed-name confirm)
    response = client.post("/projects/ui-crud/delete", data={"confirm_name": "ui-crud"}, follow_redirects=False)
    assert response.status_code == 303
    assert not project_dir.exists()
