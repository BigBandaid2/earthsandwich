"""T015 — pile data-profiling: raw ydata baseline + enhanced LLM-analyst playground (US2).

Raw artifact = untouched ydata-profiling output over the sampled pile (FR-021);
a ydata failure is a hard error (exit 2, FR-105) — the enhanced playground is
never fabricated. The enhanced playground covers the FR-024 analyst topics with
per-section provenance labels, preserving every inference's inputs (Principle V).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

from analyze import PriorArtError
from analyze._iterations import PILE_RAW, allocate_iteration, record_artifacts
from common.config import BridgeProject
from common.inference import AnalystLayer
from common.playground import Playground
from project.create import OperatorError

PILE_ENHANCED = "pile.enhanced.html"

_ANALYST_TOPICS = """For the pile sample below, produce a concise markdown analysis covering, with one
heading per topic:
1. ID-candidate columns (with justification).
2. Entity classification — what real-world entity does one row represent?
3. Pipeline-metadata vs original-source field categorization.
4. Likely derived/inferred fields, with reasoning.
5. Evidence of AI-workflow involvement per field, if any.
6. Categorical-slicing candidates beyond basic statistics.
7. Public-knowledge enrichment opportunities, citing the public sources you rely on.
Be specific to the columns and values actually present."""


def load_pile_frame(project: BridgeProject) -> pd.DataFrame:
    """Concatenate the selected pile files; `source_file` records each row's origin."""
    pile_dir = Path(project.pile.dir)
    frames = []
    for fname in project.pile.files:
        try:
            frame = pd.read_csv(pile_dir / fname, sep="\t", dtype=str, keep_default_na=False)
        except Exception as exc:
            raise OperatorError(f"could not parse pile file {fname!r}: {exc}")
        frame["source_file"] = fname
        frames.append(frame)
    if not frames:
        raise OperatorError("project has no pile files selected")
    return pd.concat(frames, ignore_index=True)


def sample_frame(frame: pd.DataFrame, strategy: str, size: int) -> pd.DataFrame:
    """FR-028/029 sampling. ``head+random``: first half + seeded random rest."""
    if len(frame) <= size:
        return frame
    if strategy == "head+random":
        head_n = size // 2
        head = frame.iloc[:head_n]
        rest = frame.iloc[head_n:].sample(n=size - head_n, random_state=0)  # deterministic
        return pd.concat([head, rest]).sort_index()
    return frame.iloc[:size]                              # unknown strategy: plain head


def _require_analyst(analyst: AnalystLayer | None) -> AnalystLayer:
    if analyst is not None:
        return analyst
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise OperatorError(
            "ANTHROPIC_API_KEY is not set - the enhanced playground's LLM-analyst layer needs it (see .env.example)"
        )
    return AnalystLayer()


def run_pile_analysis(
    project: BridgeProject,
    project_dir: Path,
    *,
    analyst: AnalystLayer | None = None,
) -> dict[str, Path]:
    """Produce ``pile.ydata-profile.html`` + ``pile.enhanced.html`` in the current iteration."""
    analyst = _require_analyst(analyst)
    frame = load_pile_frame(project)
    sample = sample_frame(frame, project.pile.sample.strategy, project.pile.sample.size)

    iteration_dir = allocate_iteration(project, project_dir, PILE_RAW)
    raw_path = iteration_dir / PILE_RAW

    # Raw prior-art baseline (FR-021) - canonical ydata output, hard error on failure (FR-105).
    try:
        from ydata_profiling import ProfileReport

        ProfileReport(sample, title=f"pile profile (sampled) - {project.name}", minimal=True).to_file(raw_path)
    except Exception as exc:
        raise PriorArtError(f"ydata-profiling failed: {exc} - no enhanced playground will be fabricated (FR-105)")

    # Enhanced playground (FR-022/023/024) - LLM-analyst layer over the sampled pile.
    sample_text = sample.head(25).to_csv(sep="\t", index=False)
    inputs = {
        "columns": list(sample.columns),
        "row_count": int(len(frame)),
        "sampled_rows": sample_text,
        "files": list(project.pile.files),
    }
    result = analyst.infer(
        "pile_profile_analysis",
        f"{_ANALYST_TOPICS}\n\nColumns: {', '.join(sample.columns)}\nRows (TSV):\n{sample_text}",
        inputs,
    )

    media_cols = [c for c in sample.columns if sample[c].astype(str).str.contains(r"[/\\]|https?://", regex=True).mean() > 0.5]
    media_samples = {col: sample[col].dropna().astype(str).head(5).tolist() for col in media_cols}

    import html as _html

    playground = (
        Playground(f"Pile profile - {project.name}")
        .add_section(
            "ydata-profiling report",
            f"<p>Canonical raw baseline: <a href=\"{PILE_RAW}\">{PILE_RAW}</a> "
            f"({int(len(frame))} rows across {len(project.pile.files)} files; sampled {len(sample)}).</p>",
            "ydata-profiling baseline",
        )
        .add_section(
            "Analyst extension (ID candidates, entities, provenance, inferred fields, enrichment)",
            f"<pre>{_html.escape(result.inferred)}</pre>",
            "LLM-extended",
        )
        .add_section(
            "Sampled linked-object inspection",
            f"<pre>{_html.escape(json.dumps(media_samples, indent=2))}</pre>",
            "toolkit-novel",
        )
        .embed_data(
            "analyst_inference",
            {"prompt_ref": result.prompt_ref, "preserved_inputs": result.preserved_inputs, "inferred": result.inferred},
        )
        .set_copy_prompt(
            f"# Pile profile - {project.name}\n"
            f"Sections: ydata-profiling baseline / LLM-extended / toolkit-novel.\n\n{result.inferred}"
        )
    )
    enhanced_path = iteration_dir / PILE_ENHANCED
    enhanced_path.write_text(playground.build(), encoding="utf-8")

    record_artifacts(iteration_dir, raw=[PILE_RAW], enhanced=[PILE_ENHANCED])
    return {"raw": raw_path, "enhanced": enhanced_path, "iteration": iteration_dir}
