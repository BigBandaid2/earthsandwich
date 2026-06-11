"""US1 — project creation + connection validation (T010).

Flow (contracts/cli.md `project create`):
validate inputs → probe pile + target → only then materialize the project
folder, so a failed validation leaves NO project state behind (FR-008).
Credentials travel by env-var name only (FR-012): a DSN-shaped ``--target`` is
used for kind detection and never persisted.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

from common.config import (
    BridgeProject,
    ConnectionValidationResult,
    PileConfig,
    PileSample,
    TargetConfig,
    save_project,
)
from common.locking import ProjectLock
from common.run_logging import get_run_logger

#: SQLAlchemy schemes the v1 toolkit treats as relational (FR-005 v1 scope).
RELATIONAL_SCHEMES = {"postgresql", "postgres", "mysql", "mariadb", "mssql", "oracle", "sqlite", "duckdb"}

NON_RELATIONAL_DEFERRED = (
    "non-relational targets are deferred to a future version (FR-005 v1 scope); "
    "provide a relational DSN (e.g. postgresql://...)"
)


class OperatorError(RuntimeError):
    """Operator-correctable error (CLI exit 1) — clear message, no stack trace."""


def default_projects_dir() -> Path:
    """``projects/`` under the App root, overridable for tests (movability-safe)."""
    override = os.environ.get("BRIDGE_PROJECTS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "projects"


def _parse_sample(spec: str) -> PileSample:
    match = re.fullmatch(r"([a-z+\-]+):(\d+)", spec.strip())
    if not match:
        raise OperatorError(f"bad --pile-sample {spec!r}; expected '<strategy>:<size>', e.g. 'head+random:200'")
    return PileSample(strategy=match.group(1), size=int(match.group(2)))


def _target_scheme(target: str) -> str | None:
    match = re.match(r"^([A-Za-z0-9+]+)://", target.strip())
    if not match:
        return None
    return match.group(1).split("+", 1)[0].lower()


def _normalize_dsn(dsn: str) -> str:
    """Pin the installed driver for bare postgres schemes (psycopg 3)."""
    for bare in ("postgresql://", "postgres://"):
        if dsn.startswith(bare):
            return "postgresql+psycopg://" + dsn[len(bare):]
    return dsn


def _probe_pile(pile_path: Path) -> bool:
    try:
        with pile_path.open("r", encoding="utf-8", errors="replace") as fh:
            fh.readline()
        return True
    except OSError:
        return False


def _probe_target(dsn: str) -> tuple[bool, bool, bool, bool, str]:
    """Return (reachable, read, insert, delete, note).

    Read probe: ``SELECT 1``. Insert/delete probes: DML on a session-scoped
    temporary table inside a rolled-back transaction — proves DML is permitted
    without touching real tables (the per-table oracle probe is US4's job).
    """
    try:
        engine = create_engine(_normalize_dsn(dsn))
    except Exception as exc:  # malformed DSN, missing driver
        return False, False, False, False, f"target DSN rejected: {exc}"

    try:
        with engine.connect() as conn:
            read = insert = delete = False
            try:
                conn.execute(text("SELECT 1"))
                read = True
            except Exception:
                pass
            conn.rollback()  # end SQLAlchemy 2.x autobegin so the probe gets its own txn
            trans = conn.begin()
            try:
                tmp = "CREATE TEMPORARY TABLE bridge_probe (id INTEGER)"
                if engine.dialect.name == "sqlite":
                    tmp = "CREATE TEMP TABLE bridge_probe (id INTEGER)"
                conn.execute(text(tmp))
                conn.execute(text("INSERT INTO bridge_probe (id) VALUES (1)"))
                insert = True
                conn.execute(text("DELETE FROM bridge_probe WHERE id = 1"))
                delete = True
            except Exception as exc:
                return True, read, insert, delete, f"DML probe stopped: {exc}"
            finally:
                trans.rollback()
            return True, read, insert, delete, ""
    except Exception as exc:
        return False, False, False, False, f"target unreachable: {exc}"
    finally:
        engine.dispose()


def create_project(
    name: str,
    *,
    pile: str,
    target: str,
    target_cred_env: str,
    pile_sample: str = "head+random:200",
    force: bool = False,
    projects_dir: Path | None = None,
) -> tuple[BridgeProject, Path]:
    """Validate, then materialize ``projects/<name>/`` with project.yml.

    Raises :class:`OperatorError` (and creates nothing) on any creation gate:
    bad inputs, existing project without --force, unreadable pile, unreachable
    target (FR-008/011). Missing insert/delete permission is NOT a gate — it is
    recorded and the oracle loop is skipped later (FR-075).
    """
    projects_root = projects_dir or default_projects_dir()
    project_dir = projects_root / name

    if project_dir.exists() and not force:
        raise OperatorError(f"project {name!r} already exists at {project_dir}; re-run with --force to overwrite (FR-011)")

    sample = _parse_sample(pile_sample)

    scheme = _target_scheme(target)
    if scheme is None or scheme not in RELATIONAL_SCHEMES:
        raise OperatorError(NON_RELATIONAL_DEFERRED)

    dsn = os.environ.get(target_cred_env, "")
    if not dsn:
        raise OperatorError(
            f"env var {target_cred_env!r} is not set; export the target DSN there "
            "(credentials are never stored or passed on the CLI, FR-012)"
        )

    pile_path = Path(pile)
    pile_readable = _probe_pile(pile_path)
    if not pile_readable:
        raise OperatorError(f"pile not readable: {pile_path} (FR-008 — no project created)")

    reachable, read, insert, delete, note = _probe_target(dsn)
    if not reachable:
        raise OperatorError(f"{note or 'target unreachable'} (FR-008 — no project created)")

    oracle_note = "" if (insert and delete) else "oracle loop will be skipped - no insert/delete permission (FR-075)"
    validation = ConnectionValidationResult(
        pile_readable=True,
        target_reachable=True,
        target_read=read,
        target_insert=insert,
        target_delete=delete,
        validated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z"),
        notes="; ".join(filter(None, [note, oracle_note])),
    )

    project = BridgeProject(
        name=name,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z"),
        pile=PileConfig(path=str(pile), kind="tsv", sample=sample),
        target=TargetConfig(connection_env=target_cred_env, kind="relational"),
        validation=validation,
    )

    # All gates passed — only now does any state appear on disk.
    project_dir.mkdir(parents=True, exist_ok=True)
    with ProjectLock(project_dir):
        save_project(project, project_dir)
        logger, _ = get_run_logger(project_dir, "project-create")
        logger.info("project %r created; validation: %s", name, validation)
    return project, project_dir


def format_validation_report(project: BridgeProject) -> str:
    v = project.validation
    yn = lambda b: "yes" if b else "NO"  # noqa: E731
    lines = [
        f"Project: {project.name}",
        f"  pile readable:    {yn(v.pile_readable)}  ({project.pile.path})",
        f"  target reachable: {yn(v.target_reachable)}  (env: {project.target.connection_env})",
        f"  target read:      {yn(v.target_read)}",
        f"  target insert:    {yn(v.target_insert)}",
        f"  target delete:    {yn(v.target_delete)}",
        f"  oracle loop:      {'will run' if v.oracle_can_run else 'will be skipped'}",
    ]
    if v.notes:
        lines.append(f"  notes: {v.notes}")
    return "\n".join(lines)
