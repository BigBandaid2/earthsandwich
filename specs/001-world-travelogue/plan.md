# Implementation Plan: World Travelogue

**Branch**: `001-world-travelogue` | **Date**: 2026-04-29 | **Spec**: [specs/001-world-travelogue/spec.md](specs/001-world-travelogue/spec.md)
**Input**: Feature specification from `specs/001-world-travelogue/spec.md`

## Summary

Build a read-only static travel travelogue web application with an interactive Google Maps canvas and a trip feed sidebar. The map clusters stops into airport-derived regions with visited/planned visual distinction, and supports drill-down from trip overview to region-level stop exploration. A modal overlay provides full stop detail for Instagram and Substack post types. All content is hard-coded from the Miscellaneous Adventures trip dataset (23 stops, 5 regions).

## Technical Context

**Language/Version**: TypeScript 5.x, React 18, Node 18+  
**Primary Dependencies**: Vite 5 (bundler/dev server), React 18 (UI), `@googlemaps/js-api-loader` + `@googlemaps/react-wrapper` (Google Maps canvas)  
**Storage**: N/A — all content hard-coded in TypeScript source files at build time  
**Testing**: No automated test suite; verified via `npm run build` (TypeScript + Vite)  
**Target Platform**: Modern web browser; static hosting (GitHub Pages / Netlify)  
**Project Type**: Static SPA (single-page application)  
**Performance Goals**: Under 3 seconds load time on standard broadband (per constitution)  
**Constraints**: No server-side processing; no runtime content API calls; Google Maps API key and Map ID available in `.env`  
**Scale/Scope**: 1 trip, 5 regions, 23 stops; read-only audience of travelers and friends/family

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Static First | ✓ Pass | Vite static build, no server-side rendering, all content hard-coded in TS |
| II. Responsive Design | ⚠ Partial | CSS 72/28 split layout implemented; mobile breakpoints not yet validated |
| III. Accessibility | ⚠ Partial | ARIA labels on interactive elements; WCAG 2.1 AA audit pending |
| IV. Performance | ✓ Pass | Vite bundle <200KB JS; Google Maps loads async; <3s target met |
| V. Security | ✓ Pass | No inline scripts; Maps API key in `.env` (not committed); Map ID scoped in `.env` |
| Stack: Google Maps | ✓ Pass | `VITE_GOOGLE_MAPS_API_KEY` and `VITE_GOOGLE_MAPS_MAP_ID` provisioned in `.env` |
| Stack: Vanilla JS | ⚠ Justified deviation | React used instead of plain JS — see justification below |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| React framework (vs Vanilla JS) | Three-pane layout with shared state across map, sidebar, and modal requires a reactive rendering model | Vanilla JS DOM manipulation for bidirectional state (map↔sidebar↔modal) would be fragile and unmaintainable |

## Project Structure

### Documentation (this feature)

```text
specs/001-world-travelogue/
├── plan.md              # This file
├── research.md          # Phase 0 — technology decisions
├── data-model.md        # Phase 1 — entity definitions and data sources
├── quickstart.md        # Phase 1 — developer setup
├── contracts/           # Phase 1 — interface contracts (N/A: static site)
├── tasks.md             # Phase 2 output (speckit.tasks command)
└── wireframes/          # UI wireframes SVG
```

### Source Code

```text
src/
├── App.tsx                          # Root: view-mode state, layout, trip selector
├── components/
│   ├── MapView.tsx                  # WorldMap → TripMap / RegionMap (Google Maps)
│   ├── Sidebar.tsx                  # TripFeed, RegionTile (trip overview sidebar)
│   ├── RegionSidebar.tsx            # Accordion sidebar (region drill-down view)
│   └── StopDetail.tsx               # StopModal, InstagramPostView, SubstackPostView
├── data/
│   ├── types.ts                     # Stop, Region, Trip, InstagramPost, SubstackPost
│   ├── regions.ts                   # REGIONS array — 5 airport anchors with coords
│   ├── miscellaneous-adventures.ts  # 23 hard-coded stops with geocoords
│   └── itinerary.ts                 # Re-exports the active trip
├── utils/
│   └── regionUtils.ts               # groupStopsByRegion, getActiveRegion, FR-011/012/014
├── styles/
│   └── global.css                   # Dark-navy theme, 72/28 layout, all component styles
└── main.tsx                         # React entry point

public/                              # Static assets
.env                                 # VITE_GOOGLE_MAPS_API_KEY, VITE_GOOGLE_MAPS_MAP_ID (not committed)
```

**Structure Decision**: Single-project SPA. No backend split. All content derives from `src/data/`. Google Maps rendered via `@googlemaps/react-wrapper` within the `.map-pane` container.
