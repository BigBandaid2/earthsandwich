"""Self-containment guardrail for the pile-app source tree.

SC-011 / FR-110: the App must be movable to a separate repo or directory
without breaking either side. This test fails when source code in
`pile-app/` reaches outside the App root in ways that would break that
portability.

What we flag (per task T233 of Phase 22):

  - Relative path traversal (``../``) that climbs above pile-app/
  - Absolute filesystem paths baking in the current workspace location
    (``C:\\workspace`` on Windows; ``/workspace`` on POSIX)
  - References to sibling Apps' directories: ``scripts/``, ``backend/``,
    ``frontend/``, ``public/``

Allow-list (NOT portability hazards):

  - URL strings (``https://``, ``http://``, ``git://``, etc.) — those
    legitimately contain ``://something/``
  - This test file and the portability test, both of which name the
    forbidden patterns deliberately in their own docs/strings

Runs in the default unit suite (fast — pure regex over the source tree).
"""

from __future__ import annotations

import re
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]  # pile-app/
EXCLUDE_DIRS = {"venv", "__pycache__", ".pytest_cache", "pile_app.egg-info"}

PATTERNS = {
    "parent_traversal": re.compile(r"\.\./"),
    "workspace_abs_win": re.compile(r"C:\\workspace", re.IGNORECASE),
    "workspace_abs_posix": re.compile(r"/workspace/"),
    "sibling_app_scripts": re.compile(r"(?<![\w/.])scripts/"),
    "sibling_app_backend": re.compile(r"(?<![\w/.])backend/"),
    "sibling_app_frontend": re.compile(r"(?<![\w/.])frontend/"),
    "sibling_app_public": re.compile(r"(?<![\w/.])public/"),
}

EXEMPT_FILES = {
    "tests/integration/test_self_containment.py",
    "tests/integration/test_portability.py",
}

URL_RE = re.compile(r"\w+://[^\s'\"`)>]+")


def _iter_py_files():
    for path in APP_ROOT.rglob("*.py"):
        rel_parts = set(path.relative_to(APP_ROOT).parts)
        if rel_parts & EXCLUDE_DIRS:
            continue
        rel = path.relative_to(APP_ROOT).as_posix()
        if rel in EXEMPT_FILES:
            continue
        yield path


def test_no_cross_app_references():
    findings: list[str] = []
    for path in _iter_py_files():
        rel = path.relative_to(APP_ROOT).as_posix()
        try:
            with path.open(encoding="utf-8") as f:
                for line_no, line in enumerate(f, 1):
                    clean = URL_RE.sub("URL", line)
                    for label, pattern in PATTERNS.items():
                        if pattern.search(clean):
                            findings.append(
                                f"{rel}:{line_no} [{label}] {line.rstrip()[:160]}"
                            )
                            break
        except UnicodeDecodeError:
            continue
    assert not findings, (
        "pile-app self-containment violated — source code references "
        "the surrounding repo in ways that would break portability.\n"
        "Each finding below is a likely hazard:\n  "
        + "\n  ".join(findings)
    )
