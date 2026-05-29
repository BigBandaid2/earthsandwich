"""Shared pytest fixtures and config for the pile-app test suite."""

import os
import sys
from pathlib import Path

# These run at module-load time (when pytest first imports this conftest),
# which happens before any test files are collected — so test-file imports
# can rely on the pile-app modules being on sys.path and ANTHROPIC_API_KEY
# being set.

PILE_APP_ROOT = Path(__file__).resolve().parent.parent

# Allow `from common.pile import ...` / `from instagram.pipeline import ...`
# without requiring a prior `pip install -e .` of pile-app.
if str(PILE_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(PILE_APP_ROOT))

# common/inference.py dereferences ANTHROPIC_API_KEY at module load. In
# environments without it (e.g. CI for unit-only runs), set a dummy so the
# import succeeds — unit tests mock the Anthropic client anyway.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-dummy-key-do-not-use")


def pytest_configure(config):
    """Register custom markers so `pytest --strict-markers` is happy."""
    config.addinivalue_line(
        "markers",
        "integration: tests that hit live external services (Instagram via "
        "instagrapi, the Anthropic API). Require INSTA_USERNAME / INSTA_PASSWORD "
        "/ ANTHROPIC_API_KEY in the environment and a working instagrapi session. "
        "Skipped automatically when credentials are missing.",
    )
