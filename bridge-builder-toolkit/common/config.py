"""Project configuration: project.yml load/save + the Bridge Project model.

Redesign (2026-06-13): a pile is one or more **directories** (data | media); a
relational endpoint records its discrete connection (never the password — that
lives only in the gitignored `.secrets`, FR-012). Identity is a **slug** derived
from the name (FR-180). Endpoints are symmetric (pile or target may be file or
relational). Pre-redesign `project.yml` shapes (single `dir`/`files`/`path`,
`target.connection_env`) are still read.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePath
from typing import Any

import yaml

PROJECT_FILE = "project.yml"

#: SQLAlchemy driver pinned per engine (psycopg 3 for postgres; others best-effort).
_ENGINE_DRIVER = {"postgresql": "postgresql+psycopg", "postgres": "postgresql+psycopg"}
#: File-based relational engines — a database file path, no host/port/credentials.
_FILE_ENGINES = {"sqlite", "duckdb"}


def derive_slug(name: str) -> str:
    """Lowercase, hyphen-separated, filesystem-safe identity from a name (FR-180)."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "project"


@dataclass
class PileSample:
    strategy: str = "head+random"          # FR-028 / FR-029
    size: int = 200


@dataclass
class PileDirectory:
    path: str                              # operator-supplied, relative for movability
    kind: str = "data"                     # data | media (FR-182)
    files: list[str] = field(default_factory=list)   # data: frozen selection; media: empty
    catalogue: dict[str, Any] | None = None          # media: {count, types: {ext: n}, bytes}


@dataclass
class PileConfig:
    directories: list[PileDirectory] = field(default_factory=list)
    kind: str = "file"                     # file | relational (endpoint symmetry)
    sample: PileSample = field(default_factory=PileSample)
    connection: "TargetConnection | None" = None   # relational pile (kind == relational)
    secret_ref: str | None = None          # key under which the pile DSN lives in .secrets
    connection_env: str | None = None      # legacy env-var name (read compat)

    def data_files(self) -> list[tuple[str, str]]:
        """(directory_path, filename) for every selected data file across directories."""
        return [(d.path, f) for d in self.directories if d.kind == "data" for f in d.files]

    def describe(self) -> str:
        if self.kind == "relational":
            if self.connection is not None:
                return self.connection.descriptor()
            if self.connection_env:
                return f"env:{self.connection_env}"
            return "(unconfigured db)"
        n = len(self.data_files())
        dirs = len(self.directories)
        return f"{dirs} director{'y' if dirs == 1 else 'ies'}, {n} data file{'' if n == 1 else 's'}"


@dataclass
class TargetConnection:
    engine: str
    host: str
    port: int
    database: str
    user: str

    def dsn(self, password: str) -> str:
        if self.engine in _FILE_ENGINES:               # sqlite/duckdb: file path, no host/creds
            return f"{self.engine}:///{self.database}"
        driver = _ENGINE_DRIVER.get(self.engine, self.engine)
        return f"{driver}://{self.user}:{password}@{self.host}:{self.port}/{self.database}"

    def descriptor(self) -> str:           # credential-free, for display
        if self.engine in _FILE_ENGINES:
            return f"{self.engine}:///{self.database}"
        return f"{self.engine}://{self.host}:{self.port}/{self.database}"


@dataclass
class TargetConfig:
    kind: str = "relational"               # relational | file (endpoint symmetry)
    connection: TargetConnection | None = None
    secret_ref: str | None = None          # key under which the DSN lives in .secrets
    connection_env: str | None = None      # legacy: env-var NAME (pre-redesign projects)
    path: str | None = None                # file target: output directory (kind == file)

    def describe(self) -> str:
        if self.kind == "file":
            return f"dir:{self.path}" if self.path else "(unconfigured dir)"
        if self.connection is not None:
            return self.connection.descriptor()
        if self.connection_env:
            return f"env:{self.connection_env}"
        return "(unconfigured)"


@dataclass
class ConnectionValidationResult:
    """Per-endpoint validation booleans recorded at create time (FR-007)."""

    pile_readable: bool = False
    target_reachable: bool = False
    target_read: bool = False
    target_insert: bool = False            # with target_delete, gates the oracle loop
    target_delete: bool = False
    validated_at: str | None = None
    notes: str = ""

    @property
    def is_creatable(self) -> bool:
        return self.pile_readable and self.target_reachable

    @property
    def oracle_can_run(self) -> bool:
        return self.target_insert and self.target_delete


@dataclass
class BridgeProject:
    name: str                              # display label
    slug: str                              # identity = folder name (FR-180)
    pile: PileConfig
    target: TargetConfig
    description: str = ""                  # markdown ≤4000 chars (FR-181)
    created_at: str | None = None
    validation: ConnectionValidationResult = field(default_factory=ConnectionValidationResult)

    # ---- serialization (explicit, to keep the project.yml shape stable) ----

    def to_dict(self) -> dict[str, Any]:
        target: dict[str, Any] = {"kind": self.target.kind}
        if self.target.kind == "file":
            target["path"] = self.target.path
        elif self.target.connection is not None:
            target["connection"] = asdict(self.target.connection)
            target["secret_ref"] = self.target.secret_ref
        elif self.target.connection_env:
            target["connection_env"] = self.target.connection_env

        pile: dict[str, Any] = {
            "kind": self.pile.kind,
            "sample": {"strategy": self.pile.sample.strategy, "size": self.pile.sample.size},
        }
        if self.pile.kind == "relational" and self.pile.connection is not None:
            pile["connection"] = asdict(self.pile.connection)
            pile["secret_ref"] = self.pile.secret_ref
        else:
            pile["directories"] = [
                {k: v for k, v in {
                    "path": d.path, "kind": d.kind,
                    "files": list(d.files) if d.kind == "data" else None,
                    "catalogue": d.catalogue,
                }.items() if v is not None}
                for d in self.pile.directories
            ]
        return {
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "created_at": self.created_at,
            "pile": pile,
            "target": target,
            "validation": asdict(self.validation),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BridgeProject":
        name = data["name"]
        slug = data.get("slug") or derive_slug(name)
        pile = _pile_from_dict(data.get("pile") or {})
        target = _target_from_dict(data.get("target") or {})
        known = ConnectionValidationResult.__dataclass_fields__
        validation = ConnectionValidationResult(
            **{k: v for k, v in (data.get("validation") or {}).items() if k in known}
        )
        return cls(
            name=name, slug=slug, pile=pile, target=target,
            description=data.get("description", "") or "",
            created_at=data.get("created_at"), validation=validation,
        )


def _connection_from(conn_raw: dict[str, Any] | None) -> TargetConnection | None:
    if not conn_raw:
        return None
    return TargetConnection(
        engine=conn_raw.get("engine", "postgresql"), host=conn_raw.get("host", ""),
        port=int(conn_raw.get("port", 5432)), database=conn_raw.get("database", ""),
        user=conn_raw.get("user", ""),
    )


def _pile_from_dict(raw: dict[str, Any]) -> PileConfig:
    sample_raw = raw.get("sample") or {}
    sample = PileSample(
        strategy=sample_raw.get("strategy", "head+random"),
        size=int(sample_raw.get("size", 200)),
    )
    directories: list[PileDirectory] = []
    if raw.get("directories"):                            # new shape
        for d in raw["directories"]:
            directories.append(PileDirectory(
                path=d.get("path", ""), kind=d.get("kind", "data"),
                files=list(d.get("files") or []), catalogue=d.get("catalogue"),
            ))
    elif raw.get("dir"):                                  # legacy multi-file (dir + files)
        directories.append(PileDirectory(path=raw["dir"], kind="data", files=list(raw.get("files") or [])))
    elif raw.get("path") and not raw.get("connection"):  # legacy single-file (path)
        parsed = PurePath(raw["path"])
        directories.append(PileDirectory(path=str(parsed.parent), kind="data", files=[parsed.name]))
    return PileConfig(
        directories=directories, kind=raw.get("kind", "file"), sample=sample,
        connection=_connection_from(raw.get("connection")),
        secret_ref=raw.get("secret_ref"), connection_env=raw.get("connection_env"),
    )


def _target_from_dict(raw: dict[str, Any]) -> TargetConfig:
    return TargetConfig(
        kind=raw.get("kind", "relational"), connection=_connection_from(raw.get("connection")),
        secret_ref=raw.get("secret_ref"), connection_env=raw.get("connection_env"),
        path=raw.get("path"),
    )


def project_yml_path(project_dir: str | Path) -> Path:
    return Path(project_dir) / PROJECT_FILE


def load_project(project_dir: str | Path) -> BridgeProject:
    with project_yml_path(project_dir).open("r", encoding="utf-8") as fh:
        return BridgeProject.from_dict(yaml.safe_load(fh) or {})


def save_project(project: BridgeProject, project_dir: str | Path) -> Path:
    path = project_yml_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(project.to_dict(), fh, sort_keys=False, allow_unicode=True)
    return path
