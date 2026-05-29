"""FR-020 inferred-path location resolution.

When a post has no explicit geo-tag, the model inspects caption + image +
recent-context and produces (location, lat, lng, region, reasoning). The
bias-guard wording in the prompt forbids defaulting to nearby posts — when
the model correctly returns empty, the *call site* applies the chronological-
neighbor fallback so the row inherits the prior post's CITY (not its exact
venue) and records the fact in `reasoning`.

Inputs (caption + media path + recent_locations) are preserved upstream
in the pile per FR-105 / Cardinal Rule #4 — this module's call can be
replayed against a different model without re-fetching the post.
"""

from __future__ import annotations

import base64
import os
from typing import Optional

from common.inference import extract_json_and_reasoning, get_anthropic_client

# Inferred-location sanity bounds. Models occasionally return prose-as-location
# despite the prompt — a "location" longer than this or containing newlines is
# treated as malformed, the row falls through to the city-level fallback, and
# the rejected text is preserved in `reasoning` for audit.
MAX_INFERRED_LOCATION_LEN = 200


def infer_post_location(
    caption: str,
    local_media_path: str,
    media_type: str,
    recent_locations: list[str],
) -> tuple[str, str, str, str, str]:
    """FR-020 inferred-location path: identify the post's location from caption + image + nearby context.

    Used ONLY when the post has no explicit geo-tag (i.e. instagrapi returned no
    `Location` object or instagrapi is unavailable). Tagged posts go through
    `canonicalize_tagged_location` instead.

    Returns a (location, lat, lng, region, reasoning) tuple. Any field may be
    empty. ``reasoning`` captures any prose the model wrote before the JSON
    object — it's the inference rationale, preserved so downstream review can
    audit why a particular location was picked.
    """
    client = get_anthropic_client()

    recent_loc_text = ""
    known_locations = [loc for loc in recent_locations if loc]
    if known_locations:
        loc_list = "\n".join(f"- {loc}" for loc in known_locations)
        recent_loc_text = (
            "\n\nLocations of recent nearby posts (context only — do NOT assume "
            f"this post is at any of these places):\n{loc_list}"
        )

    prompt = (
        f"Caption: {caption or '(none)'}"
        f"{recent_loc_text}\n\n"
        "Identify the specific location of this Instagram post using observable evidence "
        "in the image and caption: visible signage, landmarks, recognizable geographic features, "
        "language cues, or place names mentioned in the caption. "
        "Do NOT default to a recent-posts location unless the image or caption provides a clear cue. "
        "If observable evidence is insufficient, return empty strings rather than guessing. "
        "Respond with only a JSON object with four keys: "
        '"location" (human-readable name, e.g. \'Times Square, New York, USA\'), '
        '"lat" (decimal latitude as a string, e.g. \'40.7580\'), '
        '"lng" (decimal longitude as a string, e.g. \'-73.9855\'), '
        'and "region" (IATA code of the nearest in-country international airport, e.g. \'JFK\'). '
        'The "location" value MUST be a short place-name string (under 200 characters, no line breaks) — '
        "not a sentence, paragraph, or your reasoning prose. "
        "If you cannot determine the location with reasonable confidence, set all four values to empty strings. "
        "If you cannot determine the lat/lng, provide the location and region but leave lat and lng as empty strings. "
        "If you cannot determine the nearest international airport, provide the location and lat/lng but leave region as an empty string. "
        "CRITICAL: Your entire response must be exactly one JSON object and nothing else. "
        "Do not write reasoning, observations, or analysis before or after the JSON. "
        "Do not wrap the JSON in markdown code fences. The downstream parser cannot recover from a pure-prose response."
    )

    content: list[dict] = []

    # Include image for IMAGE posts so the model can use visual context
    if media_type == "IMAGE" and local_media_path and os.path.exists(local_media_path):
        with open(local_media_path, "rb") as img_file:
            image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image_data,
            },
        })

    content.append({"type": "text", "text": prompt})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": content}],
    )

    raw = response.content[0].text
    data, reasoning = extract_json_and_reasoning(raw)
    if data is not None:
        location = str(data.get("location", "")).strip()
        # Sanity-check the location string. Even when the model returns valid
        # JSON, it sometimes stuffs prose-as-location into the "location"
        # field. A real place name is short and single-line; anything else
        # is treated as malformed so the call site applies the city-level
        # fallback. The rejected text moves to `reasoning` for audit.
        if "\n" in location or len(location) > MAX_INFERRED_LOCATION_LEN:
            rejection = (
                f"[parser rejected location as malformed "
                f"(len={len(location)}, has_newline={'\\n' in location}); "
                f"first 300 chars: {location[:300]!r}]"
            )
            combined = f"{reasoning}\n\n{rejection}" if reasoning else rejection
            return ("", "", "", "", combined)
        return (
            location,
            str(data.get("lat", "")),
            str(data.get("lng", "")),
            str(data.get("region", "")),
            reasoning,
        )
    # No parseable JSON at all — return empty location so the call site applies
    # its city-level fallback. Preserve the raw text in `reasoning` for audit.
    return ("", "", "", "", raw.strip())


def extract_city_heuristic(location: str) -> str:
    """Pull a city-level name out of a canonical 'Venue, City, Country'-style
    location string. Used by the fallback path so a row with no observable
    evidence inherits the neighbor's *city*, not its exact venue (the prior
    post was probably nearby in the same city, almost never at the same venue).

    Heuristic — intentionally simple, no LLM call:
      - 3+ segments → second-to-last (the city slot in 'Venue, City, Country').
      - 2 segments → first ('City, Country' → 'City').
      - 1 segment / empty → return as-is.

    Known limitation: US 'City, State, Country' tags resolve to the state
    ('Seattle, Washington, USA' → 'Washington') rather than the city. The
    fallback is still a general-area marker — wider than the venue, which
    is the user-visible improvement — just at state level for those cases.
    """
    parts = [p.strip() for p in location.split(",") if p.strip()]
    if len(parts) >= 3:
        return parts[-2]
    if len(parts) == 2:
        return parts[0]
    return location.strip()
