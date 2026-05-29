"""Anti-detection rate presets + helpers.

Each preset bundles the knobs that shape pagination cadence:
  - page_size: posts per pagination request (smaller = more human-scroll-like)
  - page_delay: (min, max) seconds of random jitter between consecutive page fetches
  - long_rest_every / long_rest: every N pages, take a longer "human pause"
  - media_delay: (min, max) seconds between per-post processing

Throughput estimates assume ~3-5s of per-post processing (download + LLM calls).

  aggressive: ~1500 posts/hr, hit a STEP_NAME challenge after ~7 pages in testing.
              Use only when you've verified the account is warmed up and trusted.
  normal:     ~300 posts/hr, mimics a casual scroll cadence. The default.
  gentle:     ~120 posts/hr, the safest sustained rate. Use for large backfills.
"""

from __future__ import annotations

import random
import time

RATE_PRESETS: dict[str, dict] = {
    "aggressive": {
        "page_size": 50,
        "page_delay": (0.0, 0.0),
        "long_rest_every": 0,  # 0 disables the long-rest periodic pause
        "long_rest": (0.0, 0.0),
        "media_delay": (0.0, 0.0),  # no jitter between per-post processing
    },
    "normal": {
        "page_size": 12,
        "page_delay": (30.0, 90.0),
        "long_rest_every": 5,
        "long_rest": (90.0, 180.0),
        "media_delay": (1.0, 3.0),  # mimics human dwell time on each post
    },
    "gentle": {
        "page_size": 12,
        "page_delay": (90.0, 180.0),
        "long_rest_every": 3,
        "long_rest": (180.0, 300.0),
        "media_delay": (2.0, 5.0),
    },
}
DEFAULT_RATE_PRESET = "normal"


def jittered_sleep(low: float, high: float, label: str = "") -> None:
    """Sleep for a random duration in [low, high] seconds. Logs the chosen
    duration so operator output makes the wait visible. No-op when high<=0."""
    if high <= 0:
        return
    wait = random.uniform(max(0.0, low), high)
    if label:
        print(f"  … {label}: sleeping {wait:.1f}s")
    time.sleep(wait)


def is_challenge_error(exc: Exception) -> bool:
    """Identify Instagram challenge-response errors that can't be auto-resolved.

    Distinguishes these from transient network/5xx errors: a challenge requires
    the operator to verify the account in the Instagram app, so retrying the
    same request is pointless. Transient errors are worth retrying / sleeping
    through; challenges are not.
    """
    s = str(exc).lower()
    return "challenge" in s or "step_name" in s or "checkpoint" in s
