"""US2 — pile + target data-profiling (raw prior-art baselines + enhanced playgrounds)."""


class PriorArtError(RuntimeError):
    """A pinned prior-art tool (ydata-profiling, eralchemy2/dot, dbt) failed (FR-105).

    CLI exit 2 — the toolkit never fabricates the affected baseline.
    """
