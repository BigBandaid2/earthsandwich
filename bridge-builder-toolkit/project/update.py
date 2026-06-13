"""US7 — project update: edit + re-validate-then-persist (FR-172/176, redesigned).

The slug is immutable identity (no rename). Editable: description, pile
directories/selection, sample spec, target connection. Validation re-runs
against the edited inputs BEFORE anything persists; on failure the prior config
(and `.secrets`) is untouched. The stored DSN is **reused while the connection
is unchanged** — only a changed connection field requires a re-test + password
re-entry (FR-178).
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from common.config import (
    BridgeProject,
    ConnectionValidationResult,
    PileConfig,
    PileDirectory,
    PileSample,
    TargetConfig,
    TargetConnection,
    load_project,
    save_project,
)
from common.locking import LockHeldError, ProjectLock
from common.run_logging import get_run_logger
from project import secrets as secrets_mod
from project.create import (
    MAX_DESCRIPTION,
    OperatorError,
    _parse_sample,
    build_pile,
    catalogue_media_directory,
    default_projects_dir,
    probe_connection,
    resolve_data_directory,
    test_connection,
)


def _revalidate_existing_pile(pile: PileConfig, sample: PileSample) -> PileConfig:
    """Re-check the current directories/selection still resolve (FR-006)."""
    dirs: list[PileDirectory] = []
    for d in pile.directories:
        if d.kind == "data":
            files = resolve_data_directory(d.path, ",".join(d.files) if d.files else "all")
            dirs.append(PileDirectory(path=d.path, kind="data", files=files))
        else:
            dirs.append(PileDirectory(path=d.path, kind="media", catalogue=catalogue_media_directory(d.path)))
    return PileConfig(directories=dirs, kind=pile.kind, sample=sample)


def update_project(
    slug: str,
    *,
    description: str | None = None,
    directories: list[tuple[str, str]] | None = None,
    selections: dict[str, str] | None = None,
    pile_sample: str | None = None,
    engine: str | None = None,
    host: str | None = None,
    port: int | str | None = None,
    database: str | None = None,
    user: str | None = None,
    password: str | None = None,
    projects_dir: Path | None = None,
) -> tuple[BridgeProject, Path]:
    """Apply edits, re-validate, persist only on success (FR-172)."""
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

        # Pile: rebuild from supplied directories, else re-validate the existing ones.
        try:
            if directories is not None:
                project.pile = build_pile(directories, selections or {}, sample)
            else:
                project.pile = _revalidate_existing_pile(project.pile, sample)
        except OperatorError as exc:
            raise OperatorError(f"{exc} — prior config left untouched")

        # Connection: reuse the stored DSN while unchanged; re-test on any change (FR-178).
        existing = project.target.connection
        candidate = existing
        if any(v is not None for v in (engine, host, port, database, user)) and existing is not None:
            candidate = replace(
                existing,
                engine=engine or existing.engine, host=host or existing.host,
                port=int(port) if port is not None else existing.port,
                database=database or existing.database, user=user or existing.user,
            )
        connection_changed = (candidate != existing) or (password is not None)

        new_secret_dsn: str | None = None
        if connection_changed:
            if candidate is None:
                raise OperatorError("target connection requires engine, host, database and user")
            if password is None:
                raise OperatorError("changing the connection requires re-entering the password (FR-178)")
            reachable, read, insert, delete, note, new_secret_dsn = test_connection(candidate, password)
            project.target = TargetConfig(kind="relational", connection=candidate, secret_ref="target")
        else:
            dsn = secrets_mod.resolve_target_dsn(project, project_dir)
            if not dsn:
                raise OperatorError("stored target credentials are missing — re-enter the connection")
            reachable, read, insert, delete, note = probe_connection(dsn)
        if not reachable:
            raise OperatorError(f"{note or 'target unreachable'} — prior config left untouched")

        oracle_note = "" if (insert and delete) else "oracle loop will be skipped - no insert/delete permission (FR-075)"
        project.validation = ConnectionValidationResult(
            pile_readable=True, target_reachable=True, target_read=read,
            target_insert=insert, target_delete=delete,
            validated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z"),
            notes="; ".join(filter(None, [note, oracle_note])),
        )

        save_project(project, project_dir)
        if new_secret_dsn is not None:
            secrets_mod.write_secret(project_dir, "target", new_secret_dsn)
        logger, _ = get_run_logger(project_dir, "project-update")
        logger.info("project %s updated; validation: %s", slug, project.validation)
    finally:
        lock.release()
    return project, project_dir
