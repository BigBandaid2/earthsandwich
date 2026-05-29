"""instagrapi crawler authentication + session management + target resolution.

Reads INSTA_USERNAME, INSTA_PASSWORD, INSTAGRAPI_SESSION_FILE from the
environment (already loaded by `common.__init__` at import time). Provides:

  - `init_instagrapi_client()` — resume or fresh-login; returns None on
    any failure so callers fail-fast with a useful error.
  - `resolve_target_user_id(cl, username)` — username → (user_id, media_count)
    for the upfront ETA + the pagination calls. Independent of the crawler
    `cl.user_id`, which is the auth/session separation FR-016 requires.
  - Internal challenge / change-password handlers wired into the instagrapi
    Client at construction time.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from common import APP_ROOT

# Crawler credentials — the account instagrapi authenticates as. Separate from
# the target account(s) being scraped, which are resolved at run time.
INSTA_USERNAME = os.environ.get("INSTA_USERNAME", "")
INSTA_PASSWORD = os.environ.get("INSTA_PASSWORD", "")
INSTAGRAPI_SESSION_FILE = os.environ.get(
    "INSTAGRAPI_SESSION_FILE",
    str(APP_ROOT / "instagrapi_session.json"),
)


def _challenge_code_handler(username: str, choice) -> str:
    """Interactive challenge handler invoked by instagrapi when Instagram asks
    for a verification code (SMS / email / 2FA app)."""
    via_map = {0: "SMS", 1: "EMAIL"}
    try:
        via = via_map.get(int(choice), str(choice))
    except (TypeError, ValueError):
        via = str(choice)
    print(f"\n>>> Instagram challenge for @{username}: a code was sent via {via}.")
    print(">>> Check that channel and paste the code below (it expires quickly).")
    try:
        code = input(">>> Code: ").strip()
    except EOFError:
        code = ""
    return code


def _change_password_handler(username: str) -> str:
    """Stub handler for the rarer 'change your password' challenge.

    Returning an empty string tells instagrapi we can't satisfy the challenge
    in this run, so the login will fail cleanly and we fall back to the
    inferred-location path. Surface the situation so the operator can fix it
    via the Instagram app and re-run.
    """
    print(
        f"\n>>> Instagram is asking @{username} to change the password before continuing. "
        "Update the password via the Instagram app, update INSTA_PASSWORD in .env, and re-run."
    )
    return ""


def init_instagrapi_client() -> Optional["object"]:
    """Initialize an instagrapi session for FR-019 tagged-location lookups.

    Reads INSTA_USERNAME, INSTA_PASSWORD, INSTAGRAPI_SESSION_FILE from env.
    Resumes a saved session if one exists; otherwise does a fresh login and
    persists the session. Returns None if credentials are missing, instagrapi
    is not installed, or login fails — callers MUST fall back to the FR-020
    inferred-location path in that case.

    If Instagram raises a challenge during fresh login, prompts the operator
    interactively for the verification code via stdin.
    """
    if not INSTA_USERNAME or not INSTA_PASSWORD:
        print("instagrapi: INSTA_USERNAME or INSTA_PASSWORD not set; tagged-location path disabled")
        return None

    try:
        from instagrapi import Client
    except ImportError:
        print("instagrapi: package not installed; tagged-location path disabled")
        return None

    session_path = Path(INSTAGRAPI_SESSION_FILE)

    def _make_client():
        c = Client()
        c.challenge_code_handler = _challenge_code_handler
        c.change_password_handler = _change_password_handler
        return c

    cl = _make_client()

    if session_path.exists():
        try:
            cl.load_settings(str(session_path))
            cl.login(INSTA_USERNAME, INSTA_PASSWORD)
            print(f"instagrapi: resumed session from {session_path}")
            return cl
        except Exception as exc:
            print(f"instagrapi: session resume failed ({exc}); attempting fresh login")
            cl = _make_client()

    try:
        cl.login(INSTA_USERNAME, INSTA_PASSWORD)
        cl.dump_settings(str(session_path))
        print(f"instagrapi: logged in and saved session to {session_path}")
        return cl
    except Exception as exc:
        print(f"instagrapi: login failed ({exc}); tagged-location path disabled")
        return None


def resolve_target_user_id(cl: "object", username: str) -> Optional[tuple[int, int]]:
    """Resolve a target Instagram username to its (user_id, media_count).

    Independent of `cl.user_id` (the crawler) — this is what makes the
    crawler / target separation possible.

    `media_count` is the total number of posts on the account; it comes back
    on the same response as the user_id (`user_info_by_username`), so it's
    free additional data we use to estimate scrape duration. Returns None
    on failure (private account the crawler can't see, deleted, rate-limit).
    """
    try:
        info = cl.user_info_by_username(username)
        media_count = int(getattr(info, "media_count", 0) or 0)
        return (int(info.pk), media_count)
    except Exception as exc:
        print(f"  ! could not resolve user_id for @{username}: {exc}")
        return None


def get_instagrapi_location(cl: "object", shortcode: str) -> Optional[tuple[str, str, str]]:
    """Look up the explicit geo-tag for a post via instagrapi (FR-019).

    Returns (name, lat, lng) if the post has a tagged location, otherwise None.
    lat/lng may be empty strings if the tag is name-only or coordinates are (0, 0).
    """
    try:
        pk = cl.media_pk_from_url(f"https://www.instagram.com/p/{shortcode}/")
        info = cl.media_info(pk)
    except Exception as exc:
        print(f"  ! instagrapi media_info failed for shortcode={shortcode} ({exc})")
        return None

    loc = getattr(info, "location", None)
    if not loc or not getattr(loc, "name", None):
        return None

    name = loc.name
    raw_lat = getattr(loc, "lat", None)
    raw_lng = getattr(loc, "lng", None)

    # Filter (0.0, 0.0) which instagrapi sometimes returns when coords are absent
    if raw_lat in (None, 0, 0.0) and raw_lng in (None, 0, 0.0):
        return name, "", ""

    lat = "" if raw_lat is None else str(raw_lat)
    lng = "" if raw_lng is None else str(raw_lng)
    return name, lat, lng
