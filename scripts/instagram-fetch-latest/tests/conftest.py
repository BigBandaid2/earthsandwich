"""Shared pytest fixtures and config for the instagram-fetch-latest test suite."""

from pathlib import Path

from dotenv import load_dotenv


def pytest_configure(config):
    """Register custom markers so `pytest --strict-markers` is happy."""
    config.addinivalue_line(
        "markers",
        "integration: tests that hit live external services (Instagram via "
        "instagrapi, the Anthropic API). Require INSTA_USERNAME / INSTA_PASSWORD "
        "/ ANTHROPIC_API_KEY in the environment and a working instagrapi session. "
        "Skipped automatically when credentials are missing.",
    )

    # Load .env from the project root so subprocess invocations inside tests
    # inherit the same credentials the script itself uses.
    project_root = Path(__file__).resolve().parents[3]
    load_dotenv(project_root / ".env")
