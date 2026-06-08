# Quickstart: World Travelogue (useful-app frontend)

**Phase**: 1 | **Plan**: [plan.md](./plan.md) | **Date**: 2026-06-04 (overhauled; original 2026-04-24)

The frontend depends on the backend API (spec 002) being reachable at runtime. Start the backend first.

---

## Prerequisites

- Node 20+ (check: `node -v`)
- Backend API running — see [../002-database-backend/quickstart.md](../002-database-backend/quickstart.md)
- Google Maps API key (for the map component)

---

## Environment Setup

Copy the example env file and fill in the required values:

```bash
cp frontend/.env.example frontend/.env
```

Edit `frontend/.env`:

```
VITE_GOOGLE_MAPS_API_KEY=<your Google Maps JavaScript API key>
VITE_API_BASE_URL=http://localhost:8000
```

`VITE_API_BASE_URL` defaults to `http://localhost:8000` if omitted.

---

## Install Dependencies

All commands run from the `frontend/` directory:

```bash
cd frontend
npm install
```

---

## Start Dev Server

```bash
npm run dev
```

Opens at `http://localhost:5173`. The dev server proxies are not configured — the frontend calls `VITE_API_BASE_URL` directly.

---

## Build for Production

```bash
npm run build
```

Outputs to `dist/` at the project root (configured in `vite.config.ts`).

---

## Run Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

Tests live in `frontend/tests/`. Vitest is the runner; jsdom is the DOM environment. No live network connections — all API calls are mocked.

---

## Test Structure

```text
frontend/tests/
├── setup.ts                          # jest-dom matchers
├── unit/
│   ├── hooks/
│   │   ├── useTrips.test.ts          # US6: loading, error, retry
│   │   ├── useTrip.test.ts           # US6: loading, error, retry
│   │   └── useRegions.test.ts        # region fetch, error, retry
│   ├── utils/
│   │   └── regionUtils.test.ts       # groupStopsByRegion, getActiveRegion, FR-014, FR-028–FR-033
│   └── components/
│       ├── App.test.tsx              # US1, US6: loading/error surface, trip switch
│       ├── Sidebar.test.tsx          # US1, US4, US5: section grouping, suppression rules
│       ├── RegionSidebar.test.tsx    # US2, US3, US4: drill-down, stop tiles
│       ├── StopDetail.test.tsx       # US3: Instagram/Substack/planned layouts
│       ├── LandingModal.test.tsx     # FR-047: first-visit display, localStorage, dismiss
│       └── PlayTripControl.test.tsx  # FR-052: play/pause/stop transitions, region advance
```

---

## Integration Scenarios

### Happy path — all data available

1. Backend running with seeded data (`python scripts/seed.py`)
2. `npm run dev` in `frontend/`
3. Navigate to `http://localhost:5173`
4. Verify: loading indicator appears briefly, then the world map renders with trip data

### Error state — backend unavailable

1. Stop the backend (`docker compose stop api`)
2. Open `http://localhost:5173` (or reload)
3. Verify: loading indicator appears, then after retry exhaustion a human-readable error message is shown. No blank page, no stack trace.

### Empty trip list

1. Connect to a backend with no trips seeded (`docker compose exec db psql -U postgres -d earthsandwich -c "TRUNCATE trips CASCADE;"`)
2. Open `http://localhost:5173`
3. Verify: "No trips are currently available." message is displayed in the error panel.

### URL hash routing (FR-027)

1. Copy the URL hash shown when viewing a trip (e.g., `http://localhost:5173/#/trip/earth-sandwich-2015`)
2. Open it in a new tab
3. Verify: the matching trip loads immediately

### Landing modal (FR-047)

1. Clear `travelogue:landing-dismissed` from localStorage (DevTools → Application → Local Storage → delete key)
2. Open `http://localhost:5173` (or reload)
3. Verify: landing modal overlay appears before map interaction is possible
4. Click the dismiss button
5. Verify: modal disappears and the localStorage key is now set
6. Reload the page
7. Verify: modal does not reappear

### Play Trip mode (FR-052)

1. Load a trip with at least three non-abandoned regions
2. Click the Play button on the map canvas
3. Verify: the map advances to each region in chronological order, the sidebar scrolls to the matching tile, and a Pause control is visible
4. Click Pause
5. Verify: playback stops at the current region; Pause is replaced by Play
6. Click Play again
7. Verify: playback resumes from where it paused
8. Wait for playback to reach the final non-abandoned region
9. Verify: playback stops automatically and the Play button re-enables (no looping)

---

## Connecting to the Backend

The backend is defined in spec 002. Its REST API contract is at [../002-database-backend/contracts/api.md](../002-database-backend/contracts/api.md). Key read endpoints used by the frontend:

| Endpoint | Used by |
|---|---|
| `GET /trips` | `useTrips` — trip selector list |
| `GET /trips/:id` | `useTrip` — full stop data for active trip |
| `GET /regions` | `useRegions` — region reference data |

Write endpoints and authentication are not used by the frontend.
