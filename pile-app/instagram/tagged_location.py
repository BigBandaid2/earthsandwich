"""FR-019 tagged-path canonicalization.

When an Instagram post has an explicit geo-tag, the verbatim tag name is the
poster's INTENT and the authoritative signal. The latitude/longitude come
from the same Instagram entry but are occasionally inconsistent with the
name (real observed case: tag named 'Sucre, Bolivia' with coordinates in
China). This module asks the LLM to canonicalize the name to
"Venue, City, Country" form, pick an IATA region, and produce coordinates
that agree with the named place.
"""

from __future__ import annotations

from common.inference import extract_json_and_reasoning, get_anthropic_client


def canonicalize_tagged_location(name: str, lat: str, lng: str) -> tuple[str, str, str, str, str]:
    """FR-019 tagged-path enrichment: canonicalize a verbatim geo-tag, derive coords + IATA.

    The verbatim tag NAME represents the poster's geo-tagging intent and is
    the authoritative signal. The latitude/longitude come from the same
    Instagram entry but are occasionally inconsistent with the name (e.g.
    a tag named 'Sucre, Bolivia' with coordinates in China — a real case
    observed in the @ourearthsandwich corpus). When name and coordinates
    conflict, this function trusts the NAME and asks the model to produce
    canonical coordinates for the named place.

    The call also corrects typos, translates local-language names to English,
    and adds missing city/country context.

    Returns (canonical_name, canonical_lat, canonical_lng, region, reasoning).
    Any field may be empty. Callers should fall back to the verbatim
    name/coords when the canonical version is empty (hyper-local tags where
    the model can't determine precise coords).
    """
    client = get_anthropic_client()
    prompt = (
        f"Verbatim Instagram geo-tag: {name}\n"
        f"Latitude: {lat or '(unknown)'}\n"
        f"Longitude: {lng or '(unknown)'}\n\n"
        "This is the location a user typed when geo-tagging an Instagram post. "
        "The verbatim tag name represents the POSTER'S INTENT and is the "
        "AUTHORITATIVE signal. The latitude/longitude come from the same "
        "Instagram entry but are occasionally inconsistent with the name "
        "(e.g. a tag named 'Sucre, Bolivia' with coordinates in China). "
        "When the name and coordinates conflict — meaning they refer to "
        "places in different countries or wildly different regions — TRUST "
        "THE NAME and produce canonical coordinates for the named place. "
        "When they agree, simply confirm them.\n\n"
        "Respond with only a JSON object with four keys:\n"
        '  "canonical_name" — a standardized English location string in the '
        'form "Venue, City, Country" (or "Neighborhood, City, Country" if the '
        'tag is a neighborhood, or "City, State, Country" if the tag is a city). '
        "Translate to English, correct typos, add missing city/country context.\n"
        '  "lat" — canonical latitude as a decimal-string. If the input coords '
        "match the named place at country level, echo them verbatim. If they "
        "conflict with the name, produce coords for the named place. Leave "
        "empty only when you cannot determine coords with reasonable confidence.\n"
        '  "lng" — canonical longitude, same rules as lat.\n'
        '  "region" — 3-letter IATA code of the nearest major international '
        "airport within the same country as the named place (e.g. 'JFK', 'MEX', 'CDG').\n\n"
        "If you cannot determine any field with reasonable confidence, leave it "
        "as an empty string. Do not include any text outside the JSON object. "
        "Do not wrap the JSON in markdown code fences."
    )
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        print(f"  ! canonicalize call failed ({exc})")
        return ("", "", "", "", "")

    raw = response.content[0].text
    data, reasoning = extract_json_and_reasoning(raw)
    if data is None:
        return ("", "", "", "", reasoning)
    canonical = str(data.get("canonical_name", "")).strip()
    canonical_lat = str(data.get("lat", "")).strip()
    canonical_lng = str(data.get("lng", "")).strip()
    region_raw = str(data.get("region", "")).strip().upper()
    region = "".join(c for c in region_raw if c.isalpha())
    if len(region) != 3:
        region = ""
    return (canonical, canonical_lat, canonical_lng, region, reasoning)
