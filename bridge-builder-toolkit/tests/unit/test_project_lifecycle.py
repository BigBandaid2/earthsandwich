"""T048 — update / delete / status + suggested-next-step (US7 lifecycle core)."""
import os
from pathlib import Path

import pytest

from common import locking
from project.create import OperatorError, create_project
from project.delete import delete_project
from project.status import stage_status, suggest_next_step
from project.update import update_project

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def env(tmp_path, monkeypatch):
    dsn = f"sqlite:///{(tmp_path / 'target.db').as_posix()}"
    monkeypatch.setenv("LIFECYCLE_TEST_DSN", dsn)
    monkeypatch.setenv("BRIDGE_PROJECTS_DIR", str(tmp_path / "projects"))
    return tmp_path


def _create(name="proj", **overrides):
    kwargs = dict(pile=str(FIXTURES_DIR), pile_files="pile.sample.tsv", target="sqlite://local", target_cred_env="LIFECYCLE_TEST_DSN")
    kwargs.update(overrides)
    return create_project(name, **kwargs)


def test_update_revalidates_and_persists(env):
    _, project_dir = _create()
    project, _ = update_project("proj", pile_sample="head+random:50")
    assert project.pile.sample.size == 50
    assert project.validation.target_reachable          # re-validated


def test_update_failure_leaves_prior_config(env):
    _create()
    before = (env / "projects" / "proj" / "project.yml").read_text(encoding="utf-8")
    with pytest.raises(OperatorError, match="prior config left untouched"):
        update_project("proj", pile=str(env / "missing-dir"))
    after = (env / "projects" / "proj" / "project.yml").read_text(encoding="utf-8")
    assert before == after                               # FR-172: untouched on failure


def test_update_all_reexpands_and_freezes(env):
    _create()
    project, _ = update_project("proj", pile_files="all")
    assert project.pile.files == ["pile.sample.tsv", "pile.sample2.tsv"]


def test_update_requires_an_edit(env):
    _create()
    with pytest.raises(OperatorError, match="nothing to update"):
        update_project("proj")


def test_delete_removes_project(env):
    _, project_dir = _create()
    delete_project("proj")
    assert not project_dir.exists()


def test_delete_refused_while_live_locked(env, monkeypatch):
    _, project_dir = _create()
    (project_dir / locking.LOCK_FILE).write_text("4242", encoding="utf-8")
    monkeypatch.setattr(locking, "_pid_alive", lambda pid: True)
    with pytest.raises(OperatorError, match="locked by live PID 4242"):
        delete_project("proj")
    assert project_dir.exists()                          # FR-177: nothing removed


def _seed_profiling(project_dir: Path, *, pile=True, target=True, index=1):
    it = project_dir / "data-profiling" / f"iteration-{index}"
    it.mkdir(parents=True, exist_ok=True)
    if pile:
        (it / "pile.ydata-profile.html").write_text("x", encoding="utf-8")
    if target:
        (it / "target.ydata-profile.html").write_text("x", encoding="utf-8")


def _seed_mapping(project_dir: Path, *, oracle="validated", index=1):
    it = project_dir / "bridge-mapping" / f"iteration-{index}"
    it.mkdir(parents=True, exist_ok=True)
    (it / "mapping-iteration.yml").write_text(f"index: {index}\noracle_status: {oracle}\n", encoding="utf-8")


def test_suggested_next_step_progression(env):
    """SC-027: fresh → profiled → synthesized → oracle-validated → bundled."""
    _, project_dir = _create()

    primary, alts = suggest_next_step("proj", stage_status(project_dir))
    assert "analyze pile" in primary                     # fresh
    assert any("analyze target" in a for a in alts)

    _seed_profiling(project_dir, target=False)
    primary, _ = suggest_next_step("proj", stage_status(project_dir))
    assert "analyze target" in primary                   # pile done, target not

    _seed_profiling(project_dir)
    primary, _ = suggest_next_step("proj", stage_status(project_dir))
    assert "synthesize bridge" in primary                # both profiled

    _seed_mapping(project_dir, oracle="failed")
    primary, _ = suggest_next_step("proj", stage_status(project_dir))
    assert "iterate" in primary                          # oracle failed

    _seed_mapping(project_dir, oracle="validated", index=2)
    primary, alts = suggest_next_step("proj", stage_status(project_dir))
    assert "review" in primary                           # oracle validated → review primary
    assert any("iterate" in a for a in alts) and any("accept-bundle" in a for a in alts)

    bundle = project_dir / "final-bundle"
    bundle.mkdir()
    (bundle / "bundle.yml").write_text("x", encoding="utf-8")
    primary, _ = suggest_next_step("proj", stage_status(project_dir))
    assert "speckit.specify" in primary                  # bundled


def test_status_reads_lock_liveness(env, monkeypatch):
    _, project_dir = _create()
    assert stage_status(project_dir).lock_live_owner is None
    (project_dir / locking.LOCK_FILE).write_text("4242", encoding="utf-8")
    monkeypatch.setattr(locking, "_pid_alive", lambda pid: True)
    assert stage_status(project_dir).lock_live_owner == 4242
