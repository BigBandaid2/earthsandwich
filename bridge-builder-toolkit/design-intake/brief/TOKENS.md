# Current design tokens — bridge-builder-toolkit

Claude Design reads hex values from linked code but not their *semantic intent* — this glossary supplies the intent. Source of truth: `bridge-builder-toolkit/ui/pages.py` (`_STYLE`) and `bridge-builder-toolkit/common/playground.py` (`_STYLE`). Both surfaces deliberately share one idiom today.

## Color

| Token (semantic) | Hex | Used for |
|---|---|---|
| page-background | `#0f1115` | body background (dark, near-black blue) |
| surface / card | `#161922` | card backgrounds |
| surface-inset | `#0b0d12` | `<pre>` blocks, inputs (code-ish wells) |
| border | `#232732` | card borders, dividers, input borders |
| border-subtle | `#20242f` | table row separators |
| text-primary | `#e6e8eb` | body text |
| text-secondary | `#9fb3d8` | labels, captions, crumbs, notes (steel blue) |
| text-muted | `#7d8696` | de-emphasized notes |
| link | `#7fb0ff` | anchors |
| action-primary | `#3b82f6` | buttons (blue) |
| action-danger | `#b03a45` | delete button |
| status-ok bg/fg | `#173527` / `#7fdc9c` | "valid", done chips (green) |
| status-warn bg/fg | `#3a2c17` / `#e7b96d` | "oracle: skip" badge (amber) |
| status-bad bg/fg | `#3a1c20` / `#f08a93` | "invalid", error banners (red) |
| chip / label bg | `#2a3346` (`#1c2130` UI chips) | provenance labels, stage chips |

## Type & shape

- Font: `system-ui, sans-serif` at 14px/1.5; code & data: `ui-monospace` at 12-13px.
- Radii: 8px cards, 6px inputs/buttons/chips, 999px pill badges.
- Layout: single-column stack of cards, max-width 980px (UI); full-width card stack (playgrounds).

## Recurring components (both surfaces)

- **Card**: header row (title left, badge/action right) + body; 1px border, no shadow.
- **Provenance label** (playgrounds, contractual): small pill on every section header reading one of `ydata-profiling baseline` / `ER-diagram baseline` / `dbt baseline` / `LLM-extended` / `toolkit-novel`.
- **Status badge**: pill, green/amber/red semantics above.
- **Stage chip row** (UI dashboard): create → analyze pile → analyze target → synthesize → oracle → review → final bundle; done = green.
- **Copy affordance**: monospace well + "copy" button (clipboard API with select-text fallback — contractual).
- **Suggested-next-step panel** (UI): one primary copyable CLI command + "also available" alternates.
- **Typed-name delete confirm** (UI): danger-zone card.
- **Inline error / flash banners**: red / green wells above content.
