# Tasks: World Travelogue

**Input**: Design documents from `specs/001-world-travelogue/`
**Prerequisites**: `specs/001-world-travelogue/plan.md`, `specs/001-world-travelogue/spec.md`, `specs/001-world-travelogue/research.md`, `specs/001-world-travelogue/data-model.md`

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create Vite React app skeleton in `package.json`, `vite.config.ts`, `index.html`, and `src/`
- [x] T002 Create the base source directories `src/assets/`, `src/components/`, `src/data/`, `src/pages/`, and `src/styles/`
- [x] T003 Add static hosting scripts and build commands in `package.json` for `dev`, `build`, and `preview`
- [x] T004 Create initial global stylesheet in `src/styles/global.css`
- [x] T005 Create `public/images/` and add placeholder image assets for travel stops

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T006 [P] Define TypeScript itinerary data types in `src/data/types.ts`
- [x] T007 [P] Implement the hard-coded itinerary data model in `src/data/itinerary.ts` with major stops, visited/planned status, and optional city children
- [x] T008 [P] Create the base app shell in `src/App.tsx` and set up React routing or view state for the travelogue
- [x] T009 [P] Create the primary home page component in `src/pages/HomePage.tsx`
- [x] T010 [P] Create reusable UI components `src/components/MapView.tsx`, `src/components/Sidebar.tsx`, and `src/components/StopDetail.tsx`
- [x] T011 [P] Configure global responsive layout and map/itinerary styling in `src/styles/global.css`
- [x] T012 [P] Ensure `src/data/itinerary.ts` includes sample data for at least one city stop with nested child site entries

---

## Phase 3: User Story 1 - Browse trip progress on map (Priority: P1)

**Goal**: Display the world travel route and itinerary sidebar so visitors can see where the trip has been and where it is going.

**Independent Test**: Open the site and confirm the world map displays plotted stops and the sidebar lists stop names, captions, and dates.

- [x] T013 [P] [US1] Render the world map and route overview in `src/components/MapView.tsx`
- [x] T014 [P] [US1] Render the itinerary stop list in `src/components/Sidebar.tsx`
- [x] T015 [US1] Implement visited vs planned stop marker styles in `src/components/MapView.tsx`
- [x] T016 [US1] Wire map selection state into `src/pages/HomePage.tsx` and `src/App.tsx`
- [x] T017 [US1] Add legend and route summary UI to `src/pages/HomePage.tsx`
- [x] T018 [US1] Verify the map and sidebar show the top-level route with at least 10 sample stops from `src/data/itinerary.ts`

---

## Phase 4: User Story 2 - Inspect a major stop (Priority: P2)

**Goal**: Allow visitors to select a stop and view its details, including optional image and blog entry content.

**Independent Test**: Select a stop from the map or sidebar and confirm the detail panel shows location, caption, date, and any optional content.

- [x] T019 [US2] Build `src/components/StopDetail.tsx` to display stop metadata and optional content
- [x] T020 [P] [US2] Render an optional stop image only when `image` exists in `src/data/itinerary.ts`
- [x] T021 [P] [US2] Render optional long-form blog content only when `blog` exists in `src/data/itinerary.ts`
- [x] T022 [P] [US2] Add expand/collapse interaction for blurbs, pictures, and long-form entries in `src/components/StopDetail.tsx`
- [x] T023 [US2] Integrate `StopDetail` into `src/pages/HomePage.tsx` so selected stop details are displayed on the page
- [x] T024 [US2] Update at least one major stop in `src/data/itinerary.ts` with an image and one with a blog entry to validate optional rendering

---

## Phase 5: User Story 3 - Drill into city-level itinerary (Priority: P3)

**Goal**: Enable hierarchical city-level drilldown so city stops reveal nested local sites and city-specific content.

**Independent Test**: Select a city stop and confirm the view shows nested city site entries and allows returning to the top-level route.

- [x] T025 [US3] Extend `src/data/itinerary.ts` to include city-level stops with nested `children` entries for local sites
- [x] T026 [US3] Implement city drilldown navigation in `src/components/Sidebar.tsx` or `src/pages/HomePage.tsx`
- [x] T027 [P] [US3] Create `src/components/CityDetail.tsx` or reuse `StopDetail.tsx` to render nested city site entries
- [x] T028 [P] [US3] Render city-level site markers and nested site details when a city stop is selected in `src/components/MapView.tsx`
- [x] T029 [US3] Add a return control in `src/pages/HomePage.tsx` to go back from city view to the top-level world route
- [x] T030 [US3] Verify a city stop with nested sites displays correctly and that returning to the top-level route restores the main itinerary

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T031 [P] Update `specs/001-world-travelogue/quickstart.md` with the final project commands and directory notes
- [x] T032 [P] Review `src/styles/global.css` and adjust responsive breakpoints for mobile, tablet, and desktop
- [x] T033 [P] Add accessible labels, keyboard focus states, and semantic HTML in `src/components/MapView.tsx`, `src/components/Sidebar.tsx`, and `src/components/StopDetail.tsx`
- [x] T034 [P] Validate the completed feature against the acceptance criteria in `specs/001-world-travelogue/spec.md`
- [x] T035 [P] Update `README.md` or project documentation with a note that itinerary content is hard-coded in `src/data/itinerary.ts`

---

## Dependencies & Execution Order

- Setup tasks (T001-T005) must be complete before the Foundational phase begins.
- Foundational tasks (T006-T012) block all user stories and must complete before story-specific implementation.
- User stories can be worked on in parallel after foundational work is complete, with priority order P1 → P2 → P3.
- Polish tasks can start once the core story implementations are available.

## Parallel Opportunities

- `T006`, `T007`, `T008`, `T009`, `T010`, and `T011` can run in parallel because they target separate files and shared structure.
- Map rendering, sidebar rendering, and detail component creation can be developed in parallel across user stories where state wiring permits.
- Review and documentation tasks `T031`–`T035` are parallelizable across the completed implementation.
