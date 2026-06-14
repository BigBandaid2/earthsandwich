"""T048 — update / delete / status + suggested-next-step (US7 lifecycle core).

SQLite target keeps these external-service-free; the slug is the project identity.
"""
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
    monkeypatch.setenv("BRIDGE_PROJECTS_DIR", str(tmp_path / "projects"))
    return tmp_path


def _file_pile(selection="pile.sample.tsv"):
    return {"kind": "file", "directories": [(str(FIXTURES_DIR), "data")], "selections": {str(FIXTURES_DIR): selection}}


def _create(env, name="proj", **overrides):
    pile = overrides.pop("pile", _file_pile())
    target = overrides.pop("target", {"kind": "relational", "engine": "sqlite", "database": (env / "target.db").as_posix()})
    return create_project(name, pile=pile, target=target, **overrides)


def test_update_revalidates_and_persists(env):
    _, project_dir = _create(env)
    project, _ = update_project("proj", pile_sample="head+random:50")
    assert project.pile.sample.size == 50
    assert project.validation.target_reachable          # re-validated


def test_update_failure_leaves_prior_config(env):
    _create(env)
    before = (env / "projects" / "proj" / "project.yml").read_text(encoding="utf-8")
    bad = {"kind": "file", "directories": [(str(env / "missing-dir"), "data")], "selections": {str(env / "missing-dir"): "all"}}
    with pytest.raises(OperatorError, match="prior config left untouched"):
        update_project("proj", pile=bad)
    after = (env / "projects" / "proj" / "project.yml").read_text(encoding="utf-8")
    assert before == after                               # FR-172: untouched on failure


def test_update_all_reexpands_and_freezes(env):
    _create(env)
    project, _ = update_project("proj", pile=_file_pile("all"))
    assert project.pile.directories[0].files == ["pile.sample.tsv", "pile.sample2.tsv"]


def test_update_unchanged_revalidates_idempotently(env):
    _, project_dir = _create(env)
    before = (project_dir / "project.yml").read_text(encoding="utf-8")
    project, _ = update_project("proj")                  # no edits → re-validate existing, persist
    assert project.validation.target_reachable
    # only validated_at may move; the pile/target shape is unchanged
    assert "pile.sample.tsv" in (project_dir / "project.yml").read_text(encoding="utf-8")


def test_switch_target_to_file_endpoint(env):
    _create(env)
    out = env / "switched-out"
    project, _ = update_project("proj", target={"kind": "file", "path": str(out)})
    assert project.target.kind == "file" and out.is_dir()
    assert not project.validation.oracle_can_run         # file target → oracle skips


def test_delete_removes_project(env):
    _, project_dir = _create(env)
    delete_project("proj")
    assert not project_dir.exists()


def test_delete_refused_while_live_locked(env, monkeypatch):
    _, project_dir = _create(env)
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
    _, project_dir = _create(env)

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
    _, project_dir = _create(env)
    assert stage_status(project_dir).lock_live_owner is None
    (project_dir / locking.LOCK_FILE).write_text("4242", encoding="utf-8")
    monkeypatch.setattr(locking, "_pid_alive", lambda pid: True)
    assert stage_status(project_dir).lock_live_owner == 4242
