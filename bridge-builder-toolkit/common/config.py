"""Project configuration: project.yml load/save + the Bridge Project model (T005).

All paths inside a project are stored relative or as env-var *names* — never
absolute, never secrets — so the App stays movable (FR-003, FR-012).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_FILE = "project.yml"


@dataclass
class PileSample:
    strategy: str = "head+random"          # FR-028 / FR-029
    size: int = 200


@dataclass
class PileConfig:
    dir: str                               # operator-supplied pile DIRECTORY, relative for movability (FR-005)
    files: list[str] = field(default_factory=list)   # frozen selection — "all" expands at create/update
    kind: str = "tsv"                      # tsv | relational (future)
    sample: PileSample = field(default_factory=PileSample)

    def describe(self) -> str:
        count = len(self.files)
        return f"{self.dir} ({count} file{'s' if count != 1 else ''}: {', '.join(self.files)})"


@dataclass
class TargetConfig:
    connection_env: str                    # env-var NAME, never the secret (FR-012)
    kind: str = "relational"               # v1: relational only (FR-005 v1 scope)


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
        """FR-008: a project may be created only if pile + target are reachable."""
        return self.pile_readable and self.target_reachable

    @property
    def oracle_can_run(self) -> bool:
        """FR-070 / FR-075: the oracle loop runs only with insert+delete permission."""
        return self.target_insert and self.target_delete


@dataclass
class BridgeProject:
    name: str
    pile: PileConfig
    target: TargetConfig
    created_at: str | None = None
    validation: ConnectionValidationResult = field(default_factory=ConnectionValidationResult)

    # ---- serialization (explicit, to keep the project.yml shape stable) ----

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "created_at": self.created_at,
            "pile": {
                "dir": self.pile.dir,
                "files": list(self.pile.files),
                "kind": self.pile.kind,
                "sample": {"strategy": self.pile.sample.strategy, "size": self.pile.sample.size},
            },
            "target": {"kind": self.target.kind, "connection_env": self.target.connection_env},
            "validation": asdict(self.validation),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BridgeProject":
        pile_raw = data.get("pile") or {}
        sample_raw = pile_raw.get("sample") or {}
        target_raw = data.get("target") or {}
        val_raw = data.get("validation") or {}
        known = ConnectionValidationResult.__dataclass_fields__
        validation = ConnectionValidationResult(**{k: v for k, v in val_raw.items() if k in known})
        pile_dir = pile_raw.get("dir", "")
        pile_files = list(pile_raw.get("files") or [])
        legacy_path = pile_raw.get("path")
        if legacy_path and not pile_dir:                 # pre-multi-file project.yml compatibility
            from pathlib import PurePath

            parsed = PurePath(legacy_path)
            pile_dir, pile_files = str(parsed.parent), [parsed.name]
        return cls(
            name=data["name"],
            created_at=data.get("created_at"),
            pile=PileConfig(
                dir=pile_dir,
                files=pile_files,
                kind=pile_raw.get("kind", "tsv"),
                sample=PileSample(
                    strategy=sample_raw.get("strategy", "head+random"),
                    size=int(sample_raw.get("size", 200)),
                ),
            ),
            target=TargetConfig(
                connection_env=target_raw.get("connection_env", ""),
                kind=target_raw.get("kind", "relational"),
            ),
            validation=validation,
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
