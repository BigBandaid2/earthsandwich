"""Project-root outside-in segregation check — 003 US3 Acceptance Scenario #4.

The companion to ``pile-app/tests/integration/test_self_containment.py``:
that one scans pile-app/ for refs reaching OUT; this one scans the
project root for refs reaching IN to pile-app's runtime + data.

This test lives at the project root **by design**. When pile-app/ is
relocated to a separate repository (FR-110 / FR-111), this test stays
behind with the parent project — the inside-out check travels with the
App, the outside-in check belongs to the project it was carved out of.

Patterns flagged are exactly the paths the spec treats as "the App's
data / internal runtime / credentials":

  - ``pile-app/pile/``                — pile output (TSVs + media)
  - ``pile-app/logs/``                — per-run log files
  - ``pile-app/instagrapi_session.json`` — auth session
  - ``pile-app/.env``                 — credentials

References from spec / docs / planning artifacts are explicitly allowed
(those are working-process documents that legitimately describe the App).
The exclude list below codifies the allow-list.

Runnable either as a pytest test (``pytest tests/test_pile_app_segregation.py``
from project root) or as a plain script (``python tests/test_pile_app_segregation.py``)
for any operator who doesn't have pytest at the project root.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Directories where references are allowed (spec docs, planning artifacts,
# tooling, build artefacts that aren't application code, the App itself).
EXCLUDE_DIRS = {
    "pile-app",          # the App is allowed to reference its own paths
    "specs",             # spec docs legitimately describe the App
    "docs",              # planning + roadmap docs reference the App
    ".specify",          # spec-kit working tooling
    ".claude",           # claude-code config
    ".onboard",          # onboard plugin state
    ".git",
    ".github",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
}

# Individual files exempt from the scan.
EXCLUDE_FILES = {
    "README.md",
    "CLAUDE.md",
    "ONBOARDING.md",
    "tests/test_pile_app_segregation.py",  # this test contains the patterns as literals
}

PATTERNS = {
    "pile_data": re.compile(r"pile-app/pile/"),
    "pile_logs": re.compile(r"pile-app/logs/"),
    "pile_session": re.compile(r"pile-app/instagrapi_session\.json"),
    "pile_env": re.compile(r"pile-app/\.env"),
}


def _iter_text_files():
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        parts = rel.split("/")
        if any(p in EXCLUDE_DIRS for p in parts):
            continue
        if rel in EXCLUDE_FILES:
            continue
        yield path


def find_segregation_violations() -> list[str]:
    findings: list[str] = []
    for path in _iter_text_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        try:
            with path.open(encoding="utf-8") as f:
                for line_no, line in enumerate(f, 1):
                    for label, pattern in PATTERNS.items():
                        if pattern.search(line):
                            findings.append(
                                f"{rel}:{line_no} [{label}] {line.rstrip()[:160]}"
                            )
                            break
        except (UnicodeDecodeError, PermissionError, OSError):
            continue
    return findings


def test_no_outside_in_references_into_pile_app_runtime() -> None:
    findings = find_segregation_violations()
    assert not findings, (
        "Outside-in segregation violated — project code outside pile-app/ "
        "reaches INTO the App's runtime data, logs, session, or credentials.\n"
        "Each finding is a portability hazard; either move the consumer "
        "into pile-app, surface the data via a pile contract, or update the "
        "EXCLUDE_DIRS / EXCLUDE_FILES allow-list if the reference is "
        "documentation rather than code.\n"
        "Findings:\n  "
        + "\n  ".join(findings)
    )


if __name__ == "__main__":
    findings = find_segregation_violations()
    if findings:
        print(f"Outside-in segregation violations ({len(findings)}):")
        for f in findings:
            print(f"  {f}")
        sys.exit(1)
    print("OK: no outside-in references into pile-app runtime data.")
    sys.exit(0)
