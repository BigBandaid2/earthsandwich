"""Unit tests for the `process_media` function in instagram.pipeline.

`process_media` is the per-post handler. It does field extraction, media
URL/type resolution, media download, dual-path location resolution (FR-019
tagged vs FR-020 inferred), and path normalization — returning a row dict
ready for `csv.DictWriter`.

All external collaborators (`download_media`, `canonicalize_tagged_location`,
`infer_post_location`) are mocked via monkeypatch on the import site
(`instagram.pipeline`). The whole module runs in well under a second with
no network and no credentials.

Test groups:
  - TestDualPathBranching: tagged vs. inferred dispatch, including edge
    cases of (0,0) coords, name-only tags, and missing locations.
  - TestMediaUrlExtraction: IMAGE / VIDEO / Album (`media_type` 1 / 2 / 8)
    URL selection and the no-resources fallback.
  - TestTimestamp: ISO-with-`+0000` formatting matching the existing TSV.
  - TestPathNormalization: APP_ROOT-relative POSIX paths in the TSV row.
  - TestFieldExtraction: pk → instagram_id, code → shortcode, caption_text
    → caption, local_id → id.
"""

import os
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import requests

import instagram.pipeline
from common import APP_ROOT
from instagram.pipeline import process_media


# ---------------------------------------------------------------------------
# Builders for instagrapi-shaped fakes
# ---------------------------------------------------------------------------

def make_location(name="Mexico City", lat=19.43, lng=-99.13):
    """Construct a fake instagrapi `Location`. Pass name=None to get a
    Location object with a missing name (treated as "no usable tag")."""
    return SimpleNamespace(name=name, lat=lat, lng=lng)


def make_media(
    pk=12345,
    code="ABCDEF",
    caption_text="hello",
    taken_at=None,
    media_type=1,
    thumbnail_url="",
    video_url="",
    resources=None,
    location=None,
):
    """Construct a fake instagrapi `Media`. Defaults to a Photo with no
    geo-tag and no download URL — override the fields you're exercising."""
    if taken_at is None:
        taken_at = datetime(2026, 5, 8, 14, 39, 41, tzinfo=timezone.utc)
    return SimpleNamespace(
        pk=pk,
        code=code,
        caption_text=caption_text,
        taken_at=taken_at,
        media_type=media_type,
        thumbnail_url=thumbnail_url,
        video_url=video_url,
        resources=resources,
        location=location,
    )


def make_resource(media_type=1, thumbnail_url="", video_url=""):
    """Construct a fake instagrapi carousel `Resource` (used for media_type=8)."""
    return SimpleNamespace(
        media_type=media_type, thumbnail_url=thumbnail_url, video_url=video_url
    )


# ---------------------------------------------------------------------------
# Common fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def patched(monkeypatch):
    """Patch the three external collaborators of `process_media` at the
    import site in `instagram.pipeline`. Returns a SimpleNamespace exposing
    each mock so tests can set behavior and assert calls."""
    download = MagicMock(return_value="")
    canonicalize = MagicMock(return_value=("", "", "", "", ""))
    inferred = MagicMock(return_value=("", "", "", "", ""))
    monkeypatch.setattr(instagram.pipeline, "download_media", download)
    monkeypatch.setattr(instagram.pipeline, "canonicalize_tagged_location", canonicalize)
    monkeypatch.setattr(instagram.pipeline, "infer_post_location", inferred)
    return SimpleNamespace(
        download_media=download,
        canonicalize_tagged_location=canonicalize,
        infer_post_location=inferred,
    )


# ---------------------------------------------------------------------------
# TestDualPathBranching — the core reason this function was extracted
# ---------------------------------------------------------------------------

class TestDualPathBranching:
    def test_tagged_path_uses_canonical_name_and_coords_when_available(self, patched):
        """When Media.location is populated, canonicalize returns canonical
        name + coords + IATA. Tagged path uses all of them; infer_post_location
        must NOT be called."""
        patched.canonicalize_tagged_location.return_value = (
            "Mexico City, Mexico", "19.432", "-99.131", "MEX", "",
        )
        m = make_media(location=make_location("Mexico City", 19.432, -99.131))

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        assert row["location"] == "Mexico City, Mexico"
        assert row["lat"] == "19.432"
        assert row["lng"] == "-99.131"
        assert row["region"] == "MEX"
        patched.canonicalize_tagged_location.assert_called_once_with(
            "Mexico City", "19.432", "-99.131"
        )
        patched.infer_post_location.assert_not_called()

    def test_tagged_path_name_authoritative_overrides_conflicting_coords(self, patched):
        """When tag name and instagrapi coords conflict, the model produces
        canonical coords FOR THE NAMED PLACE — and the row stores those,
        not the conflicting instagrapi coords. This is the Sucre→Bolivia
        regression case: don't let bad coords flip the location to China."""
        patched.canonicalize_tagged_location.return_value = (
            "Sucre, Chuquisaca, Bolivia", "-19.04", "-65.26", "SRE", "",
        )
        m = make_media(location=make_location("Sucre, Bolivia", 28.99, 118.85))

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        assert row["location"] == "Sucre, Chuquisaca, Bolivia"
        assert row["lat"] == "-19.04"
        assert row["lng"] == "-65.26"
        assert row["region"] == "SRE"

    def test_tagged_path_falls_back_to_verbatim_coords_when_canonical_coords_empty(self, patched):
        """For hyper-local tags where the model can't determine precise coords,
        canonicalize returns empty lat/lng. The row falls back to the
        instagrapi-provided coords (they're approximately right for the
        named place, just not precise)."""
        patched.canonicalize_tagged_location.return_value = (
            "Some Hyper-Local Place, City, Country", "", "", "XYZ", "",
        )
        m = make_media(location=make_location("hyperlocal tag", 47.58, -122.41))

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        assert row["location"] == "Some Hyper-Local Place, City, Country"
        assert row["lat"] == "47.58"
        assert row["lng"] == "-122.41"
        assert row["region"] == "XYZ"

    def test_tagged_path_falls_back_to_verbatim_name_when_canonical_empty(self, patched):
        """When the canonicalize call returns nothing usable, keep the
        poster's verbatim tag rather than blanking the location."""
        patched.canonicalize_tagged_location.return_value = ("", "", "", "", "")
        m = make_media(location=make_location("Oxaca", 17.06, -96.72))

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        assert row["location"] == "Oxaca"
        assert row["lat"] == "17.06"
        assert row["lng"] == "-96.72"
        assert row["region"] == ""

    def test_tagged_path_records_canonicalize_reasoning(self, patched):
        """When the model writes prose during canonicalization, that prose is
        captured in the reasoning column."""
        patched.canonicalize_tagged_location.return_value = (
            "Oaxaca City, Mexico", "17.06", "-96.72", "OAX", "Note: original tag had a typo",
        )
        m = make_media(location=make_location("Oxaca", 17.06, -96.72))

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        assert row["location"] == "Oaxaca City, Mexico"
        assert row["reasoning"] == "Note: original tag had a typo"

    def test_inferred_path_used_when_no_location(self, patched):
        """When Media.location is None, the inferred call carries the
        full burden and canonicalize_tagged_location is NOT called."""
        patched.infer_post_location.return_value = ("Paris", "48.85", "2.35", "CDG", "")
        m = make_media(location=None)

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=["Tokyo"])

        assert row["location"] == "Paris"
        assert row["lat"] == "48.85"
        assert row["lng"] == "2.35"
        assert row["region"] == "CDG"
        patched.infer_post_location.assert_called_once()
        patched.canonicalize_tagged_location.assert_not_called()
        assert patched.infer_post_location.call_args.kwargs["recent_locations"] == ["Tokyo"]

    def test_inferred_path_records_reasoning(self, patched):
        """When the inferred call returns prose-before-JSON, the prose
        lands in the reasoning column instead of being lost."""
        patched.infer_post_location.return_value = (
            "JFK Airport, Queens, NY, USA", "40.6413", "-73.7781", "JFK",
            "Looking at the boarding pass, this is clearly Virgin America VX 23 out of JFK."
        )
        m = make_media(location=None)

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        assert row["location"] == "JFK Airport, Queens, NY, USA"
        assert row["region"] == "JFK"
        assert "Virgin America" in row["reasoning"]

    def test_inferred_path_falls_back_to_prior_post_city_when_inference_empty(self, patched):
        """When inference returns no location AND a previous_row is provided,
        the row's location becomes the prior post's CITY (not its exact venue),
        and lat/lng/region are inherited from that prior post."""
        patched.infer_post_location.return_value = ("", "", "", "", "")
        m = make_media(location=None)

        prior = {
            "location": "Sistine Chapel, Vatican City, Italy",
            "lat": "41.9029",
            "lng": "12.4534",
            "region": "FCO",
        }
        row = process_media(
            m, target="acct", local_id=999, media_dir="/tmp",
            recent_locations=["Sistine Chapel, Vatican City, Italy"],
            previous_row=prior,
        )

        assert row["location"] == "Vatican City"
        assert row["lat"] == "41.9029"
        assert row["lng"] == "12.4534"
        assert row["region"] == "FCO"
        assert "fallback" in row["reasoning"]
        assert "Vatican City" in row["reasoning"]

    def test_inferred_path_fallback_uses_city_segment_for_two_segment_form(self, patched):
        """'City, Country' form → first segment is the city."""
        patched.infer_post_location.return_value = ("", "", "", "", "")
        m = make_media(location=None)
        prior = {"location": "Lisbon, Portugal", "lat": "38.7", "lng": "-9.1", "region": "LIS"}

        row = process_media(
            m, target="acct", local_id=999, media_dir="/tmp",
            recent_locations=["Lisbon, Portugal"],
            previous_row=prior,
        )

        assert row["location"] == "Lisbon"
        assert row["region"] == "LIS"

    def test_inferred_path_no_fallback_when_no_previous_row(self, patched):
        """No previous_row → no fallback. The row stays genuinely empty."""
        patched.infer_post_location.return_value = ("", "", "", "", "")
        m = make_media(location=None)

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        assert row["location"] == ""
        assert row["reasoning"] == ""

    def test_inferred_path_no_fallback_when_previous_row_has_no_location(self, patched):
        """If previous_row exists but its location is empty (an edge case
        where the prior post was itself unresolved), no fallback fires."""
        patched.infer_post_location.return_value = ("", "", "", "", "")
        m = make_media(location=None)
        prior = {"location": "", "lat": "", "lng": "", "region": ""}

        row = process_media(
            m, target="acct", local_id=999, media_dir="/tmp",
            recent_locations=[],
            previous_row=prior,
        )

        assert row["location"] == ""
        assert row["reasoning"] == ""

    def test_inferred_path_preserves_inference_when_non_empty(self, patched):
        """When inference returns a real location, the fallback path does NOT
        fire — even with recent_locations present. We trust the model."""
        patched.infer_post_location.return_value = ("Tokyo, Japan", "35.68", "139.69", "HND", "")
        m = make_media(location=None)

        row = process_media(
            m, target="acct", local_id=999, media_dir="/tmp",
            recent_locations=["Kyoto, Japan"],
        )

        assert row["location"] == "Tokyo, Japan"
        assert "fallback" not in row["reasoning"]

    def test_inferred_path_fallback_preserves_existing_reasoning(self, patched):
        """When inference returns prose-but-no-location, both the prose AND
        the fallback note end up in the reasoning column (separated)."""
        patched.infer_post_location.return_value = (
            "", "", "", "", "I considered Tokyo but couldn't confirm the building.",
        )
        m = make_media(location=None)
        prior = {"location": "Kyoto, Japan", "lat": "35.0", "lng": "135.7", "region": "ITM"}

        row = process_media(
            m, target="acct", local_id=999, media_dir="/tmp",
            recent_locations=["Kyoto, Japan"],
            previous_row=prior,
        )

        assert row["location"] == "Kyoto"
        assert row["region"] == "ITM"
        assert "I considered Tokyo" in row["reasoning"]
        assert "fallback" in row["reasoning"]

    def test_inferred_path_used_when_location_name_is_none(self, patched):
        """A Location object whose .name is None/empty still triggers the
        inferred path — there's no usable tag to honor."""
        patched.infer_post_location.return_value = ("Inferred Place", "1", "2", "XYZ", "")
        m = make_media(location=make_location(name=None))

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        assert row["location"] == "Inferred Place"
        patched.infer_post_location.assert_called_once()
        patched.canonicalize_tagged_location.assert_not_called()

    def test_tagged_path_with_zero_zero_coords_drops_coords(self, patched):
        """instagrapi sometimes returns Location with lat/lng = (0.0, 0.0)
        when coords are absent. We keep the name but blank the coords so
        the TSV doesn't accumulate bogus 0,0 points."""
        patched.canonicalize_tagged_location.return_value = ("Some Place, Country", "", "", "", "")
        m = make_media(location=make_location("Some Place", 0.0, 0.0))

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        assert row["location"] == "Some Place, Country"
        assert row["lat"] == ""
        assert row["lng"] == ""
        patched.canonicalize_tagged_location.assert_called_once_with("Some Place", "", "")

    def test_tagged_path_with_no_coord_attrs_keeps_name_only(self, patched):
        """Location with no lat/lng attributes at all (only name). Coords
        come out empty, the canonicalize call still fires."""
        patched.canonicalize_tagged_location.return_value = ("Name Only, Country", "", "", "ABC", "")
        loc = SimpleNamespace(name="Name Only")
        m = make_media(location=loc)

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        assert row["location"] == "Name Only, Country"
        assert row["lat"] == ""
        assert row["lng"] == ""
        assert row["region"] == "ABC"

    def test_inferred_path_swallows_exceptions_into_empty_row(self, patched):
        """If infer_post_location raises, the row's location fields
        stay empty rather than crashing the whole run. Other fields still
        populate from the Media object."""
        patched.infer_post_location.side_effect = RuntimeError("inference down")
        m = make_media(location=None)

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        assert row["location"] == ""
        assert row["lat"] == ""
        assert row["lng"] == ""
        assert row["region"] == ""
        assert row["reasoning"] == ""
        assert row["instagram_id"] == "12345"
        assert row["shortcode"] == "ABCDEF"


# ---------------------------------------------------------------------------
# TestMediaUrlExtraction
# ---------------------------------------------------------------------------

class TestMediaUrlExtraction:
    def test_photo_uses_thumbnail_url(self, patched):
        """media_type=1 (Photo) → IMAGE type, thumbnail_url is the source."""
        m = make_media(media_type=1, thumbnail_url="https://cdn.example/img.jpg")

        process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        patched.download_media.assert_called_once_with(
            "https://cdn.example/img.jpg", "acct", "ABCDEF", "IMAGE", "/tmp"
        )

    def test_video_uses_video_url(self, patched):
        """media_type=2 (Video) → VIDEO type, video_url is the source."""
        m = make_media(media_type=2, video_url="https://cdn.example/vid.mp4")

        process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        patched.download_media.assert_called_once_with(
            "https://cdn.example/vid.mp4", "acct", "ABCDEF", "VIDEO", "/tmp"
        )

    def test_album_image_resource(self, patched):
        """media_type=8 (Album) with a photo as the first resource → IMAGE,
        first resource's thumbnail_url is the source."""
        m = make_media(
            media_type=8,
            resources=[make_resource(media_type=1, thumbnail_url="https://cdn.example/a.jpg")],
        )

        process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        patched.download_media.assert_called_once_with(
            "https://cdn.example/a.jpg", "acct", "ABCDEF", "IMAGE", "/tmp"
        )

    def test_album_video_resource(self, patched):
        """media_type=8 (Album) with a video as the first resource → VIDEO,
        first resource's video_url is the source."""
        m = make_media(
            media_type=8,
            resources=[make_resource(media_type=2, video_url="https://cdn.example/a.mp4")],
        )

        process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        patched.download_media.assert_called_once_with(
            "https://cdn.example/a.mp4", "acct", "ABCDEF", "VIDEO", "/tmp"
        )

    def test_album_with_no_resources_falls_back_to_image(self, patched):
        """media_type=8 but resources is None/empty → fall through to the
        IMAGE branch and use the top-level thumbnail_url."""
        m = make_media(media_type=8, thumbnail_url="https://cdn.example/fallback.jpg")

        process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        patched.download_media.assert_called_once_with(
            "https://cdn.example/fallback.jpg", "acct", "ABCDEF", "IMAGE", "/tmp"
        )

    def test_empty_media_url_skips_download(self, patched):
        """No URL → no download call; row's media_url stays empty."""
        m = make_media(media_type=1, thumbnail_url="")

        row = process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        patched.download_media.assert_not_called()
        assert row["media_url"] == ""

    def test_download_failure_leaves_media_url_empty(self, patched):
        """download_media raising a transport error → row's media_url is
        empty but every other field still populates (FR-021)."""
        patched.download_media.side_effect = requests.RequestException("timeout")
        m = make_media(media_type=1, thumbnail_url="https://cdn.example/x.jpg")

        row = process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        assert row["media_url"] == ""
        assert row["instagram_id"] == "12345"
        assert row["shortcode"] == "ABCDEF"


# ---------------------------------------------------------------------------
# TestTimestamp
# ---------------------------------------------------------------------------

class TestTimestamp:
    def test_tz_aware_utc_formats_to_existing_tsv_style(self, patched):
        m = make_media(taken_at=datetime(2026, 5, 8, 14, 39, 41, tzinfo=timezone.utc))

        row = process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        assert row["timestamp"] == "2026-05-08T14:39:41+0000"

    def test_naive_datetime_treated_as_utc(self, patched):
        """A datetime with tzinfo=None is assumed UTC. instagrapi's response
        shape is inconsistent here; we normalize so the TSV format is stable."""
        m = make_media(taken_at=datetime(2026, 5, 8, 14, 39, 41))

        row = process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        assert row["timestamp"] == "2026-05-08T14:39:41+0000"


# ---------------------------------------------------------------------------
# TestPathNormalization
# ---------------------------------------------------------------------------

class TestPathNormalization:
    def test_absolute_path_under_app_root_becomes_relative_posix(self, patched):
        """download_media returns an absolute path inside APP_ROOT;
        the row should carry the relative POSIX form so it stays portable
        across Windows/Linux."""
        downloaded = os.path.join(str(APP_ROOT), "pile", "media", "instagram", "acct_10.jpg")
        patched.download_media.return_value = downloaded
        m = make_media(media_type=1, thumbnail_url="x")

        row = process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        assert row["media_url"] == "pile/media/instagram/acct_10.jpg"
        assert "\\" not in row["media_url"]


# ---------------------------------------------------------------------------
# TestFieldExtraction
# ---------------------------------------------------------------------------

class TestFieldExtraction:
    def test_pk_to_instagram_id(self, patched):
        m = make_media(pk=987654321)

        row = process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        assert row["instagram_id"] == "987654321"

    def test_code_to_shortcode(self, patched):
        m = make_media(code="XYZ123")

        row = process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        assert row["shortcode"] == "XYZ123"

    def test_caption_text_to_caption(self, patched):
        m = make_media(caption_text="Travel day")

        row = process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        assert row["caption"] == "Travel day"

    def test_local_id_passes_through_to_row_id(self, patched):
        m = make_media()

        row = process_media(m, target="acct", local_id=42, media_dir="/tmp", recent_locations=[])

        assert row["id"] == 42

    def test_empty_caption_falls_back_to_empty_string(self, patched):
        """instagrapi returns caption_text=None for caption-less posts."""
        m = make_media(caption_text=None)

        row = process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        assert row["caption"] == ""

    def test_empty_code_falls_back_to_empty_string(self, patched):
        m = make_media(code=None)

        row = process_media(m, target="acct", local_id=10, media_dir="/tmp", recent_locations=[])

        assert row["shortcode"] == ""


# ---------------------------------------------------------------------------
# TestVerbatimAndTombstoneColumns — FR-105 / Cardinal Rule #4 + FR-106 defaults
# ---------------------------------------------------------------------------

class TestVerbatimAndTombstoneColumns:
    """The Instagram TSV's verbatim-input columns (tag_verbatim, lat_verbatim,
    lng_verbatim) preserve the canonicalization call's inputs (FR-105 /
    Cardinal Rule #4). The tombstone columns (deleted_upstream,
    deleted_upstream_at) default to empty at row-creation time; FR-106
    detection runs as a separate post-pass against the existing pile.
    """

    def test_tagged_path_populates_verbatim_triple(self, patched):
        """When Media.location is populated, the row captures the raw
        instagrapi name/lat/lng verbatim — regardless of what canonicalization
        returns. The principle: the inference call's inputs must be
        recoverable from the row alone."""
        patched.canonicalize_tagged_location.return_value = (
            "Mexico City, Mexico", "19.432", "-99.131", "MEX", "",
        )
        m = make_media(location=make_location("Mexico City", 19.432, -99.131))

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        assert row["tag_verbatim"] == "Mexico City"
        assert row["lat_verbatim"] == "19.432"
        assert row["lng_verbatim"] == "-99.131"

    def test_tagged_path_verbatim_preserved_when_canonical_overrides(self, patched):
        """The Sucre→Bolivia case: canonical coords differ from the verbatim
        ones. The verbatim columns MUST still carry the original instagrapi
        values, not the canonical override — that's the whole point of FR-105."""
        patched.canonicalize_tagged_location.return_value = (
            "Sucre, Chuquisaca, Bolivia", "-19.04", "-65.26", "SRE", "",
        )
        m = make_media(location=make_location("Sucre, Bolivia", 28.99, 118.85))

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        # Canonical wins in the resolved columns
        assert row["lat"] == "-19.04"
        assert row["lng"] == "-65.26"
        # Verbatim is the original instagrapi triple
        assert row["tag_verbatim"] == "Sucre, Bolivia"
        assert row["lat_verbatim"] == "28.99"
        assert row["lng_verbatim"] == "118.85"

    def test_tagged_path_with_zero_zero_coords_records_empty_lat_lng_verbatim(self, patched):
        """instagrapi sometimes returns Location with (0,0) coords. The
        verbatim columns for lat/lng should be empty (matching how the
        tagged tuple is populated), since (0,0) is semantically 'no coords'."""
        patched.canonicalize_tagged_location.return_value = ("Some Place, Country", "", "", "", "")
        m = make_media(location=make_location("Some Place", 0.0, 0.0))

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        assert row["tag_verbatim"] == "Some Place"
        assert row["lat_verbatim"] == ""
        assert row["lng_verbatim"] == ""

    def test_inferred_path_leaves_verbatim_triple_empty(self, patched):
        """No tag → verbatim columns are all empty (there was nothing to
        verbatim-capture). The inferred path's input preservation comes
        from `caption` + `media_url`, not from the verbatim columns."""
        patched.infer_post_location.return_value = ("Paris", "48.85", "2.35", "CDG", "")
        m = make_media(location=None)

        row = process_media(m, target="acct", local_id=999, media_dir="/tmp", recent_locations=[])

        assert row["tag_verbatim"] == ""
        assert row["lat_verbatim"] == ""
        assert row["lng_verbatim"] == ""

    def test_tombstone_columns_default_to_empty(self, patched):
        """A fresh row never starts tombstoned. FR-106 detection runs
        downstream of process_media."""
        m = make_media(location=make_location("Somewhere"))

        row = process_media(m, target="acct", local_id=1, media_dir="/tmp", recent_locations=[])

        assert row["deleted_upstream"] == ""
        assert row["deleted_upstream_at"] == ""
