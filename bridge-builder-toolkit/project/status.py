"""US7 — derived stage status + suggested next step (T043, FR-173/174).

Everything here is a pure READ of the on-disk structures defined in
data-model.md — no parallel state is kept. ``suggest_next_step`` returns ONE
primary copyable CLI command plus labeled alternates (Clarification 2026-06-10).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from common.locking import live_owner

_ITERATION_RE = re.compile(r"iteration-(\d+)$")


@dataclass
class ProjectStageStatus:
    profiling_iterations: int = 0
    pile_profiled: bool = False        # latest profiling iteration has pile artifacts
    target_profiled: bool = False      # latest profiling iteration has target artifacts
    mapping_iterations: int = 0
    latest_oracle_status: str | None = None   # validated | failed | skipped | None
    bundle_present: bool = False
    lock_live_owner: int | None = None
    review_sessions: int = 0
    alternates: list[str] = field(default_factory=list)


def _iteration_dirs(loop_dir: Path) -> list[Path]:
    if not loop_dir.is_dir():
        return []
    found = []
    for entry in loop_dir.iterdir():
        match = _ITERATION_RE.search(entry.name)
        if entry.is_dir() and match:
            found.append((int(match.group(1)), entry))
    return [path for _, path in sorted(found)]


def _latest_oracle_status(iteration_dir: Path) -> str | None:
    meta = iteration_dir / "mapping-iteration.yml"
    if meta.is_file():
        try:
            status = (yaml.safe_load(meta.read_text(encoding="utf-8")) or {}).get("oracle_status")
            if status:
                return str(status)
        except Exception:
            pass
    result = iteration_dir / "oracle.result.json"
    if result.is_file():
        try:
            data = json.loads(result.read_text(encoding="utf-8"))
            if not data.get("ran", False):
                return "skipped"
            return "validated" if data.get("passed") else "failed"
        except Exception:
            return None
    return None


def stage_status(project_dir: str | Path) -> ProjectStageStatus:
    project_dir = Path(project_dir)
    status = ProjectStageStatus()

    profiling = _iteration_dirs(project_dir / "data-profiling")
    status.profiling_iterations = len(profiling)
    if profiling:
        latest = profiling[-1]
        status.pile_profiled = (latest / "pile.ydata-profile.html").is_file()
        status.target_profiled = (latest / "target.ydata-profile.html").is_file()

    mapping = _iteration_dirs(project_dir / "bridge-mapping")
    status.mapping_iterations = len(mapping)
    if mapping:
        latest_map = mapping[-1]
        status.latest_oracle_status = _latest_oracle_status(latest_map)
        review_dir = latest_map / "review"
        if review_dir.is_dir():
            status.review_sessions = len(list(review_dir.glob("session-*.summary.json")))

    bundle = project_dir / "final-bundle"
    status.bundle_present = bundle.is_dir() and any(bundle.iterdir())
    status.lock_live_owner = live_owner(project_dir)
    return status


def suggest_next_step(name: str, status: ProjectStageStatus, *, validation_ok: bool = True) -> tuple[str, list[str]]:
    """Return (primary_command, alternates) for the project's stage state (FR-174)."""
    proj = f'--project "{name}"'

    if not validation_ok:
        return (f'bridge_builder project update "{name}"', [])
    if status.bundle_present:
        return ("# Final Bundle ready - hand final-bundle/ to /speckit.specify", [f"bridge_builder review {proj} ..."])
    if not (status.pile_profiled and status.target_profiled):
        if status.pile_profiled:
            return (f"bridge_builder analyze target {proj}", [])
        if status.target_profiled:
            return (f"bridge_builder analyze pile {proj}", [])
        return (f"bridge_builder analyze pile {proj}", [f"bridge_builder analyze target {proj}"])
    if status.mapping_iterations == 0:
        return (f"bridge_builder synthesize bridge {proj}", [])
    if status.latest_oracle_status == "failed":
        return (f"bridge_builder iterate {proj} --feedback <path>", [f"bridge_builder synthesize bridge {proj}"])
    # oracle validated or skipped: review is the primary; iterate / accept-bundle are real options
    return (
        f"bridge_builder review {proj} --baseline truth-baseline/baseline.tsv --join-key <col>",
        [f"bridge_builder iterate {proj} --feedback <path>", f"bridge_builder accept-bundle {proj}"],
    )
