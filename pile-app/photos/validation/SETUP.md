# Google Photos API spike — one-time setup

Goal: get an OAuth **client secret** so `gphotos_spike.py` can read your Google
Photos and test whether an API-downloaded photo keeps its GPS EXIF.

This is a personal **Testing**-mode app — no Google review/verification needed.

## Steps (Google Cloud Console — https://console.cloud.google.com)

1. **Create/select a project** (top bar → project dropdown → New Project). Any name.
2. **Enable the API**: ☰ → *APIs & Services → Library* → search **"Photos Library API"** → **Enable**.
3. **OAuth consent screen**: *APIs & Services → OAuth consent screen*
   - User type: **External** → Create.
   - App name + your email in the required fields → Save and continue.
   - Scopes: skip (Save and continue).
   - **Test users**: add **your own Google account email** → Save. Leave the app in **Testing** (do NOT publish).
4. **Create credentials**: *APIs & Services → Credentials → Create Credentials → OAuth client ID*
   - Application type: **Desktop app** → name it → **Create**.
   - **Download JSON**.
5. Save that file as:  `pile-app/photos/validation/client_secret.json`
   (gitignored — it's a credential, never commit it.)

## Run the spike

```pwsh
cd pile-app
venv\Scripts\python.exe photos\validation\gphotos_spike.py
```

- A browser opens → sign in with the account you added as a test user.
- You'll see **"Google hasn't verified this app"** — expected for a personal test app.
  Click **Advanced → Go to <app> (unsafe)** → **Continue**, and grant read-only
  Photos access.
- The token is cached as `token.json` (also gitignored) so later runs skip the browser.

## What the output means

- **`[1] Listing ... HTTP 200`** → the API still lets us enumerate the library.
  A non-200 here means Google's 2025 restrictions block continuous pulling.
- **`✅ GPS SURVIVED`** → build the "download + EXIF" pipeline as planned.
- **`❌ NO GPS ...`** → the API strips location on download; fall back to periodic
  Google Takeout (originals + geoData sidecars).

Paste the script's output back and I'll interpret it + plan the next step.
