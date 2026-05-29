"""LLM SDK wrapper + the JSON-and-prose response parser.

Provides:
  - `get_anthropic_client()` — single source of truth for the SDK client.
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


def get_anthropic_client() -> anthropic.Anthropic:
    """Build a fresh Anthropic SDK client. Cheap; safe to call per request."""
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


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
