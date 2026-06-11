"""T049 — UI route behavior via FastAPI TestClient (no live DB; sqlite DSN)."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from common import locking
from project.create import create_project
from ui.server import create_app

FIXTURE_PILE = Path(__file__).parent.parent / "fixtures" / "pile.sample.tsv"


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    dsn = f"sqlite:///{(tmp_path / 'target.db').as_posix()}"
    monkeypatch.setenv("UI_TEST_DSN", dsn)
    projects = tmp_path / "projects"
    client = TestClient(create_app(projects_dir=projects))
    return client, projects, dsn


def _create_form(name="ui-proj", **overrides):
    form = {
        "name": name,
        "pile": str(FIXTURE_PILE),
        "target": "sqlite://local",
        "target_cred_env": "UI_TEST_DSN",
        "pile_sample": "head+random:200",
    }
    form.update(overrides)
    return form


def test_root_redirects_to_projects(ctx):
    client, _, _ = ctx
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303 and response.headers["location"] == "/projects"


def test_create_via_form_renders_validation_report(ctx):
    client, projects, _ = ctx
    response = client.post("/projects", data=_create_form(), follow_redirects=True)
    assert response.status_code == 200
    assert "pile readable:    yes" in response.text       # FR-007 report inline
    assert "oracle loop:" in response.text
    assert (projects / "ui-proj" / "project.yml").exists()


def test_missing_env_var_is_inline_error_no_state(ctx):
    client, projects, _ = ctx
    response = client.post("/projects", data=_create_form(name="bad", target_cred_env="UNSET_VAR_XYZ"))
    assert response.status_code == 400
    assert "UNSET_VAR_XYZ" in response.text                # names the variable
    assert not (projects / "bad").exists()                 # FR-008 parity


def test_no_dsn_value_in_any_response(ctx):
    client, _, dsn = ctx
    client.post("/projects", data=_create_form())
    for path in ("/projects", "/projects/ui-proj", "/projects/ui-proj/edit"):
        assert dsn not in client.get(path).text            # FR-178


def test_dashboard_suggests_analyze_pile(ctx):
    client, _, _ = ctx
    client.post("/projects", data=_create_form())
    response = client.get("/projects/ui-proj")
    assert "analyze pile" in response.text                 # FR-174 primary
    assert "Suggested next step" in response.text


def test_update_revalidates_and_redirects(ctx):
    client, projects, _ = ctx
    client.post("/projects", data=_create_form())
    response = client.post(
        "/projects/ui-proj/update",
        data={"pile_sample": "head+random:50"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "size: 50" in (projects / "ui-proj" / "project.yml").read_text(encoding="utf-8")


def test_update_failure_inline_prior_config_untouched(ctx):
    client, projects, _ = ctx
    client.post("/projects", data=_create_form())
    before = (projects / "ui-proj" / "project.yml").read_text(encoding="utf-8")
    response = client.post("/projects/ui-proj/update", data={"pile": "C:/nope/missing.tsv"})
    assert response.status_code == 400 and "pile not readable" in response.text
    assert (projects / "ui-proj" / "project.yml").read_text(encoding="utf-8") == before


def test_delete_requires_typed_name(ctx):
    client, projects, _ = ctx
    client.post("/projects", data=_create_form())
    response = client.post("/projects/ui-proj/delete", data={"confirm_name": "wrong-name"})
    assert "typed name does not match" in response.text
    assert (projects / "ui-proj").exists()
    response = client.post("/projects/ui-proj/delete", data={"confirm_name": "ui-proj"}, follow_redirects=False)
    assert response.status_code == 303
    assert not (projects / "ui-proj").exists()


def test_locked_project_mutations_refused(ctx, monkeypatch):
    client, projects, _ = ctx
    client.post("/projects", data=_create_form())
    (projects / "ui-proj" / locking.LOCK_FILE).write_text("4242", encoding="utf-8")
    monkeypatch.setattr(locking, "_pid_alive", lambda pid: True)

    dashboard = client.get("/projects/ui-proj")
    assert "operation in progress" in dashboard.text       # FR-177 indicator + poll
    assert "location.reload" in dashboard.text             # FR-173 auto-poll while locked

    response = client.post("/projects/ui-proj/delete", data={"confirm_name": "ui-proj"})
    assert "locked by live PID 4242" in response.text
    assert (projects / "ui-proj").exists()

    response = client.post("/projects/ui-proj/update", data={"pile_sample": "head+random:9"})
    assert response.status_code == 400                     # refused, inline


def test_artifact_traversal_rejected_and_listing_contained(ctx, tmp_path):
    client, projects, _ = ctx
    client.post("/projects", data=_create_form())
    (tmp_path / "outside.txt").write_text("secret", encoding="utf-8")

    response = client.get("/projects/ui-proj/artifacts/../../outside.txt")
    assert response.status_code in (403, 404)              # FR-175
    assert "secret" not in response.text

    listing = client.get("/projects/ui-proj/artifacts/")
    assert listing.status_code == 200
    assert "project.yml" in listing.text                   # contained listing works


def test_missing_project_dashboard_is_clean_404(ctx):
    client, _, _ = ctx
    response = client.get("/projects/ghost")
    assert response.status_code == 404
    assert "no project named" in response.text             # edge case: vanished folder
