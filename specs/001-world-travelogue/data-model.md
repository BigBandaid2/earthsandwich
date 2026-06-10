# Data Model: World Travelogue

**Phase**: 1 | **Plan**: [plan.md](./plan.md) | **Date**: 2026-06-04 (overhauled; original 2026-04-24)

All data originates from the backend REST API (spec 002). The frontend holds no local copy of trip content. Region reference data is also API-sourced. See [../002-database-backend/contracts/api.md](../002-database-backend/contracts/api.md) for the authoritative wire shapes.

---

## API Layer Types (`src/api/client.ts`)

These interfaces mirror the backend's JSON responses exactly. They are the raw network shapes — no camelCase conversion, no derived fields.

### `ApiTrip`
```ts
interface ApiTrip {
  id: string;
  title: string;
  description: string;
  start_date: string;   // "YYYY-MM-DD"
  end_date: string;     // "YYYY-MM-DD"
  created_at: string;   // ISO 8601
  updated_at: string;   // ISO 8601
}
```

### `ApiInstagramPost`
```ts
interface ApiInstagramPost {
  id: string;
  stop_id: string;
  instagram_id: string;
  shortcode: string;
  media_url: string;
  caption: string;
  timestamp: string;    // ISO 8601
  created_at: string;   // ISO 8601
}
```

### `ApiSubstackPost`
```ts
interface ApiSubstackPost {
  id: string;
  stop_id: string | null;
  substack_id: string;
  title: string;
  subtitle: string | null;
  body: string;
  published_at: string; // ISO 8601
  created_at: string;   // ISO 8601
}
```

### `ApiStop`
```ts
interface ApiStop {
  id: string;
  trip_id: string;
  date: string;         // "YYYY-MM-DD"
  location: string;
  lat: number;
  lng: number;
  status: 'visited' | 'planned';
  region_code: string;  // IATA airport code; matches ApiRegion.iata_code
  post_type: 'instagram' | 'substack' | 'planned';
  caption: string | null;
  post: ApiInstagramPost | ApiSubstackPost | null;
}
```

### `ApiTripDetail` (extends `ApiTrip`)
```ts
interface ApiTripDetail extends ApiTrip {
  stops: ApiStop[];
}
```

### `ApiRegion` *(new — add to client.ts)*
```ts
interface ApiRegion {
  iata_code: string;      // e.g. "MDE"
  name: string;           // e.g. "Medellín"
  airport_name: string;   // e.g. "José María Córdova International Airport"
  country: string;        // e.g. "Colombia"
  lat: number;
  lng: number;
}
```

---

## App Layer Types (`src/data/types.ts`)

These are the canonical app-layer shapes after adaptation. Components, hooks, and utilities operate on these types only — never directly on API types.

### `StopStatus` / `EffectiveStopStatus`
```ts
type StopStatus = 'visited' | 'planned';
// Derived at render time (FR-028); never stored or returned by the API
type EffectiveStopStatus = 'visited' | 'planned' | 'abandoned';
```

### `Coordinates`
```ts
interface Coordinates {
  lat: number;
  lng: number;
}
```

### `InstagramPost`
```ts
interface InstagramPost {
  type: 'instagram';
  image: string;        // media_url from API
  caption: string;
  instagramId?: string;
  shortcode?: string;
}
```

### `SubstackPost`
```ts
interface SubstackPost {
  type: 'substack';
  title: string;
  subtitle?: string;
  body: string;
}
```

### `PlannedPost`
```ts
interface PlannedPost {
  type: 'planned';
  caption?: string;
}
```

### `StopPost`
```ts
type StopPost = InstagramPost | SubstackPost | PlannedPost;
```

### `Stop`
```ts
interface Stop {
  id: string;
  date: string;         // "YYYY-MM-DD"
  location: string;
  coords: Coordinates;
  status: StopStatus;   // stored authored value; never reclassified
  regionCode: string;   // matches Region.code
  post: StopPost;
}
```

### `Region`
```ts
interface Region {
  code: string;         // IATA airport code (iata_code from API)
  name: string;
  airportName: string;  // airport_name from API
  country: string;
  coords: Coordinates;  // { lat, lng } from API
}
```

### `Trip`
```ts
interface Trip {
  id: string;
  title: string;
  description: string;
  stops: Stop[];
}
```

---

## Derived / Computed Types (`src/utils/regionUtils.ts`)

These types are produced by the view layer, not from the API directly.

### `RegionGroup`
```ts
interface RegionGroup {
  region: Region;
  stops: Stop[];
  startDate: string;    // "YYYY-MM-DD" — derived per FR-014 / FR-033
  endDate: string;      // "YYYY-MM-DD" — derived per FR-014 / FR-033
  overallStatus: 'visited' | 'planned' | 'mixed' | 'abandoned'; // FR-029
}
```

**Derivation rules**:
- `overallStatus = 'abandoned'` iff every stop's effective status is `'abandoned'` (FR-029).
- Otherwise: `'visited'` if all non-abandoned stops are visited; `'planned'` if all are planned; `'mixed'` if both.
- `startDate` = earliest non-Substack stop date, or earliest stop date if all Substack (FR-033).
- `endDate` = max of last non-Substack stop date vs. one day before the next non-abandoned region's start (FR-014). Abandoned regions receive no end-date extension.

---

## UI State Types (`src/App.tsx`)

These types model interactive UI state owned by the root component.

### `PlayTripState` *(new — FR-052)*

```ts
type PlayTripState = {
  isPlaying: boolean;
  currentIndex: number;  // index into the non-abandoned regions array (chronological order)
};

type PlayTripAction =
  | { type: 'play' }     // start or restart from currentIndex
  | { type: 'pause' }    // suspend interval; retain currentIndex
  | { type: 'advance' }  // move to next non-abandoned region
  | { type: 'stop' };    // final region reached; reset to ready state (isPlaying: false, currentIndex: 0)
```

**Transition rules** (enforced in reducer):
- `play` from ready state → `isPlaying: true`; index unchanged (restarts from 0 on first play after stop).
- `pause` → `isPlaying: false`; index unchanged.
- `advance` while playing and `currentIndex < lastIndex` → increment index.
- `advance` while playing and `currentIndex === lastIndex` → `stop`.
- `stop` → `isPlaying: false`, `currentIndex: 0`.

**Landing modal dismissed state** is a `boolean` `useState` in `App.tsx`, initialised from `localStorage.getItem('travelogue:landing-dismissed')`. No separate type needed; value is `true` (suppress modal) or `false` (show modal).

---

## Adapter Functions (`src/api/adapters.ts`)

Adapters translate API types to app types. One function per API entity.

| Function | Input | Output |
|---|---|---|
| `adaptPost(stop: ApiStop)` | `ApiStop` | `StopPost` |
| `adaptStop(apiStop: ApiStop)` | `ApiStop` | `Stop` |
| `adaptTrip(apiTrip: ApiTripDetail)` | `ApiTripDetail` | `Trip` |
| `adaptTripSummary(apiTrip: ApiTrip)` | `ApiTrip` | `Trip` (empty stops) |
| `adaptRegion(apiRegion: ApiRegion)` | `ApiRegion` | `Region` *(new)* |

`adaptRegion` maps: `iata_code` → `code`, `airport_name` → `airportName`, `lat`/`lng` → `coords`.

---

## Data Flow

```
GET /trips          → ApiTrip[]      → Trip[] (summaries, empty stops)
GET /trips/:id      → ApiTripDetail  → Trip (full stop list)
GET /regions        → ApiRegion[]    → Region[]

Region[] + Trip → groupStopsByRegion(trip, regions) → RegionGroup[]
RegionGroup[]   → WorldMap, TripFeed, RegionSidebar components
Stop            → StopModal component
```

**No auto-refresh**: Data is fetched once on page load and once per explicit trip switch. A browser reload is required to see new backend data (clarification Q4 2026-06-04).

---

## Effective Status Derivation (FR-028)

```
today_UTC = new Date().toISOString().slice(0, 10)

getEffectiveStopStatus(stop):
  if stop.status === 'planned' && stop.date < today_UTC → 'abandoned'
  else → stop.status
```

This derivation is a pure function with no side effects. The stored `status` field is never mutated.

---

## Notes on `src/data/regions.ts`

The hard-coded `REGIONS` array in `src/data/regions.ts` is **retained** because `scripts/export-seed-data.ts` imports it to seed the database. It must NOT be imported from the React runtime application — all runtime region data comes from `GET /regions` via `useRegions`.
