# Contract: Substack Pile Artifact

**Producer**: `pile-app/substack/pipeline.py` (new in this plan)
**Consumer**: `bridge-app/` (planned, no spec yet).

This is a **producer-side** contract: it states what the App promises to write. See [`../data-model.md`](../data-model.md) § "Pile artifact: Substack TSV" for the full column reference.

---

## File layout

- **TSV path**: `pile-app/pile/articles.<publication>.local.tsv`
- **No media files** in v1 — article images live as `<img>` tags inside the HTML `body` column. A future enhancement may extract them; the bridge-app can render the HTML directly without that step.
- **Encoding**: UTF-8 (no BOM), LF newlines, TAB column delimiter.
- **Header row**: present, single line, matches [data-model.md § Substack header](../data-model.md#header-row-1).

---

## Stability guarantees

| What | Guarantee |
|---|---|
| Header row order | Stable for v1. |
| `substack_id` (= RSS `<guid>`) | **Canonical dedup key**. Stable per article. |
| `link` | Retained for traceability per FR-024; bridge-app MAY use it as a fallback identifier if `<guid>` is ever absent (Substack publishes it for all current articles). |
| `id` (local) | **Unstable**: re-numbered each run. |
| `published_at` | Stable: derived from RSS `<pubDate>`. |
| `title` / `subtitle` / `body` | Producer-derived; may change on a re-run if the upstream RSS feed has updated content (Substack allows article edits). Producer MAY overwrite these on re-encounter. |
| `deleted_upstream` / `deleted_upstream_at` | Set-once-monotonic. |

---

## Producer guarantees

1. **Atomicity of a row** — same as Instagram.
2. **TSV well-formedness** — embedded tabs in any string column are escaped to single spaces; newlines preserved as `\n` literal characters in `body` only (HTML content needs structure preserved; the bridge-app's HTML parser handles newlines fine).
3. **`substack_id` uniqueness** within a TSV.
4. **Sorted by `published_at ASC`** after the post-pass.
5. **No body truncation** — Substack RSS `<content:encoded>` can be large (multi-thousand-word essays); the producer writes the full HTML body. Consumers SHOULD handle multi-MB cells.

---

## Consumer requirements

1. **Treat the pile as read-only.**
2. **Re-read on each run.**
3. **Respect `deleted_upstream`.**
4. **Handle RSS-truncation cap.** Substack RSS feeds typically include only the last ~20 entries. The pile will NOT contain articles older than the publication's first RSS-windowed pull. Bridge-app SHOULD NOT interpret an article's absence from the pile as "deleted upstream" unless the corresponding tombstone column is set — the article may simply have aged out of the RSS window before the first pull.
5. **Body content is HTML.** Render via a sanitizer; do not assume plain text.

---

## Versioning

Same versioning policy as the Instagram contract — amend in lockstep with spec + data-model changes; coordinate with bridge-app before merging breaking changes.

---

## Note on Substack v1 inference absence

Substack v1 has no LLM inference step in its pipeline. The pile artifact carries no verbatim-input columns analogous to the Instagram `tag_verbatim` / `lat_verbatim` / `lng_verbatim` triple. If a future Substack enhancement infers locations or other derived data via LLM, that spec amendment MUST add the corresponding verbatim columns per Cardinal Rule #4 (inference inputs preserved).
