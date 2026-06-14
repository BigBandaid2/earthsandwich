# Project context — paste this into Claude Design (both projects)

You are redesigning two related surfaces of **bridge-builder-toolkit**, a local single-operator data-engineering tool that builds validated "bridge specifications" between a file-based data pile and a relational database. An operator works through stages: create project → profile pile & target → synthesize mapping → oracle validation → iterate → review → final bundle.

**Design within this medium — these are hard engineering contracts, not preferences:**

1. **No frameworks, no build step.** Output must be expressible as vanilla HTML/CSS/JS. No React, no Tailwind, no Node toolchain, no CDN fonts/icons/scripts — everything fully offline. (CSS custom properties, grid/flex, inline SVG are all fine.)
2. **Surface A — the Web UI** (project list, create/edit forms, per-project dashboard): server-rendered multi-page documents from a Python backend. No client-side state or SPA routing; forms POST and re-render. A lightweight ~5s auto-refresh exists only while a project is locked.
3. **Surface B — analysis playgrounds** (pile profile, target profile, later bridge review): each is ONE self-contained HTML file with data embedded inline (target ≤5 MB), opened from disk, shareable as a file. Same no-external-assets rule.
4. **Provenance labeling is contractual (Surface B):** every content section must visibly carry exactly one label — `ydata-profiling baseline`, `ER-diagram baseline`, `dbt baseline`, `LLM-extended`, or `toolkit-novel` — so a reader always knows whether content is prior-art tool output, AI-extended analysis, or toolkit-original. Treat these labels as a first-class visual language to elevate, not a footnote.
5. **The copy-out-a-prompt affordance is contractual (Surface B):** a prominent control that copies an AI-actionable text payload (clipboard API, degrading to a selectable textarea).
6. **UI must surface (Surface A):** per-endpoint connection-validation report; stage-flow progress across two independent iteration loops (data-profiling, bridge-mapping); a suggested-next-step panel with ONE primary copyable CLI command + labeled alternates (the UI guides but never launches stages); artifact browsing; typed-project-name delete confirmation; lock-held read-only state; inline form errors. Credential VALUES never appear anywhere — only environment-variable names.
7. **Audience & tone:** a technical operator at a desk; dark theme; data-dense but calm; monospace where content is data/commands.

Current implementation, tokens, and component inventory are in the attached TOKENS.md and screenshots; sample real artifacts are attached as standalone HTML. Keep information architecture; rethink the visual system freely.
