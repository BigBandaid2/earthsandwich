"""Per-project secrets: the gitignored `.secrets` DSN map (T056, FR-012 reversal).

`projects/<slug>/.secrets` is a small YAML map `{ <ref>: "<dsn>" }` holding the
assembled connection string(s) for the project's relational endpoint(s). It is
never echoed back, never written to `project.yml`, and `projects/` is gitignored
so it is never committed. Legacy projects that reference an env-var name instead
resolve the DSN from the environment at run time.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml

from common.config import BridgeProject

SECRETS_FILE = ".secrets"


def secrets_path(project_dir: str | Path) -> Path:
    return Path(project_dir) / SECRETS_FILE


def load_secrets(project_dir: str | Path) -> dict[str, str]:
    path = secrets_path(project_dir)
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_secret(project_dir: str | Path, ref: str, dsn: str) -> None:
    secrets = load_secrets(project_dir)
    secrets[ref] = dsn
    path = secrets_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(secrets, sort_keys=False), encoding="utf-8")


def resolve_target_dsn(project: BridgeProject, project_dir: str | Path) -> str | None:
    """The target's runtime DSN: from `.secrets` (redesign) or the env var (legacy)."""
    target = project.target
    if target.secret_ref:
        dsn = load_secrets(project_dir).get(target.secret_ref)
        if dsn:
            return dsn
    if target.connection_env:
        return os.environ.get(target.connection_env) or None
    return None
