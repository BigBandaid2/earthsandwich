"""Portability guardrail for the pile-app/ directory — SC-010 / FR-110.

Exercises the "movable to a fresh repo" claim: copy pile-app/ to a temp
directory, create an isolated venv inside that copy, `pip install -e .`,
and run the unit suite. If it passes there, the App is portable.

Gated behind an env var because a clean run is ~3-5 minutes (venv build
+ pip install + full unit pass) and the IO is heavy enough that we don't
want it running on every `pytest` invocation. To execute:

    PILE_APP_PORTABILITY_TEST=1 pytest tests/integration/test_portability.py

The inner pytest run skips the live-IG smoke (`test_instagram_pull.py`,
which needs .env credentials we don't carry across) and skips THIS test
file (to prevent infinite recursion).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

APP_ROOT = Path(__file__).resolve().parents[2]  # pile-app/

# Items NOT to copy: built artefacts, runtime data, credentials, the venv itself.
IGNORE_NAMES = {
    "venv",
    "__pycache__",
    ".pytest_cache",
    "pile_app.egg-info",
    "pile",          # gitignored runtime output
    "logs",          # gitignored runtime logs
    ".env",          # credentials
    "instagrapi_session.json",
}


def _ignore(_src: str, names: list[str]) -> list[str]:
    return [n for n in names if n in IGNORE_NAMES or n.endswith(".pyc")]


@pytest.mark.skipif(
    os.environ.get("PILE_APP_PORTABILITY_TEST") != "1",
    reason="set PILE_APP_PORTABILITY_TEST=1 to run; ~3-5 min, builds a fresh venv",
)
def test_pile_app_is_portable(tmp_path: Path) -> None:
    dest = tmp_path / "pile-app"
    shutil.copytree(APP_ROOT, dest, ignore=_ignore)

    venv_dir = dest / "venv"
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
    )
    py = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    assert py.exists(), f"venv python not at expected path {py}"

    # Install the package in editable mode against the COPY, not the original.
    subprocess.run(
        [str(py), "-m", "pip", "install", "-e", str(dest), "--quiet"],
        check=True,
    )

    result = subprocess.run(
        [
            str(py), "-m", "pytest", "tests",
            "--ignore=tests/integration/test_portability.py",
            "--ignore=tests/instagram/test_instagram_pull.py",
            "-q", "--no-header",
        ],
        cwd=dest,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "pile-app pytest in the fresh-copy venv failed — portability broken.\n"
        f"stdout (last 3000 chars):\n{result.stdout[-3000:]}\n"
        f"stderr (last 1500 chars):\n{result.stderr[-1500:]}"
    )
