"""LLM SDK wrapper + the JSON-and-prose response parser.

Provides:
  - `get_anthropic_client()` — single source of truth for the SDK client.
  - `call_messages(client, **kwargs)` — wraps `client.messages.create` and
    translates Anthropic's no-retry-will-help error classes (auth failure,
    permanent rate limit, credit exhaustion, permission denied) into
    `InferenceHardBlockError`. Callers MUST let that propagate — it's the
    inference-side equivalent of an Instagram checkpoint per FR-052.
  - `extract_json_and_reasoning(raw)` — handles markdown code fences AND
    prose preambles, so a model that writes reasoning before its JSON
    doesn't lose either piece. The prose lands in the `reasoning` column
    per FR-105 (inference inputs / rationale preserved).

The module reads `ANTHROPIC_API_KEY` at import time. Tests that mock the
SDK set `ANTHROPIC_API_KEY=test-dummy-key-do-not-use` in conftest before
importing — python-dotenv's default override=False keeps the dummy.
"""

from __future__ import annotations

import json
import os
from typing import Optional

import anthropic

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]


class InferenceHardBlockError(Exception):
    """Raised when the LLM provider returns an error no retry can recover.

    Per FR-052's edge-case bullet, the spec treats inference exhaustion the
    same as an Instagram challenge: halt the scrape, preserve everything
    already written to the pile, surface an operator-facing prompt.

    Callers between the SDK and the run-loop MUST let this propagate — do
    not catch it in `except Exception`, do not absorb it into a returned
    empty tuple. `run_for_target` is the only legitimate catch site.
    """


# The Anthropic SDK exception classes that mean "no retry will help":
#   - RateLimitError (429) — exhausted quota; usually rolls over at the
#     monthly cycle but a mid-run retry won't help.
#   - AuthenticationError (401) — bad / revoked key.
#   - PermissionDeniedError (403) — disabled key, missing scope, etc.
# Transient classes (APIConnectionError, APITimeoutError, 5xx APIStatusError)
# are intentionally NOT in this set — they should percolate up as ordinary
# exceptions for the caller's existing soft-failure handling.
_HARD_BLOCK_EXC = (
    anthropic.RateLimitError,
    anthropic.AuthenticationError,
    anthropic.PermissionDeniedError,
)


def get_anthropic_client() -> anthropic.Anthropic:
    """Build a fresh Anthropic SDK client. Cheap; safe to call per request."""
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def call_messages(client: anthropic.Anthropic, **kwargs):
    """Wrap `client.messages.create(**kwargs)` so the hard-block exception
    classes get translated to `InferenceHardBlockError`. Other exceptions
    pass through unchanged for the caller's existing soft-failure handling.
    """
    try:
        return client.messages.create(**kwargs)
    except _HARD_BLOCK_EXC as exc:
        raise InferenceHardBlockError(f"{type(exc).__name__}: {exc}") from exc


def extract_json_and_reasoning(raw: str) -> tuple[Optional[dict], str]:
    """Parse a model response that may have prose preamble before its JSON.

    Strips ``` fences first, then looks for the last balanced {...} block —
    that's the JSON we asked for. Anything before it is returned as
    ``reasoning`` so it isn't lost (helpful when the model's inference
    rationale is itself useful context for downstream review).

    Returns (parsed_dict_or_None, reasoning_string). When no JSON is parseable,
    the whole raw text becomes the reasoning and the dict is None.
    """
    raw = raw.strip()
    if raw.startswith("```"):
        first_nl = raw.find("\n")
        if first_nl != -1:
            raw = raw[first_nl + 1:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    last_open = raw.rfind("{")
    last_close = raw.rfind("}")
    if last_open != -1 and last_close > last_open:
        json_text = raw[last_open:last_close + 1]
        reasoning = raw[:last_open].strip()
        try:
            return json.loads(json_text), reasoning
        except json.JSONDecodeError:
            pass
    return None, raw
