"""US1 — project creation + connection validation (redesigned 2026-06-13).

Flow: derive slug (FR-180) → build the pile from one or more data/media
directories with table-validation (FR-182) → Test Connection against the
discrete relational connection (FR-183) → only then materialize the project
folder, writing the DSN to the gitignored `.secrets` (never `project.yml`,
FR-012). A failed gate leaves NO project state behind (FR-008).
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
    PileDirectory,
    PileSample,
    TargetConfig,
    TargetConnection,
    derive_slug,
    save_project,
)
from common.locking import ProjectLock
from common.run_logging import get_run_logger
from project import secrets as secrets_mod
from project.pile_scan import catalogue_media_directory, scan_data_directory

#: SQLAlchemy engines the v1 toolkit treats as relational.
RELATIONAL_ENGINES = {"postgresql", "postgres", "mysql", "mariadb", "mssql", "oracle", "sqlite", "duckdb"}
MAX_DESCRIPTION = 4000


class OperatorError(RuntimeError):
    """Operator-correctable error (CLI exit 1) — clear message, no stack trace."""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def default_projects_dir() -> Path:
    """``projects/`` under the App root, overridable for tests (movability-safe)."""
    override = os.environ.get("BRIDGE_PROJECTS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "projects"


def _parse_sample(spec: str) -> PileSample:
    match = re.fullmatch(r"([a-z+\-]+):(\d+)", spec.strip())
    if not match:
        raise OperatorError(f"bad sample spec {spec!r}; expected '<strategy>:<size>', e.g. 'head+random:200'")
    return PileSample(strategy=match.group(1), size=int(match.group(2)))


def _normalize_dsn(dsn: str) -> str:
    """Pin the installed driver for bare postgres schemes (psycopg 3)."""
    for bare in ("postgresql://", "postgres://"):
        if dsn.startswith(bare):
            return "postgresql+psycopg://" + dsn[len(bare):]
    return dsn


# ---------------------------------------------------------------- connection probe

def probe_connection(dsn: str) -> tuple[bool, bool, bool, bool, str]:
    """Return (reachable, read, insert, delete, note) for a relational DSN.

    Read probe: ``SELECT 1``. Insert/delete probes: DML on a session-temp table
    inside a rolled-back transaction — proves DML without touching real tables.
    """
    normalized = _normalize_dsn(dsn)
    connect_args: dict = {}
    if normalized.startswith(("postgresql", "mysql", "mariadb")):
        connect_args["connect_timeout"] = 10   # unreachable host fails in seconds, not minutes
    try:
        engine = create_engine(normalized, connect_args=connect_args)
    except Exception as exc:
        return False, False, False, False, f"connection rejected: {exc}"
    try:
        with engine.connect() as conn:
            read = insert = delete = False
            try:
                conn.execute(text("SELECT 1"))
                read = True
            except Exception:
                pass
            conn.rollback()                      # end SQLAlchemy 2.x autobegin
            trans = conn.begin()
            try:
                tmp = "CREATE TEMP TABLE bridge_probe (id INTEGER)" if engine.dialect.name == "sqlite" \
                    else "CREATE TEMPORARY TABLE bridge_probe (id INTEGER)"
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


def test_connection(connection: TargetConnection, password: str) -> tuple[bool, bool, bool, bool, str, str]:
    """Assemble the DSN and probe it WITHOUT persisting (FR-183). Returns probe + the DSN."""
    if connection.engine not in RELATIONAL_ENGINES:
        raise OperatorError(f"engine {connection.engine!r} is not a supported relational engine")
    dsn = connection.dsn(password)
    reachable, read, insert, delete, note = probe_connection(dsn)
    return reachable, read, insert, delete, note, dsn


# ---------------------------------------------------------------- pile selection

def resolve_data_directory(path: str | Path, spec: str = "all") -> list[str]:
    """Selected VALID table filenames in a data directory (FR-182).

    ``all`` freezes to every currently-valid file; a comma-separated list names
    files that must exist AND parse as tables. Raises :class:`OperatorError`.
    """
    pile_dir = Path(path)
    if not pile_dir.is_dir():
        raise OperatorError(f"data directory not found (or not a directory): {pile_dir}")
    scans = {s.name: s for s in scan_data_directory(pile_dir)}
    if spec.strip().lower() == "all":
        valid = sorted(name for name, s in scans.items() if s.valid)
        if not valid:
            raise OperatorError(f"data directory has no valid table files: {pile_dir}")
        return valid
    names = [p.strip() for p in spec.split(",") if p.strip()]
    if not names:
        raise OperatorError("empty file selection; name files or use 'all'")
    missing = [n for n in names if n not in scans]
    if missing:
        raise OperatorError(f"file(s) not found in {pile_dir}: {', '.join(missing)}")
    invalid = [f"{n} ({scans[n].reason})" for n in names if not scans[n].valid]
    if invalid:
        raise OperatorError(f"file(s) not a valid table in {pile_dir}: {', '.join(invalid)}")
    return names


def build_pile(directories: list[tuple[str, str]], selections: dict[str, str], sample: PileSample) -> PileConfig:
    """Build a file-based PileConfig from (path, kind) pairs + per-data-dir selections."""
    pile_dirs: list[PileDirectory] = []
    for dpath, dkind in directories:
        if dkind == "data":
            files = resolve_data_directory(dpath, selections.get(dpath, "all"))
            pile_dirs.append(PileDirectory(path=dpath, kind="data", files=files))
        elif dkind == "media":
            pile_dirs.append(PileDirectory(path=dpath, kind="media", catalogue=catalogue_media_directory(dpath)))
        else:
            raise OperatorError(f"unknown directory kind {dkind!r} (expected data | media)")
    if not any(d.kind == "data" and d.files for d in pile_dirs):
        raise OperatorError("select at least one valid data file (FR-007)")
    return PileConfig(directories=pile_dirs, kind="file", sample=sample)


# ---------------------------------------------------------------- create

def create_project(
    name: str,
    *,
    directories: list[tuple[str, str]],
    selections: dict[str, str] | None = None,
    sample: str = "head+random:200",
    description: str = "",
    engine: str,
    host: str,
    port: int | str = 5432,
    database: str,
    user: str,
    password: str,
    projects_dir: Path | None = None,
) -> tuple[BridgeProject, Path]:
    """Validate, then materialize ``projects/<slug>/`` with project.yml + .secrets."""
    projects_root = projects_dir or default_projects_dir()
    slug = derive_slug(name)
    project_dir = projects_root / slug
    if project_dir.exists():
        raise OperatorError(
            f"slug {slug!r} already exists at {project_dir} — delete the existing project first; "
            "this view never overwrites (FR-011/FR-180)"
        )
    if description and len(description) > MAX_DESCRIPTION:
        raise OperatorError(f"description exceeds {MAX_DESCRIPTION} characters (FR-181)")

    pile = build_pile(directories, selections or {}, _parse_sample(sample))

    if not all([engine, host, database, user]):
        raise OperatorError("target connection requires engine, host, database and user")
    connection = TargetConnection(engine=engine, host=host, port=int(port or 5432), database=database, user=user)
    reachable, read, insert, delete, note, dsn = test_connection(connection, password)
    if not reachable:
        raise OperatorError(f"{note or 'target unreachable'} — no project created (FR-008)")

    oracle_note = "" if (insert and delete) else "oracle loop will be skipped - no insert/delete permission (FR-075)"
    validation = ConnectionValidationResult(
        pile_readable=True, target_reachable=True, target_read=read,
        target_insert=insert, target_delete=delete, validated_at=_now(),
        notes="; ".join(filter(None, [note, oracle_note])),
    )
    project = BridgeProject(
        name=name, slug=slug, pile=pile,
        target=TargetConfig(kind="relational", connection=connection, secret_ref="target"),
        description=description, created_at=_now(), validation=validation,
    )

    # All gates passed — only now does any state appear on disk.
    project_dir.mkdir(parents=True, exist_ok=True)
    with ProjectLock(project_dir):
        save_project(project, project_dir)
        secrets_mod.write_secret(project_dir, "target", dsn)   # the password lives ONLY here
        logger, _ = get_run_logger(project_dir, "project-create")
        logger.info("project %r (slug %s) created; validation: %s", name, slug, validation)
    return project, project_dir


def format_validation_report(project: BridgeProject) -> str:
    v = project.validation
    yn = lambda b: "yes" if b else "NO"  # noqa: E731
    lines = [
        f"Project: {project.name}  (slug {project.slug})",
        f"  pile readable:    {yn(v.pile_readable)}  ({project.pile.describe()})",
        f"  target reachable: {yn(v.target_reachable)}  ({project.target.describe()})",
        f"  target read:      {yn(v.target_read)}",
        f"  target insert:    {yn(v.target_insert)}",
        f"  target delete:    {yn(v.target_delete)}",
        f"  oracle loop:      {'will run' if v.oracle_can_run else 'will be skipped'}",
    ]
    if v.notes:
        lines.append(f"  notes: {v.notes}")
    return "\n".join(lines)
