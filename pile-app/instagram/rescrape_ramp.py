#!/usr/bin/env python3
"""rescrape_ramp.py — risk-aware full Instagram pile rebuild.

Walks small -> large scrape sizes against the same target to surface a
challenge / Bloks block / IP-throttle EARLY, before committing to the
~2.5h marathon. Each step's stdout is scanned for halt-marker patterns
(challenge, STEP_NAME, login_required, private-API throttle); any hit
halts escalation to preserve the burner account.

Step ladder:
  0. session sanity         (~30 sec, no scrape)
  1. pytest smoke test      (1 post,    rate=normal — pinned by test;
                             only runs when target == 'ourearthsandwich')
  2. small probe            (~10 posts, rate=gentle, single page)
  3. multi-page probe       (~29 posts, rate=gentle, 3 pages)
  4. full re-scrape         (all posts, rate=gentle, ~2-3h marathon)

Cooldowns between scrape steps (skip with --no-cooldowns, discouraged):
  - 20 min after step 1 / step 2
  - 60 min before step 4 (the marathon)

Halt rule: any halt-marker in a step's stdout -> script exits non-zero
with the offending pattern named. Operator must investigate before
re-running. CLI exit code 0 is NOT used as the success signal — many
session-failure paths exit 0 silently (resolve_target_user_id returns
None without raising).

Origin: 2026-06-01 burner-rotation ramp, after the `ottomann12345`
Bloks-challenge burn. Documented in docs/planning/2026-W22.md.

Usage:
    cd pile-app
    venv/Scripts/python.exe instagram/rescrape_ramp.py <target>
    venv/Scripts/python.exe instagram/rescrape_ramp.py <target> --no-cooldowns
    venv/Scripts/python.exe instagram/rescrape_ramp.py <target> --from-step 3
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]  # pile-app/
CLI = APP_ROOT / "cli.py"
TSV_DIR = APP_ROOT / "pile"
LOG_DIR = APP_ROOT / "logs"

HALT_PATTERNS = [
    re.compile(r"! could not resolve user_id"),
    re.compile(r"STEP_NAME"),
    re.compile(r"login_required"),
    re.compile(r"\bchallenge\b", re.IGNORECASE),
    re.compile(r"Bloks"),
    # Private-API throttle (NOT the public web-endpoint 429, which is benign here)
    re.compile(r"Max retries exceeded.*url: /api/v1/users/[^/]+/info"),
    # Any FetchInterruptedError / inference hard-block / generic failure -> rollback banner
    re.compile(r"FAILURE — @.* scrape rolled back"),
]

COOLDOWN_AFTER_SMOKE = 20 * 60      # step 1 -> step 2
COOLDOWN_AFTER_SMALL = 20 * 60      # step 2 -> step 3
COOLDOWN_BEFORE_MARATHON = 60 * 60  # step 3 -> step 4

DEFAULT_FULL_CUTOFF = "2015-01-01T00:00:00+0000"
SMOKE_TEST_TARGET = "ourearthsandwich"


def _python_bin() -> str:
    """Return the venv python (Windows path) or fall back to sys.executable."""
    venv_py = APP_ROOT / "venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)
    venv_py_posix = APP_ROOT / "venv" / "bin" / "python"
    if venv_py_posix.exists():
        return str(venv_py_posix)
    return sys.executable


def _scan_halt(text: str, step_label: str) -> None:
    """Raise SystemExit if any halt-marker pattern is present in the text."""
    for pattern in HALT_PATTERNS:
        match = pattern.search(text)
        if match:
            raise SystemExit(
                f"\nHALT — step {step_label} matched halt pattern "
                f"{pattern.pattern!r} (snippet: {match.group(0)!r}).\n"
                f"Burner account may be flagged. Investigate before re-running."
            )


def session_sanity(target: str) -> None:
    print(f"\n=== Step 0: session sanity check for @{target} ===", flush=True)
    snippet = (
        "from instagram.instagrapi_client import init_instagrapi_client; "
        "cl = init_instagrapi_client(); "
        f"info = cl.user_info_by_username({target!r}); "
        "print(f'OK: user_id={info.pk} media_count={info.media_count}')"
    )
    proc = subprocess.run(
        [_python_bin(), "-c", snippet],
        cwd=APP_ROOT, capture_output=True, text=True,
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    sys.stdout.flush()
    _scan_halt(proc.stdout + proc.stderr, step_label="0 session sanity")
    if "OK: user_id=" not in proc.stdout:
        raise SystemExit(
            "Step 0: session sanity did NOT return OK. "
            "Refresh the session (delete instagrapi_session.json, re-run)."
        )


def smoke_test(target: str) -> None:
    if target != SMOKE_TEST_TARGET:
        print(
            f"\n=== Step 1: pytest smoke test SKIPPED (target {target!r} != "
            f"{SMOKE_TEST_TARGET!r}; smoke test is pinned to that account) ===",
            flush=True,
        )
        return
    print("\n=== Step 1: pytest smoke test (1 post, normal rate) ===", flush=True)
    proc = subprocess.run(
        [_python_bin(), "-m", "pytest", "tests/instagram/test_instagram_pull.py", "-q"],
        cwd=APP_ROOT, capture_output=True, text=True,
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    sys.stdout.flush()
    _scan_halt(proc.stdout + proc.stderr, step_label="1 smoke test")
    if proc.returncode != 0:
        raise SystemExit(
            f"Step 1 pytest failed (returncode {proc.returncode}). "
            f"Investigate before continuing."
        )


def _nth_newest_timestamp(target: str, n: int) -> str:
    """Return the ISO timestamp of the n-th most recent row in the target's TSV.

    Used to derive --newer-than cutoffs that yield ~N posts to re-fetch.
    """
    tsv = TSV_DIR / f"posts.{target}.local.tsv"
    if not tsv.exists():
        raise SystemExit(
            f"TSV not found at {tsv}; can't derive cutoff. "
            "Either run a baseline scrape first, or pass --from-step 4 to skip "
            "the probes and go straight to the full re-scrape."
        )
    timestamps = []
    with tsv.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            ts = row.get("timestamp", "")
            if ts:
                timestamps.append(ts)
    if len(timestamps) < n:
        raise SystemExit(
            f"TSV has {len(timestamps)} timestamped rows; can't pick the "
            f"{n}-th most recent (probe size too large for current pile)."
        )
    timestamps.sort(reverse=True)
    return timestamps[n - 1]


def run_scrape(target: str, newer_than: str, rate: str, step_label: str) -> None:
    """Run cli.py run instagram with the given cutoff. Stream stdout, tee to log, scan."""
    LOG_DIR.mkdir(exist_ok=True)
    log_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = LOG_DIR / f"ramp-{target}-step{step_label[0]}-{log_ts}.log"
    print(f"  log: {log_path}", flush=True)
    cmd = [
        _python_bin(), str(CLI), "run", "instagram",
        "--targets", target,
        "--rate", rate,
        "--newer-than", newer_than,
    ]
    chunks: list[str] = []
    with log_path.open("w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(
            cmd, cwd=APP_ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            log_file.write(line)
            chunks.append(line)
        proc.wait()
    _scan_halt("".join(chunks), step_label=step_label)


def cooldown(seconds: int, label: str, skip: bool) -> None:
    if skip:
        print(f"\n--- [SKIPPED] cooldown {label} ({seconds // 60} min) ---", flush=True)
        return
    minutes = seconds // 60
    print(f"\n--- cooldown {label}: sleeping {minutes} min ---", flush=True)
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        remaining = int(end - time.monotonic())
        rmin = remaining // 60
        rsec = remaining % 60
        print(f"  ... {rmin}m {rsec}s remaining", flush=True)
        time.sleep(min(60, remaining))
    print(f"--- cooldown done ---", flush=True)


def main() -> None:
    # Force UTF-8 stdout/stderr so the em-dashes and Unicode in our help text +
    # the cli.py output we tee print correctly on Windows (cp1252 default).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

    parser = argparse.ArgumentParser(
        description="Risk-aware full Instagram pile re-scrape ramp.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("target", help="Instagram handle (without @)")
    parser.add_argument(
        "--no-cooldowns", action="store_true",
        help="Skip the 20/60-min inter-step pauses. STRONGLY DISCOURAGED — "
             "the pauses are anti-throttle measures.",
    )
    parser.add_argument(
        "--from-step", type=int, default=0, choices=range(5),
        help="Resume from a specific step (0-4). Earlier steps skipped. Default: 0.",
    )
    parser.add_argument(
        "--full-cutoff", default=DEFAULT_FULL_CUTOFF,
        help=f"Step 4 cutoff timestamp (ISO 8601). Default: {DEFAULT_FULL_CUTOFF} "
             "(captures full Instagram history).",
    )
    args = parser.parse_args()

    target = args.target.lstrip("@")

    banner = (
        "================================================================\n"
        f"  Full re-scrape ramp for @{target}\n"
        f"  From step: {args.from_step}\n"
        f"  Cooldowns: {'SKIPPED (risky)' if args.no_cooldowns else 'enforced'}\n"
        f"  Full cutoff: {args.full_cutoff}\n"
        "================================================================"
    )
    print(banner, flush=True)

    if args.from_step <= 0:
        session_sanity(target)

    if args.from_step <= 1:
        smoke_test(target)
        if args.from_step <= 1:  # only sleep if we actually ran step 1 or earlier
            cooldown(COOLDOWN_AFTER_SMOKE, "after smoke test", args.no_cooldowns)

    if args.from_step <= 2:
        cutoff = _nth_newest_timestamp(target, 11)
        print(f"\n=== Step 2: small probe (10 posts, gentle, single page) ===", flush=True)
        print(f"  --newer-than {cutoff}", flush=True)
        run_scrape(target, cutoff, rate="gentle", step_label="2 small probe")
        cooldown(COOLDOWN_AFTER_SMALL, "after small probe", args.no_cooldowns)

    if args.from_step <= 3:
        cutoff = _nth_newest_timestamp(target, 30)
        print(f"\n=== Step 3: multi-page probe (~29 posts, gentle, 3 pages) ===", flush=True)
        print(f"  --newer-than {cutoff}", flush=True)
        run_scrape(target, cutoff, rate="gentle", step_label="3 multi-page probe")
        cooldown(COOLDOWN_BEFORE_MARATHON, "before full re-scrape", args.no_cooldowns)

    if args.from_step <= 4:
        print(f"\n=== Step 4: FULL RE-SCRAPE (gentle, ~2-3h marathon) ===", flush=True)
        print(f"  --newer-than {args.full_cutoff}", flush=True)
        run_scrape(target, args.full_cutoff, rate="gentle", step_label="4 full")

    print("\n[OK] Ramp complete. Pile rebuilt.", flush=True)


if __name__ == "__main__":
    main()
