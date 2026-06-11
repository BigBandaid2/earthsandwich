"""T018 — US2 acceptance: pile + target analyses against a real relational target.

Generic by design (no host-project fore-knowledge): point
``BRIDGE_TEST_TARGET_DSN`` at any disposable relational database. The
LLM-analyst layer is stubbed — no API key or network needed. ER rendering
requires GraphViz; that single assertion skips with a reason when absent.
"""
import os
from pathlib import Path

import pytest
import yaml
from sqlalchemy import create_engine, text

from analyze.pile import run_pile_analysis
from analyze.target import _find_dot, run_target_analysis
from common.inference import AnalystLayer
from project.create import OperatorError, create_project
from project.status import stage_status, suggest_next_step

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
TEST_DSN = os.environ.get("BRIDGE_TEST_TARGET_DSN", "")
STUB_ANALYST = AnalystLayer(responder=lambda prompt: "## ranked candidates\n1. stops - locations match")


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
    reason="set BRIDGE_TEST_TARGET_DSN to a reachable, disposable relational DSN to run the US2 acceptance suite",
)


def _graphviz_available() -> bool:
    try:
        _find_dot()
        return True
    except OperatorError:
        return False


@pytest.fixture
def project_env(tmp_path, monkeypatch):
    monkeypatch.setenv("ANALYZE_TARGET_DSN", TEST_DSN)
    monkeypatch.setenv("BRIDGE_PROJECTS_DIR", str(tmp_path / "projects"))
    project, project_dir = create_project(
        "analysis-acceptance", pile=str(FIXTURES_DIR), pile_files="all",
        target="postgresql://test-target", target_cred_env="ANALYZE_TARGET_DSN",
    )
    return project, project_dir


def test_us2_independent_test(project_env):
    """Both sides profiled into iteration-1; labels present; raw baselines canonical."""
    project, project_dir = project_env

    pile_artifacts = run_pile_analysis(project, project_dir, analyst=STUB_ANALYST)
    iteration = pile_artifacts["iteration"]
    assert iteration.name == "iteration-1"
    assert (iteration / "pile.ydata-profile.html").stat().st_size > 10_000   # real ydata output

    enhanced = (iteration / "pile.enhanced.html").read_text(encoding="utf-8")
    assert "ydata-profiling baseline" in enhanced                            # SC-006 labels
    assert "LLM-extended" in enhanced and "toolkit-novel" in enhanced
    assert "ER-diagram baseline" not in enhanced                             # FR-027: TSV pile, no ER
    assert "preserved_inputs" in enhanced                                    # Principle V in embedded data

    if _graphviz_available():
        target_artifacts = run_target_analysis(project, project_dir, analyst=STUB_ANALYST)
        assert target_artifacts["iteration"] == iteration                    # same profiling iteration
        assert (iteration / "target.er-diagram.svg").stat().st_size > 0      # SC-004 raw ER
        target_enhanced = (iteration / "target.enhanced.html").read_text(encoding="utf-8")
        assert "ER-diagram baseline" in target_enhanced
        assert "ranked candidates" in target_enhanced                        # FR-026
    else:
        pytest.skip("GraphViz dot not available - ER-dependent half skipped")

    meta = yaml.safe_load((iteration / "profiling.yml").read_text(encoding="utf-8"))
    assert meta["index"] == 1 and meta["origin"] == "initial"
    assert meta["pile_fingerprint"]["rows"] == 5
    assert "pile.ydata-profile.html" in meta["artifacts"]["raw"]

    # The dashboard's stage detection sees both sides -> synthesize is next.
    status = stage_status(project_dir)
    assert status.pile_profiled and status.target_profiled
    primary, _ = suggest_next_step(project.name, status)
    assert "synthesize bridge" in primary
