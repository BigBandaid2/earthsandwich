"""US7 — project update: edit + re-validate-then-persist (FR-172/176, symmetric endpoints).

The slug is immutable identity (no rename). Editable: description, both endpoints
(each file or relational), pile selection, and sample spec. Validation re-runs
against the edited inputs BEFORE anything persists; on failure the prior config
(and `.secrets`) is untouched. A relational endpoint's stored DSN is **reused
while its connection is unchanged** — only a changed field requires a re-test +
password re-entry (FR-178).
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from common.config import (
    BridgeProject,
    ConnectionValidationResult,
    PileConfig,
    PileDirectory,
    PileSample,
    TargetConfig,
    load_project,
    save_project,
)
from common.locking import LockHeldError, ProjectLock
from common.run_logging import get_run_logger
from project import secrets as secrets_mod
from project.create import (
    MAX_DESCRIPTION,
    OperatorError,
    _connection_from_spec,
    _parse_sample,
    build_pile,
    catalogue_media_directory,
    default_projects_dir,
    probe_connection,
    resolve_data_directory,
    test_connection,
    writable_dir,
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def _revalidate_existing_pile_dirs(pile: PileConfig, sample: PileSample) -> PileConfig:
    """Re-check the current data/media directories still resolve (FR-006)."""
    dirs: list[PileDirectory] = []
    for d in pile.directories:
        if d.kind == "data":
            files = resolve_data_directory(d.path, ",".join(d.files) if d.files else "all")
            dirs.append(PileDirectory(path=d.path, kind="data", files=files))
        else:
            dirs.append(PileDirectory(path=d.path, kind="media", catalogue=catalogue_media_directory(d.path)))
    return PileConfig(directories=dirs, kind="file", sample=sample)


def _stored_dsn(project_dir: Path, ref: str | None, connection_env: str | None) -> str | None:
    if ref:
        dsn = secrets_mod.load_secrets(project_dir).get(ref)
        if dsn:
            return dsn
    if connection_env:
        return os.environ.get(connection_env)
    return None


def _resolve_relational_update(spec: dict, existing_conn, project_dir: Path, ref: str):
    """Validate a relational endpoint on edit; reuse the stored DSN while unchanged (FR-178).

    Returns (connection, new_secret_dsn|None, probe-dict). Raises OperatorError on
    failure without mutating anything.
    """
    candidate = _connection_from_spec(spec)              # requires engine/host/database/user
    password = spec.get("password") or None
    changed = (candidate != existing_conn) or (password is not None)
    if changed:
        if password is None:
            raise OperatorError("changing the connection requires re-entering the password (FR-178)")
        reachable, read, insert, delete, note, dsn = test_connection(candidate, password)
        return candidate, dsn, {"reachable": reachable, "read": read, "insert": insert, "delete": delete, "note": note}
    stored = secrets_mod.load_secrets(project_dir).get(ref)
    if not stored:
        raise OperatorError("stored credentials are missing — re-enter the connection")
    reachable, read, insert, delete, note = probe_connection(stored)
    return candidate, None, {"reachable": reachable, "read": read, "insert": insert, "delete": delete, "note": note}


def update_project(
    slug: str,
    *,
    description: str | None = None,
    pile: dict | None = None,
    target: dict | None = None,
    pile_sample: str | None = None,
    projects_dir: Path | None = None,
) -> tuple[BridgeProject, Path]:
    """Apply edits, re-validate both endpoints, persist only on success (FR-172).

    ``pile`` / ``target`` are endpoint specs (``{"kind": "file"|"relational", ...}``)
    or ``None`` to re-validate the existing endpoint unchanged.
    """
    projects_root = projects_dir or default_projects_dir()
    project_dir = projects_root / slug
    if not (project_dir / "project.yml").is_file():
        raise OperatorError(f"no project with slug {slug!r} under {projects_root}")

    lock = ProjectLock(project_dir)
    try:
        lock.acquire()
    except LockHeldError as exc:
        raise OperatorError(f"{exc} — an operation is in progress; try again when it finishes (FR-177)")
    try:
        project = load_project(project_dir)
        if description is not None:
            if len(description) > MAX_DESCRIPTION:
                raise OperatorError(f"description exceeds {MAX_DESCRIPTION} characters — prior config left untouched")
            project.description = description
        sample = _parse_sample(pile_sample) if pile_sample is not None else project.pile.sample

        secrets_to_write: dict[str, str] = {}

        # ---- PILE endpoint ----
        try:
            pile_readable = _apply_pile(project, project_dir, pile, sample, secrets_to_write)
        except OperatorError as exc:
            raise OperatorError(f"{exc} — prior config left untouched" if "untouched" not in str(exc) else str(exc))

        # ---- TARGET endpoint ----
        probe = _apply_target(project, project_dir, target, secrets_to_write)

        oracle_note = "" if (probe["insert"] and probe["delete"]) else "oracle loop will be skipped - no insert/delete permission (FR-075)"
        project.validation = ConnectionValidationResult(
            pile_readable=pile_readable, target_reachable=probe["reachable"], target_read=probe["read"],
            target_insert=probe["insert"], target_delete=probe["delete"], validated_at=_now(),
            notes="; ".join(filter(None, [probe["note"], oracle_note])),
        )

        save_project(project, project_dir)
        for ref, dsn in secrets_to_write.items():
            secrets_mod.write_secret(project_dir, ref, dsn)
        logger, _ = get_run_logger(project_dir, "project-update")
        logger.info("project %s updated; validation: %s", slug, project.validation)
    finally:
        lock.release()
    return project, project_dir


def _apply_pile(project, project_dir, pile, sample, secrets_to_write) -> bool:  # noqa: ANN001
    """Mutate project.pile; return pile_readable. Raises on failure."""
    if pile is not None:
        kind = pile.get("kind", project.pile.kind)
        if kind == "file":
            project.pile = build_pile(pile.get("directories") or [], pile.get("selections") or {}, sample)
            return True
        conn, new_secret, probe = _resolve_relational_update(pile, project.pile.connection, project_dir, "pile")
        if not (probe["reachable"] and probe["read"]):
            raise OperatorError(f"pile database not readable: {probe['note'] or 'unreachable'}")
        project.pile = PileConfig(directories=[], kind="relational", sample=sample, connection=conn, secret_ref="pile")
        if new_secret:
            secrets_to_write["pile"] = new_secret
        return True
    # re-validate existing pile unchanged
    if project.pile.kind == "file":
        project.pile = _revalidate_existing_pile_dirs(project.pile, sample)
        return True
    stored = _stored_dsn(project_dir, project.pile.secret_ref or "pile", project.pile.connection_env)
    if not stored:
        raise OperatorError("stored pile credentials are missing — re-enter the connection")
    reachable, read, _i, _d, _n = probe_connection(stored)
    if not (reachable and read):
        raise OperatorError("pile database unreachable")
    project.pile.sample = sample
    return True


def _apply_target(project, project_dir, target, secrets_to_write) -> dict:  # noqa: ANN001
    """Mutate project.target; return probe-dict. Raises on failure (prior config untouched)."""
    if target is not None:
        kind = target.get("kind", project.target.kind)
        if kind == "file":
            path = (target.get("path") or "").strip()
            if not path:
                raise OperatorError("file target requires an output directory — prior config left untouched")
            exists, writable, note = writable_dir(path)
            if not writable:
                raise OperatorError(f"{note or 'target directory not writable'} — prior config left untouched")
            project.target = TargetConfig(kind="file", path=path)
            return {"reachable": True, "read": exists, "insert": False, "delete": False, "note": note}
        conn, new_secret, probe = _resolve_relational_update(target, project.target.connection, project_dir, "target")
        if not probe["reachable"]:
            raise OperatorError(f"{probe['note'] or 'target unreachable'} — prior config left untouched")
        project.target = TargetConfig(kind="relational", connection=conn, secret_ref="target")
        if new_secret:
            secrets_to_write["target"] = new_secret
        return probe
    # re-validate existing target unchanged
    if project.target.kind == "file":
        exists, writable, note = writable_dir(project.target.path or "")
        if not writable:
            raise OperatorError(f"{note or 'target directory not writable'} — prior config left untouched")
        return {"reachable": True, "read": exists, "insert": False, "delete": False, "note": note}
    stored = _stored_dsn(project_dir, project.target.secret_ref or "target", project.target.connection_env)
    if not stored:
        raise OperatorError("stored target credentials are missing — re-enter the connection")
    reachable, read, insert, delete, note = probe_connection(stored)
    if not reachable:
        raise OperatorError(f"{note or 'target unreachable'} — prior config left untouched")
    return {"reachable": reachable, "read": read, "insert": insert, "delete": delete, "note": note}
