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
