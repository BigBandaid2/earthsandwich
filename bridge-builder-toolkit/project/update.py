"""US7 — project update: edit + re-validate-then-persist (T041, FR-172/176).

The project NAME is immutable identity (no rename). Editable: pile path, pile
sample spec, credential env-var name. Connection validation re-runs against the
edited inputs BEFORE anything persists; on any failed gate the prior config is
left untouched.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from common.config import BridgeProject, ConnectionValidationResult, load_project, save_project
from common.locking import LockHeldError, ProjectLock
from common.run_logging import get_run_logger
from project.create import (
    OperatorError,
    _parse_sample,
    default_projects_dir,
    probe_pile,
    probe_target,
)


def update_project(
    name: str,
    *,
    pile: str | None = None,
    pile_sample: str | None = None,
    target_cred_env: str | None = None,
    projects_dir: Path | None = None,
) -> tuple[BridgeProject, Path]:
    """Apply edits, re-validate, persist only on success (FR-172)."""
    projects_root = projects_dir or default_projects_dir()
    project_dir = projects_root / name
    if not (project_dir / "project.yml").is_file():
        raise OperatorError(f"no project named {name!r} under {projects_root}")

    if pile is None and pile_sample is None and target_cred_env is None:
        raise OperatorError("nothing to update — pass at least one of --pile / --pile-sample / --target-cred-env")

    lock = ProjectLock(project_dir)
    try:
        lock.acquire()
    except LockHeldError as exc:
        raise OperatorError(f"{exc} — an operation is in progress; try again when it finishes (FR-177)")
    try:
        project = load_project(project_dir)

        # Apply edits to an in-memory candidate; disk stays untouched until validation passes.
        if pile is not None:
            project.pile.path = pile
        if pile_sample is not None:
            project.pile.sample = _parse_sample(pile_sample)
        if target_cred_env is not None:
            project.target.connection_env = target_cred_env

        dsn = os.environ.get(project.target.connection_env, "")
        if not dsn:
            raise OperatorError(
                f"env var {project.target.connection_env!r} is not set; export the target DSN there "
                "(credentials are never stored or passed on the CLI, FR-012)"
            )

        if not probe_pile(Path(project.pile.path)):
            raise OperatorError(f"pile not readable: {project.pile.path} — prior config left untouched")

        reachable, read, insert, delete, note = probe_target(dsn)
        if not reachable:
            raise OperatorError(f"{note or 'target unreachable'} — prior config left untouched")

        oracle_note = "" if (insert and delete) else "oracle loop will be skipped - no insert/delete permission (FR-075)"
        project.validation = ConnectionValidationResult(
            pile_readable=True,
            target_reachable=True,
            target_read=read,
            target_insert=insert,
            target_delete=delete,
            validated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z"),
            notes="; ".join(filter(None, [note, oracle_note])),
        )

        save_project(project, project_dir)
        logger, _ = get_run_logger(project_dir, "project-update")
        logger.info("project %r updated; validation: %s", name, project.validation)
    finally:
        lock.release()
    return project, project_dir
