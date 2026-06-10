"""pile-app CLI entry point.

Invoked via the `pile_app` console script (after `pip install -e .`) or
directly with `python cli.py ...` from inside `pile-app/`.

Surface: `run instagram <target>` (mirrors the prior `load_posts_tsv.py
--targets ... --rate ...` invocation) and `run substack <publication>`
(Phase 23). The scheduler subcommand is added in Phase 24.
"""

from __future__ import annotations

import argparse
import os
import sys

from common.anti_throttle import DEFAULT_RATE_PRESET, RATE_PRESETS
from common.pile import (
    APP_ROOT,
    DEFAULT_MEDIA_DIR,
    DEFAULT_OUTPUT_TEMPLATE,
    DEFAULT_SUBSTACK_OUTPUT_TEMPLATE,
)
from instagram.instagrapi_client import (
    INSTAGRAPI_SESSION_FILE,
    init_instagrapi_client,
)
from instagram.pipeline import parse_unix_timestamp, run_for_target
from substack.pipeline import run_archive_backfill, run_for_publication

DEFAULT_TARGETS = os.environ.get("INSTAGRAM_TARGET_ACCOUNTS", "ourearthsandwich")


def _run_instagram(args: argparse.Namespace) -> int:
    targets = [t.strip().lstrip("@") for t in args.targets.split(",") if t.strip()]
    if not targets:
        print("\nERROR: no target accounts specified. Set --targets or INSTAGRAM_TARGET_ACCOUNTS.")
        return 1
    if len(targets) > 1 and "{target}" not in args.output:
        print("\nERROR: multiple targets require '{target}' in --output template.")
        return 1

    newer_than_ts = None
    if args.newer_than:
        try:
            newer_than_ts = parse_unix_timestamp(args.newer_than)
        except ValueError as exc:
            print(
                f"\nERROR: --newer-than value {args.newer_than!r} is not a valid ISO 8601 "
                f"timestamp ({exc}). Examples: '2024-02-20', '2024-02-20T02:27:16+0000', "
                f"'2024-02-20T02:27:16+00:00'."
            )
            return 1

    ig_client = init_instagrapi_client()
    if ig_client is None:
        print(
            "\nERROR: instagrapi is required. Set INSTA_USERNAME and INSTA_PASSWORD "
            "in .env and re-run. If a previous session file is corrupted, delete "
            f"{INSTAGRAPI_SESSION_FILE} and try again."
        )
        return 1

    rate_config = RATE_PRESETS[args.rate]
    print(f"Anti-throttle rate: {args.rate} (page_size={rate_config['page_size']}, page_delay={rate_config['page_delay']}s)")

    log_dir = str(APP_ROOT / "logs")
    os.makedirs(log_dir, exist_ok=True)

    for target in targets:
        run_for_target(
            ig_client, target, args.output, args.media_dir, rate_config,
            log_dir=log_dir, newer_than_ts=newer_than_ts,
        )
    return 0


def _run_substack(args: argparse.Namespace) -> int:
    slug = args.publication.strip().lstrip("@").rstrip("/")
    if not slug:
        print("\nERROR: no publication slug specified.")
        return 1

    log_dir = str(APP_ROOT / "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Both paths handle their own failures (log + clean return), so an upstream
    # error is a clean exit, not a crash — US4 Independent Test / FR-031.
    if args.archive:
        run_archive_backfill(
            slug, args.output, log_dir=log_dir,
            page_delay=(args.page_delay, args.page_delay),
            max_posts=args.max_posts,
        )
    else:
        run_for_publication(slug, args.output, log_dir=log_dir, feed_url=args.feed_url)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pile_app", description="Ingestion Pipeline App CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a single pipeline service once.")
    run_sub = run_parser.add_subparsers(dest="service", required=True)

    ig = run_sub.add_parser("instagram", help="Run the Instagram pipeline service for one or more targets.")
    ig.add_argument(
        "--targets",
        default=DEFAULT_TARGETS,
        help=(
            "Comma-separated Instagram usernames to scrape "
            f"(default: $INSTAGRAM_TARGET_ACCOUNTS or {DEFAULT_TARGETS!r})."
        ),
    )
    ig.add_argument(
        "--output",
        metavar="TEMPLATE",
        default=DEFAULT_OUTPUT_TEMPLATE,
        help=(
            f"TSV path template; {{target}} is substituted per target "
            f"(default: {DEFAULT_OUTPUT_TEMPLATE}). Required when --targets has multiple entries."
        ),
    )
    ig.add_argument(
        "--media-dir",
        metavar="DIR",
        default=DEFAULT_MEDIA_DIR,
        help=(
            f"Single shared directory for downloaded media (default: {DEFAULT_MEDIA_DIR}). "
            "Filenames are <target>_<id>.<ext> to avoid cross-target collisions."
        ),
    )
    ig.add_argument(
        "--rate",
        choices=sorted(RATE_PRESETS.keys()),
        default=DEFAULT_RATE_PRESET,
        help=(
            f"Anti-throttle preset (default: {DEFAULT_RATE_PRESET}). "
            "'aggressive' = no delays (fast but trips Instagram challenges); "
            "'normal' = ~300 posts/hr, random 30-90s between pages + long rests; "
            "'gentle' = ~120 posts/hr, the safest sustained rate."
        ),
    )
    ig.add_argument(
        "--newer-than",
        metavar="ISO",
        default=None,
        help=(
            "Cutoff timestamp (ISO 8601). When set, the existing TSV is "
            "truncated in place to rows with timestamp <= cutoff, and the "
            "scrape fetches everything strictly newer. Used to size "
            "integration tests in one command (replaces 'manually truncate, "
            "then re-run'). Examples: '2024-02-20', "
            "'2024-02-20T02:27:16+0000', '2024-02-20T02:27:16+00:00'. "
            "Naive timestamps (no offset) are treated as UTC. Truncation "
            "rolls back atomically on scrape failure via the run snapshot."
        ),
    )
    ig.set_defaults(func=_run_instagram)

    sub = run_sub.add_parser("substack", help="Run the Substack pipeline service for one publication.")
    sub.add_argument(
        "publication",
        help="Substack publication slug (e.g. 'welalive' for welalive.substack.com).",
    )
    sub.add_argument(
        "--output",
        metavar="TEMPLATE",
        default=DEFAULT_SUBSTACK_OUTPUT_TEMPLATE,
        help=(
            f"TSV path template; {{publication}} is substituted "
            f"(default: {DEFAULT_SUBSTACK_OUTPUT_TEMPLATE})."
        ),
    )
    sub.add_argument(
        "--feed-url",
        metavar="URL",
        default=None,
        help=(
            "Override the RSS feed URL (default: https://<slug>.substack.com/feed). "
            "Accepts a URL, a local file path, or literal XML — primarily for testing. "
            "Ignored in --archive mode."
        ),
    )
    sub.add_argument(
        "--archive",
        action="store_true",
        help=(
            "Full-archive backfill (FR-028): enumerate the publication's COMPLETE "
            "post history via the archive API and fetch each body, instead of the "
            "~20-entry RSS window. Merges with prior RSS pulls (dedup by substack_id)."
        ),
    )
    sub.add_argument(
        "--max-posts",
        type=int,
        default=None,
        metavar="N",
        help="(--archive only) Cap the backfill to the N most-recent archived posts.",
    )
    sub.add_argument(
        "--page-delay",
        type=float,
        default=0.7,
        metavar="SECONDS",
        help="(--archive only) Polite delay between per-post body fetches (default: 0.7s).",
    )
    sub.set_defaults(func=_run_substack)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Force line-buffered stdout/stderr so live tailing of tee'd logs shows
    # progress as it happens, and reconfigure to UTF-8 for the arrow/accent
    # chars in operator-facing prints (Windows cp1252 → utf-8).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
