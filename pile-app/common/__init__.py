"""Shared infrastructure for the Ingestion Pipeline App's pipeline services.

Loads `pile-app/.env` at import time so any subsequent `from common import ...`
inherits the operator's credentials. python-dotenv defaults to NOT overriding
existing env vars, so test fixtures that set dummies before importing this
package keep their dummies.
"""

from pathlib import Path

from dotenv import load_dotenv

APP_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(APP_ROOT / ".env")
