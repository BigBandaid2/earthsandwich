# Research: World Travelogue

**Phase**: 0 | **Plan**: [plan.md](./plan.md) | **Date**: 2026-06-04 (overhauled; original 2026-04-24)

## 1. Testing Framework

**Decision**: Vitest + React Testing Library

**Rationale**: Vitest reuses the Vite config directly — no separate bundler, no `ts-jest`, no duplicate transform configuration. It shares TypeScript and module resolution with the runtime, so tests run in the same mental model as the code. React Testing Library enforces behavior-driven tests over implementation details, which aligns with the acceptance-scenario-based TDD mandate (FR-045). They are the community standard for Vite + React as of 2026.

**Environment**: `jsdom` — Vitest's browser-like DOM environment for React component rendering without a real browser.

**Packages to add** (devDependencies in `frontend/`):
- `vitest` — test runner and assertion library
- `@vitest/coverage-v8` — V8-native coverage (no Babel instrumentation overhead)
- `jsdom` — DOM environment
- `@testing-library/react` — React component render + query utilities
- `@testing-library/user-event` — realistic user interaction simulation
- `@testing-library/jest-dom` — DOM matchers (`toBeInTheDocument`, `toHaveTextContent`, etc.)

**Config additions** to `frontend/vite.config.ts`:
```ts
test: {
  environment: 'jsdom',
  setupFiles: ['./tests/setup.ts'],
  globals: true,
}
```

**Setup file** (`frontend/tests/setup.ts`):
```ts
import '@testing-library/jest-dom';
```

**Alternatives considered**:
- Jest + ts-jest: Requires separate bundler config, slower cold start, transform mismatch risk with Vite plugins.
- Playwright: E2E browser testing — valuable for full integration flows but heavier to run. Deferred; unit + component tests satisfy SC-012 for now.

---

## 2. Retry / Backoff Strategy

**Decision**: 3 total attempts (1 initial + 2 retries), exponential backoff: 1 s → 2 s. Loading indicator stays visible throughout. After exhaustion: human-readable error message per FR-044.

**Rationale**: Three attempts give a flaky backend a chance to recover without keeping the visitor waiting more than ~7 seconds total. Exponential backoff avoids hammering a struggling server. No visible retry button (auto-retry only, per clarification Q3 2026-06-04).

**Implementation**: A standalone `retry.ts` utility wraps any `Promise`-returning function:
```ts
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxAttempts = 3,
  baseDelayMs = 1000,
): Promise<T>
```

This makes retry logic testable in isolation and reusable across `useTrips`, `useTrip`, and `useRegions`.

**Error escalation surface**: After retry exhaustion, hooks set `error` to a user-facing string. `App.tsx` renders it in a simple error panel — no stack trace, no internal details.

**Alternatives considered**:
- `TanStack Query`: Rich retry, caching, and background refresh. Overkill for a read-only travelogue with a small data set and no auto-refresh (clarification Q4 2026-06-04). Adds a significant dependency for marginal gain.
- No retry: Violates FR-044; single-request failure shows an error too aggressively.

---

## 3. Region Data Sourcing

**Decision**: Fetch region reference data from `GET /regions`; remove the runtime import of `src/data/regions.ts` from the React component tree.

**Rationale**: FR-042 mandates all trip, stop, and post content — including region reference data — is retrieved from the backend API. The hard-coded `src/data/regions.ts` was the original approach and must not be the runtime source of truth after the spec overhaul.

**Migration path**:
1. Add `ApiRegion` interface and `getRegions()` to `src/api/client.ts`.
2. Add `adaptRegion()` to `src/api/adapters.ts` (`ApiRegion` → `Region`).
3. Add `useRegions` hook (`src/hooks/useRegions.ts`) mirroring the `useTrips` pattern, with retry.
4. Update `groupStopsByRegion(trip, regions)` in `regionUtils.ts` to accept `Region[]` as a parameter instead of reading from the module-level `REGIONS` import.
5. Update `App.tsx` to call `useRegions`, gate on loading/error, and pass the fetched array to `groupStopsByRegion`.
6. Retain `src/data/regions.ts` — it is imported by `scripts/export-seed-data.ts` for database seeding. Do NOT delete it; just stop importing it in the runtime React app.

**Alternatives considered**:
- Bundle regions in the frontend build: Simple, but violates FR-042 and ties new regions to a frontend redeploy.
- Derive region from stop coordinates: Was the pre-clarification approach; explicitly rejected in Q1 (2026-06-04) — use API-provided `region_code`.

---

## 4. Map Tile Provider & Postcard Style (FR-050)

**Decision**: CartoDB Voyager (via the `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png` tile URL, or equivalent via the Google Maps Cloud-based map styling JSON if sticking with the Google Maps JavaScript API).

**Rationale**: CartoDB Voyager has a warm, illustrated aesthetic with no country name labels at global zoom and suppressed road/terrain detail — matching FR-050's "postcard-inspired" style. It requires no API key of its own and is free for public, non-commercial use at the project's expected traffic volumes. If the site remains on the Google Maps JavaScript API, a custom Cloud-based map style (JSON) can approximate the same aesthetic while retaining the existing `@vis.gl/react-google-maps` integration.

**Implementation**: Pass the chosen style configuration to the map component at the global zoom level only. At the region drill-down level, revert to the default full-detail style so roads, terrain, and waterways are visible (FR-050 applies only to the global level).

**Alternatives considered**:
- Stamen Watercolor: Highly artistic but now requires a Stadia Maps API key. Heavier visual style may obscure markers.
- OpenStreetMap (default tiles): No postcard aesthetic; full road and label detail at all zooms.
- Google Maps default: Shows country labels; not compliant with FR-050.

---

## 5. Anti-Meridian Wrap Prevention (FR-048)

**Decision**: Restrict the Google Maps instance at the global trip overview level to a single world copy using `restriction: { latLngBounds: { north: 85, south: -85, west: -180, east: 180 }, strictBounds: true }` or the equivalent `minZoom` cap that prevents the user from zooming out to see adjacent world copies.

**Rationale**: FR-048 requires that map tiles do not repeat into adjacent copies of the globe. The Google Maps JavaScript API supports `restriction` on the `Map` object which enforces a pan/zoom boundary. Setting `strictBounds: true` with world-spanning bounds prevents tile wrapping while still allowing free pan within those bounds. Polyline edge-jumping across the antimeridian is explicitly accepted by the spec (clarification Q3, 2026-06-04) — only tile repetition is prevented.

**Implementation**: Apply restriction only in `viewMode: 'trip'`. In `viewMode: 'region'` remove the restriction so the user can pan freely within the zoomed region.

**Alternatives considered**:
- `worldCopyJump: false` (Leaflet API concept): Not directly applicable to the Google Maps JS API.
- Coordinate normalization of polyline points: Would prevent edge-jumping but is explicitly out of scope per the clarification.

---

## 6. Directional Arrowheads on Route Segments (FR-049)

**Decision**: Render arrowheads as SVG `AdvancedMarkerElement` overlays placed near the destination end of each polyline segment. Each arrowhead is an SVG triangle rotated to the bearing of its segment.

**Rationale**: The Google Maps JavaScript API's `Polyline` does not natively support arrowheads. The `AdvancedMarkerElement` API (available in `@vis.gl/react-google-maps` via `<AdvancedMarker>`) allows custom HTML/SVG content to be placed at any latitude/longitude. Computing the segment bearing and placing a rotated SVG arrow near the destination point is a self-contained, testable approach with no additional library dependency.

**Implementation**:
- For each pair of adjacent non-abandoned endpoints, compute the geodesic bearing (lat/lng → degrees).
- Place an `<AdvancedMarker>` at a point 10–15% of the segment distance from the destination end.
- The marker content is a small SVG polygon (arrowhead) rotated via CSS `transform: rotate({bearing}deg)`.
- Applies to both the trip view segments (between region markers) and the region view segments (between stop markers).

**Alternatives considered**:
- `google.maps.Symbol` with `FORWARD_OPEN_ARROW`: Available on `Polyline` via `icons`, but limited styling control and behavior in newer Maps API versions is inconsistent.
- Canvas overlay: More complex, harder to test.

---

## 7. Country Clustering for Region Markers (FR-051)

**Decision**: `@googlemaps/markerclusterer` with a custom renderer that groups only markers sharing the same country, excluding US, Canada, and China.

**Rationale**: `@vis.gl/react-google-maps` supports `@googlemaps/markerclusterer` via the `useMarkerClusterer` hook pattern. This library is the standard Google Maps clustering solution and integrates directly with `AdvancedMarkerElement`. The exclusion logic (US, CA, CN) is implemented by pre-filtering: markers from those countries are added to the map individually outside the clusterer, while all others are added through the clusterer.

**Algorithm**: Standard `GridAlgorithm` or `SuperClusterAlgorithm` (better geographic accuracy). Cluster count badge is rendered via the default or a custom renderer.

**Click behavior**: Clicking a cluster calls `map.fitBounds(cluster.bounds)` which zooms the map until markers separate — matching the clarification (Q1, 2026-06-04): no spiderfy.

**Countries excluded from clustering**: United States (`US`), Canada (`CA`), China (`CN`). Country codes are derived from the `country` field on each `Region` reference record.

**Alternatives considered**:
- Supercluster standalone: Lower-level, requires more wiring. `@googlemaps/markerclusterer` wraps it.
- Custom distance-based grouping: Reinvents the wheel; harder to tune visually.

---

## 8. Play Trip Mode (FR-052)

**Decision**: `useReducer`-managed playback state in `App.tsx`; interval driven by `useEffect` with `setInterval`; map focuses each region via `map.panTo` / `map.fitBounds`.

**Rationale**: Play Trip is a UI state machine: playing → paused → stopped → playing. `useReducer` cleanly models the transitions without prop drilling or a separate context. The interval is created inside a `useEffect` that depends on `isPlaying` — when paused, the effect cleanup clears the interval. This is idiomatic React and straightforward to test by dispatching actions against the reducer.

**State shape** (held in `App.tsx`):
```ts
type PlayTripState = {
  isPlaying: boolean;
  currentIndex: number;  // index into non-abandoned regions array
};
type PlayTripAction =
  | { type: 'play' }
  | { type: 'pause' }
  | { type: 'advance' }
  | { type: 'stop' };   // final region reached
```

**Playback interval**: 3 seconds per region (configurable constant). Advancing calls `dispatch({ type: 'advance' })`; when `currentIndex` reaches the last non-abandoned region, `dispatch({ type: 'stop' })` fires, returning to the ready-to-play state.

**Sidebar sync**: `App.tsx` passes `playTripActiveRegionCode` down to `<TripFeed />`, which scrolls and highlights the matching tile.

**Tests**: `PlayTripControl.test.tsx` verifies play/pause/stop transitions and that the region advances correctly using fake timers (`vi.useFakeTimers()`).

**Alternatives considered**:
- `useState`: Adequate for a boolean but becomes unwieldy for the index + playing combo; transitions harder to test atomically.
- External animation library (GSAP, framer-motion): Overkill for a timed interval advance.

---

## 9. Landing Modal & Local Storage Persistence (FR-047)

**Decision**: Check `localStorage.getItem('travelogue:landing-dismissed')` on mount; if absent, show the modal. On dismiss, write the key with a truthy value.

**Rationale**: FR-047 requires the dismissed state to persist in the visitor's browser with no server-side tracking. `localStorage` is the canonical browser-native persistent store for exactly this pattern. The key is namespaced (`travelogue:landing-dismissed`) to avoid collision with other uses of `localStorage` on the same origin.

**Implementation**: `<LandingModal>` receives an `onDismiss` callback from `App.tsx`. The `App.tsx` decides whether to render `<LandingModal>` at all based on a `useState` flag initialized from `localStorage`. On `onDismiss`, `App.tsx` writes the localStorage key and sets the flag to `false`.

**Test approach**: `LandingModal.test.tsx` uses `vi.stubGlobal` or `Object.defineProperty` to mock `localStorage`; asserts modal renders when key is absent, does not render when key is present, and that `onDismiss` causes the key to be written.

**Alternatives considered**:
- `sessionStorage`: Does not survive tab close / browser restart — too ephemeral.
- Cookie: Works but requires no server; heavier API than localStorage for this use case.
- IndexedDB: Overkill for a single boolean flag.

---

## 4. Loading and Error State Architecture

**Decision**: Single shared loading/error surface in `App.tsx`, not distributed across child components.

**Rationale**: All data required to render the app (trips list, selected trip detail, region reference data) must be loaded before any meaningful view can render. Gating at the app shell level keeps component logic clean — child components receive fully-loaded data and never handle null/loading states internally. This extends the existing `if (tripsLoading || !activeTrip)` pattern already present in `App.tsx`.

**App.tsx loading gate**:
- Loading state: any of `tripsLoading`, `tripLoading`, `regionsLoading` is true → loading indicator
- Error state: any error string is non-null after all retries → error message panel
- Empty trips list: `trips.length === 0` after a successful load → "No trips are currently available." in the same error panel (per clarification Q2 2026-06-04)

**Alternatives considered**:
- Per-component loading/error: More granular, but adds complexity and is unnecessary for a single-user read-only app where all data is needed simultaneously.

---

## 5. URL Hash Routing

**Decision**: Retain existing `window.location.hash` implementation in `App.tsx`; no additional library.

**Rationale**: The existing implementation correctly handles initial hash resolution, trip switching, and browser back/forward (`hashchange` + `popstate` listeners). FR-027 is already implemented correctly. The TDD requirement means adding tests for the `tripIdFromHash` helper and hash-update behavior — not a rewrite. Hash routing avoids server-side rewrite requirements for a static SPA.

**Alternatives considered**:
- React Router with `HashRouter`: Adds a dependency for behavior that is already working. Not needed.

---

## 6. Component Testing Approach

**Decision**: RTL rendering with `vi.stubGlobal` / `vi.fn()` mocks for `fetch` in hook tests; component tests receive fixture props directly.

**Hook tests** (`useTrips`, `useTrip`, `useRegions`): mock `fetch` at the global level to verify retry behavior, loading-state transitions, and error escalation — no real network. Uses `renderHook` from RTL.

**Component tests** (`Sidebar`, `RegionSidebar`, `StopDetail`, etc.): pass pre-built fixture props; assert rendered output via RTL queries. No fetch mocking needed.

**App-level integration tests**: mock the three data hooks (`useTrips`, `useTrip`, `useRegions`) via `vi.mock` to control loading/error/data states; assert that the correct UI surface (loading indicator vs. error panel vs. travelogue) is rendered in each scenario.

**Alternatives considered**:
- MSW (Mock Service Worker): More realistic `fetch` interception. Worthwhile when Playwright E2E tests are introduced, but adds setup overhead not justified for unit-level hook tests alone.
