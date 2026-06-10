# Component Contracts: World Travelogue

**Phase**: 1 | **Plan**: [../plan.md](../plan.md) | **Date**: 2026-06-04

This document defines the public prop interfaces of the travelogue's React components. These contracts are the test boundary: acceptance-scenario tests assert rendered output against these interfaces without depending on internal implementation.

> The backend API contract lives in [../../002-database-backend/contracts/api.md](../../002-database-backend/contracts/api.md). This document covers only frontend component and hook contracts.

---

## Data Hooks

### `useTrips() → UseTripsResult`

Fetches the trip list from `GET /trips`. Includes retry (see research.md §2).

```ts
interface UseTripsResult {
  trips: Trip[];       // empty while loading or on error
  loading: boolean;
  error: string | null;
}
```

**Behavior**:
- On mount: sets `loading = true`, fetches `GET /trips`.
- On success with data: sets `trips`, clears `error`, sets `loading = false`.
- On success with empty list: sets `trips = []`, clears `error`, sets `loading = false`. (Caller renders empty-state message.)
- On error after retry exhaustion: sets `error` string, keeps `trips = []`, sets `loading = false`.
- Cleanup: cancels in-flight fetch on unmount.

---

### `useTrip(tripId: string | null) → UseTripResult`

Fetches full trip detail from `GET /trips/:id`. Includes retry.

```ts
interface UseTripResult {
  trip: Trip | null;
  loading: boolean;
  error: string | null;
}
```

**Behavior**:
- When `tripId` is `null`: does nothing; all fields at initial state.
- On `tripId` change: sets `loading = true`, fetches `GET /trips/${tripId}`.
- On success: sets `trip`, clears `error`, sets `loading = false`.
- On error after retry exhaustion: sets `error` string, sets `trip = null`, sets `loading = false`.
- Cleanup: cancels in-flight fetch on `tripId` change or unmount.

---

### `useRegions() → UseRegionsResult` *(new)*

Fetches all region reference records from `GET /regions`. Includes retry.

```ts
interface UseRegionsResult {
  regions: Region[];
  loading: boolean;
  error: string | null;
}
```

**Behavior**: mirrors `useTrips` — retry on failure, clears on unmount.

---

## Components

### `<App />`

Root component. No props (reads from URL hash). Orchestrates all data hooks and owns all navigation state, Play Trip state, and landing modal state.

**Rendered surfaces by app state**:

| Condition | Rendered output |
|---|---|
| Any data hook `loading = true` | Loading indicator: `<div class="app-loading">` with "Loading…" text |
| Any data hook `error` non-null | Error panel: `<div class="app-error">` with human-readable message |
| `trips.length === 0` (after load) | Error panel with "No trips are currently available." |
| All data loaded, `viewMode = 'trip'` | Split layout: `<WorldMap>` + `<TripFeed>` + `<PlayTripControl>` overlay |
| All data loaded, `viewMode = 'region'` | Split layout: `<WorldMap>` + `<RegionSidebar>` |
| `openStop` is non-null | `<StopModal>` overlaid on current split layout |
| `showLandingModal = true` | `<LandingModal>` overlaid before any map interaction (FR-047, SC-013) |

---

### `<TripFeed />` (Sidebar.tsx)

Trip overview sidebar — View 1. Shows regions grouped into "Visited", "Planned", and "Abandoned" sections.

```ts
interface TripFeedProps {
  regionGroups: RegionGroup[];
  trip: Trip;
  onExpandRegion: (regionCode: string) => void;
  onOpenStop: (stopId: string, contextStopIds: string[]) => void;
}
```

**Rendered content**:
- Three collapsible sections in fixed order: Visited → Planned → Abandoned (FR-031). Empty sections are hidden (FR-002).
- Within each section: region tiles in reverse-chronological order.
- Each region tile: marker icon, region name, country, date range, up to 4 Instagram thumbnails ("+X" overflow badge if more), up to 4 Substack tiles ("+X" overflow badge if more), "Expand Region →" button.
- Omits Instagram thumbnail row and Substack tile row for regions with only Planned stops (FR-021).
- Abandoned region tiles and their connector lines are visually distinct (FR-030).

---

### `<RegionSidebar />` (RegionSidebar.tsx)

Region drill-down sidebar — View 2. Shows all regions collapsed except the active one.

```ts
interface RegionSidebarProps {
  regionGroups: RegionGroup[];
  activeRegionCode: string | null;
  onSelectRegion: (regionCode: string) => void;
  onOpenStop: (stopId: string, contextStopIds: string[]) => void;
}
```

**Rendered content**:
- Regions in reverse-chronological order (most recent first).
- Active region: expanded with header + stop tiles below.
- All other regions: collapsed header rows only; clicking activates (FR-015).
- Sidebar scrolls so active region header is near the top on activation (FR-023).
- Stop tiles per type:
  - Instagram: marker icon, Instagram icon, caption (≤3 lines, ellipsis), photo full-width at original aspect ratio.
  - Substack: marker icon, Substack icon, title, 3-line body preview.
  - Planned/Abandoned: shown only if region has no Instagram or Substack stops (FR-018). Shows location, date, optional caption. No click action (FR-019, FR-032).
- Independent scrollbar (FR-022).

---

### `<WorldMap />` (MapView.tsx)

Google Maps canvas — shared across View 1 and View 2.

```ts
interface WorldMapProps {
  regionGroups: RegionGroup[];
  viewMode: 'trip' | 'region';
  activeRegionCode: string | null;
  openStopId: string | null;
  playTripActiveRegionCode: string | null;  // new — FR-052; null when not playing
  onSelectRegion: (regionCode: string) => void;
  onOpenStop: (stopId: string, contextStopIds: string[]) => void;
  onClusterClick: (regionCodes: string[]) => void; // new — FR-051; called when a cluster is clicked
}
```

**View 1 (trip)**:
- Region markers use **flag pin** style (FR-046); the active region's pin is highlighted. Markers for qualifying countries are clustered via `@googlemaps/markerclusterer`; US, CA, CN always render individually (FR-051). Clicking a cluster zooms until pins separate.
- Route polyline connects non-abandoned regions only (FR-030); solid for visited-adjacent segments, dashed for planned-only (FR-012). Each segment bears a directional arrowhead near the destination endpoint (FR-049).
- Map tiles use postcard-inspired style with no country labels and no road/terrain detail (FR-050). Map is restricted to a single world copy (FR-048).
- `<PlayTripControl />` is rendered as a floating overlay by the parent `<App />`; `playTripActiveRegionCode` drives pan/focus animation (FR-052).

**View 2 (region)**: Individual stop markers use **pushpin** style (FR-046); dashed light-blue chronological route line with arrowheads (FR-049); full map detail (roads, terrain, waterways); single-world-copy restriction is lifted.

**Route polyline logic**: Only non-abandoned regions participate (FR-030). Solid vs. dashed per FR-012.

---

---

### `<LandingModal />` (LandingModal.tsx) *(new — FR-047)*

First-visit overlay. Rendered by `App.tsx` only when `localStorage` does not contain the dismissed key.

```ts
interface LandingModalProps {
  onDismiss: () => void;
}
```

**Rendered content**:
- Site headline and one-sentence purpose.
- Trip context block (placeholder copy acceptable initially).
- How-to-browse guidance.
- Follow-along callout for friends and family.
- Dismiss button (e.g. "Start Exploring") — calls `onDismiss`, which causes `App.tsx` to write `localStorage.setItem('travelogue:landing-dismissed', '1')` and unmount the modal.

**Persistence rule**: `App.tsx` initialises a `showLandingModal` state from `localStorage.getItem('travelogue:landing-dismissed')`; if absent the modal renders; once dismissed the key is written and the modal never reappears in the same browser (SC-013).

---

### `<PlayTripControl />` (PlayTripControl.tsx) *(new — FR-052)*

Floating play/pause/exit control. Rendered by `App.tsx` as an overlay on the map canvas when `viewMode = 'trip'`.

```ts
interface PlayTripControlProps {
  isPlaying: boolean;
  onPlay: () => void;   // dispatches 'play' action
  onPause: () => void;  // dispatches 'pause' action
  onExit: () => void;   // dispatches 'stop' action and returns to normal map interaction
}
```

**Rendered states**:
- **Ready / Paused**: Play button visible; Exit control hidden (only visible when playback has started at least once in this session).
- **Playing**: Pause button replaces Play; Exit affordance visible.
- **After final region**: Play button re-enabled (restarts from first region); Pause hidden.

**Behavior**: Play Trip advances through non-abandoned regions in chronological order on a fixed interval (≥1 s). The map animates to each region via `<WorldMap />`'s `playTripActiveRegionCode` prop. Sidebar scrolls to the highlighted tile. At the last non-abandoned region, playback stops automatically (SC-018).

---

### `<StopModal />` (StopDetail.tsx)

Stop detail pop-up overlay — View 3.

```ts
interface StopModalProps {
  stop: Stop;
  stopList: string[];          // ordered stop IDs for prev/next navigation
  allStops: Stop[];
  regionGroups: RegionGroup[];
  onClose: () => void;
  onNav: (direction: 'prev' | 'next') => void;
}
```

**Layout**: Dims background. Left-side prev arrow; right-side next arrow + X close button. Content area: breadcrumb (Trip / Region / Location · Date).

**Instagram layout**: location heading, caption subheading, hero image at original aspect ratio, sized to fit ≤95vh without scrolling (width shrinks if portrait image would overflow, FR-026).

**Substack layout**: title heading, subtitle subheading, long-form body text (may scroll within modal).

---

## Utility Functions

### `groupStopsByRegion(trip: Trip, regions: Region[]): RegionGroup[]`

Updated signature — `regions` is now a parameter (not a module-level import) so the function can be tested with fixture data and is decoupled from the hard-coded `REGIONS` array.

Returns `RegionGroup[]` sorted by `startDate` ascending, with `endDate` computed per FR-014.

---

### `withRetry<T>(fn: () => Promise<T>, maxAttempts?: number, baseDelayMs?: number): Promise<T>`

Retry wrapper for any async operation. Throws the last error after all attempts are exhausted.

```ts
// Default: 3 attempts, 1 s → 2 s exponential backoff
withRetry(() => fetch('/trips').then(r => r.json()))
```

---

## Test Coverage Expectations (SC-012)

Each acceptance scenario in the spec maps to at least one automated test:

| User Story | Acceptance Scenario | Test location |
|---|---|---|
| US1 | Map visible with region markers (live backend) | `App.test.tsx` — mock useTrips/useTrip/useRegions |
| US1 | Sidebar lists Visited / Planned sections | `Sidebar.test.tsx` |
| US2 | Expand Region → switches to region view | `App.test.tsx` |
| US2 | Clicking collapsed region header activates it | `RegionSidebar.test.tsx` |
| US3 | Stop tile click opens detail pop-up | `App.test.tsx` |
| US3 | Missing optional content handled gracefully | `StopDetail.test.tsx` |
| US4 | Planned-only region shows planned tiles | `Sidebar.test.tsx`, `RegionSidebar.test.tsx` |
| US4 | Planned tile click does nothing | `RegionSidebar.test.tsx` |
| US5 | Abandoned stop grouped under "Abandoned" section | `Sidebar.test.tsx` |
| US5 | Route line skips abandoned region | `regionUtils.test.ts` |
| US6 | Loading indicator visible during fetch | `App.test.tsx` |
| US6 | Error message shown when backend unavailable | `App.test.tsx` |
| US6 | Trip switch triggers new data fetch | `App.test.tsx` |
| FR-047 | Landing modal renders on first visit (no localStorage key) | `LandingModal.test.tsx` |
| FR-047 | Landing modal does not render when localStorage key is set | `LandingModal.test.tsx` |
| FR-047 | Dismiss writes localStorage key and hides modal | `LandingModal.test.tsx` |
| FR-052 | Play advances through all non-abandoned regions in order | `PlayTripControl.test.tsx` |
| FR-052 | Pause suspends interval; resume continues from same index | `PlayTripControl.test.tsx` |
| FR-052 | Playback stops at final region; Play control re-enabled | `PlayTripControl.test.tsx` |
