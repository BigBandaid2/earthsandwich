"""Unit tests for the location helper functions in load_posts_tsv.

These tests mock `anthropic.Anthropic` so they're fast (<1s total), don't
require credentials, and don't hit any external service. Safe to run on
every PR push and in pre-commit hooks.

What they cover:
  - `get_region_only_via_claude` sanitizing Claude's reply into a 3-letter
    IATA code (or empty string) — the FR-019 tagged-path tail.
  - `get_location_via_claude` parsing JSON responses, including markdown-
    fenced variants Claude occasionally returns despite the prompt — the
    FR-020 inferred path.
  - Image inclusion semantics: included for IMAGE posts with a real file,
    skipped for VIDEO and for IMAGE posts where the download failed.
  - Recent-locations injection into the inferred prompt, and the bias-
    guard wording that prevents Claude from defaulting to nearby context.

The end-to-end branching logic in `main()` (tagged vs. inferred dispatch)
is covered by the live integration test in `test_instagram_pull.py`.
"""

from unittest.mock import MagicMock

import pytest

import load_posts_tsv
from load_posts_tsv import get_location_via_claude, get_region_only_via_claude


def _claude_response(text: str) -> MagicMock:
    """Build a fake Anthropic API response with the given text content."""
    block = MagicMock()
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


@pytest.fixture
def mock_anthropic_client(monkeypatch):
    """Patch `anthropic.Anthropic` inside load_posts_tsv to return a mock
    client. Tests configure `mock_client.messages.create.return_value` (or
    `.side_effect`) to control Claude's reply."""
    mock_client = MagicMock()
    mock_class = MagicMock(return_value=mock_client)
    monkeypatch.setattr(load_posts_tsv.anthropic, "Anthropic", mock_class)
    return mock_client


# ---------------------------------------------------------------------------
# get_region_only_via_claude — FR-019 tail
# ---------------------------------------------------------------------------

class TestGetRegionOnlyViaClaude:
    def test_returns_clean_iata_code(self, mock_anthropic_client):
        mock_anthropic_client.messages.create.return_value = _claude_response("MEX")
        assert get_region_only_via_claude("Mexico City", "19.43", "-99.13") == "MEX"

    def test_uppercases_lowercase_response(self, mock_anthropic_client):
        mock_anthropic_client.messages.create.return_value = _claude_response("jfk")
        assert get_region_only_via_claude("New York", "40.75", "-73.99") == "JFK"

    def test_strips_whitespace(self, mock_anthropic_client):
        mock_anthropic_client.messages.create.return_value = _claude_response("  CDG  ")
        assert get_region_only_via_claude("Paris", "48.85", "2.35") == "CDG"

    def test_strips_punctuation(self, mock_anthropic_client):
        mock_anthropic_client.messages.create.return_value = _claude_response("LAX.")
        assert get_region_only_via_claude("Los Angeles", "34.05", "-118.24") == "LAX"

    def test_returns_empty_on_verbose_response(self, mock_anthropic_client):
        """When Claude refuses the format and writes a sentence, fail closed."""
        mock_anthropic_client.messages.create.return_value = _claude_response(
            "I'm not sure which airport applies"
        )
        assert get_region_only_via_claude("Nowhere", "0", "0") == ""

    def test_returns_empty_on_too_short_response(self, mock_anthropic_client):
        mock_anthropic_client.messages.create.return_value = _claude_response("X")
        assert get_region_only_via_claude("X", "0", "0") == ""

    def test_returns_empty_on_empty_response(self, mock_anthropic_client):
        mock_anthropic_client.messages.create.return_value = _claude_response("")
        assert get_region_only_via_claude("Unknown", "", "") == ""

    def test_returns_empty_when_api_raises(self, mock_anthropic_client):
        mock_anthropic_client.messages.create.side_effect = RuntimeError("rate limit")
        assert get_region_only_via_claude("Anywhere", "0", "0") == ""

    def test_does_not_send_image(self, mock_anthropic_client):
        """The text-only IATA call must not include an image — coordinates
        and name are authoritative under FR-019, so vision isn't needed."""
        mock_anthropic_client.messages.create.return_value = _claude_response("MEX")
        get_region_only_via_claude("Mexico City", "19.43", "-99.13")
        messages = mock_anthropic_client.messages.create.call_args.kwargs["messages"]
        # `content` is a plain string here, not a list with image blocks.
        assert isinstance(messages[0]["content"], str)

    def test_prompt_includes_location_and_coords(self, mock_anthropic_client):
        """Sanity check that the prompt carries the inputs Claude needs."""
        mock_anthropic_client.messages.create.return_value = _claude_response("MEX")
        get_region_only_via_claude("Mexico City", "19.43", "-99.13")
        prompt = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "Mexico City" in prompt
        assert "19.43" in prompt
        assert "-99.13" in prompt


# ---------------------------------------------------------------------------
# get_location_via_claude — FR-020 inferred path
# ---------------------------------------------------------------------------

class TestGetLocationViaClaude:
    VALID_JSON = '{"location":"Paris","lat":"48.8566","lng":"2.3522","region":"CDG"}'
    PARSED = ("Paris", "48.8566", "2.3522", "CDG")

    def test_parses_clean_json(self, mock_anthropic_client):
        mock_anthropic_client.messages.create.return_value = _claude_response(self.VALID_JSON)
        result = get_location_via_claude(
            caption="Eiffel views", local_media_path="", media_type="IMAGE", recent_locations=[]
        )
        assert result == self.PARSED

    def test_strips_json_code_fences(self, mock_anthropic_client):
        """Regression: Claude sometimes wraps the JSON in ```json fences
        despite the prompt asking not to. The parser must tolerate this."""
        wrapped = f"```json\n{self.VALID_JSON}\n```"
        mock_anthropic_client.messages.create.return_value = _claude_response(wrapped)
        result = get_location_via_claude(
            caption="x", local_media_path="", media_type="IMAGE", recent_locations=[]
        )
        assert result == self.PARSED

    def test_strips_plain_code_fences(self, mock_anthropic_client):
        wrapped = f"```\n{self.VALID_JSON}\n```"
        mock_anthropic_client.messages.create.return_value = _claude_response(wrapped)
        result = get_location_via_claude(
            caption="x", local_media_path="", media_type="IMAGE", recent_locations=[]
        )
        assert result == self.PARSED

    def test_falls_back_to_raw_text_on_invalid_json(self, mock_anthropic_client):
        """When Claude writes prose instead of JSON, the raw text becomes the
        location name and coords/region stay empty. Documented behavior."""
        mock_anthropic_client.messages.create.return_value = _claude_response(
            "I think this is somewhere in France"
        )
        result = get_location_via_claude(
            caption="x", local_media_path="", media_type="IMAGE", recent_locations=[]
        )
        assert result == ("I think this is somewhere in France", "", "", "")

    def test_handles_empty_string_fields(self, mock_anthropic_client):
        """All-empty JSON (Claude couldn't determine anything) → all-empty tuple."""
        mock_anthropic_client.messages.create.return_value = _claude_response(
            '{"location":"","lat":"","lng":"","region":""}'
        )
        result = get_location_via_claude(
            caption="x", local_media_path="", media_type="IMAGE", recent_locations=[]
        )
        assert result == ("", "", "", "")

    def test_includes_image_for_photo_when_file_exists(self, mock_anthropic_client, tmp_path):
        """IMAGE posts with a downloaded media file send the image bytes to
        Claude (vision input)."""
        img = tmp_path / "post.jpg"
        img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 50)  # minimal JPEG header
        mock_anthropic_client.messages.create.return_value = _claude_response(self.VALID_JSON)

        get_location_via_claude(
            caption="x", local_media_path=str(img), media_type="IMAGE", recent_locations=[]
        )

        content = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        image_blocks = [p for p in content if isinstance(p, dict) and p.get("type") == "image"]
        assert len(image_blocks) == 1
        assert image_blocks[0]["source"]["type"] == "base64"
        assert image_blocks[0]["source"]["media_type"] == "image/jpeg"

    def test_skips_image_for_video(self, mock_anthropic_client, tmp_path):
        """VIDEO posts must not send the video file as an image input —
        Claude's vision API rejects video bytes and we'd waste tokens."""
        vid = tmp_path / "post.mp4"
        vid.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 100)
        mock_anthropic_client.messages.create.return_value = _claude_response(self.VALID_JSON)

        get_location_via_claude(
            caption="x", local_media_path=str(vid), media_type="VIDEO", recent_locations=[]
        )

        content = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        image_blocks = [p for p in content if isinstance(p, dict) and p.get("type") == "image"]
        assert image_blocks == []

    def test_skips_image_when_file_missing(self, mock_anthropic_client):
        """If the IMAGE download failed earlier (no local file), the call
        still goes out with caption + context only — no image block."""
        mock_anthropic_client.messages.create.return_value = _claude_response(self.VALID_JSON)

        get_location_via_claude(
            caption="x", local_media_path="/nonexistent/path.jpg",
            media_type="IMAGE", recent_locations=[]
        )

        content = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        image_blocks = [p for p in content if isinstance(p, dict) and p.get("type") == "image"]
        assert image_blocks == []

    def test_includes_recent_locations_in_prompt(self, mock_anthropic_client):
        """The inferred path passes up to RECENT_LOCATION_COUNT recent
        locations as context. They must appear in the prompt text."""
        mock_anthropic_client.messages.create.return_value = _claude_response(self.VALID_JSON)

        get_location_via_claude(
            caption="x", local_media_path="", media_type="IMAGE",
            recent_locations=["Oaxaca City", "Mexico City", "Puebla"],
        )

        content = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        text_blocks = [p for p in content if isinstance(p, dict) and p.get("type") == "text"]
        assert text_blocks, "no text block in prompt"
        prompt_text = text_blocks[0]["text"]
        assert "Oaxaca City" in prompt_text
        assert "Mexico City" in prompt_text
        assert "Puebla" in prompt_text

    def test_excludes_empty_recent_locations_from_prompt(self, mock_anthropic_client):
        """Empty entries in the recent list are filtered before formatting
        so they don't produce empty "- " bullets in the prompt."""
        mock_anthropic_client.messages.create.return_value = _claude_response(self.VALID_JSON)

        get_location_via_claude(
            caption="x", local_media_path="", media_type="IMAGE",
            recent_locations=["", "Tokyo", "", "Kyoto", ""],
        )

        content = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        prompt_text = next(p["text"] for p in content if p.get("type") == "text")
        assert "Tokyo" in prompt_text
        assert "Kyoto" in prompt_text
        # An empty entry would render as the bullet "- " followed by newline
        # or end-of-string. Spot-check neither pattern exists.
        assert "\n- \n" not in prompt_text
        assert not prompt_text.rstrip().endswith("- ")

    def test_prompt_includes_recent_locations_bias_guard(self, mock_anthropic_client):
        """Regression: the bias-guard wording prevents Claude from defaulting
        to a recent-context location. Removing it caused the Mexico City =>
        Oaxaca bug. Keep this assertion strict."""
        mock_anthropic_client.messages.create.return_value = _claude_response(self.VALID_JSON)

        get_location_via_claude(
            caption="x", local_media_path="", media_type="IMAGE",
            recent_locations=["Oaxaca"],
        )

        content = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        prompt_text = next(p["text"] for p in content if p.get("type") == "text")
        assert "do NOT assume" in prompt_text, (
            "The bias-guard wording is missing from the inferred-path prompt. "
            "Removing this guard previously caused tagged Mexico City posts "
            "(when the geo-tag wasn't available) to be mis-identified as "
            "Oaxaca City because the recent-locations context dominated."
        )
