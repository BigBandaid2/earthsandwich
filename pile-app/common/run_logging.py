"""Per-run log file lifecycle helpers.

The shell tee's the run output into `scrape-<service>-<target>-<ts>.log` —
this module's job is to enforce FR-072's retention policy (keep the 5 most
recent per service+target) AND to write a structured `scrape-failures.jsonl`
record per failed run so an admin can troubleshoot after the fact.

The structured failure log is intentionally append-only JSON Lines so the
operator can `jq`-grep it and so the scheduler's stdout/stderr isn't the
only place failure context survives.
"""

from __future__ import annotations

import glob as _glob
import json
import os
from datetime import datetime, timezone


FAILURE_LOG_FILENAME = "scrape-failures.jsonl"


def write_failure_record(log_dir: str, record: dict) -> None:
    """Append one JSON line to `<log_dir>/scrape-failures.jsonl`.

    The caller passes structured fields (target, failure_type, detail,
    elapsed_seconds, etc.). This helper adds `logged_at` automatically.

    Best-effort: if the write itself fails (disk full, permissions), the
    error is printed to stdout but the function does NOT raise — we're
    already on a failure path and must not compound it.
    """
    if not log_dir:
        return
    augmented = {**record, "logged_at": datetime.now(timezone.utc).isoformat()}
    path = os.path.join(log_dir, FAILURE_LOG_FILENAME)
    try:
        os.makedirs(log_dir, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(augmented) + "\n")
    except OSError as exc:
        print(f"  ! could not write failure record to {path}: {exc}")


def prune_scrape_logs(target: str, log_dir: str, keep: int = 5) -> None:
    """Keep only the most recent `keep - 1` `scrape-<target>-*.log` files in
    `log_dir`. The in-flight log being written by the shell's `tee` (if any)
    will bring the total to `keep` after this run completes.

    Best-effort: file-system errors during deletion are reported but do not
    abort the scrape. Matches strictly `scrape-<target>-*.log` so an account
    `test` won't sweep an account `testing`'s logs (the trailing `-`
    separator after the target name enforces the boundary).
    """
    pattern = os.path.join(log_dir, f"scrape-{target}-*.log")
    logs = _glob.glob(pattern)
    if not logs or len(logs) < keep:
        return
    logs.sort(key=lambda p: os.path.getmtime(p))  # oldest first
    keep_count = max(0, keep - 1)
    to_delete = logs[:-keep_count] if keep_count else logs
    pruned: list[str] = []
    for path in to_delete:
        try:
            os.remove(path)
            pruned.append(os.path.basename(path))
        except OSError as exc:
            print(f"  ! could not prune log {os.path.basename(path)}: {exc}")
    if pruned:
        sample = ", ".join(pruned[:3])
        more = f" (+{len(pruned) - 3} more)" if len(pruned) > 3 else ""
        print(f"  pruned {len(pruned)} stale scrape log(s): {sample}{more}")
