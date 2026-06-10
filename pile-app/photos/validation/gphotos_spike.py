#!/usr/bin/env python3
"""Google Photos API validation spike — does an API-downloaded photo keep its GPS?

THROWAWAY exploratory spike (not part of the App). It answers the two questions
that decide whether a "connect to Google Photos -> download media -> extract EXIF"
pipeline can actually recover location:

  1. Can we still LIST the library via the API?  (Google's 2025 changes restricted
     library-wide reads for third-party apps — if listing 403s/empties, a
     continuous background pull is likely off the table.)
  2. When we DOWNLOAD a photo's original bytes via the API (`baseUrl=d`), does the
     EXIF GPS survive?  (The API is reputed to strip location on download. The
     manual web "download" button preserves it; the API path is the unknown.)

Run:
    cd pile-app
    venv/Scripts/python.exe photos/validation/gphotos_spike.py

Prereqs (one-time Google Cloud setup — see SETUP.md in this folder):
    - Put your OAuth client secret here as  photos/validation/client_secret.json
    - First run opens a browser for consent; the token is cached as token.json.
Both files are gitignored (credentials — never commit).
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import requests
from PIL import Image
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]
HERE = Path(__file__).resolve().parent
CLIENT_SECRET = HERE / "client_secret.json"
TOKEN = HERE / "token.json"
LIST_URL = "https://photoslibrary.googleapis.com/v1/mediaItems"


def get_creds() -> Credentials:
    creds: Credentials | None = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET.exists():
                sys.exit(
                    f"\nMISSING {CLIENT_SECRET}\n"
                    "Create an OAuth client (Desktop app) in Google Cloud, download the\n"
                    "client secret JSON, and save it at that path. See SETUP.md."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN.write_text(creds.to_json())
    return creds


def _to_deg(rat, ref) -> float:
    d, m, s = [float(x) for x in rat]
    v = d + m / 60 + s / 3600
    return round(-v if ref in ("S", "W") else v, 6)


def main() -> None:
    creds = get_creds()
    sess = requests.Session()
    sess.headers["Authorization"] = f"Bearer {creds.token}"

    # ---- Q1: can we list the library? ----
    print("\n[1] Listing media items via the API ...")
    r = sess.get(LIST_URL, params={"pageSize": 25}, timeout=30)
    print(f"    HTTP {r.status_code}")
    if r.status_code != 200:
        body = r.text
        print("    body:", body[:600])
        low = body.lower()
        if "service_disabled" in low or "has not been used in project" in low:
            print("\n=> Photos Library API is NOT ENABLED on this project. Enable it in the\n"
                  "   Cloud Console, wait ~1 min, then re-run. (Setup gap, not a real block.)")
        elif "insufficient authentication scopes" in low or "scope" in low:
            print("\n=> SCOPE problem. Most likely a STALE cached token. Delete token.json and\n"
                  "   re-run for a fresh consent:  rm pile-app/photos/validation/token.json\n"
                  "   If a FRESH consent still returns this, it confirms Google's 2025 removal\n"
                  "   of library-wide read via 'photoslibrary.readonly' -> pivot to Takeout.")
        else:
            print("\n=> Listing failed for another reason (see body above).")
        return
    items = r.json().get("mediaItems", [])
    print(f"    got {len(items)} item(s)")
    photo = next((m for m in items if m.get("mimeType", "").startswith("image/")), None)
    if not photo:
        print("    no image item returned; can't test download. Try again with more items.")
        return

    md = photo.get("mediaMetadata", {})
    print(f"    sample: {photo.get('filename')}  creationTime={md.get('creationTime')}  "
          f"{md.get('width')}x{md.get('height')}")
    print(f"    API mediaMetadata exposes a 'location' field?  {'location' in md}")

    # ---- Q2: does the API-downloaded original keep EXIF GPS? ----
    print("\n[2] Downloading the original via baseUrl=d and checking EXIF ...")
    dl = requests.get(photo["baseUrl"] + "=d", timeout=60)  # baseUrl is pre-authorized
    print(f"    HTTP {dl.status_code}, {len(dl.content)} bytes")
    if dl.status_code != 200:
        print("    download failed:", dl.text[:300]); return

    ex = Image.open(io.BytesIO(dl.content)).getexif()
    eifd = ex.get_ifd(0x8769)
    gps = ex.get_ifd(0x8825)
    print(f"    EXIF DateTimeOriginal: {eifd.get(36867)}")
    print(f"    EXIF Make/Model: {ex.get(271)} / {ex.get(272)}")
    if gps and 2 in gps and 4 in gps:
        lat = _to_deg(gps[2], gps.get(1, "")); lng = _to_deg(gps[4], gps.get(3, ""))
        print(f"\n    ✅ GPS SURVIVED THE API DOWNLOAD: ({lat}, {lng})")
        print("    => The 'download via API -> extract EXIF' approach WORKS. Build it.")
    else:
        print("\n    ❌ NO GPS in the API-downloaded bytes — the API stripped location.")
        print("    => EXIF-from-API-download will NOT recover coordinates. Fall back to")
        print("       periodic Google Takeout (originals + geoData sidecars).")


if __name__ == "__main__":
    main()
