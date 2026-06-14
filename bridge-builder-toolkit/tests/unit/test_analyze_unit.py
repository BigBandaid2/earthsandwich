"""US2 unit coverage: sampling, iteration allocation, introspection, error gates."""
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

import analyze.pile as pile_mod
import analyze.target as target_mod
from analyze import PriorArtError
from analyze._iterations import PILE_RAW, TARGET_RAW, allocate_iteration, pile_fingerprint
from analyze.introspect import reflect_schema
from analyze.pile import load_pile_frame, run_pile_analysis, sample_frame
from common.inference import AnalystLayer
from project.create import OperatorError, create_project

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
STUB_ANALYST = AnalystLayer(responder=lambda prompt: "## stub analysis\n- finding")


@pytest.fixture
def env(tmp_path, monkeypatch):
    dsn = f"sqlite:///{(tmp_path / 'target.db').as_posix()}"
    monkeypatch.setenv("ANALYZE_TEST_DSN", dsn)
    monkeypatch.setenv("BRIDGE_PROJECTS_DIR", str(tmp_path / "projects"))
    engine = create_engine(dsn)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE stops (id INTEGER PRIMARY KEY, name TEXT NOT NULL, region_code TEXT)"))
        conn.execute(text(
            "CREATE TABLE posts (id INTEGER PRIMARY KEY, stop_id INTEGER REFERENCES stops(id), caption TEXT)"
        ))
    engine.dispose()
    return tmp_path


def _project(env, name="ana-proj"):
    return create_project(
        name,
        pile={"kind": "file", "directories": [(str(FIXTURES_DIR), "data")], "selections": {str(FIXTURES_DIR): "all"}},
        target={"kind": "relational", "engine": "sqlite", "database": (env / "target.db").as_posix()},
    )


def test_load_pile_frame_concatenates_with_source_file(env):
    project, _ = _project(env)
    frame = load_pile_frame(project)
    assert "source_file" in frame.columns
    assert set(frame["source_file"]) == {"pile.sample.tsv", "pile.sample2.tsv"}
    assert len(frame) == 5                                  # 3 + 2 fixture rows


def test_sampling_is_deterministic():
    frame = pd.DataFrame({"value": range(100)})
    first = sample_frame(frame, "head+random", 10)
    second = sample_frame(frame, "head+random", 10)
    assert len(first) == 10
    assert first["value"].tolist() == second["value"].tolist()
    assert first["value"].tolist()[:5] == [0, 1, 2, 3, 4]   # head half


def test_iteration_allocation_shares_then_advances(env):
    project, project_dir = _project(env)
    first = allocate_iteration(project, project_dir, PILE_RAW)
    assert first.name == "iteration-1"
    (first / PILE_RAW).write_text("x", encoding="utf-8")

    same = allocate_iteration(project, project_dir, TARGET_RAW)   # other side joins iteration-1
    assert same == first
    (same / TARGET_RAW).write_text("x", encoding="utf-8")

    rerun = allocate_iteration(project, project_dir, PILE_RAW)    # re-run opens iteration-2
    assert rerun.name == "iteration-2"


def test_fingerprint_changes_with_pile_content(env, tmp_path):
    project, project_dir = _project(env)
    before = pile_fingerprint(project, project_dir)
    assert before["rows"] == 5 and before["content_sha256"]

    clone_dir = tmp_path / "pile-clone"
    clone_dir.mkdir()
    for f in project.pile.directories[0].files:
        (clone_dir / f).write_text((FIXTURES_DIR / f).read_text(encoding="utf-8") + "extra\trow\n", encoding="utf-8")
    project.pile.directories[0].path = str(clone_dir)
    after = pile_fingerprint(project, project_dir)
    assert after["content_sha256"] != before["content_sha256"]


def test_reflect_schema_reads_pk_fk_notnull(env):
    import os

    schema = reflect_schema(os.environ["ANALYZE_TEST_DSN"])
    tables = {t["name"]: t for t in schema["tables"]}
    assert set(tables) == {"stops", "posts"}
    stops_cols = {c["name"]: c for c in tables["stops"]["columns"]}
    assert stops_cols["id"]["primary_key"] is True
    assert stops_cols["name"]["nullable"] is False
    assert any("stops" in fk["references"] for fk in tables["posts"]["foreign_keys"])


def test_ydata_failure_is_prior_art_error_no_enhanced(env, monkeypatch):
    project, project_dir = _project(env)

    import ydata_profiling

    class Boom:
        def __init__(self, *a, **k):
            raise RuntimeError("ydata exploded")

    monkeypatch.setattr(ydata_profiling, "ProfileReport", Boom)
    with pytest.raises(PriorArtError, match="FR-105"):
        run_pile_analysis(project, project_dir, analyst=STUB_ANALYST)
    iteration = project_dir / "data-profiling" / "iteration-1"
    assert not (iteration / "pile.enhanced.html").exists()  # never fabricated


def test_missing_graphviz_is_operator_error(env, monkeypatch):
    monkeypatch.delenv("BRIDGE_GRAPHVIZ_DOT", raising=False)
    monkeypatch.setattr(target_mod.shutil, "which", lambda name: None)
    monkeypatch.setattr(target_mod, "_DOT_FALLBACKS", ())
    with pytest.raises(OperatorError, match="GraphViz"):
        target_mod._find_dot()


def test_missing_api_key_is_operator_error(env, monkeypatch):
    project, project_dir = _project(env, "no-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(OperatorError, match="ANTHROPIC_API_KEY"):
        run_pile_analysis(project, project_dir, analyst=None)
