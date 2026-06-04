# Tasks: World Travelogue

**Input**: Design documents from `specs/001-world-travelogue/`
**Prerequisites**: `specs/001-world-travelogue/plan.md`, `specs/001-world-travelogue/spec.md`, `specs/001-world-travelogue/data-model.md`

**Status**: Updated for flat stop model with dynamic region clustering (2026-04-24)

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Project initialization and basic structure

- [x] T001 [P] Initialize Vite React TypeScript project with dependencies in `package.json`
- [x] T002 [P] Configure Vite config (`vite.config.ts`) with React plugin
- [x] T003 [P] Setup TypeScript configuration (`tsconfig.json`) for React JSX
- [x] T004 Create entry point (`index.html` and `src/main.tsx`)

---

## Phase 2: Foundational (Core Data & Types)

**Purpose**: Core data structure and shared type definitions for flat stop model

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 [P] Update Stop type to flat model: id, title, caption, date, coords, status, regionCode, regionName, image?, blog? in `src/data/types.ts`
- [x] T006 [P] Add Region type definition: code, name, airportName, country, coords in `src/data/types.ts`
- [x] T007 [P] Add Trip Itinerary type: id, title, description, stops[] in `src/data/types.ts`
- [x] T008 Refactor hard-coded itinerary data to flat model (remove nested children) in `src/data/itinerary.ts`
- [x] T009 [P] Setup global CSS styling framework (map layout, sidebar, panels) in `src/styles/global.css`
- [x] T010 [P] Setup responsive grid layout for map and sidebar in `src/styles/layout.css`
- [x] T011 Create App.tsx root component with state management for selectedStop and selectedRegion

**Checkpoint**: Data types defined, flat itinerary loaded, App container ready

---

## Phase 3: User Story 1 - Browse trip progress on map (Priority: P1) 🎯 MVP

**Goal**: Visitors can view the round-the-world route on an interactive map with visited/planned stops distinguished, and use the sidebar to jump to stops.

**Independent Test**: Load the site, verify the map renders with all stops plotted, sidebar displays all major stops with location/caption/date, and clicking a stop selects it.

### Implementation for User Story 1

- [x] T012 [P] [US1] Update MapView component to render flat stops (no nested children) in `src/components/MapView.tsx`
- [x] T013 [P] [US1] Add visited (blue) vs planned (red) marker styling in `src/styles/map.css`
- [x] T014 [P] [US1] Add legend (visited, planned, selected) to MapView in `src/components/MapView.tsx`
- [x] T015 [US1] Draw route polyline connecting stops in order in `src/components/MapView.tsx`
- [x] T016 [P] [US1] Update Sidebar component to display flat stop list (no city drill-down) in `src/components/Sidebar.tsx`
- [x] T017 [US1] Wire stop selection between MapView and Sidebar in `src/App.tsx`
- [x] T018 [US1] Add responsive layout: stack sidebar below map on mobile in `src/styles/layout.css`
- [x] T019 [US1] Manual test: Open site, verify map displays all stops, sidebar shows itinerary, selections work

**Checkpoint**: User Story 1 complete - visitors can browse trip and identify major stops

---

## Phase 4: User Story 2 - Explore region clusters on zoomed-out map (Priority: P2)

**Goal**: Visitors zoomed out on the map see nearby stops clustered by region (derived from nearest international airport), and can select a region to see grouped stops.

**Independent Test**: Zoom map out, verify region clusters appear, select a region and confirm the stops assigned to it display.

### Implementation for User Story 2

- [x] T020 [P] [US2] Implement region derivation utility in `src/utils/regionUtils.ts` to find nearest international airport for each stop
- [x] T021 [US2] Add region grouping function to compute regions from flat stop list in `src/utils/regionUtils.ts`
- [x] T022 [US2] Implement zoom level detection in MapView (track viewport) in `src/components/MapView.tsx`
- [x] T023 [US2] Render region cluster markers (aggregated points) when zoomed out in `src/components/MapView.tsx`
- [x] T024 [US2] Add region cluster styling (circle with count badge) in `src/styles/regions.css`
- [x] T025 [US2] Implement region selection handler in MapView in `src/components/MapView.tsx`
- [x] T026 [US2] Update Sidebar to show stops grouped by region when region is selected in `src/components/Sidebar.tsx`
- [x] T027 [US2] Manual test: Zoom out, verify region clustering appears; select region, confirm grouped display works

**Checkpoint**: User Stories 1 & 2 complete - map supports both detailed and clustered views

---

## Phase 5: User Story 3 - Inspect a single stop (Priority: P3)

**Goal**: Visitors click on a stop and see its details: location, caption, date, optional image, optional blog text, and visited/planned status.

**Independent Test**: Click a stop on the map or in sidebar, verify detail panel opens with all required fields, optional fields appear only when present.

### Implementation for User Story 3

- [x] T028 [P] [US3] Update StopDetail component to display flat stop fields (no nested children) in `src/components/StopDetail.tsx`
- [x] T029 [P] [US3] Add conditional rendering for optional image field in `src/components/StopDetail.tsx`
- [x] T030 [P] [US3] Add conditional rendering for optional blog/long-form text field in `src/components/StopDetail.tsx`
- [x] T031 [US3] Add status badge (visited/planned) styling in `src/styles/stop-detail.css`
- [x] T032 [US3] Implement detail panel expand/collapse animation in `src/components/StopDetail.tsx`
- [x] T033 [US3] Wire StopDetail into App.tsx and update stop selection state in `src/App.tsx`
- [x] T034 [US3] Show StopDetail when stop is selected from map or sidebar in `src/App.tsx`
- [x] T035 [US3] Close detail panel when another stop selected or close button clicked in `src/App.tsx`
- [x] T036 [US3] Add responsive styling so detail panel works on mobile (slides up from bottom) in `src/styles/layout.css`
- [x] T037 [US3] Manual test: Click each stop, verify details display, optional fields appear only when present

**Checkpoint**: All core user stories complete - map browsing, region clustering, and stop inspection working

---

## Phase 6: Decommission Old Features

**Purpose**: Remove nested city/site hierarchy code (from old model)

- [x] T038 Remove CityDetail component references from App.tsx and components
- [x] T038a Remove nested city drilling logic from MapView.tsx (topLevelStops, cityViewId, etc.)
- [x] T039 Remove cityChildren or nested stop handling from Sidebar.tsx
- [x] T040 Clean up dead code and unused state variables from App.tsx

---

## Phase 8: Planned Stop Type & New Trip Data

**Purpose**: Implement the Planned post type, load two new trips, and add the region-view suppression logic

**Status**: Partially complete — types and data files created; UI display logic pending

- [x] T051 Add `PlannedPost` interface and update `StopPost` union in `src/data/types.ts`
- [x] T052 Create `src/data/earth-sandwich-2015.ts` with 82 hard-coded planned stops (geocoords pre-computed)
- [x] T053 Create `src/data/earth-club-sandwich-2027.ts` with 30 hard-coded planned stops (geocoords pre-computed)
- [x] T054 Expand `src/data/regions.ts` with all new airport anchor entries (~100 regions total)
- [x] T055 Update `src/data/itinerary.ts` to export `trips: Trip[]` array and default `itinerary` (Earth Club Sandwich 2027)
- [x] T056 [US4] Implement planned stop suppression filter in `src/components/RegionSidebar.tsx`: hide Planned tiles when any Instagram or Substack stop exists in the same region (FR-018)
- [x] T057 [US4] Render Planned stop tiles in region sidebar when the region contains only Planned stops: show location, date, and optional caption (FR-018)
- [x] T058 [US4] Suppress stop detail pop-up for Planned stops: clicking a Planned marker or tile takes no action (FR-019)
- [x] T059 [US4] Omit Instagram thumbnail row and Substack tile row from trip overview region tile when all stops in that region are Planned (FR-021)
- [x] T060 Update `src/App.tsx` to consume `trips` array from `itinerary.ts` and wire the trip selector to all three trips
- [x] T061 Manual test: load each of the three trips, verify map route, sidebar display, and planned stop suppression logic

**Checkpoint**: All three trips render; planned stop suppression and no-pop-up behavior verified

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Enhancements affecting multiple user stories and overall quality

- [ ] T041 [P] Add accessibility labels and ARIA attributes to all interactive elements in `src/components/`
- [ ] T042 [P] Add keyboard navigation support (arrow keys, Enter, Escape) across map and sidebar in `src/components/`
- [ ] T043 [P] Test responsive layout on mobile/tablet viewport sizes in `src/styles/`
- [ ] T044 [P] Optimize map rendering performance for 50+ markers in `src/components/MapView.tsx`
- [ ] T045 [P] Add visual feedback for map interactions (hover states, animations) in `src/styles/`
- [ ] T046 [P] Run performance benchmark: ensure initial page load under 3 seconds (npm run build)
- [ ] T047 Add comprehensive inline documentation to modified components in `src/components/`
- [ ] T048 Update or create `specs/001-world-travelogue/quickstart.md` with usage examples and local development instructions
- [ ] T049 Validate all tasks completed and run final browser testing (map, sidebar, detail panel, region clustering)
- [ ] T050 Test edge cases: stops with missing images/blogs, very long blog text, many stops in one region

### Stakeholder visual feedback (added 2026-05-04, not yet sprinted)

- [ ] T093 [US-Polish] Replace large default Google Maps pin in continental view with a country-flag pin of similar size (decorative + informational about each stop's country) in `src/components/MapView.tsx`. If the flag pin is judged visually overwhelming after a side-by-side review, fall back to a smaller profile push-pin instead.
- [ ] T094 [US-Polish] Add directional arrowheads to the route polyline connecting region pins so the trip direction is visually unambiguous in `src/components/MapView.tsx`.
- [ ] T095 [US-Polish] Add distinct Start and Finish pins for the first and last stop of each trip so big trips have an obvious visual focal point in `src/components/MapView.tsx`. Today, large trips read as a tangle of lines with no anchor for the eye.
- [ ] T096 [US-Polish] Apply a vintage postcard-style map skin to the continental view: simpler palette, no country labels, no desert/mountain terrain detail. Likely via a custom Google Maps style or `mapId`. Region drill-down view should retain current full detail.

**Checkpoint**: Feature complete, polished, and ready for deployment

---

## Phase 9: Multi-Trip URL Routing

**Status**: Shipped 2026-05-01. New phase appended after work was completed; not in original plan.

- [x] T062 Add FR-027 (hash routing `#/trip/{tripId}`) to `specs/001-world-travelogue/spec.md`
- [x] T063 Implement hash parsing + `tripFromHash()` in `src/App.tsx`
- [x] T064 Wire trip selector to push history state on switch
- [x] T065 Listen for `hashchange`/`popstate` events to handle browser back/forward navigation

---

## Phase 10: Abandoned Stop Status

**Status**: Shipped 2026-05-01.

- [x] T066 Add FR-028–FR-032 + User Story 5 + edge cases to `spec.md`; update `data-model.md` notes
- [x] T067 Add `EffectiveStopStatus` type and `getEffectiveStopStatus()` helper in `src/utils/regionUtils.ts`
- [x] T068 Update region rollup logic for abandoned classification (FR-029) in `src/utils/regionUtils.ts`
- [x] T069 Implement `getRoutedGroups()` to skip fully-abandoned regions in route polyline (FR-030)
- [x] T070 Add Abandoned section to trip feed sidebar (FR-031) in `src/components/Sidebar.tsx`
- [x] T071 Apply visual treatment: strike-through + faded grey + dashed dot, no connector line in `src/styles/global.css`
- [x] T072 Adjust FR-014 region end-date computation to skip abandoned regions

---

## Phase 11: Substack Post Integration

**Status**: Shipped 2026-05-01.

- [x] T073 Parse `wela-posts.txt` and add 14 Substack stops to `src/data/earth-sandwich-2015.ts`
- [x] T074 Add FR-033 to `spec.md`: exclude Substack dates from region date-range bounds; implement filter in `groupStopsByRegion()`
- [x] T075 Update Substack Post entity description in `spec.md` to clarify date represents publication, not visit

---

## Phase 12: Stop Data Backfill (Earth Sandwich 2015)

**Status**: Shipped 2026-05-01.

- [x] T076 Add 178 Instagram stops to `src/data/earth-sandwich-2015.ts` from `posts.local.tsv`
- [x] T077 Geocode/location-fill ~30 posts in `posts.local.tsv` that lacked location metadata; delete invalid (non-JPG) media files
- [x] T078 Add YYZ, NAS, SEA, YVR, LAS, SFO regions to `src/data/regions.ts` for the pre-trip North American leg
- [x] T079 Validate trip data via `npx tsc --noEmit -p .`

---

## Phase 13: Map and Sidebar UX Refinements

**Status**: Shipped 2026-05-01.

- [x] T080 Enable Google Maps `zoomControl` on both trip and region map views in `src/components/MapView.tsx`
- [x] T081 Bump default zoom +0.4 above `fitBounds` default for continental view
- [x] T082 Move "Expand Region" button inline with region title; shorten label to "Expand →" in `src/components/Sidebar.tsx`
- [x] T083 Include day (not just month/year) in `formatDateRange()` output

---

## Phase 14: Spec-Kit / JIRA Integration

**Status**: Shipped 2026-05-04.

- [x] T084 Install `mbachorik/spec-kit-jira` extension via custom catalog override (`.specify/extension-catalogs.yml`)
- [x] T085 Configure OCS project: Epic > Story > Subtask hierarchy with parent-field linkage in `.specify/extensions/jira/jira-config.yml`
- [x] T086 Discover JIRA custom fields (Story Points, Sprint, Priority, Team) via Atlassian MCP and record in `discovered-fields.json`
- [x] T087 Run smoke test: `999-jira-integration-test` push and sync round-trip; verify Story → Subtask hierarchy works
- [x] T088 Push `001-world-travelogue` Epic and 8 Phase Stories to OCS-11 through OCS-19
- [x] T089 Push Phase 7 polish backlog as Subtasks OCS-39 through OCS-48 (active work for forward sprints)

---

## Phase 15: Drift Reconciliation (2026-05-04 weekly scan)

**Status**: Backfill of work that shipped between commits `c24c263` (Photo pins) and `650040b` (workflow-guide draft) without a prior task entry. Identified by a `docs/workflow.md` §Reconciliation drift scan.

- [x] T090 Rename media files that were actually videos from `.jpg` to `.mp4` extension in `public/media/` — affects posts 35, 62, 83, 91, 99, 106, 153, 171, 212, 314. Commit: `06de9d5`.
- [x] T091 Add Instagram deep-link to the stop detail modal for Instagram-typed posts in `src/components/StopDetail.tsx` and `src/styles/global.css`. Commit: `ad19e4e`.
- [x] T092 Bulk-upload 299 Earth Sandwich 2015 post images to `public/media/`. Commit: `d1ed59f`. (Implicit under T076 but recorded explicitly per team convention.)

---

## Phase 16: Drift Reconciliation (2026-05-15 weekly scan)

**Status**: Backfill of work that shipped between commits `1b5f11a` (Phase 15 close) and `6faeb11` (HEAD) without a prior task entry. Some entries here arguably belong to the data-ingestion direction (originally spec 002-data-ingestion, split 2026-05-22 into 002-database-backend and 003-ingestion-pipeline) but landed on the 001 branch before that spec existed.

- [x] T097 Update Earth Sandwich 2015 trip image routes in `src/data/earth-sandwich-2015.ts`. Commit: `0a689de`.
- [x] T098 First-pass Instagram data ingestion: emit `public/posts.json` via `scripts/export_posts_json.py`, add `src/hooks/usePosts.ts`, wire into `src/App.tsx`. Commit: `57aeb53`. **Note**: predates the 002-data-ingestion spec; superseded direction lives in `specs/003-ingestion-pipeline/plan.md` (after the 2026-05-22 split of 002).
- [x] T099 Add Kos (Greek Islands) airport anchor entry to `src/data/regions.ts`. Commit: `17b532f`.

---

## Phase 17: Drift Reconciliation (2026-06-01 weekly scan)

**Status**: Backfill from the 2026-05-25 global drift baseline (`2265cf6`) through HEAD. One drift commit identified for 001 — a top-level ErrorBoundary added to harden the frontend against runtime errors now that data flows from the live API rather than hardcoded modules.

- [x] T100 Add top-level `ErrorBoundary` component (`frontend/src/components/ErrorBoundary.tsx`) to gracefully surface runtime errors instead of white-screening; wire into `frontend/src/App.tsx`; clean up the now-obsolete `effectiveActiveTrip` state that became dead with API-fetched data. Commit: `ec3faf3`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion - MVP core
- **User Story 2 (Phase 4)**: Depends on Phase 3 (region logic builds on US1 map)
- **User Story 3 (Phase 5)**: Depends on Phase 3 (detail panel independent from clustering)
- **Decommission (Phase 6)**: After US1/US2/US3 ready, before Polish
- **Polish (Phase 7)**: Depends on Phases 3-6 completion

### Within Each Phase

- **Phase 1**: All [P] tasks can run in parallel
- **Phase 2**: T005-T007, T009-T010 [P] tasks can run in parallel; T008 and T011 depend on types from T005-T007
- **Phase 3**: T012-T014 [P] tasks can run in parallel; T015-T019 depend on component structure being ready
- **Phase 4**: T020-T021, T024 [P] tasks can run in parallel; T022-T023, T025-T027 depend on core logic
- **Phase 5**: T028-T030 [P] tasks can run in parallel; T031-T037 depend on component structure
- **Phase 6**: Sequential cleanup as old code is identified
- **Phase 7**: All [P] tasks (T041-T046) can run in parallel

### Parallel Opportunities

- All Setup [P] tasks (T001-T003)
- All Foundational [P] tasks (T005-T007, T009-T010)
- All US1 [P] component tasks (T012-T014)
- All US2 [P] utility and clustering tasks (T020-T021, T024)
- All US3 [P] component fields (T028-T030)
- All Phase 7 [P] tasks (T041-T046)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (basic project structure)
2. Complete Phase 2: Foundational (types, flat itinerary data, App container)
3. Complete Phase 3: User Story 1 (map + sidebar browsing)
4. **STOP and VALIDATE**: Verify core browsing works independently
5. Deploy basic MVP

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Browse) → Test independently → Deploy MVP
3. Add US2 (Regions) → Test independently → Deploy enhancement
4. Add US3 (Details) → Test independently → Deploy final feature
5. Decommission old code → Polish → Deploy polished version

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (map + sidebar)
   - Developer B: User Story 2 (region logic + clustering)
   - Developer C: User Story 3 (detail panel)
3. Stories complete and integrate with existing app
4. Team reconvenes for decommissioning and Phase 7 (Polish)

---

## Notes

- [P] tasks can run in parallel (different files, no blocking dependencies)
- [Story] labels map each task to specific user story for clear traceability
- Each user story should be independently completable and testable
- Current components exist but must be updated for the flat stop model (no nested children)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- SVG projection map is acceptable; Google Maps API integration can be an enhancement
- Hard-coded itinerary data keeps the site static-deployable

---

## Phase 18: Testing Infrastructure Setup

**Status**: Not started (2026-06-04 — added following spec overhaul; TDD mandate per FR-045)

**Purpose**: Install and configure Vitest + React Testing Library so that all subsequent phases can follow the test-first approach mandated by FR-045.

**⚠️ CRITICAL**: All phases below (19+) depend on this phase. No test can be written until testing infrastructure is in place.

- [x] T101 [P] Add Vitest devDependencies to `frontend/package.json`: `vitest`, `@vitest/coverage-v8`, `jsdom`, `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`; add `"test": "vitest"`, `"test:watch": "vitest --watch"`, `"test:coverage": "vitest run --coverage"` scripts
- [x] T102 [P] Add Vitest test config block to `frontend/vite.config.ts`: `test: { environment: 'jsdom', setupFiles: ['./tests/setup.ts'], globals: true }`
- [x] T103 [P] Create `frontend/tests/setup.ts` with `import '@testing-library/jest-dom'`

**Checkpoint**: `npm test` runs successfully (no test files yet; 0 passing is expected)

---

## Phase 19: API Migration Foundation

**Status**: Not started (2026-06-04 — prerequisite for useRegions and retry-enabled hooks)

**Purpose**: Add the missing API types, adapter, and retry utility that underpin the spec-overhauled data flow. These are shared by all user story phases and must exist before any hook tests can be written.

- [x] T104 [P] Add `ApiRegion` interface (`iata_code`, `name`, `airport_name`, `country`, `lat`, `lng`) and `getRegions(params?)` fetch function to `frontend/src/api/client.ts`
- [x] T105 [P] Add `adaptRegion(apiRegion: ApiRegion): Region` adapter (maps `iata_code→code`, `airport_name→airportName`, `lat/lng→coords`) to `frontend/src/api/adapters.ts`
- [x] T106 [P] Create `withRetry<T>(fn: () => Promise<T>, maxAttempts = 3, baseDelayMs = 1000): Promise<T>` exponential-backoff utility in `frontend/src/utils/retry.ts`; delays: 1 s → 2 s; throws last error after exhaustion

**Checkpoint**: TypeScript compiles with no errors (`npm run build`)

---

## Phase 20: User Story 6 — Reliable Data Loading (Priority: P1, TDD)

**Goal**: A visitor sees a loading indicator while data fetches; if the backend is unavailable after retries, a clear error message appears. Empty trips list shows a human-readable message using the same error surface (FR-042–FR-044; clarifications Q2, Q3 2026-06-04).

**Independent Test**: Mock all three data hooks. Verify loading indicator → travelogue on success; loading indicator → error message on failure; "No trips are currently available." for empty list.

**⚠️ TDD**: Write failing tests first (T107–T110), then implement (T111–T115). All tests must pass before this story is complete.

- [x] T107 [P] [US6] Write `useTrips` hook tests in `frontend/tests/unit/hooks/useTrips.test.ts`: (a) `loading` is `true` on mount before fetch resolves; (b) successful fetch sets `trips` array and clears `loading`; (c) after 3 failed attempts `error` is a non-null string and `trips` is empty; mock `fetch` via `vi.stubGlobal`
- [x] T108 [P] [US6] Write `useTrip` hook tests in `frontend/tests/unit/hooks/useTrip.test.ts`: (a) does nothing when `tripId` is null; (b) sets `loading=true` on `tripId` change; (c) successful fetch populates `trip`; (d) after retry exhaustion `error` is set and `trip` is null
- [x] T109 [P] [US6] Write `useRegions` hook tests in `frontend/tests/unit/hooks/useRegions.test.ts`: (a) `loading=true` initially; (b) success yields `regions: Region[]` array; (c) retry exhaustion yields `error` string
- [x] T110 [US6] Write `App` integration tests in `frontend/tests/unit/components/App.test.tsx` — mock `useTrips`, `useTrip`, `useRegions` via `vi.mock`: (a) loading indicator visible while any hook reports `loading=true`; (b) error panel visible when `useTrips` yields an error; (c) "No trips are currently available." rendered when `useTrips` yields empty list; (d) trip switch triggers `useTrip` with the new trip id
- [x] T111 [P] [US6] Update `useTrips` to wrap `getTrips()` in `withRetry` from `frontend/src/utils/retry.ts` in `frontend/src/hooks/useTrips.ts`
- [x] T112 [P] [US6] Update `useTrip` to wrap `getTripDetail()` in `withRetry` in `frontend/src/hooks/useTrip.ts`
- [x] T113 [P] [US6] Create `useRegions` hook in `frontend/src/hooks/useRegions.ts`: on mount calls `getRegions()` wrapped in `withRetry`; returns `{ regions: Region[], loading: boolean, error: string | null }`; cancels on unmount
- [x] T114 [US6] Update `groupStopsByRegion` in `frontend/src/utils/regionUtils.ts` to accept `regions: Region[]` as a second parameter instead of importing from the module-level `REGIONS` constant; remove the `REGIONS` import from this file
- [ ] T115 [US6] Update `frontend/src/App.tsx`: call `useRegions()`; extend the loading gate to include `regionsLoading`; extend the error gate to include `regionsError`; render "No trips are currently available." when `trips.length === 0` after load; pass the fetched `regions` array to `groupStopsByRegion`

**Checkpoint**: `npm test` — all T107–T110 tests pass; TypeScript clean

---

## Phase 21: User Story 1 — Trip Overview Tests (Priority: P1, TDD)

**Goal**: Automated test coverage for the trip overview map + sidebar, including region grouping logic, date-range derivation, status classification, and the three-section sidebar layout.

**Independent Test**: Pass fixture `RegionGroup[]` and `Trip` to `TripFeed`; assert Visited / Planned / Abandoned sections render in order with the correct region tiles.

- [ ] T116 [P] [US1] Write `regionUtils` unit tests in `frontend/tests/unit/utils/regionUtils.test.ts`: `groupStopsByRegion` groups stops by `region_code`; derives `startDate`/`endDate` per FR-014 (skips abandoned for next-region anchor); excludes Substack dates when non-Substack stops exist (FR-033); rolls up `overallStatus` per FR-028/FR-029; `getActiveRegion` returns last region with a visited stop; `getRoutedGroups` excludes abandoned regions (FR-030); `isSegmentSolid` per FR-012
- [ ] T117 [US1] Write `TripFeed` (Sidebar) tests in `frontend/tests/unit/components/Sidebar.test.tsx`: (a) renders Visited → Planned → Abandoned sections in that order (FR-031); (b) hides sections containing zero regions; (c) region tile shows name, country, and formatted date range; (d) abandoned region tile appears in Abandoned section with strike-through styling and no connector line (US5, FR-030)

**Checkpoint**: All Phase 21 tests pass; `npm test` green

---

## Phase 22: User Story 2 — Region Drill-Down Tests (Priority: P2, TDD)

**Goal**: Test coverage for the region sidebar drill-down: active region expansion, collapsed headers, stop tile rendering, planned/abandoned suppression, and no-pop-up-on-click for non-openable stop types.

**Independent Test**: Render `RegionSidebar` with fixture data; click a collapsed header; assert it becomes the active (expanded) region.

- [ ] T118 [US2] Write `RegionSidebar` tests in `frontend/tests/unit/components/RegionSidebar.test.tsx`: (a) active region is expanded showing stop tiles; (b) other regions render as collapsed header rows; (c) clicking a collapsed header calls `onSelectRegion` with its `region_code`; (d) Planned stop tiles suppressed when any Instagram/Substack stop exists in the same region (FR-018); (e) Planned stop tile click does NOT call `onOpenStop` (FR-019); (f) Instagram stop tile shows caption and photo; (g) Substack stop tile shows title and preview

**Checkpoint**: All Phase 22 tests pass; `npm test` green

---

## Phase 23: User Story 3 — Stop Detail Tests (Priority: P3, TDD)

**Goal**: Test coverage for the stop detail pop-up: Instagram and Substack post layouts, graceful handling of missing optional fields, and prev/next navigation.

**Independent Test**: Render `StopModal` with an Instagram fixture stop; assert location, caption, and image element are present; assert prev/next arrows call `onNav`.

- [ ] T119 [US3] Write `StopDetail` tests in `frontend/tests/unit/components/StopDetail.test.tsx`: (a) Instagram layout renders location heading, caption, and `<img>` with `media_url` as src; (b) Substack layout renders title heading, subtitle, and body text; (c) missing optional subtitle or caption not rendered; (d) prev arrow calls `onNav('prev')`; (e) next arrow calls `onNav('next')`; (f) close button calls `onClose`

**Checkpoint**: All Phase 23 tests pass; `npm test` fully green — SC-012 satisfied for all US1–US6 acceptance scenarios

