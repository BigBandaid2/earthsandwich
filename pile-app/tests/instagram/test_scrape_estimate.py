"""Phase 21 / SC-008: tests for `estimate_scrape_seconds`.

Locks the midpoint math against regressions and sanity-checks the
rate-preset throughput claims in `common/anti_throttle.py`'s docstrings.

Empirical SC-008 verification (actual ±30% of estimate for ≥80% of runs)
requires accumulated run logs, which aren't available immediately after the
Phase 19 migration — that part of T230 awaits log accumulation.
"""

import pytest

from common.anti_throttle import RATE_PRESETS
from instagram.pipeline import (
    PER_POST_WORK_SEC,
    SCRAPE_SETUP_OVERHEAD_SEC,
    estimate_scrape_seconds,
)


class TestEstimateScrapeSeconds:
    def test_zero_posts_returns_zero(self):
        assert estimate_scrape_seconds(0, RATE_PRESETS["normal"]) == 0.0

    def test_negative_posts_returns_zero(self):
        """Defensive — `expected_new` can briefly go negative if the existing
        TSV has more rows than the account's current media_count (e.g., posts
        deleted upstream)."""
        assert estimate_scrape_seconds(-5, RATE_PRESETS["normal"]) == 0.0

    def test_single_post_normal_preset_includes_setup_overhead(self):
        """The 1-post case dominated by setup overhead — the per-post math
        alone would give ~6s. With the overhead constant, ~21s, which is
        in the right ballpark for the integration test's observed ~25s."""
        eta = estimate_scrape_seconds(1, RATE_PRESETS["normal"])
        # SCRAPE_SETUP_OVERHEAD_SEC (15) + 1 * (PER_POST_WORK_SEC (4) + avg media_delay (2)) = 21
        expected = SCRAPE_SETUP_OVERHEAD_SEC + 1 * (PER_POST_WORK_SEC + 2.0)
        assert eta == pytest.approx(expected, abs=0.5)

    def test_normal_preset_300_posts_matches_docstring_throughput_claim(self):
        """The `normal` preset docstring claims ~300 posts/hr. The estimate
        should fall in the [50, 80] min range for 300 posts (the docstring's
        claim is a midpoint approximation)."""
        eta_seconds = estimate_scrape_seconds(300, RATE_PRESETS["normal"])
        eta_minutes = eta_seconds / 60
        assert 50 <= eta_minutes <= 80, (
            f"300 posts at `normal` preset estimated at {eta_minutes:.1f} min — "
            f"outside the [50, 80] min window implied by the ~300 posts/hr claim"
        )

    def test_gentle_preset_120_posts_matches_docstring_throughput_claim(self):
        """`gentle` preset claims ~120 posts/hr."""
        eta_seconds = estimate_scrape_seconds(120, RATE_PRESETS["gentle"])
        eta_minutes = eta_seconds / 60
        assert 45 <= eta_minutes <= 75, (
            f"120 posts at `gentle` preset estimated at {eta_minutes:.1f} min — "
            f"outside the [45, 75] min window implied by the ~120 posts/hr claim"
        )

    def test_aggressive_preset_has_no_inter_page_delay(self):
        """`aggressive` preset means zero page_delay and zero media_delay
        and no long rests — the estimate boils down to setup + per-post work."""
        eta = estimate_scrape_seconds(50, RATE_PRESETS["aggressive"])
        expected = SCRAPE_SETUP_OVERHEAD_SEC + 50 * (PER_POST_WORK_SEC + 0)
        assert eta == pytest.approx(expected, abs=0.5)

    def test_estimate_monotonically_increases_with_post_count(self):
        """A 100-post scrape can't take less than a 50-post one at the same rate."""
        eta_50 = estimate_scrape_seconds(50, RATE_PRESETS["normal"])
        eta_100 = estimate_scrape_seconds(100, RATE_PRESETS["normal"])
        eta_200 = estimate_scrape_seconds(200, RATE_PRESETS["normal"])
        assert eta_50 < eta_100 < eta_200

    def test_aggressive_strictly_faster_than_normal_strictly_faster_than_gentle(self):
        """For the same post count, the preset throughput claims order
        the runtimes: aggressive < normal < gentle."""
        n = 100
        assert (
            estimate_scrape_seconds(n, RATE_PRESETS["aggressive"])
            < estimate_scrape_seconds(n, RATE_PRESETS["normal"])
            < estimate_scrape_seconds(n, RATE_PRESETS["gentle"])
        )
