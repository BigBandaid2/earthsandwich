# Tasks: World Travelogue

**Input**: Design documents from `specs/001-world-travelogue/`
**Prerequisites**: `specs/001-world-travelogue/plan.md`, `specs/001-world-travelogue/spec.md`, `specs/001-world-travelogue/data-model.md`

**Status**: Updated for flat stop model with dynamic region clustering (2026-04-24)

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Initialize Vite React TypeScript project with dependencies in `package.json`
- [ ] T002 [P] Configure Vite config (`vite.config.ts`) with React plugin
- [ ] T003 [P] Setup TypeScript configuration (`tsconfig.json`) for React JSX
- [ ] T004 Create entry point (`index.html` and `src/main.tsx`)

---

## Phase 2: Foundational (Core Data & Types)

**Purpose**: Core data structure and shared type definitions for flat stop model

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Update Stop type to flat model: id, title, caption, date, coords, status, regionCode, regionName, image?, blog? in `src/data/types.ts`
- [ ] T006 [P] Add Region type definition: code, name, airportName, country, coords in `src/data/types.ts`
- [ ] T007 [P] Add Trip Itinerary type: id, title, description, stops[] in `src/data/types.ts`
- [ ] T008 Refactor hard-coded itinerary data to flat model (remove nested children) in `src/data/itinerary.ts`
- [ ] T009 [P] Setup global CSS styling framework (map layout, sidebar, panels) in `src/styles/global.css`
- [ ] T010 [P] Setup responsive grid layout for map and sidebar in `src/styles/layout.css`
- [ ] T011 Create App.tsx root component with state management for selectedStop and selectedRegion

**Checkpoint**: Data types defined, flat itinerary loaded, App container ready

---

## Phase 3: User Story 1 - Browse trip progress on map (Priority: P1) 🎯 MVP

**Goal**: Visitors can view the round-the-world route on an interactive map with visited/planned stops distinguished, and use the sidebar to jump to stops.

**Independent Test**: Load the site, verify the map renders with all stops plotted, sidebar displays all major stops with location/caption/date, and clicking a stop selects it.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Update MapView component to render flat stops (no nested children) in `src/components/MapView.tsx`
- [ ] T013 [P] [US1] Add visited (blue) vs planned (red) marker styling in `src/styles/map.css`
- [ ] T014 [P] [US1] Add legend (visited, planned, selected) to MapView in `src/components/MapView.tsx`
- [ ] T015 [US1] Draw route polyline connecting stops in order in `src/components/MapView.tsx`
- [ ] T016 [P] [US1] Update Sidebar component to display flat stop list (no city drill-down) in `src/components/Sidebar.tsx`
- [ ] T017 [US1] Wire stop selection between MapView and Sidebar in `src/App.tsx`
- [ ] T018 [US1] Add responsive layout: stack sidebar below map on mobile in `src/styles/layout.css`
- [ ] T019 [US1] Manual test: Open site, verify map displays all stops, sidebar shows itinerary, selections work

**Checkpoint**: User Story 1 complete - visitors can browse trip and identify major stops

---

## Phase 4: User Story 2 - Explore region clusters on zoomed-out map (Priority: P2)

**Goal**: Visitors zoomed out on the map see nearby stops clustered by region (derived from nearest international airport), and can select a region to see grouped stops.

**Independent Test**: Zoom map out, verify region clusters appear, select a region and confirm the stops assigned to it display.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement region derivation utility in `src/utils/regionUtils.ts` to find nearest international airport for each stop
- [ ] T021 [US2] Add region grouping function to compute regions from flat stop list in `src/utils/regionUtils.ts`
- [ ] T022 [US2] Implement zoom level detection in MapView (track viewport) in `src/components/MapView.tsx`
- [ ] T023 [US2] Render region cluster markers (aggregated points) when zoomed out in `src/components/MapView.tsx`
- [ ] T024 [US2] Add region cluster styling (circle with count badge) in `src/styles/regions.css`
- [ ] T025 [US2] Implement region selection handler in MapView in `src/components/MapView.tsx`
- [ ] T026 [US2] Update Sidebar to show stops grouped by region when region is selected in `src/components/Sidebar.tsx`
- [ ] T027 [US2] Manual test: Zoom out, verify region clustering appears; select region, confirm grouped display works

**Checkpoint**: User Stories 1 & 2 complete - map supports both detailed and clustered views

---

## Phase 5: User Story 3 - Inspect a single stop (Priority: P3)

**Goal**: Visitors click on a stop and see its details: location, caption, date, optional image, optional blog text, and visited/planned status.

**Independent Test**: Click a stop on the map or in sidebar, verify detail panel opens with all required fields, optional fields appear only when present.

### Implementation for User Story 3

- [ ] T028 [P] [US3] Update StopDetail component to display flat stop fields (no nested children) in `src/components/StopDetail.tsx`
- [ ] T029 [P] [US3] Add conditional rendering for optional image field in `src/components/StopDetail.tsx`
- [ ] T030 [P] [US3] Add conditional rendering for optional blog/long-form text field in `src/components/StopDetail.tsx`
- [ ] T031 [US3] Add status badge (visited/planned) styling in `src/styles/stop-detail.css`
- [ ] T032 [US3] Implement detail panel expand/collapse animation in `src/components/StopDetail.tsx`
- [ ] T033 [US3] Wire StopDetail into App.tsx and update stop selection state in `src/App.tsx`
- [ ] T034 [US3] Show StopDetail when stop is selected from map or sidebar in `src/App.tsx`
- [ ] T035 [US3] Close detail panel when another stop selected or close button clicked in `src/App.tsx`
- [ ] T036 [US3] Add responsive styling so detail panel works on mobile (slides up from bottom) in `src/styles/layout.css`
- [ ] T037 [US3] Manual test: Click each stop, verify details display, optional fields appear only when present

**Checkpoint**: All core user stories complete - map browsing, region clustering, and stop inspection working

---

## Phase 6: Decommission Old Features

**Purpose**: Remove nested city/site hierarchy code (from old model)

- [ ] T038 Remove CityDetail component references from App.tsx and components
- [ ] T038a Remove nested city drilling logic from MapView.tsx (topLevelStops, cityViewId, etc.)
- [ ] T039 Remove cityChildren or nested stop handling from Sidebar.tsx
- [ ] T040 Clean up dead code and unused state variables from App.tsx

---

## Phase 8: Planned Stop Type & New Trip Data

**Purpose**: Implement the Planned post type, load two new trips, and add the region-view suppression logic

**Status**: Partially complete — types and data files created; UI display logic pending

- [x] T051 Add `PlannedPost` interface and update `StopPost` union in `src/data/types.ts`
- [x] T052 Create `src/data/earth-sandwich-2015.ts` with 82 hard-coded planned stops (geocoords pre-computed)
- [x] T053 Create `src/data/earth-club-sandwich-2027.ts` with 30 hard-coded planned stops (geocoords pre-computed)
- [x] T054 Expand `src/data/regions.ts` with all new airport anchor entries (~100 regions total)
- [x] T055 Update `src/data/itinerary.ts` to export `trips: Trip[]` array and default `itinerary` (Earth Club Sandwich 2027)
- [ ] T056 [US4] Implement planned stop suppression filter in `src/components/RegionSidebar.tsx`: hide Planned tiles when any Instagram or Substack stop exists in the same region (FR-018)
- [ ] T057 [US4] Render Planned stop tiles in region sidebar when the region contains only Planned stops: show location, date, and optional caption (FR-018)
- [ ] T058 [US4] Suppress stop detail pop-up for Planned stops: clicking a Planned marker or tile takes no action (FR-019)
- [ ] T059 [US4] Omit Instagram thumbnail row and Substack tile row from trip overview region tile when all stops in that region are Planned (FR-021)
- [ ] T060 Update `src/App.tsx` to consume `trips` array from `itinerary.ts` and wire the trip selector to all three trips
- [ ] T061 Manual test: load each of the three trips, verify map route, sidebar display, and planned stop suppression logic

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

**Checkpoint**: Feature complete, polished, and ready for deployment

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

