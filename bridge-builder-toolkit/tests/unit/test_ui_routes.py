"""T049 — UI route behavior via FastAPI TestClient (no live DB; SQLite target).

Exercises the redesigned, endpoint-symmetric forms: pile via ``sources_json``,
target via discrete connection fields (SQLite needs no host/credentials).
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from common import locking
from ui.server import create_app

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
ALL_FILES = ["pile.sample.tsv", "pile.sample2.tsv"]


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    projects = tmp_path / "projects"
    db = (tmp_path / "target.db").as_posix()
    client = TestClient(create_app(projects_dir=projects))
    return client, projects, db


def _create_form(db, name="ui-proj", files=None, **overrides):
    files = ALL_FILES if files is None else files
    sources = [{"path": str(FIXTURES_DIR), "kind": "data", "files": files}]
    form = {
        "name": name, "description": "", "sample": "head+random:200",
        "pile_kind": "file", "sources_json": json.dumps(sources),
        "target_kind": "relational", "engine": "sqlite", "host": "", "port": "5432",
        "database": db, "user": "", "password": "",
    }
    form.update(overrides)
    return form


def test_list_files_endpoint_validates_tables(ctx):
    client, _, _ = ctx
    sources = [{"path": str(FIXTURES_DIR), "kind": "data"}]
    response = client.post("/projects/list-files", data={"sources_json": json.dumps(sources)})
    assert response.status_code == 200
    files = {f["name"]: f for f in response.json()[0]["files"]}
    assert files["pile.sample.tsv"]["valid"] and files["pile.sample.tsv"]["fmt"] == "tsv"


def test_partial_selection_is_frozen(ctx):
    client, projects, db = ctx
    response = client.post("/projects", data=_create_form(db, name="multi", files=["pile.sample2.tsv"]), follow_redirects=True)
    assert response.status_code == 200
    persisted = (projects / "multi" / "project.yml").read_text(encoding="utf-8")
    assert "pile.sample2.tsv" in persisted and "pile.sample.tsv" not in persisted   # frozen partial


def test_nothing_selected_is_inline_error(ctx):
    client, projects, db = ctx
    response = client.post("/projects", data=_create_form(db, name="none-picked", files=[]))
    assert response.status_code == 400 and "valid data file" in response.text
    assert not (projects / "none-picked").exists()


def test_create_all_files_freezes_explicit_list(ctx):
    client, projects, db = ctx
    client.post("/projects", data=_create_form(db, name="all-proj"), follow_redirects=True)
    persisted = (projects / "all-proj" / "project.yml").read_text(encoding="utf-8")
    assert "pile.sample.tsv" in persisted and "pile.sample2.tsv" in persisted
    assert "files: all" not in persisted


def test_root_redirects_to_projects(ctx):
    client, _, _ = ctx
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303 and response.headers["location"] == "/projects"


def test_create_redirects_to_dashboard_with_confirms(ctx):
    client, projects, db = ctx
    response = client.post("/projects", data=_create_form(db), follow_redirects=True)
    assert response.status_code == 200
    assert "Pile valid" in response.text and "Target valid" in response.text       # collapsed confirms
    assert "Suggested next step" in response.text
    assert (projects / "ui-proj" / "project.yml").exists()


def test_unreachable_target_is_inline_error_no_state(ctx):
    client, projects, db = ctx
    form = _create_form(db, name="bad", engine="postgresql", host="localhost", port="59999",
                        database="nodb", user="nobody", password="nope")
    response = client.post("/projects", data=form)
    assert response.status_code == 400 and "no project created" in response.text
    assert not (projects / "bad").exists()                 # FR-008


def test_no_password_persisted_in_project_yml(ctx):
    client, projects, db = ctx
    client.post("/projects", data=_create_form(db))
    persisted = (projects / "ui-proj" / "project.yml").read_text(encoding="utf-8")
    assert "password:" not in persisted                    # FR-012: no password key in project.yml
    assert "secret_ref: target" in persisted               # only a secret marker


def test_dashboard_suggests_analyze_pile(ctx):
    client, _, db = ctx
    client.post("/projects", data=_create_form(db))
    response = client.get("/projects/ui-proj")
    assert "analyze pile" in response.text                  # FR-174 primary CLI command
    assert "Suggested next step" in response.text


def test_update_revalidates_and_redirects(ctx):
    client, projects, db = ctx
    client.post("/projects", data=_create_form(db))
    response = client.post("/projects/ui-proj/update", data={"sample": "head+random:50"}, follow_redirects=True)
    assert response.status_code == 200
    assert "size: 50" in (projects / "ui-proj" / "project.yml").read_text(encoding="utf-8")


def test_update_failure_inline_prior_config_untouched(ctx):
    client, projects, db = ctx
    client.post("/projects", data=_create_form(db))
    before = (projects / "ui-proj" / "project.yml").read_text(encoding="utf-8")
    bad_sources = json.dumps([{"path": "C:/nope/missing-dir", "kind": "data", "files": ["pile.sample.tsv"]}])
    response = client.post("/projects/ui-proj/update", data={"sources_json": bad_sources})
    assert response.status_code == 400 and "prior config left untouched" in response.text
    assert (projects / "ui-proj" / "project.yml").read_text(encoding="utf-8") == before


def test_delete_requires_typed_slug(ctx):
    client, projects, db = ctx
    client.post("/projects", data=_create_form(db))
    response = client.post("/projects/ui-proj/delete", data={"confirm_name": "wrong-slug"})
    assert "typed slug does not match" in response.text
    assert (projects / "ui-proj").exists()
    response = client.post("/projects/ui-proj/delete", data={"confirm_name": "ui-proj"}, follow_redirects=False)
    assert response.status_code == 303
    assert not (projects / "ui-proj").exists()


def test_locked_project_mutations_refused(ctx, monkeypatch):
    client, projects, db = ctx
    client.post("/projects", data=_create_form(db))
    (projects / "ui-proj" / locking.LOCK_FILE).write_text("4242", encoding="utf-8")
    monkeypatch.setattr(locking, "_pid_alive", lambda pid: True)

    dashboard = client.get("/projects/ui-proj")
    assert "operation in progress" in dashboard.text       # FR-177 indicator
    assert "location.reload" in dashboard.text             # FR-173 auto-poll while locked

    response = client.post("/projects/ui-proj/delete", data={"confirm_name": "ui-proj"})
    assert "locked by live PID 4242" in response.text
    assert (projects / "ui-proj").exists()

    response = client.post("/projects/ui-proj/update", data={"sample": "head+random:9"})
    assert response.status_code == 400                     # refused, inline


def test_artifact_traversal_rejected_and_listing_contained(ctx, tmp_path):
    client, projects, db = ctx
    client.post("/projects", data=_create_form(db))
    (tmp_path / "outside.txt").write_text("secret", encoding="utf-8")

    response = client.get("/projects/ui-proj/artifacts/../../outside.txt")
    assert response.status_code in (403, 404)              # FR-175
    assert "secret" not in response.text

    listing = client.get("/projects/ui-proj/artifacts/")
    assert listing.status_code == 200
    assert "project.yml" in listing.text                   # contained listing works


def test_secrets_file_never_browsable(ctx):
    client, projects, db = ctx
    client.post("/projects", data=_create_form(db))
    assert (projects / "ui-proj" / ".secrets").is_file()   # SQLite DSN stored here
    listing = client.get("/projects/ui-proj/artifacts/")
    assert ".secrets" not in listing.text                  # FR-012/FR-178: not listed
    blocked = client.get("/projects/ui-proj/artifacts/.secrets")
    assert blocked.status_code == 403                      # nor served


def test_missing_project_dashboard_is_clean_404(ctx):
    client, _, _ = ctx
    response = client.get("/projects/ghost")
    assert response.status_code == 404
    assert "no project with slug" in response.text         # vanished folder
