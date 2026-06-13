"""T016 — target data-profiling: schema ydata + eralchemy2 ER diagram + enhanced playground (US2).

ER rendering: eralchemy2's pure-Python schema-extraction + dot emission, rendered
to SVG by the system GraphViz ``dot`` binary. (eralchemy2's own image renderer
needs pygraphviz, a C extension that rarely builds on Windows; its package
import is shimmed so the pure path stays importable.) Missing GraphViz is an
operator error with install guidance (exit 1); tool crashes are FR-105 hard
errors (exit 2).
"""
from __future__ import annotations

import html as _html
import json
import os
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pandas as pd

from analyze import PriorArtError
from analyze._iterations import TARGET_RAW, allocate_iteration, record_artifacts
from analyze.introspect import reflect_schema
from common.config import BridgeProject
from common.inference import AnalystLayer
from common.playground import Playground
from project.create import OperatorError, _normalize_dsn
from analyze.pile import _require_analyst, load_pile_frame

TARGET_ER = "target.er-diagram.svg"
TARGET_ER_DOT = "target.er-diagram.dot"
TARGET_ENHANCED = "target.enhanced.html"

_DOT_FALLBACKS = (r"C:\Program Files\Graphviz\bin\dot.exe", "/usr/bin/dot", "/usr/local/bin/dot")


def _find_dot() -> str:
    override = os.environ.get("BRIDGE_GRAPHVIZ_DOT")
    if override:
        return override
    found = shutil.which("dot")
    if found:
        return found
    for candidate in _DOT_FALLBACKS:
        if Path(candidate).is_file():
            return candidate
    raise OperatorError(
        "GraphViz 'dot' binary not found - the target ER diagram needs it. "
        "Install GraphViz (e.g. `winget install Graphviz.Graphviz` / `apt install graphviz`) "
        "or set BRIDGE_GRAPHVIZ_DOT to the dot executable path."
    )


def _import_eralchemy():
    """Import eralchemy2's pure dot-emitter path, shimming its pygraphviz import.

    Only ``all_to_intermediary`` + ``intermediary_to_dot`` are used - both pure
    Python; pygraphviz would only be needed for eralchemy2's own image renderer,
    which is replaced here by the GraphViz ``dot`` binary.
    """
    try:
        import pygraphviz  # noqa: F401 - real one, if present
    except ModuleNotFoundError:
        agraph = types.ModuleType("pygraphviz.agraph")

        class AGraph:  # pragma: no cover - placeholder, never used on the dot path
            def __init__(self, *args, **kwargs):
                raise RuntimeError("pygraphviz unavailable; ER rendering uses the GraphViz dot binary")

        agraph.AGraph = AGraph
        stub = types.ModuleType("pygraphviz")
        stub.agraph = agraph
        sys.modules.setdefault("pygraphviz", stub)
        sys.modules.setdefault("pygraphviz.agraph", agraph)
    from eralchemy2.main import all_to_intermediary, intermediary_to_dot

    return all_to_intermediary, intermediary_to_dot


def render_er_diagram(dsn: str, iteration_dir: Path) -> Path:
    """eralchemy2 schema → dot → SVG via GraphViz (raw artifacts preserved, FR-101)."""
    dot_binary = _find_dot()                              # operator gate first (exit 1)
    dot_path = iteration_dir / TARGET_ER_DOT
    svg_path = iteration_dir / TARGET_ER
    try:
        all_to_intermediary, intermediary_to_dot = _import_eralchemy()
        tables, relationships = all_to_intermediary(_normalize_dsn(dsn))
        intermediary_to_dot(tables, relationships, str(dot_path))
    except OperatorError:
        raise
    except Exception as exc:
        raise PriorArtError(f"eralchemy2 failed to derive the ER intermediary: {exc} (FR-105)")
    result = subprocess.run(
        [dot_binary, "-Tsvg", str(dot_path), "-o", str(svg_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not svg_path.is_file():
        raise PriorArtError(f"GraphViz dot failed to render the ER diagram: {result.stderr.strip()} (FR-105)")
    return svg_path


def run_target_analysis(
    project: BridgeProject,
    project_dir: Path,
    *,
    analyst: AnalystLayer | None = None,
) -> dict[str, Path]:
    """Produce target ydata profile + ER diagram + enhanced playground in the current iteration."""
    analyst = _require_analyst(analyst)
    from project.secrets import resolve_target_dsn

    dsn = resolve_target_dsn(project, project_dir)
    if not dsn:
        raise OperatorError("target connection unavailable — re-validate the project (FR-012)")

    schema = reflect_schema(dsn)
    iteration_dir = allocate_iteration(project, project_dir, TARGET_RAW)
    raw_path = iteration_dir / TARGET_RAW

    # Raw ydata baseline over the introspected schema metadata (FR-020/021, FR-105).
    rows = [
        {
            "table": table["name"], "column": col["name"], "type": col["type"],
            "nullable": col["nullable"], "primary_key": col["primary_key"],
        }
        for table in schema["tables"] for col in table["columns"]
    ]
    try:
        from ydata_profiling import ProfileReport

        frame = pd.DataFrame(rows)
        ProfileReport(frame, title=f"target schema profile - {project.name}", minimal=True).to_file(raw_path)
    except Exception as exc:
        raise PriorArtError(f"ydata-profiling failed: {exc} - no enhanced playground will be fabricated (FR-105)")

    # Raw ER diagram (relational target, FR-101).
    render_er_diagram(dsn, iteration_dir)

    # Enhanced playground: ranked candidate tables (FR-025/026) - reasoning only;
    # relationship-graph rendering stays with the raw ER artifact.
    try:
        pile_columns = list(load_pile_frame(project).columns)
    except OperatorError:
        pile_columns = []
    inputs = {"schema": schema, "pile_columns": pile_columns}
    result = analyst.infer(
        "target_candidate_tables",
        "Given this introspected target schema (JSON) and the pile's column names, produce a RANKED "
        "markdown list of target tables that are candidates to be populated from the pile, with "
        "reasoning per candidate. Do not re-describe the schema graph; reference the ER diagram for "
        f"relationships.\n\nSchema:\n{json.dumps(schema, indent=1)}\n\nPile columns: {', '.join(pile_columns)}",
        inputs,
    )

    playground = (
        Playground(f"Target profile - {project.name}")
        .add_section(
            "ydata-profiling schema report",
            f'<p>Canonical raw baseline: <a href="{TARGET_RAW}">{TARGET_RAW}</a> '
            f"({len(schema['tables'])} tables, {len(rows)} columns).</p>",
            "ydata-profiling baseline",
        )
        .add_section(
            "ER diagram",
            f'<p>Canonical raw artifact: <a href="{TARGET_ER}">{TARGET_ER}</a> '
            f'(eralchemy2 schema extraction + GraphViz dot; source: <a href="{TARGET_ER_DOT}">{TARGET_ER_DOT}</a>).</p>',
            "ER-diagram baseline",
        )
        .add_section(
            "Ranked candidate tables to populate from the pile",
            f"<pre>{_html.escape(result.inferred)}</pre>",
            "LLM-extended",
        )
        .embed_data(
            "analyst_inference",
            {"prompt_ref": result.prompt_ref, "preserved_inputs": result.preserved_inputs, "inferred": result.inferred},
        )
        .set_copy_prompt(
            f"# Target profile - {project.name}\n"
            f"Sections: ydata-profiling baseline / ER-diagram baseline / LLM-extended.\n\n{result.inferred}"
        )
    )
    enhanced_path = iteration_dir / TARGET_ENHANCED
    enhanced_path.write_text(playground.build(), encoding="utf-8")

    record_artifacts(iteration_dir, raw=[TARGET_RAW, TARGET_ER, TARGET_ER_DOT], enhanced=[TARGET_ENHANCED])
    return {"raw": raw_path, "er": iteration_dir / TARGET_ER, "enhanced": enhanced_path, "iteration": iteration_dir}
