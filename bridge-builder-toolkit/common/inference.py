"""LLM-analyst inference wrapper (T008).

Role-based naming only (Rule #3): the public surface speaks of an
``AnalystLayer`` that returns ``inferred`` values with a ``rationale`` and the
``preserved_inputs`` that produced them (Principle V / Rule #4) — never a model
name. The provider call sits behind a swappable ``responder`` seam so tests run
with no network and no credentials.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable

# Configurable model id. This is a configuration *value*, not an identifier
# name, so Rule #3 (no model names in identifiers) is preserved.
DEFAULT_MODEL = os.environ.get("BRIDGE_INFERENCE_MODEL", "claude-fable-5")
DEFAULT_MAX_TOKENS = 1024

Responder = Callable[[str], str]


@dataclass
class InferenceResult:
    """An inferred value bundled with the inputs that produced it (Principle V)."""

    prompt_ref: str                        # role-named reference, e.g. "infer_region"
    inferred: str
    preserved_inputs: dict[str, Any] = field(default_factory=dict)
    rationale: str | None = None


class AnalystLayer:
    """The LLM-analyst seam shared by every enhanced/synthesis stage."""

    def __init__(
        self,
        *,
        responder: Responder | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self._responder = responder or self._provider_responder
        self._model = model
        self._max_tokens = max_tokens

    def infer(
        self,
        prompt_ref: str,
        prompt: str,
        inputs: dict[str, Any] | None = None,
        *,
        rationale: str | None = None,
    ) -> InferenceResult:
        """Run one inference, preserving ``inputs`` alongside the output."""
        output = self._responder(prompt)
        return InferenceResult(
            prompt_ref=prompt_ref,
            inferred=output,
            preserved_inputs=dict(inputs or {}),
            rationale=rationale,
        )

    def _provider_responder(self, prompt: str) -> str:
        import anthropic  # lazy: tests inject a responder and never import this

        client = anthropic.Anthropic()    # reads ANTHROPIC_API_KEY from the env
        message = client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )
