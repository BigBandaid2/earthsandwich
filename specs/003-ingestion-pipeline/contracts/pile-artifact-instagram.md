# Contract: Instagram Pile Artifact

**Producer**: `pile-app/instagram/pipeline.py`
**Consumer**: `bridge-app/` (planned, no spec yet) — and any hand-rolled operator scripts that grep the pile.

This is a **producer-side** contract: it states what the App promises to write. The bridge-app's interpretation MAY add semantics (e.g., trip assignment, region normalization) but MUST NOT require schema changes here without amending this contract.

See [`../data-model.md`](../data-model.md) for the full column reference. This document captures the consumer-facing guarantees.

---

## File layout

- **TSV path**: `pile-app/pile/posts.<target>.local.tsv`
- **Media root**: `pile-app/pile/media/instagram/<target>_<shortcode>.<ext>`
- **Encoding**: UTF-8 (no BOM), LF newlines, TAB column delimiter, double-quote NOT used.
- **Header row**: present, single line, matches the order in [data-model.md § Header row](../data-model.md#header-row).

The producer writes one TSV per target. Multi-target operators see multiple TSVs in `pile/`.

---

## Stability guarantees

| What | Guarantee |
|---|---|
| Header row order | Stable for the life of v1. Adding columns at the end is non-breaking; reordering is breaking and requires a new contract version. |
| `shortcode` | Stable: the canonical dedup key. A given pile row's `shortcode` will never change. Bridge-app SHOULD key its own records by `(target, shortcode)`. |
| `instagram_id` | Stable per-post but retained for traceability only; bridge-app SHOULD NOT use it as its primary key (instagrapi's `pk` semantics are opaque and could theoretically change format). |
| `id` (local) | **Unstable**: re-numbered 1..N after every run's post-pass. Bridge-app MUST NOT key by it. |
| `timestamp` | Stable: derived from `Media.taken_at`; the producer MUST NOT munge it. |
| Verbatim columns (`tag_verbatim`, `lat_verbatim`, `lng_verbatim`) | Stable: written exactly as instagrapi reports them. Empty only when the source had no tag. |
| `location` / `lat` / `lng` / `region` | Producer-derived. The producer reserves the right to RE-RESOLVE these on a future run if the original resolution was empty AND a new run finds resolvable data. The producer will NEVER overwrite a non-empty resolution. |
| `reasoning` | Audit field. The producer MAY append to this on re-runs; consumers SHOULD treat it as opaque audit text, not structured data. |
| `deleted_upstream` / `deleted_upstream_at` | Set-once-monotonic: once `true`, stays `true`. `_at` is set at the first tombstoning and never overwritten. |

---

## Producer guarantees (what the bridge-app can rely on)

1. **Atomicity of a row** — the producer writes complete rows; consumers will never see a partially-written row. (File-level: writes are buffered and flushed once per page.)
2. **TSV is well-formed** — embedded tabs in `caption` / `reasoning` are escaped to single spaces before write. Newlines in those fields are stripped (replaced with `\n` literal sequence? no — replaced with single space; multi-paragraph captions become space-separated).
3. **Media file referenced by `media_url` exists at the moment of TSV write** — race-free for a single-target run. Cross-run, a media file may be deleted by the orphan sweep; if a consumer caches `media_url` from a prior read, it MUST re-check the file's existence before opening it.
4. **`shortcode` uniqueness** — no two surviving rows in the same TSV share a `shortcode`.
5. **Timestamp ordering** — after the post-pass completes, rows are sorted by `timestamp ASC`. During a mid-scrape run the file may be temporarily unsorted; consumers reading mid-run SHOULD re-sort.
6. **Sweep cleans only its own prefix** — orphan sweep MUST only touch files matching `<target>_*` for the target being processed. Sweeping never crosses targets, never touches non-Instagram media.

---

## Consumer requirements (what the bridge-app MUST do)

1. **Treat the pile as read-only.** No writes back into `pile-app/pile/` by the bridge-app or any downstream consumer.
2. **Re-read on each run.** The pile is a snapshot, not a stream. Bridge-app SHOULD re-process the full TSV per run (or maintain its own watermark).
3. **Respect `deleted_upstream`.** Tombstoned rows are still valid pile data; consumers MAY choose to surface them as "deleted from source" or hide them, but MUST NOT drop them silently — the row's content (caption, media, location) was real at the time of capture.
4. **Tolerate empty location columns.** A row with empty `location` / `lat` / `lng` / `region` is valid — the inference simply didn't resolve. Bridge-app SHOULD handle this (e.g., flag for manual review, or skip until resolution).
5. **Trust verbatim columns over derived columns** when the two disagree. If `tag_verbatim` is non-empty but `location` is empty, that's a producer-side resolution gap; the bridge-app SHOULD treat the verbatim tag as ground truth and may apply its own canonicalization.

---

## Versioning

This contract has no explicit version field. If the column set, ordering, or stability guarantees change, the producer MUST:

1. Amend the spec (`spec.md`) and this file in the same change.
2. Update `[data-model.md](../data-model.md)`.
3. Mark the change in `tasks.md` as a separate phase (per Cardinal Rule #1).
4. Coordinate with the bridge-app maintainer before merging.

A future version field MAY be added as column 0 if backwards-incompatible changes accumulate.
