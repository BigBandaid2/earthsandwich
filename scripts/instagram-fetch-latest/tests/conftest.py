"""Shared pytest fixtures and config for the instagram-fetch-latest test suite."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# These run at module-load time (when pytest first imports this conftest),
# which happens before any test files are collected — so test-file imports
# can rely on the load_posts_tsv module being importable.

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent.parent

# Load real .env so live tests inherit credentials.
load_dotenv(PROJECT_ROOT / ".env")

# Allow `import load_posts_tsv` from test modules.
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# load_posts_tsv.py dereferences ANTHROPIC_API_KEY at module load. In
# environments without it (e.g. clean CI for unit-only runs), set a dummy
# so the import succeeds — unit tests mock the Anthropic client anyway.
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
