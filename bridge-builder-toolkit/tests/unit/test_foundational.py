"""Phase 2 Foundational checkpoint coverage: config, locking, inference, playground."""
import os

import pytest

from common import config, inference, locking, playground


def test_config_round_trip(tmp_path):
    proj = config.BridgeProject(
        name="sample-project",
        slug="sample-project",
        description="## intent\nbridge it",
        created_at="2026-06-10T00:00:00+0000",
        pile=config.PileConfig(
            directories=[config.PileDirectory(path="./data", kind="data", files=["sample-pile.tsv", "sample-pile2.tsv"])],
            kind="file",
            sample=config.PileSample(strategy="head+random", size=200),
        ),
        target=config.TargetConfig(
            kind="relational",
            connection=config.TargetConnection(engine="postgresql", host="db.local", port=5432, database="travelogue", user="writer"),
            secret_ref="target",
        ),
        validation=config.ConnectionValidationResult(
            pile_readable=True, target_reachable=True, target_read=True,
            target_insert=True, target_delete=True, validated_at="2026-06-10T00:00:01+0000",
        ),
    )
    config.save_project(proj, tmp_path)
    loaded = config.load_project(tmp_path)
    assert loaded == proj
    assert loaded.validation.is_creatable
    assert loaded.validation.oracle_can_run
    # the redesign keeps no password in project.yml (FR-012); only a secret marker
    persisted = (tmp_path / config.PROJECT_FILE).read_text(encoding="utf-8")
    assert "secret_ref: target" in persisted and "password" not in persisted


def test_config_round_trips_symmetric_endpoints(tmp_path):
    """A relational pile + a file target round-trip through project.yml (endpoint symmetry)."""
    proj = config.BridgeProject(
        name="db to dir", slug="db-to-dir",
        pile=config.PileConfig(
            kind="relational",
            connection=config.TargetConnection(engine="postgresql", host="src.local", port=5432, database="src", user="reader"),
            secret_ref="pile",
        ),
        target=config.TargetConfig(kind="file", path="../out"),
    )
    config.save_project(proj, tmp_path)
    loaded = config.load_project(tmp_path)
    assert loaded == proj
    assert loaded.pile.kind == "relational" and loaded.pile.connection.database == "src"
    assert loaded.target.kind == "file" and loaded.target.path == "../out"


def test_lock_acquire_release_roundtrip(tmp_path):
    lock = locking.ProjectLock(tmp_path).acquire()
    assert (tmp_path / locking.LOCK_FILE).exists()
    lock.release()
    assert not (tmp_path / locking.LOCK_FILE).exists()


def test_lock_blocks_other_live_owner(tmp_path, monkeypatch):
    (tmp_path / locking.LOCK_FILE).write_text("4242", encoding="utf-8")   # another owner...
    monkeypatch.setattr(locking, "_pid_alive", lambda pid: True)          # ...still alive
    with pytest.raises(locking.LockHeldError):
        locking.ProjectLock(tmp_path).acquire()
    locking.ProjectLock(tmp_path).acquire(force=True)                     # --force overrides
    assert (tmp_path / locking.LOCK_FILE).read_text().strip() == str(os.getpid())


def test_lock_reclaims_stale_pid(tmp_path):
    (tmp_path / locking.LOCK_FILE).write_text("999999999", encoding="utf-8")  # dead PID
    with locking.ProjectLock(tmp_path):
        assert (tmp_path / locking.LOCK_FILE).read_text().strip() == str(os.getpid())


def test_inference_mock_preserves_inputs():
    analyst = inference.AnalystLayer(responder=lambda prompt: "MEX")
    result = analyst.infer("infer_region", "Which region?", {"caption": "Mexico City"})
    assert result.inferred == "MEX"
    assert result.prompt_ref == "infer_region"
    assert result.preserved_inputs == {"caption": "Mexico City"}


def test_playground_build_is_standalone_with_copy_button():
    out = (
        playground.Playground("Pile profile")
        .add_section("Overview", "<p>hi</p>", "ydata-profiling baseline")
        .embed_data("rows", [{"shortcode": "abc"}])
        .build()
    )
    assert out.startswith("<!DOCTYPE html>")
    assert "navigator.clipboard" in out            # clipboard path
    assert 'id="copy-payload"' in out              # selectable-textarea fallback (FR-054)
    assert "ydata-profiling baseline" in out        # provenance label present
    assert "abc" in out                             # inline-embedded data


def test_playground_rejects_unknown_label():
    with pytest.raises(ValueError):
        playground.Playground("x").add_section("h", "b", "made-up-label")
