"""Phase 21 / US2: tests for the FR-052 hard-block categorization and the
inference-exhaustion-as-hard-block behavior from the spec's edge-case bullet.

What's covered:
  - `is_challenge_error` classifies the spec-named hard-block patterns
    (challenge_required, checkpoint_required, login_required) correctly and
    NOT the transient ones (connection-reset, 5xx, timeout, network).
  - `InferenceHardBlockError` propagates from `infer_post_location` through
    `process_media` (the existing `except Exception` in process_media MUST
    NOT swallow it) so `run_for_target` can halt cleanly.
  - The tagged-path equivalent: `canonicalize_tagged_location`'s broad
    except clause MUST also let `InferenceHardBlockError` through.
  - Non-hard-block inference exceptions (e.g., transient network glitches)
    still get the soft-failure handling — the row is written with empty
    location and the scrape proceeds.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import anthropic
import pytest

import common.inference
import instagram.inferred_location
import instagram.pipeline
import instagram.tagged_location
from common.anti_throttle import is_challenge_error
from common.inference import InferenceHardBlockError, call_messages
from instagram.inferred_location import infer_post_location
from instagram.pipeline import process_media
from instagram.tagged_location import canonicalize_tagged_location


# ---------------------------------------------------------------------------
# T231 — is_challenge_error categorization audit
# ---------------------------------------------------------------------------

class TestIsChallengeErrorCategorization:
    """The FR-052 keyword set. Hard blocks halt; everything else is treated
    as transient and retried once."""

    @pytest.mark.parametrize("message", [
        "ChallengeRequired: please complete verification",
        "challenge_required (user must verify)",
        "STEP_NAME: VERIFY_EMAIL",
        "checkpoint_required",
        "CheckpointRequired",
        "LoginRequired",
        "login_required (session expired)",
    ])
    def test_hard_block_patterns_classified_as_challenge(self, message):
        assert is_challenge_error(RuntimeError(message)) is True

    @pytest.mark.parametrize("message", [
        "Connection reset by peer",
        "HTTPSConnectionPool: timeout",
        "503 Service Unavailable",
        "504 Gateway Timeout",
        "Temporary failure in name resolution",
        "JSONDecodeError: Expecting value",
    ])
    def test_transient_patterns_not_classified_as_challenge(self, message):
        assert is_challenge_error(RuntimeError(message)) is False


# ---------------------------------------------------------------------------
# T229 — InferenceHardBlockError propagation
# ---------------------------------------------------------------------------

def _mock_response(text: str) -> MagicMock:
    block = MagicMock()
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


class TestCallMessagesHardBlockTranslation:
    """`call_messages` is the single chokepoint that translates the SDK's
    no-retry-will-help error classes into InferenceHardBlockError. Other
    SDK exceptions percolate up unchanged."""

    def test_rate_limit_translates_to_hard_block(self, monkeypatch):
        client = MagicMock()
        # anthropic.RateLimitError signature: (message, response, body)
        client.messages.create.side_effect = anthropic.RateLimitError(
            "quota exhausted",
            response=MagicMock(request=MagicMock(), status_code=429),
            body=None,
        )
        with pytest.raises(InferenceHardBlockError, match="RateLimitError"):
            call_messages(client, model="x", max_tokens=1, messages=[])

    def test_authentication_error_translates_to_hard_block(self, monkeypatch):
        client = MagicMock()
        client.messages.create.side_effect = anthropic.AuthenticationError(
            "invalid x-api-key",
            response=MagicMock(request=MagicMock(), status_code=401),
            body=None,
        )
        with pytest.raises(InferenceHardBlockError, match="AuthenticationError"):
            call_messages(client, model="x", max_tokens=1, messages=[])

    def test_permission_denied_translates_to_hard_block(self):
        client = MagicMock()
        client.messages.create.side_effect = anthropic.PermissionDeniedError(
            "key disabled",
            response=MagicMock(request=MagicMock(), status_code=403),
            body=None,
        )
        with pytest.raises(InferenceHardBlockError, match="PermissionDenied"):
            call_messages(client, model="x", max_tokens=1, messages=[])

    def test_other_exceptions_pass_through_unchanged(self):
        client = MagicMock()
        client.messages.create.side_effect = RuntimeError("network glitch")
        with pytest.raises(RuntimeError, match="network glitch"):
            call_messages(client, model="x", max_tokens=1, messages=[])


class TestInferredPathHardBlockPropagation:
    """When `infer_post_location` raises InferenceHardBlockError,
    `process_media`'s `except Exception` MUST NOT swallow it — it has to
    reach `run_for_target` so the scrape halts cleanly per FR-052."""

    def _make_post_with_no_tag(self):
        return SimpleNamespace(
            pk=42, code="HBLOCK1",
            caption_text="x",
            taken_at=datetime(2026, 5, 29, 10, 0, 0, tzinfo=timezone.utc),
            media_type=1,
            thumbnail_url="",
            video_url="",
            resources=None,
            location=None,
        )

    def test_inferred_hard_block_propagates_through_process_media(self, monkeypatch):
        def _raise_hard_block(*args, **kwargs):
            raise InferenceHardBlockError("RateLimitError: quota exhausted")
        monkeypatch.setattr(instagram.pipeline, "infer_post_location", _raise_hard_block)
        # Stub download_media so we don't try to fetch a real URL
        monkeypatch.setattr(instagram.pipeline, "download_media", MagicMock(return_value=""))

        m = self._make_post_with_no_tag()
        with pytest.raises(InferenceHardBlockError):
            process_media(m, target="acct", local_id=1, media_dir="/tmp", recent_locations=[])

    def test_inferred_transient_failure_still_soft_swallowed(self, monkeypatch):
        """A non-hard-block exception (RuntimeError simulating a network blip)
        keeps the existing soft-failure behavior: empty location fields,
        row still constructed, scrape continues."""
        def _raise_transient(*args, **kwargs):
            raise RuntimeError("ConnectionError: temporary")
        monkeypatch.setattr(instagram.pipeline, "infer_post_location", _raise_transient)
        monkeypatch.setattr(instagram.pipeline, "download_media", MagicMock(return_value=""))

        m = self._make_post_with_no_tag()
        row = process_media(m, target="acct", local_id=1, media_dir="/tmp", recent_locations=[])
        assert row["location"] == ""
        assert row["instagram_id"] == "42"


class TestTaggedPathHardBlockPropagation:
    """canonicalize_tagged_location's broad `except Exception` exists for the
    soft-failure case (network glitch → return empty tuple). The hard-block
    case must skip that and let InferenceHardBlockError propagate."""

    def test_canonicalize_hard_block_propagates(self, monkeypatch):
        # Inject a hard-block into the SDK call via call_messages's translation.
        # Patch at the IMPORT SITE — tagged_location.py does
        # `from common.inference import ... get_anthropic_client`, so the
        # local binding has to be what's patched.
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.RateLimitError(
            "quota exhausted",
            response=MagicMock(request=MagicMock(), status_code=429),
            body=None,
        )
        monkeypatch.setattr(instagram.tagged_location, "get_anthropic_client", lambda: mock_client)

        with pytest.raises(InferenceHardBlockError):
            canonicalize_tagged_location("Anywhere", "0", "0")

    def test_canonicalize_transient_failure_still_returns_empty_tuple(self, monkeypatch):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("network glitch")
        monkeypatch.setattr(instagram.tagged_location, "get_anthropic_client", lambda: mock_client)

        # Soft failure — function returns empty tuple, caller falls back to verbatim.
        result = canonicalize_tagged_location("Anywhere", "0", "0")
        assert result == ("", "", "", "", "")


class TestInferPostLocationHardBlockPath:
    """End-to-end: a rate-limit hitting the SDK during infer_post_location
    must surface as InferenceHardBlockError (via call_messages), NOT as the
    function's normal empty-location return."""

    def test_rate_limit_during_inference_surfaces_as_hard_block(self, monkeypatch):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.RateLimitError(
            "quota exhausted",
            response=MagicMock(request=MagicMock(), status_code=429),
            body=None,
        )
        # Patch at the import site — inferred_location.py does
        # `from common.inference import ... get_anthropic_client`.
        monkeypatch.setattr(instagram.inferred_location, "get_anthropic_client", lambda: mock_client)

        with pytest.raises(InferenceHardBlockError):
            infer_post_location(
                caption="x", local_media_path="", media_type="IMAGE", recent_locations=[]
            )
