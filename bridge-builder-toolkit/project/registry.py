"""US1 — ``project list``: every project's name, pile, target, status (T011, FR-010)."""
from __future__ import annotations

from pathlib import Path

from common.config import PROJECT_FILE, BridgeProject, load_project
from project.create import default_projects_dir


def list_projects(projects_dir: Path | None = None) -> list[BridgeProject]:
    root = projects_dir or default_projects_dir()
    if not root.is_dir():
        return []
    projects: list[BridgeProject] = []
    for entry in sorted(root.iterdir()):
        if (entry / PROJECT_FILE).is_file():
            try:
                projects.append(load_project(entry))
            except Exception:
                continue  # unreadable project.yml — skip rather than crash the listing
    return projects


def format_project_lines(projects: list[BridgeProject]) -> str:
    if not projects:
        return "(no projects)"
    lines = []
    for p in projects:
        v = p.validation
        if not (v.pile_readable and v.target_reachable):
            status = "invalid"
        else:
            status = "valid (oracle: run)" if v.oracle_can_run else "valid (oracle: skip)"
        lines.append(f"{p.name}  |  pile: {p.pile.path}  |  target env: {p.target.connection_env}  |  {status}")
    return "\n".join(lines)
