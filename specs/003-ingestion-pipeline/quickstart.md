# Quickstart: Ingestion Pipeline App

**Phase 1 output of `/speckit.plan`.** Operator-facing first-run + everyday-use guide. Assumes the migration to `pile-app/` is complete; if you're still on `scripts/instagram-fetch-latest/`, see [research.md § Migration strategy](research.md#decision-migration-strategy--scriptsinstagram-fetch-latest--pile-app) first.

---

## Prerequisites

- Python 3.14 (verify with `python --version`)
- A burner Instagram crawler account that's separate from your target accounts (use a phone number you control; expect occasional re-verification challenges)
- An Anthropic API key with credit (the inferred-location path uses vision + text; ~$0.01–0.05 per scraped post depending on caption length)
- For Substack: just the public RSS feed URLs of the publications you want to ingest

---

## First-time setup

```pwsh
# 1. Clone the repo (or you're already in it)
cd c:\workspace\earthsandwich

# 2. Create the App's venv
cd pile-app
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure credentials
copy .env.example .env
# Open .env in your editor and fill in:
#   INSTA_USERNAME=...
#   INSTA_PASSWORD=...
#   ANTHROPIC_API_KEY=sk-ant-...

# 5. Configure schedules + targets
# Open config.yml in your editor; the shipped default has the targets used today
# (ourearthsandwich, welawen). Adjust target list and cadence to your needs.
```

## Verify the install with a dry-run

```pwsh
python -m pile_app run instagram ourearthsandwich --dry-run --max-pages 1
```

Expected output: the App fetches the first page of @ourearthsandwich, runs canonicalization + inference on each post, and prints the rows it WOULD have written, without touching the TSV or media files. If you see an Instagram challenge error here, resolve it in a browser (Instagram → Settings → Security → re-verify) before continuing.

## Run a real first-scrape

```pwsh
python -m pile_app run instagram ourearthsandwich
```

A full first-scrape for a ~300-post account at the `normal` rate preset takes about 60–70 minutes. The App prints an ETA at the start and progress per page; you can `Ctrl-C` at any time and the pile rows already written are preserved (resume on the next run is automatic).

After completion, verify:

```pwsh
# Row count
Get-Content pile\posts.ourearthsandwich.local.tsv | Measure-Object -Line

# Media file count (should roughly match the row count)
Get-ChildItem pile\media\instagram\ourearthsandwich_*.jpg | Measure-Object | Select-Object Count

# Most recent run log
Get-ChildItem logs\scrape-instagram-ourearthsandwich-*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 20
```

## Add a Substack publication

```pwsh
# In config.yml, add the publication slug under schedules.substack.publications:
# substack:
#   enabled: true
#   publications:
#     - "welalive"

# Then run it once manually
python -m pile_app run substack welalive
```

Substack RSS feeds are capped at the most-recent ~20 entries; the first scrape captures only what RSS exposes. Older posts won't be in the pile — this is a known limitation, not a bug.

## Run on a schedule (in-process)

```pwsh
python -m pile_app schedule
```

Runs in the foreground. APScheduler dispatches each enabled service per the `cadence` in `config.yml`. Open a separate terminal to tail logs; `Ctrl-C` in the scheduler terminal halts gracefully.

For unattended operation, wrap with your OS's session-keepalive tool of choice (Windows Task Scheduler scheduled at boot, `nohup` + `tmux` on Linux, `launchd` on macOS).

## Run on a schedule (external cron)

If you prefer external scheduling (recommended for survivability across reboots without extra wrapping):

```text
# Windows Task Scheduler: create a task that runs hourly:
#   C:\workspace\earthsandwich\pile-app\venv\Scripts\python.exe -m pile_app run instagram ourearthsandwich

# Linux/macOS cron equivalent:
#   0 * * * * cd /path/to/pile-app && ./venv/bin/python -m pile_app run instagram ourearthsandwich
```

You can have multiple cron entries running different services in parallel — the App's pile artifacts are per-`(service, target)` pair, so cross-service contention is structurally absent.

---

## Troubleshooting

### "instagrapi challenge_required" on first login

Open instagram.com in a normal browser logged in as your crawler account, complete the verification, then re-run. The session file is preserved across runs.

### Inference returning empty for every post

Check the run log for `[ERROR] anthropic.RateLimitError` or `[ERROR] anthropic.AuthenticationError`. The former means you've hit the API rate limit (wait an hour); the latter means your `ANTHROPIC_API_KEY` is wrong or expired.

### "scrape end ... 0 new rows" on every incremental run

If incremental runs report no new rows but you've posted new content upstream, check:

1. Is your `INSTAGRAM_TARGET_ACCOUNTS` env var or `config.yml` `targets` list using the correct handle (no `@`, lowercase)?
2. Is the target account public, or is your crawler one of its approved followers? Private posts require follow approval.

### Stale media files accumulating in `pile/media/instagram/`

Run any incremental scrape — the post-pass orphan sweep removes media not referenced by the current TSV. If the sweep isn't catching files you expect it to, check that the prefix matches (`<target>_*`).

### How do I know if I've been hard-blocked?

The CLI exits with code `2` and the run log ends with a `[ERROR] challenge_required` or `[ERROR] checkpoint_required` line. Resolve in a browser before re-running. The App will NOT auto-retry — by design, per FR-052.

### Where do I check for upstream-deleted posts?

Rows with `deleted_upstream` = `true`. Quick view:

```pwsh
# Show shortcode + deletion timestamp for tombstoned rows
Get-Content pile\posts.ourearthsandwich.local.tsv |
  ConvertFrom-Csv -Delimiter "`t" |
  Where-Object { $_.deleted_upstream -eq "true" } |
  Select-Object shortcode, deleted_upstream_at
```

---

## Common operator workflows

### Adding a new Instagram target

1. Edit `config.yml`, append the handle to `schedules.instagram.targets`.
2. Run a one-off first-scrape: `python -m pile_app run instagram <handle>`.
3. Verify the TSV + media files were created.
4. If using in-process scheduling, restart `python -m pile_app schedule` to pick up the new target.

### Rotating the crawler account

If your crawler gets perma-banned (rare with the `normal` preset, eventual at scale):

1. Stop any running schedule (Ctrl-C).
2. Update `INSTA_USERNAME` + `INSTA_PASSWORD` in `.env`.
3. Delete `pile-app/instagrapi_session.json` (forces a fresh login).
4. Run a small test: `python -m pile_app run instagram <small_target> --max-pages 1`.
5. If login succeeds, resume normal operation.

### Inspecting why a post got an empty `location`

1. Find the row in the TSV.
2. Check `tag_verbatim` — if non-empty, the canonicalization LLM failed (likely a transient error; re-run will retry).
3. If `tag_verbatim` is empty, the inferred path ran. Check `reasoning` for the model's prose; this usually explains why the model couldn't pin a location (caption was abstract, image was a close-up, etc.).
4. The post's `caption` and `media_url` are preserved per FR-105 so you can re-run inference manually:

```pwsh
python -c "from pile_app.common.inference import infer_post_location; print(infer_post_location(caption='...', media_path='pile/media/instagram/...'))"
```

(or open an interactive Python shell and call the function directly.)

---

## What to do next

- **For the operator**: just let it run. Hourly cadence at `normal` preset has survived 100+ runs in our usage; the App is well-behaved at this scale.
- **For the developer extending the App**: see `pile-app/instagram/README.md` and `pile-app/substack/README.md` for service-specific internals, or [`spec.md`](spec.md) for the feature-level requirements.
- **For the bridge-app maintainer (future)**: this App is your data source. See [`contracts/pile-artifact-instagram.md`](contracts/pile-artifact-instagram.md) and [`contracts/pile-artifact-substack.md`](contracts/pile-artifact-substack.md) for the read-side contracts.
