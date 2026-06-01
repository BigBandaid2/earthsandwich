"""Unit tests for the location helper functions.

These tests mock `anthropic.Anthropic` so they're fast (<1s total), don't
require credentials, and don't hit any external service. Safe to run on
every PR push and in pre-commit hooks.

What they cover:
  - `canonicalize_tagged_location` (FR-019 tagged path) — canonical name +
    coords + IATA in one call, with the tag-name-authoritative semantics.
  - `infer_post_location` (FR-020 inferred path) — JSON parsing including
    markdown-fenced variants and prose preambles.
  - Image inclusion semantics: included for IMAGE posts with a real file,
    skipped for VIDEO and for IMAGE posts where the download failed.
  - Recent-locations injection into the inferred prompt, and the bias-
    guard wording that prevents the model from defaulting to nearby context.

The end-to-end branching logic (tagged vs. inferred dispatch in
`process_media`) is covered by `test_process_media.py`.
"""

from unittest.mock import MagicMock

import pytest

import common.inference
from instagram.inferred_location import infer_post_location
from instagram.tagged_location import canonicalize_tagged_location


def _mock_response(text: str) -> MagicMock:
    """Build a fake Anthropic API response with the given text content."""
    block = MagicMock()
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


@pytest.fixture
def mock_anthropic_client(monkeypatch):
    """Patch `anthropic.Anthropic` (referenced inside common.inference) to
    return a mock client. Tests configure `mock_client.messages.create.return_value`
    (or `.side_effect`) to control the model's reply."""
    mock_client = MagicMock()
    mock_class = MagicMock(return_value=mock_client)
    monkeypatch.setattr(common.inference.anthropic, "Anthropic", mock_class)
    return mock_client


# ---------------------------------------------------------------------------
# canonicalize_tagged_location — FR-019 tail (canonical name + IATA in one call)
# ---------------------------------------------------------------------------

class TestCanonicalizeTaggedLocation:
    """Tag NAME is authoritative (poster's intent); the model returns canonical
    name + canonical coords + IATA. When name and input coords conflict, the
    model produces coords for the *named* place rather than echoing the
    conflicting input."""

    VALID_JSON = (
        '{"canonical_name":"Alki Beach Park, Seattle, USA",'
        '"lat":"47.58","lng":"-122.41","region":"SEA"}'
    )
    PARSED = ("Alki Beach Park, Seattle, USA", "47.58", "-122.41", "SEA", "")

    def test_parses_clean_json(self, mock_anthropic_client):
        mock_anthropic_client.messages.create.return_value = _mock_response(self.VALID_JSON)
        assert canonicalize_tagged_location("Alki Beach Park", "47.58", "-122.41") == self.PARSED

    def test_name_coord_conflict_overrides_with_named_place_coords(self, mock_anthropic_client):
        """Regression for the @ourearthsandwich corpus's tag-coord mismatches:
        a tag named 'Sucre, Bolivia' with coordinates in China should be
        canonicalized to Sucre with Bolivian coordinates, not Lishui with
        Chinese coordinates. The model trusts the NAME."""
        mock_anthropic_client.messages.create.return_value = _mock_response(
            '{"canonical_name":"Sucre, Chuquisaca, Bolivia",'
            '"lat":"-19.04","lng":"-65.26","region":"SRE"}'
        )
        result = canonicalize_tagged_location("Sucre, Bolivia", "28.99", "118.85")
        assert result == ("Sucre, Chuquisaca, Bolivia", "-19.04", "-65.26", "SRE", "")

    def test_matching_name_and_coords_echoes_input_coords(self, mock_anthropic_client):
        """Common case: name and coords agree. The model echoes the input
        coords verbatim (or near-verbatim) as the canonical coords."""
        mock_anthropic_client.messages.create.return_value = _mock_response(
            '{"canonical_name":"Paris, France",'
            '"lat":"48.8566","lng":"2.3522","region":"CDG"}'
        )
        result = canonicalize_tagged_location("Paris", "48.8566", "2.3522")
        assert result == ("Paris, France", "48.8566", "2.3522", "CDG", "")

    def test_lowercased_region_is_uppercased_and_validated(self, mock_anthropic_client):
        mock_anthropic_client.messages.create.return_value = _mock_response(
            '{"canonical_name":"Paris, France","lat":"48.85","lng":"2.35","region":"cdg"}'
        )
        result = canonicalize_tagged_location("Paris", "48.85", "2.35")
        assert result == ("Paris, France", "48.85", "2.35", "CDG", "")

    def test_punctuated_region_is_stripped(self, mock_anthropic_client):
        mock_anthropic_client.messages.create.return_value = _mock_response(
            '{"canonical_name":"Los Angeles, USA","lat":"34.05","lng":"-118.24","region":"LAX."}'
        )
        result = canonicalize_tagged_location("LA", "34.05", "-118.24")
        assert result == ("Los Angeles, USA", "34.05", "-118.24", "LAX", "")

    def test_typo_in_tag_gets_corrected_when_canonicalize_does(self, mock_anthropic_client):
        """Passes the typo through to the model; the test mocks the canonical
        form. Real correction quality is exercised by the integration test."""
        mock_anthropic_client.messages.create.return_value = _mock_response(
            '{"canonical_name":"Oaxaca City, Oaxaca, Mexico",'
            '"lat":"17.06","lng":"-96.72","region":"OAX"}'
        )
        result = canonicalize_tagged_location("Oxaca", "17.06", "-96.72")
        assert result == ("Oaxaca City, Oaxaca, Mexico", "17.06", "-96.72", "OAX", "")

    def test_empty_canonical_name_returns_empty(self, mock_anthropic_client):
        """All-empty JSON (model couldn't determine anything) → empty fields.
        Callers fall back to the verbatim tag in that case."""
        mock_anthropic_client.messages.create.return_value = _mock_response(
            '{"canonical_name":"","lat":"","lng":"","region":""}'
        )
        assert canonicalize_tagged_location("???", "", "") == ("", "", "", "", "")

    def test_empty_canonical_lat_lng_returns_empty_strings(self, mock_anthropic_client):
        """For hyper-local tags where the model can produce a canonical name
        but can't determine precise coords, the lat/lng come back empty so
        the caller can fall back to the verbatim instagrapi-provided coords."""
        mock_anthropic_client.messages.create.return_value = _mock_response(
            '{"canonical_name":"Some Hyper-Local Place, Some City, Country",'
            '"lat":"","lng":"","region":"XYZ"}'
        )
        result = canonicalize_tagged_location("hyperlocal tag", "1.23", "4.56")
        assert result == ("Some Hyper-Local Place, Some City, Country", "", "", "XYZ", "")

    def test_invalid_region_format_is_blanked(self, mock_anthropic_client):
        """A region that isn't a clean 3-letter code is rejected — better empty
        than wrong. Other fields pass through."""
        mock_anthropic_client.messages.create.return_value = _mock_response(
            '{"canonical_name":"Somewhere, Country","lat":"0","lng":"0","region":"NOT-VALID"}'
        )
        assert canonicalize_tagged_location("X", "0", "0") == ("Somewhere, Country", "0", "0", "", "")

    def test_returns_empty_when_api_raises(self, mock_anthropic_client):
        mock_anthropic_client.messages.create.side_effect = RuntimeError("rate limit")
        assert canonicalize_tagged_location("Anywhere", "0", "0") == ("", "", "", "", "")

    def test_returns_empty_on_unparseable_response(self, mock_anthropic_client):
        """When the model writes prose with no JSON at all, all fields blank
        and the prose is surfaced as reasoning."""
        mock_anthropic_client.messages.create.return_value = _mock_response(
            "I'm not sure where this is"
        )
        canonical, lat, lng, region, reasoning = canonicalize_tagged_location("???", "0", "0")
        assert canonical == ""
        assert lat == lng == region == ""
        assert "I'm not sure" in reasoning

    def test_does_not_send_image(self, mock_anthropic_client):
        """The canonicalize call is text-only — no vision required since the
        tag name + coords carry all the necessary input."""
        mock_anthropic_client.messages.create.return_value = _mock_response(self.VALID_JSON)
        canonicalize_tagged_location("Alki Beach Park", "47.58", "-122.41")
        messages = mock_anthropic_client.messages.create.call_args.kwargs["messages"]
        assert isinstance(messages[0]["content"], str)

    def test_prompt_includes_verbatim_tag_and_coords(self, mock_anthropic_client):
        """Sanity check that the prompt carries the inputs the model needs."""
        mock_anthropic_client.messages.create.return_value = _mock_response(self.VALID_JSON)
        canonicalize_tagged_location("Oxaca", "17.06", "-96.72")
        prompt = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "Oxaca" in prompt
        assert "17.06" in prompt
        assert "-96.72" in prompt

    def test_prompt_states_tag_name_is_authoritative(self, mock_anthropic_client):
        """Regression: the prompt MUST tell the model the tag NAME is
        authoritative when conflicting with coords. Removing this language
        previously caused Sucre→Lishui and Medellín→Mexico City failures."""
        mock_anthropic_client.messages.create.return_value = _mock_response(self.VALID_JSON)
        canonicalize_tagged_location("Anywhere", "0", "0")
        prompt = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "AUTHORITATIVE" in prompt
        assert "TRUST THE NAME" in prompt or "trust the name" in prompt.lower()

    def test_extracts_json_from_prose_preamble(self, mock_anthropic_client):
        """Regression: the model sometimes writes reasoning prose before the
        JSON. The parser must skip the prose and parse the trailing object,
        and preserve the prose as `reasoning`."""
        mock_anthropic_client.messages.create.return_value = _mock_response(
            "The tag name and coords both point to Mexico City — they agree.\n\n"
            '{"canonical_name":"Mexico City, Mexico","lat":"19.43","lng":"-99.13","region":"MEX"}'
        )
        canonical, lat, lng, region, reasoning = canonicalize_tagged_location("Mexico City", "19.43", "-99.13")
        assert canonical == "Mexico City, Mexico"
        assert lat == "19.43"
        assert lng == "-99.13"
        assert region == "MEX"
        assert "tag name and coords both point" in reasoning


# ---------------------------------------------------------------------------
# infer_post_location — FR-020 inferred path
# ---------------------------------------------------------------------------

class TestInferPostLocation:
    VALID_JSON = '{"location":"Paris","lat":"48.8566","lng":"2.3522","region":"CDG"}'
    PARSED = ("Paris", "48.8566", "2.3522", "CDG", "")

    def test_parses_clean_json(self, mock_anthropic_client):
        mock_anthropic_client.messages.create.return_value = _mock_response(self.VALID_JSON)
        result = infer_post_location(
            caption="Eiffel views", local_media_path="", media_type="IMAGE", recent_locations=[]
        )
        assert result == self.PARSED

    def test_strips_json_code_fences(self, mock_anthropic_client):
        """Regression: the model sometimes wraps the JSON in ```json fences
        despite the prompt asking not to. The parser must tolerate this."""
        wrapped = f"```json\n{self.VALID_JSON}\n```"
        mock_anthropic_client.messages.create.return_value = _mock_response(wrapped)
        result = infer_post_location(
            caption="x", local_media_path="", media_type="IMAGE", recent_locations=[]
        )
        assert result == self.PARSED

    def test_strips_plain_code_fences(self, mock_anthropic_client):
        wrapped = f"```\n{self.VALID_JSON}\n```"
        mock_anthropic_client.messages.create.return_value = _mock_response(wrapped)
        result = infer_post_location(
            caption="x", local_media_path="", media_type="IMAGE", recent_locations=[]
        )
        assert result == self.PARSED

    def test_extracts_json_from_prose_preamble(self, mock_anthropic_client):
        """Regression for the prose-preamble bug found during the @ourearthsandwich
        from-scratch scrape (23 rows affected). The model sometimes writes
        reasoning before the JSON object — the parser must skip the prose,
        parse the JSON, and preserve the prose as `reasoning`."""
        response = (
            "Looking at the evidence:\n\n"
            "1. The boarding pass is from Virgin America, Flight VX 23\n"
            "2. The destination appears to be Los Angeles (LAX)\n\n"
            "The person is at JFK Airport, departing from New York.\n\n"
            '{"location":"JFK Airport, Queens, NY, USA","lat":"40.6413","lng":"-73.7781","region":"JFK"}'
        )
        mock_anthropic_client.messages.create.return_value = _mock_response(response)
        location, lat, lng, region, reasoning = infer_post_location(
            caption="adios", local_media_path="", media_type="IMAGE", recent_locations=[]
        )
        assert location == "JFK Airport, Queens, NY, USA"
        assert lat == "40.6413"
        assert lng == "-73.7781"
        assert region == "JFK"
        assert "Looking at the evidence" in reasoning
        assert "Virgin America" in reasoning

    def test_pure_prose_response_returns_empty_location(self, mock_anthropic_client):
        """When the model writes prose with no JSON at all, location returns
        EMPTY (so the call-site city-level fallback engages) and the prose
        is preserved in `reasoning` for audit. This is the post-fix behavior;
        previously the raw prose was used as the location string."""
        mock_anthropic_client.messages.create.return_value = _mock_response(
            "I think this is somewhere in France based on the architecture"
        )
        location, lat, lng, region, reasoning = infer_post_location(
            caption="x", local_media_path="", media_type="IMAGE", recent_locations=[]
        )
        assert location == ""
        assert lat == lng == region == ""
        assert "France" in reasoning

    def test_rejects_location_exceeding_max_length(self, mock_anthropic_client):
        """The model occasionally puts prose into the JSON's `location` field
        despite the prompt — a 'location' string over 200 chars is rejected
        as malformed; location returns empty and the rejected text plus a
        rejection note end up in `reasoning`."""
        long_loc = "I can see a sign that says XYZ " * 10
        payload = (
            '{"location":"' + long_loc + '","lat":"","lng":"","region":""}'
        )
        mock_anthropic_client.messages.create.return_value = _mock_response(payload)
        location, lat, lng, region, reasoning = infer_post_location(
            caption="x", local_media_path="", media_type="IMAGE", recent_locations=[]
        )
        assert location == ""
        assert lat == lng == region == ""
        assert "parser rejected location" in reasoning

    def test_rejects_location_containing_newline(self, mock_anthropic_client):
        """A 'location' field containing a newline is treated as malformed
        regardless of length — real place names are single-line."""
        payload = '{"location":"Empire State\\nBuilding","lat":"40.7","lng":"-74","region":"JFK"}'
        mock_anthropic_client.messages.create.return_value = _mock_response(payload)
        location, lat, lng, region, reasoning = infer_post_location(
            caption="x", local_media_path="", media_type="IMAGE", recent_locations=[]
        )
        assert location == ""
        assert "parser rejected location" in reasoning

    def test_handles_empty_string_fields(self, mock_anthropic_client):
        """All-empty JSON (model couldn't determine anything) → all-empty tuple
        with no reasoning preamble."""
        mock_anthropic_client.messages.create.return_value = _mock_response(
            '{"location":"","lat":"","lng":"","region":""}'
        )
        result = infer_post_location(
            caption="x", local_media_path="", media_type="IMAGE", recent_locations=[]
        )
        assert result == ("", "", "", "", "")

    def test_includes_image_for_photo_when_file_exists(self, mock_anthropic_client, tmp_path):
        """IMAGE posts with a downloaded media file send the image bytes to
        the model (vision input)."""
        img = tmp_path / "post.jpg"
        img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 50)
        mock_anthropic_client.messages.create.return_value = _mock_response(self.VALID_JSON)

        infer_post_location(
            caption="x", local_media_path=str(img), media_type="IMAGE", recent_locations=[]
        )

        content = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        image_blocks = [p for p in content if isinstance(p, dict) and p.get("type") == "image"]
        assert len(image_blocks) == 1
        assert image_blocks[0]["source"]["type"] == "base64"
        assert image_blocks[0]["source"]["media_type"] == "image/jpeg"

    def test_skips_image_for_video(self, mock_anthropic_client, tmp_path):
        """VIDEO posts must not send the video file as an image input —
        the vision API rejects video bytes and we'd waste tokens."""
        vid = tmp_path / "post.mp4"
        vid.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 100)
        mock_anthropic_client.messages.create.return_value = _mock_response(self.VALID_JSON)

        infer_post_location(
            caption="x", local_media_path=str(vid), media_type="VIDEO", recent_locations=[]
        )

        content = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        image_blocks = [p for p in content if isinstance(p, dict) and p.get("type") == "image"]
        assert image_blocks == []

    def test_skips_image_when_file_missing(self, mock_anthropic_client):
        """If the IMAGE download failed earlier (no local file), the call
        still goes out with caption + context only — no image block."""
        mock_anthropic_client.messages.create.return_value = _mock_response(self.VALID_JSON)

        infer_post_location(
            caption="x", local_media_path="/nonexistent/path.jpg",
            media_type="IMAGE", recent_locations=[]
        )

        content = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        image_blocks = [p for p in content if isinstance(p, dict) and p.get("type") == "image"]
        assert image_blocks == []

    def test_includes_recent_locations_in_prompt(self, mock_anthropic_client):
        """The inferred path passes up to RECENT_LOCATION_COUNT recent
        locations as context. They must appear in the prompt text."""
        mock_anthropic_client.messages.create.return_value = _mock_response(self.VALID_JSON)

        infer_post_location(
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
        mock_anthropic_client.messages.create.return_value = _mock_response(self.VALID_JSON)

        infer_post_location(
            caption="x", local_media_path="", media_type="IMAGE",
            recent_locations=["", "Tokyo", "", "Kyoto", ""],
        )

        content = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        prompt_text = next(p["text"] for p in content if p.get("type") == "text")
        assert "Tokyo" in prompt_text
        assert "Kyoto" in prompt_text
        assert "\n- \n" not in prompt_text
        assert not prompt_text.rstrip().endswith("- ")

    def test_prompt_includes_recent_locations_bias_guard(self, mock_anthropic_client):
        """Regression: the bias-guard wording prevents the model from defaulting
        to a recent-context location. Removing it caused the Mexico City =>
        Oaxaca bug. Keep this assertion strict."""
        mock_anthropic_client.messages.create.return_value = _mock_response(self.VALID_JSON)

        infer_post_location(
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
