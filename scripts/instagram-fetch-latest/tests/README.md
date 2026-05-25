# Tests for the Instagram pull pipeline

## What's here

- `test_process_media.py` — **unit tests** for `process_media`, the
  per-post handler extracted from `main()`. 22 tests covering the dual-
  path branching (tagged vs. inferred), edge cases for `(0,0)` and
  name-only Location tags, IMAGE/VIDEO/Album URL selection, timestamp
  normalization, path normalization, and field extraction. Mocks
  `download_media`, `get_region_only_via_claude`, and
  `get_location_via_claude` so the whole file runs in <1s. Unmarked.
- `test_location_helpers.py` — **unit tests** for `get_region_only_via_claude`
  and `get_location_via_claude`. Mocks the Anthropic client so they run in
  ~2s with no network, no credentials. 21 tests covering response
  sanitization, JSON-fence stripping, image-inclusion rules, recent-locations
  injection, and the bias-guard wording. Unmarked.
- `test_instagram_pull.py` — **integration smoke test**. Truncates
  `posts.local.tsv` to row 322, runs `load_posts_tsv.py`, and verifies that
  row 323 (the Mexico City test post on `@welawen`) comes back with its
  explicit geo-tag intact. ~8s. Marked `@pytest.mark.integration`.

## How to run

```bash
# All tests (unit + integration) from the project root:
scripts\instagram-fetch-latest\venv\Scripts\pytest scripts/instagram-fetch-latest/tests

# Unit tests only — the fast path; skip the live-API integration test:
scripts\instagram-fetch-latest\venv\Scripts\pytest scripts/instagram-fetch-latest/tests -m "not integration"

# Cross-platform from an activated venv:
pytest scripts/instagram-fetch-latest/tests
```

Required env (read from `.env` automatically by `conftest.py`):

- `INSTA_USERNAME`
- `INSTA_PASSWORD`
- `ANTHROPIC_API_KEY`

If any are missing, the test skips with a clear message rather than failing.

The test rewrites `posts.local.tsv` on every run (it's how we guarantee
row 323 is re-pulled). Don't be surprised by the diff after a successful run.

## When to run this in CI

This is an integration test — it hits live Instagram (via instagrapi) and
the Anthropic API. Treat it accordingly.

| Trigger | Recommended? | Rationale |
|---|---|---|
| **Nightly cron** | ✅ Strongly recommended | Catches credential expiry, prompt drift, Instagram API changes, and Claude regressions before they're discovered the hard way. Cost is fractions of a cent per run. |
| **`workflow_dispatch` (manual)** | ✅ Recommended | On-demand sanity check after touching the script or the prompt. |
| **On merge to `master`** | ✅ Recommended | Final gate so regressions don't sneak in. |
| **On PRs that change `scripts/instagram-fetch-latest/**` or `backend/app/ingestion/**`** | ✅ Recommended (path-filtered) | Scoped opt-in for ingestion-related PRs only. |
| **On every PR push** | ❌ Avoid | Too expensive at scale; Instagram will rate-limit aggressive login churn even with session caching. |
| **In pre-commit hooks** | ❌ Avoid | Too slow (≥30s per run), and requires secrets that shouldn't be on dev machines that don't already have them. |

## CI/CD wiring notes

Two things to get right for this to work in GitHub Actions (or equivalent):

1. **Secrets**: store `INSTA_USERNAME`, `INSTA_PASSWORD`, and
   `ANTHROPIC_API_KEY` as repository secrets and inject them into the job's
   env. Don't put them in `.env.example`.

2. **Session caching**: instagrapi's session file
   (`scripts/instagram-fetch-latest/instagrapi_session.json`) MUST persist
   across runs. Without it, every job triggers a fresh login, which (a) is
   slow, (b) eventually triggers Instagram's challenge flow that can't be
   answered in non-interactive CI, and (c) gets the account rate-limited
   for excessive login attempts. Use `actions/cache` keyed on
   `INSTA_USERNAME` (or a hash of `requirements.txt` if you want it tied to
   instagrapi version).

   Sketch:

   ```yaml
   - uses: actions/cache@v4
     with:
       path: scripts/instagram-fetch-latest/instagrapi_session.json
       key: instagrapi-session-${{ secrets.INSTA_USERNAME_HASH }}-${{ hashFiles('scripts/instagram-fetch-latest/requirements.txt') }}
   ```

3. **First-run bootstrapping**: the very first CI run still needs a valid
   session file in the cache. Best to generate it locally once (run the
   script with credentials, let it log in, copy the resulting
   `instagrapi_session.json` into the cache via a manual seed action) and
   then let cron keep it warm.

## Building on this

Patterns established here, to follow as the suite grows:

- Live-service tests get `@pytest.mark.integration`; offline/mocked tests
  get no marker.
- Default per-PR CI: `pytest -m "not integration"` — fast, no credentials.
- Nightly cron + `master` merges: `pytest` — runs everything.
- Keep integration tests small in count and short in runtime — they're slow
  and rate-limit-prone. Cover code logic in unit tests with mocks instead.
- Mocking pattern: see `mock_anthropic_client` fixture in
  `test_location_helpers.py` for how to patch `anthropic.Anthropic` from
  inside the `load_posts_tsv` module via `monkeypatch.setattr`.

Natural next steps for expanding coverage:

1. ✅ **Dual-path branching test** — done. `process_media` was extracted
   from `main()` and `test_process_media.py` covers the tagged-vs-inferred
   dispatch, plus the media URL/type, timestamp, and path-normalization
   logic.
2. **`fetch_new_media_instagrapi` cursor walk** — verify the
   "stop when ts <= since_ts" logic with a fake paginated client. Would
   need a small wrapper or `monkeypatch` on `cl.user_medias_paginated_v1`
   that returns synthetic Media lists with controlled timestamps.
