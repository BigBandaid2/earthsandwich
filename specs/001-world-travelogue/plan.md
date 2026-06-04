# Implementation Plan: World Travelogue

**Branch**: `001-world-travelogue` | **Date**: 2026-06-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-world-travelogue/spec.md`

## Summary

A read-only single-page React/Vite travelogue that renders trip itineraries — region grouping, multi-level map navigation, and stop detail pop-ups — sourced entirely from the `useful-app` backend REST API (spec 002). All new feature code follows TDD: automated tests covering each acceptance scenario must pass before a feature is releasable (FR-045, SC-012). This plan supersedes the original 2026-04-24 plan; it reflects the spec overhaul (2026-06-04) that replaced hard-coded data with live API data and added the TDD mandate.

## Technical Context

**Language/Version**: TypeScript 5.5+ / Node 20+
**Primary Dependencies**: React 18, Vite 5, @vis.gl/react-google-maps, react-error-boundary; Vitest + React Testing Library (new — TDD)
**Storage**: N/A — read-only SPA; all data from the backend API
**Testing**: Vitest + @testing-library/react + @testing-library/jest-dom; jsdom environment (see research.md §1)
**Target Platform**: Browser (desktop/tablet primary, mobile responsive)
**Project Type**: Static SPA (web-app)
**Performance Goals**: Initial load + render ≤ 3 s under normal network (SC-010); error state visible ≤ 5 s when backend unavailable (SC-011)
**Constraints**: Read-only; no auth; URL hash routing; Google Maps API key via env; backend must be reachable at runtime
**Scale/Scope**: ~3 trips, up to 80+ stops per trip, 114 region reference records

## Constitution Check

| Gate | Status | Notes |
|---|---|---|
| App label (`useful-app`) | PASS | Spec header: `App: useful-app` |
| Evolutionary Development | PASS | Plan aligns with working code; no invented scope |
| Apps as architectural unit | PASS | 001 is `useful-app`; reads 002 via REST contract only; no shared code or filesystem reach-arounds |
| No model-specific names | N/A | No AI inference in this App |
| Inference inputs preserved | N/A | No AI inference in this App |
| Lean on references | PASS | Spec references 002 API contract; plan references spec and data-model.md |
| TDD mandate (FR-045, SC-012) | PASS | Vitest + RTL selected; test-first requirement explicit in every user-story phase |
| Cardinal Rule #1 (tasks.md historical) | APPLICABLE | Existing tasks.md has completed work; new phases will append to the bottom only |

**Post-design re-check** (after Phase 1): All gates still PASS. No new complexity introduced.

## Project Structure

### Documentation (this feature)

```text
specs/001-world-travelogue/
├── plan.md              # This file
├── research.md          # Phase 0 — testing framework, retry, region sourcing
├── data-model.md        # Phase 1 — API types, app types, adapters, derivations
├── quickstart.md        # Phase 1 — setup, dev, test, integration scenarios
├── contracts/
│   └── components.md    # Phase 1 — component prop contracts + hook interfaces
└── tasks.md             # Phase 2 output (/speckit.tasks — not created here)
```

### Source Code

```text
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts          # add: ApiRegion interface, getRegions() fetch fn
│   │   └── adapters.ts        # add: adaptRegion()
│   ├── components/
│   │   ├── MapView.tsx        # exists; update: prop types after regionUtils sig change
│   │   ├── RegionSidebar.tsx  # exists; US2, US3, US4, US5 behavior
│   │   ├── Sidebar.tsx        # exists; US1, US4, US5 — Abandoned section (FR-031)
│   │   └── StopDetail.tsx     # exists; US3 — Instagram/Substack/Planned layouts
│   ├── data/
│   │   ├── regions.ts         # KEEP — used by scripts/export-seed-data.ts; NOT imported at runtime
│   │   └── types.ts           # exists; no changes required
│   ├── hooks/
│   │   ├── useTrip.ts         # exists; add: retry wrapper
│   │   ├── useTrips.ts        # exists; add: retry wrapper
│   │   └── useRegions.ts      # NEW — fetch GET /regions with retry
│   ├── utils/
│   │   ├── regionUtils.ts     # update: groupStopsByRegion(trip, regions: Region[])
│   │   └── retry.ts           # NEW — withRetry<T>() exponential-backoff wrapper
│   ├── App.tsx                # update: useRegions, combined loading/error gate, empty-list state
│   └── main.tsx               # no changes
├── tests/
│   ├── setup.ts               # NEW — @testing-library/jest-dom import
│   └── unit/
│       ├── hooks/
│       │   ├── useTrips.test.ts     # NEW
│       │   ├── useTrip.test.ts      # NEW
│       │   └── useRegions.test.ts   # NEW
│       ├── utils/
│       │   └── regionUtils.test.ts  # NEW
│       └── components/
│           ├── App.test.tsx         # NEW
│           ├── Sidebar.test.tsx     # NEW
│           ├── RegionSidebar.test.tsx # NEW
│           └── StopDetail.test.tsx  # NEW
├── package.json               # add Vitest devDependencies + test scripts
├── tsconfig.json              # add: "types": ["vitest/globals"] if using globals
└── vite.config.ts             # add: test: { environment: 'jsdom', setupFiles: [...], globals: true }
```

**Structure Decision**: All frontend work stays within `frontend/`. No new directories at the project root. `backend/` is spec 002's territory and is not touched.

## Implementation Strategy

### Existing code baseline

The frontend is substantially built. The following is already implemented and should NOT be reimplemented — only tested and, where noted, updated:

- API client (`client.ts`): `ApiTrip`, `ApiStop`, `ApiInstagramPost`, `ApiSubstackPost`, all fetch functions
- Adapters (`adapters.ts`): `adaptStop`, `adaptTrip`, `adaptTripSummary`, `adaptPost`
- Hooks: `useTrips`, `useTrip` (working but without retry)
- `App.tsx`: trip selector, URL hash routing (FR-027), view mode state, stop modal state
- `MapView.tsx`, `Sidebar.tsx`, `RegionSidebar.tsx`, `StopDetail.tsx`: core UI behavior
- `regionUtils.ts`: `groupStopsByRegion`, `getActiveRegion`, `getRoutedGroups`, `isSegmentSolid`, status derivation (FR-028–FR-033), date-range computation (FR-014)

### What this plan adds

1. **Vitest + RTL**: test infrastructure to satisfy FR-045 and SC-012
2. **`retry.ts`**: `withRetry` utility; wire into all three data hooks
3. **`useRegions`**: new hook; wire into `App.tsx`
4. **`ApiRegion` + `adaptRegion`**: add to `client.ts` and `adapters.ts`
5. **`groupStopsByRegion` signature update**: accept `Region[]` parameter; remove module-level `REGIONS` import
6. **`App.tsx` error/loading gate**: extend to cover `useRegions`; add empty-trips-list message
7. **Automated tests**: written test-first for every user story's acceptance scenarios

### MVP scope

US6 (data loading + error experience) and the retry infrastructure underpin all other user stories. Implement and test these first, then proceed US1 → US2 → US3 → US4 → US5.
