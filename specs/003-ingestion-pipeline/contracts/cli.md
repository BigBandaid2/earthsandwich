# Contract: CLI surface

**Producer**: `pile-app/cli.py` + per-service entry points.
**Consumer**: human operator + OS-level schedulers (cron, Windows Task Scheduler) if the operator chooses not to use the in-process scheduler.

The CLI is invoked as `python -m pile_app <subcommand> ...` from within an activated venv at `pile-app/`. Today's working invocation (`python load_posts_tsv.py ...` from `scripts/instagram-fetch-latest/`) is grandfathered until the migration phase ships; new code targets the namespaced form.

---

## Subcommands

### `run <service> <target> [options]`

One-off invocation of a single pipeline service against a single target / publication.

- **service**: positional, required. One of `instagram`, `substack`.
- **target**: positional, required. Account handle (Instagram) or publication slug (Substack).
- **options**:
  - `--rate {aggressive,normal,gentle}` — overrides the rate preset from `config.yml`. Default: `normal` (Instagram), `aggressive` (Substack).
  - `--max-pages N` — caps the number of pages fetched (Instagram only; debug-only). Default: unlimited.
  - `--dry-run` — fetches without writing TSV rows or media files. Default: off.

Exit codes:

- `0` — success (incremental or first-time scrape completed cleanly)
- `1` — operator error (bad arguments, missing credentials, target not found)
- `2` — hard block (FR-052: challenge / checkpoint encountered; operator must resolve before re-running)
- `3` — partial progress (mid-pagination crash; pile is in a consistent state with rows up to the last completed page)

### `schedule [options]`

Starts the in-process APScheduler with all enabled services from `config.yml`.

- **options**:
  - `--config PATH` — path to schedule config. Default: `pile-app/config.yml`.

Runs in the foreground; Ctrl-C halts gracefully (in-flight scrapes finish their current page before exit). No daemonization in v1 — operator MAY wrap with `nohup` / `screen` / `tmux` / `systemd` as desired.

Exit codes:

- `0` — graceful shutdown via Ctrl-C
- `1` — config parse error
- `2` — a service's hard-block halted the scheduler (operator must resolve)

### `list-targets <service>`

Lists the configured targets/publications for the given service from `config.yml`. Useful for verifying the operator's allow-list.

### `version`

Prints the App's version (from `pile-app/pyproject.toml`).

---

## Environment variables

Read from `.env` at the App root via `python-dotenv`. The App MUST fail-fast with a descriptive error if a required variable is missing.

| Variable | Required | Purpose |
|---|---|---|
| `INSTA_USERNAME` | yes (for Instagram service) | Crawler account handle |
| `INSTA_PASSWORD` | yes (for Instagram service) | Crawler account password |
| `ANTHROPIC_API_KEY` | yes (for any service that does inference) | LLM provider key |
| `ANTHROPIC_MODEL` | optional | Override the default model (`claude-sonnet-4-6`). Useful for cost experiments. |

The `.env.example` file at the App root documents these with placeholder values.

---

## Logging behaviour

Every invocation that fetches data writes a run log (see [data-model.md § Run Log](../data-model.md#internal-run-log)). The log file is created at the start of the run and finalized at exit (including the hard-block exit path).

`stdout` mirrors the key events from the log file: scrape start/end, per-page completion, sleep durations, hard-block trigger, post-pass summary. Verbose-level logs (per-post detail, request timings) go only to the file.

---

## Backward compatibility

The current `scripts/instagram-fetch-latest/load_posts_tsv.py` CLI accepts a different argument shape (`--targets <csv>`, `--rate ...`). The migration phase MUST either:

1. Preserve a thin compatibility shim at the old path that maps to the new CLI, OR
2. Document the new invocation in `README.md` + this contract + the operator's shell history.

Option 2 is preferred (less code; cleaner state).
