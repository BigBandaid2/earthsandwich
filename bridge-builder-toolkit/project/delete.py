"""US7 — project delete: lock-aware, irreversible folder removal (T042, FR-176/177)."""
from __future__ import annotations

import shutil
from pathlib import Path

from common.locking import live_owner
from common.run_logging import close_run_loggers
from project.create import OperatorError, default_projects_dir


def delete_project(name: str, *, projects_dir: Path | None = None) -> Path:
    """Remove ``projects/<name>/`` entirely. Refuses while a live process holds the lock."""
    projects_root = projects_dir or default_projects_dir()
    project_dir = projects_root / name
    if not project_dir.is_dir():
        raise OperatorError(f"no project named {name!r} under {projects_root}")

    owner = live_owner(project_dir)
    if owner is not None:
        raise OperatorError(
            f"project {name!r} is locked by live PID {owner} — an operation is in progress; nothing was removed (FR-177)"
        )

    close_run_loggers(project_dir)   # open run-log handles block rmtree on Windows
    shutil.rmtree(project_dir)
    return project_dir
