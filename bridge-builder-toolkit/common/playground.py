"""Single-file HTML playground builder (T009, FR-050-054).

Shared by the US2/US3/US6 enhanced playgrounds. Produces one self-contained,
dependency-free HTML document: inline-embedded data, per-section provenance
labels, and a "copy out a prompt" affordance that uses the clipboard API and
degrades to a selectable textarea where it is unavailable (FR-054).

The returned string is UTF-8 HTML; write it with ``encoding="utf-8"``.
"""
from __future__ import annotations

import html
import json
from dataclasses import dataclass
from typing import Any

# Provenance labels (FR-022 / FR-044) — the only allowed section labels.
PROVENANCE = {
    "ydata-profiling baseline",
    "ER-diagram baseline",
    "dbt baseline",
    "LLM-extended",
    "toolkit-novel",
}


@dataclass
class _Section:
    heading: str
    body_html: str
    label: str


def _embed_json(value: Any) -> str:
    """Serialize for safe inline <script> embedding (guards ``</script>``)."""
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


_STYLE = """<style>
:root { color-scheme: dark; }
body { margin:0; font:14px/1.5 system-ui,sans-serif; background:#0f1115; color:#e6e8eb; }
header { padding:16px 20px; border-bottom:1px solid #232732; }
h1 { font-size:18px; margin:0; }
main { padding:20px; display:flex; flex-direction:column; gap:16px; }
.card { background:#161922; border:1px solid #232732; border-radius:8px; overflow:hidden; }
.card-head { display:flex; align-items:center; justify-content:space-between; padding:10px 14px; border-bottom:1px solid #232732; }
.card-head h2 { font-size:14px; margin:0; }
.label { font-size:11px; padding:2px 8px; border-radius:999px; background:#2a3346; color:#9fb3d8; }
.card-body { padding:14px; }
footer { position:sticky; bottom:0; background:#0f1115; border-top:1px solid #232732; padding:12px 20px; }
textarea { width:100%; min-height:90px; background:#0b0d12; color:#e6e8eb; border:1px solid #232732; border-radius:6px; padding:8px; font:12px/1.4 ui-monospace,monospace; box-sizing:border-box; }
button { margin-top:8px; padding:8px 14px; background:#3b82f6; color:#fff; border:0; border-radius:6px; cursor:pointer; }
#copy-status { margin-left:10px; font-size:12px; color:#9fb3d8; }
</style>
"""

_BEHAVIOR_JS = """<script>
window.DATA = JSON.parse(document.getElementById('embedded-data').textContent || '{}');
(function () {
  var btn = document.getElementById('copy-btn');
  var ta = document.getElementById('copy-payload');
  var status = document.getElementById('copy-status');
  function fallback() {
    ta.focus();
    ta.select();
    status.textContent = 'Selected - press Ctrl/Cmd+C to copy.';
  }
  btn.addEventListener('click', function () {
    var text = ta.value;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () { status.textContent = 'Copied to clipboard.'; },
        fallback
      );
    } else {
      fallback();
    }
  });
})();
</script>
"""


class Playground:
    """Builder for a single enhanced/review playground HTML file."""

    def __init__(self, title: str) -> None:
        self.title = title
        self._sections: list[_Section] = []
        self._data: dict[str, Any] = {}
        self._copy_prompt: str | None = None

    def add_section(self, heading: str, body_html: str, label: str) -> "Playground":
        if label not in PROVENANCE:
            raise ValueError(
                f"unknown provenance label {label!r}; expected one of {sorted(PROVENANCE)}"
            )
        self._sections.append(_Section(heading, body_html, label))
        return self

    def embed_data(self, name: str, value: Any) -> "Playground":
        """Inline a JSON-serializable object reachable as ``window.DATA[name]``."""
        self._data[name] = value
        return self

    def set_copy_prompt(self, text: str) -> "Playground":
        self._copy_prompt = text
        return self

    def _default_copy_prompt(self) -> str:
        # FR-052/053: AI-actionable payload that carries the section labels.
        lines = [f"# {self.title}", "", "Sections and their provenance:"]
        lines += [f"- {s.heading} [{s.label}]" for s in self._sections]
        return "\n".join(lines)

    def build(self) -> str:
        copy_payload = self._copy_prompt if self._copy_prompt is not None else self._default_copy_prompt()
        sections_html = "\n".join(
            '<section class="card"><div class="card-head"><h2>'
            + html.escape(s.heading)
            + '</h2><span class="label">'
            + html.escape(s.label)
            + '</span></div><div class="card-body">'
            + s.body_html
            + "</div></section>"
            for s in self._sections
        )
        title = html.escape(self.title)
        return (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{title}</title>\n"
            + _STYLE
            + "</head>\n<body>\n"
            + f"<header><h1>{title}</h1></header>\n<main>\n"
            + sections_html
            + "\n</main>\n"
            + '<footer><label for="copy-payload">Copy out a prompt</label>\n'
            + f'<textarea id="copy-payload" readonly>{html.escape(copy_payload)}</textarea>\n'
            + '<button id="copy-btn" type="button">Copy prompt</button>\n'
            + '<span id="copy-status"></span></footer>\n'
            + f'<script type="application/json" id="embedded-data">{_embed_json(self._data)}</script>\n'
            + _BEHAVIOR_JS
            + "\n</body>\n</html>\n"
        )
