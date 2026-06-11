# Handoff: Travelogue — "Postmark" Design System

## Overview
This package restyles the Travelogue app end-to-end with a custom design system
(direction: **Postmark**) and adds a redesigned **post detail** view. It covers
three surfaces of your existing app:

1. **Map** (`MapView`) — restyled Google map, national-flag pins on poles, and a
   solid directional route line with arrowheads (dashed for planned legs).
2. **Itinerary sidebar** (`RegionSidebar` / region list) — a timeline feed with
   status dots, handwritten dates, photo strips, and a "Dispatch" chip.
3. **Post detail** (`StopDetail`) — a postcard/journal modal that handles two
   post kinds: an **Instagram** snapshot (photo carousel + caption) and a
   **Substack** dispatch (full article inline). The Substack cover has two
   interchangeable layouts (cover on the **side** or on **top**) and a
   no-cover **typographic fallback**.

The aesthetic: one bold accent (**postal red `#C5402A`**) on warm cream paper,
a characterful italic serif for headlines, handwritten dates, and passport /
postmark motifs. Voice is warm, witty, first-person — telling friends about a trip.

---

## About the design files
**The files in this bundle are design references created in HTML/React-via-Babel.**
They are prototypes showing the intended look and behavior — **not** production
code to copy verbatim. Your task is to **recreate these designs inside the
existing app** (React + TypeScript + `@vis.gl/react-google-maps`), using its
established components, data layer, and patterns.

The one exception you *can* lift almost directly is the **design-token CSS**
(`design-system/`), which is plain custom properties meant to drop into
`src/styles/global.css`.

## Fidelity
**High-fidelity.** Colors, typography, spacing, radii, shadows, and interactions
are final. Recreate the UI pixel-accurately using your existing libraries. Exact
values are listed under **Design Tokens** and per-component below.

---

## Integration at a glance (mapping to your codebase)

| Your file | Change |
|---|---|
| `src/styles/global.css` | Replace the `:root` block with the Postmark tokens (see `design-system/`). Add the Google Fonts `@import`. Swap the base `font-family` to `var(--font-body)`. |
| `index.html` / fonts | Add Newsreader, Hanken Grotesk, Caveat, JetBrains Mono (see **Fonts**). |
| `src/components/MapView.tsx` | Apply `postmarkMapStyle` to the map; replace markers with **flag pins** (AdvancedMarker w/ flag image on a pole); draw the route as a **solid Polyline with arrow symbols**, plus a **dashed** segment to the planned stop. |
| `src/components/RegionSidebar.tsx` (+ region/stop tiles) | Rebuild as the **timeline feed** (`.tg-tile` markup in `reference-app/parts.jsx`). Add the **Dispatch chip** for stops/regions that have a Substack writeup. |
| `src/components/StopDetail.tsx` | Replace with the **PostDetail** component (`reference-app/detail.jsx` + `detail.css`). Branch on `post.kind` (`instagram` | `substack`) and, for Substack, on `post.layout` (`side` | `top`). |
| `src/components/CityDetail.tsx` | If this is the "region" expansion, reuse the same tile/strip styling; (full region drill-in is not yet designed — flagged as a next step). |
| `src/components/LandingModal.tsx` | Restyle with tokens (cream surface, italic serif title, postal-red accent). |
| `src/data/types.ts` | Extend `Post` to a discriminated union and add optional `dispatch`, `cover`, `layout`, and per-photo `count` fields (see **Data model**). |
| `src/utils/regionUtils.ts` | No logic change; the effective-status derivation (`visited` / `planned` / `abandoned`) maps directly to the status dot + route styling. |

> The reference React mock in `reference-app/` (`parts.jsx`, `detail.jsx`,
> `data.jsx`) is plain React — the component structure, props, and JSX map almost
> 1:1 to TSX. Port it, add types, and wire it to your real `Stop`/`Region` data.

---

## Design Tokens
Drop-in CSS lives in `design-system/styles.css` (which `@import`s the four token
files). The full values:

### Color
```
/* Paper & surfaces */
--paper:        #F4EDDF;   /* app canvas / page background (warm cream) */
--surface:      #FBF7EE;   /* sidebar, raised cards, modal */
--surface-sunk: #EAE0CC;   /* wells, inputs, photo placeholders */
--surface-tint: #F0E7D5;   /* subtle banded sections */

/* Ink (text) */
--ink:       #2B2620;      /* primary text, headlines */
--ink-soft:  #6C6253;      /* body, secondary */
--ink-faint: #A99B82;      /* meta, captions, disabled */

/* Postal-red accent ramp */
--red-700: #9A2D1B;   /* pressed / strong */
--red-600: #C5402A;   /* PRIMARY accent  ← --accent */
--red-500: #D6543D;   /* hover */
--red-100: #F2DDD3;   /* tint fills */

/* Journey status */
--status-visited:   #C5402A;  /* postal red, solid dot */
--status-planned:   #B6AC95;  /* warm neutral, hollow dashed dot */
--status-abandoned: #9E9072;  /* faded sepia, struck-through */

/* Lines */
--line:        #E3D8C2;
--line-strong: #D2C4A8;

/* Map (Postmark sepia) */
--map-land:  #E7DCC4;
--map-water: #F4ECD9;
--map-grid:  rgba(120,92,52,0.13);
--route:     #C5402A;
--flag-frame:#FBF7EE;
--flag-pole: #8A7A5C;
--chip:      rgba(251,247,238,0.86);  /* translucent cream for map overlays */
```

### Typography
```
--font-display: 'Newsreader', Georgia, serif;        /* headlines — set ITALIC */
--font-body:    'Hanken Grotesk', system-ui, sans-serif;
--font-script:  'Caveat', cursive;                    /* dates & one-line asides ONLY */
--font-mono:    'JetBrains Mono', monospace;          /* labels, coords, counts */

/* scale */  xs 11 · sm 13 · base 15 · md 17 · lg 20 · xl 26 · 2xl 34 · 3xl 46 (px)
/* leading */ tight 1.08 · snug 1.4 · body 1.62
/* weight */  400 / 500 / 600 / 700
/* tracking */ display -0.01em · mono-label 0.14em (uppercase)
```
Rules of thumb: **Newsreader is italic** for titles (journal masthead) and for
in-article notes. **Caveat only** for dates and short asides — never body. **Mono**
carries uppercase eyebrows, coordinates, and counts.

### Spacing / Radius / Elevation / Motion
```
space:  4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 (px, 4px base)
radius: sm 4 · md 8 · lg 14 · xl 20 · pill 999
shadow-sm:  0 1px 2px rgba(28,40,34,.06), 0 1px 3px rgba(28,40,34,.07)
shadow-md:  0 4px 14px rgba(28,40,34,.10)
shadow-lg:  0 16px 40px rgba(28,40,34,.16)
shadow-pin: 0 2px 5px rgba(28,40,34,.26)   /* map markers */
ease-out: cubic-bezier(0.2,0.7,0.3,1)   dur-fast 0.14s · dur-med 0.24s
```

### Motif tokens
```
--route-width: 2.4px;          /* route line weight */
--route-dash-planned: 5 5;     /* dashed pattern for planned legs */
--arrow-size: 9px;             /* arrowhead */
--flag-pole-h: 27px; --flag-banner-h: 15px;
```

---

## Fonts
Add once (e.g. in `index.html` `<head>` or top of `global.css`):
```css
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500;1,6..72,600&family=Hanken+Grotesk:wght@400;500;600;700&family=Caveat:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
```

---

## Screens / Views

### 1 · Map (`MapView`)
**Purpose:** see the whole trip geographically; tap a flag to open that stop.

**Map style:** apply `reference-app/postmark-map-style.js` (a Google Maps
`styles` array tuned to the tokens — cream land, pale water, hidden POIs, muted
roads). Pass via the `styles` prop (raster styling) or migrate to a cloud
`mapId`. Disable default UI; keep zoom/pan.

**Flag pin (marker)** — replace the current flag markers with this structure
(use `AdvancedMarker` with an HTML element, or a custom OverlayView):
- A 1.5px **pole**, 27px tall, color `--flag-pole`, with a 5px round **base** dot
  at the bottom (the geo-anchor point).
- A **banner** at the pole top: ~21×15px, `--flag-frame` background, 1px border
  `rgba(60,42,20,.22)`, radius 2px, `shadow-pin`. The flag image fills it
  **edge-to-edge** (`object-fit: cover`, slight crop OK — this was an explicit
  request: no letterbox padding).
- **Active** stop: banner border = `--accent`, `box-shadow: 0 0 0 2px var(--accent), shadow-md`, scale 1.2 from bottom-left, and show the stop name in a mono cream pill to the right.
- **Planned** stop: whole pin at `opacity .62`, pole/base in `--ink-faint`.
- Hover: scale 1.12 from bottom-left.
- Cluster naturally — multiple nearby stops just render adjacent pins (your
  existing per-stop markers already do this).

**Route line** — replace any faded/gradient line:
- **Solid** `Polyline`, weight `--route-width` (≈2.4px on-screen), color `--route`,
  rounded caps/joins, through visited stops **in travel order**.
- **Arrowheads** at each segment midpoint indicating direction. With the JS API
  use a `Polyline` icon: `{ icon: { path: FORWARD_CLOSED_ARROW, scale: 3, fillColor: '#C5402A', fillOpacity: 1, strokeWeight: 0 }, offset: '50%' }` per segment, or render the arrows as DOM overlays (see `.tg-arrow` in `app.css` / `RouteLayer` in `parts.jsx`).
- The final leg to a **planned** stop is a **dashed** polyline (`--route` at
  opacity .45, dash `5 5`).

**Trip bar** — top-left cream chip (`--chip`, 1px `--line`, radius 14,
`shadow-md`, `backdrop-filter: blur(8px)`): hamburger → trip switcher menu, trip
title in italic-capable display font, stop count in mono.

See `RouteLayer`, `FlagPin`, `Satellites` in `reference-app/parts.jsx` and the
`.tg-map*`, `.tg-flag*`, `.tg-route*`, `.tg-arrow*` rules in `app.css`.

### 2 · Itinerary sidebar (`RegionSidebar`)
**Purpose:** scannable list of regions/stops in order; entry point to details.

- **Header:** mono eyebrow (accent), italic serif trip title (`2xl`/34), a
  one-line sub with a Caveat phrase, and a mono stat row (`visited · planned · countries`).
- **Section label:** mono uppercase "Itinerary".
- **Region tile** (`.tg-tile`): a left **status rail** (13px dot + 2px connector
  line) beside the body:
  - Head row: region name (display 600, `lg`/20) + **handwritten date** (Caveat,
    accent, `lg`) right-aligned, `white-space: nowrap`.
  - Country line: mono uppercase `--ink-faint`.
  - **Photo strip:** 58px **prints** — `--flag-frame` mat, 1px `--line`, radius 2,
    soft shadow, alternating ±2° tilt; straighten + lift on hover. A `+N` mono
    overflow marker.
  - **Dispatch chip** (`.tg-dispatch`) when the region/stop has a Substack
    writeup: `surface-tint` pill, dark "S" badge, "Dispatch · N min read", accent →.
  - **Note:** Newsreader italic, `md`/17.
  - **"Open region"** ghost button (region drill-in — not yet designed).
- **Status dot colors:** visited = `--accent` solid; planned = hollow dashed
  `--status-planned`; abandoned = hollow dashed `--status-abandoned` + the name
  gets `line-through`.

### 3 · Post detail (`StopDetail`) — the new view
A centered modal (`.pd-overlay` + `.pd-card`, max-width 920px, radius 14,
`shadow-lg`) with a **dotted "torn-postcard" seam** between its two panels.
Prev/next chevrons **outside** the card flip through every post in the trip;
Esc / ←/→ keys; click-dim to close.

Branch on `post.kind`:

**(a) Instagram snapshot** — `[data-kind="instagram"]`
- **Left (≈57%):** the photo as a framed print (6px `--flag-frame` border,
  shadow) inset in `--surface-sunk`. Carousel when >1 image: `‹ ›` arrows, a
  `n / N` count chip (mono), location pill bottom-left, and active dots
  (`.pd-dots i.on` widens to a bar).
- **Right (≈43%):** breadcrumb (`flag · Trip / Region`, mono), handwritten date
  (Caveat `28`), kicker "Snapshot", location title (italic serif `25`), caption
  (italic serif `18`), a faint rotated "VISITED" passport stamp, and a footer
  with the IG badge + handle and a **subtle** "On Instagram ↗" link
  (`.pd-extlink` — not a button).

**(b) Substack dispatch** — `[data-kind="substack"]`
The **full article is shown inline** (no "read more" CTA — opening the detail
implies intent to read). Body supports paragraphs, **subheads** (`{sub}`), and
**pull-quotes** (`{quote}`), with an accent drop-cap on the first paragraph and
an end byline carrying a subtle "Open on Substack ↗" link.

Two **cover layouts** (per-post `post.layout`):
- **`side`** (default): cover fills the left panel (≈46%) — masthead "THE
  DISPATCH · No.", a region stamp, the headline overlaid at the bottom, plus
  legibility gradients. When a cover image exists, a dashed **"cover photo loads
  here"** slot labels it.
- **`top`**: cover is a **horizontal banner** across the top (masthead + stamp +
  headline), with the article **full-width below** — reclaims horizontal space
  and reads like an article page. Card narrows to ≈660px.

**No-cover fallback** (`post.noCover`, both layouts): the cover area becomes a
**typographic cover** — warm paper texture (`surface-tint`→`surface-sunk` +
dotted grain), ink masthead, and the region stamp enlarged in accent as the
hero. Never a blank color block.

All specs are in `reference-app/detail.css`; component logic in
`reference-app/detail.jsx` (`PostDetail`, `InstaMedia`/`InstaBody`,
`DispatchCover`/`DispatchBanner`/`DispatchBody`).

---

## Interactions & Behavior
- **Open detail:** clicking a sidebar photo opens that Instagram post; a Dispatch
  chip (or a flag with a primary dispatch) opens the Substack post.
- **Stop nav:** `‹ ›` and ←/→ move across a flat, trip-ordered list of all posts
  (each photo = one Instagram post; each region's dispatch = one Substack post).
  Disable at ends. **Esc** closes; clicking the dim closes.
- **Carousel:** arrows/dots cycle a post's images; resets to first on post change.
- **Hover:** flag pins and photo prints scale slightly; ghost buttons fill with
  `--accent-tint`; ext-links underline.
- **Transitions:** use `--ease-out`, `--dur-fast`/`--dur-med`. Respect
  `prefers-reduced-motion`.
- **Responsive:** below ~760px the post card stacks (cover above body) and the
  outside stop-nav hides.

## State Management
Minimal and local (mirrors the mock):
- `openPostIndex: number | null` — which post is open (null = closed).
- `carouselIndex` — per open Instagram post (local to the media component).
- `tripMenuOpen: boolean` — trip switcher.
Build the flat `posts[]` + an `index{}` lookup from your regions on mount
(`buildPosts()` in `parts.jsx`): for each region push its photos as `instagram`
posts then its `dispatch` as a `substack` post; key them `"<code>-p<i>"` /
`"<code>-d"` so clicks resolve to a position. Wire `onClose/onPrev/onNext` to
`openPostIndex`.

## Data model (extend `src/data/types.ts`)
Make `Post` a discriminated union and add optional fields. Illustrative:
```ts
type InstagramPost = {
  kind: 'instagram';
  location: string;
  caption: string;
  images: string[];        // urls; mock uses count + hues as placeholders
  permalink?: string;      // → subtle "On Instagram" link
};
type SubstackDispatch = {
  kind: 'substack';
  no: number;              // issue number
  title: string;
  dek?: string;            // standfirst
  readMins: number;
  body: (string | { sub: string } | { quote: string })[];
  cover?: { src: string } | null;  // null/absent → typographic fallback
  layout?: 'side' | 'top';         // default 'side'
  url?: string;            // → subtle "Open on Substack" link
  location?: string;
};
// On a Region/Stop: optional `dispatch?: SubstackDispatch`, and per-photo
// `count?: number` for carousels. Status stays `visited | planned | abandoned`
// (your derived effective status) and drives the dot + route styling.
```
The mock's sample data + voice is in `reference-app/data.jsx` — useful as a shape
and tone reference; replace with your real `adapters.ts` output.

## Assets
- **Flags:** the mock uses `https://flagcdn.com/<iso>.svg`. Your app already has
  flag assets — keep those; just restyle the marker container.
- **Photos / covers:** placeholders only in the mock (CSS gradients). Real
  Instagram images and Substack covers slot into the same boxes.
- **Map style:** `reference-app/postmark-map-style.js`.
- No icon font needed; the few glyphs (≡ ✕ ‹ › ↗ ✶ ⌖) are Unicode.

## Files in this bundle
```
design-system/
  styles.css            ← link/import this (or paste tokens into global.css)
  tokens/{fonts,colors,typography,foundations,base}.css
reference-app/          ← working React-via-Babel reference (port to TSX)
  index.html            full app (map + sidebar + detail)
  post-detail.html      all four post-detail states side by side
  parts.jsx             map, sidebar, tiles, buildPosts(), App
  detail.jsx            PostDetail (Instagram + Substack, side/top/fallback)
  app.css               map + sidebar + component styles
  detail.css            post-detail styles
  data.jsx              sample content (shape + voice reference)
  postmark-map-style.js Google Maps style array
```
Open `reference-app/index.html` and `post-detail.html` in a browser to see the
intended result. The live, latest versions also exist in the project root
(`ui_kits/app/`, `Travelogue Design System.html`).

## Not yet designed (next steps, if you want them)
- **Region drill-in** ("Open region" expansion / `CityDetail`).
- **Empty & loading states** for stops whose Instagram/Substack content is still
  fetching.
- Whether dispatches default to `side` or `top` cover layout app-wide.
