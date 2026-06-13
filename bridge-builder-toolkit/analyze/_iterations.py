"""Data-profiling iteration allocation + profiling.yml bookkeeping (data-model.md).

The data-profiling loop has its own preserved history: ``analyze pile`` and
``analyze target`` share an iteration while each side's raw artifact is still
missing; a re-run of an already-present side opens the next iteration
(origin ``operator-rerun``). Each iteration records a fingerprint of the pile
state it saw, so pile evolution is auditable.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from common.config import BridgeProject

LOOP_DIR = "data-profiling"
_ITER_RE = re.compile(r"iteration-(\d+)$")

PILE_RAW = "pile.ydata-profile.html"
TARGET_RAW = "target.ydata-profile.html"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def pile_fingerprint(project: BridgeProject, project_dir: Path) -> dict:
    """Row count + content hash over the selected pile files (data-model.md)."""
    digest = hashlib.sha256()
    rows = 0
    for dpath, fname in project.pile.data_files():       # across all data directories
        fpath = Path(dpath) / fname
        digest.update(f"{dpath}/{fname}".encode("utf-8"))
        with fpath.open("rb") as fh:
            content = fh.read()
        digest.update(content)
        rows += max(0, content.count(b"\n") - 1)        # data rows, headers excluded
    return {"rows": rows, "content_sha256": digest.hexdigest(), "observed_at": _now()}


def _iteration_dirs(project_dir: Path) -> list[tuple[int, Path]]:
    loop = project_dir / LOOP_DIR
    if not loop.is_dir():
        return []
    found = []
    for entry in loop.iterdir():
        match = _ITER_RE.search(entry.name)
        if entry.is_dir() and match:
            found.append((int(match.group(1)), entry))
    return sorted(found)


def allocate_iteration(project: BridgeProject, project_dir: Path, side_raw_artifact: str) -> Path:
    """Return the iteration dir this side should write into (creating it if needed)."""
    iterations = _iteration_dirs(project_dir)
    if iterations:
        index, latest = iterations[-1]
        if not (latest / side_raw_artifact).exists():
            return latest                                # other side started this iteration
        index += 1
        origin = "operator-rerun"
    else:
        index, origin = 1, "initial"

    iteration_dir = project_dir / LOOP_DIR / f"iteration-{index}"
    iteration_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "index": index,
        "origin": origin,
        "created_at": _now(),
        "pile_fingerprint": pile_fingerprint(project, project_dir),
        "driving_feedback": None,
        "artifacts": {"raw": [], "enhanced": []},
    }
    (iteration_dir / "profiling.yml").write_text(
        yaml.safe_dump(meta, sort_keys=False), encoding="utf-8"
    )
    return iteration_dir


def record_artifacts(iteration_dir: Path, *, raw: list[str] = (), enhanced: list[str] = ()) -> None:
    meta_path = iteration_dir / "profiling.yml"
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
    artifacts = meta.setdefault("artifacts", {"raw": [], "enhanced": []})
    for name in raw:
        if name not in artifacts["raw"]:
            artifacts["raw"].append(name)
    for name in enhanced:
        if name not in artifacts["enhanced"]:
            artifacts["enhanced"].append(name)
    meta_path.write_text(yaml.safe_dump(meta, sort_keys=False), encoding="utf-8")
