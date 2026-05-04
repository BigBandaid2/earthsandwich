# Data Model: World Travelogue

## Core Entities

### Trip Itinerary
Represents the full round-the-world route and includes the major stop sequence.

- `id`: string
- `title`: string
- `description`: string
- `stops`: `Stop[]`

### Region
Represents a geographic grouping derived from the nearest international airport. Regions are used for map clustering and navigation, but are not explicit itinerary entries.

- `code`: string  
  International airport code used to identify the region.
- `name`: string  
  Human-readable region label.
- `airportName`: string  
  Full international airport name.
- `country`: string  
  Country where the airport is located.
- `coords`: `{ lat: number; lng: number }`  
  Reference coordinates for the airport or region anchor.

### Stop
Represents a single itinerary entry belonging to a region.

- `id`: string
- `title`: string
- `caption`: string
- `date`: string
- `coords`: `{ lat: number; lng: number }`  
  Geocoded from the stop's location string. Required for map rendering and region assignment.
- `location`: string  
  Human-readable address string (e.g., `"Oaxaca Centro, Mexico"`). Source of truth for geocoding.
- `status`: `"visited" | "planned"`  
  Stored authored status. At render time a derived status of `"abandoned"` is computed for any stop whose stored status is `"planned"` and whose `date` is strictly before today. The stored value is never changed by this derivation.
- `regionCode`: string  
  The nearest international airport code used to derive region membership.
- `regionName?`: string  
  Optional display label for the derived region.
- `image?`: string
- `blog?`: string
- `details?`: string
- `instagramId?`: string  
  Instagram media ID for stops sourced from Instagram posts (e.g., `"17990443415376031"`).
- `shortcode?`: string  
  Instagram shortcode for linking to the source post (e.g., `"C3jXFRlMZoJ"`).

### Planned Post
A stop post type for itinerary entries that have no published content.

- `type`: `"planned"`
- `caption?`: string (optional; a brief note about the stop)

**Constraints**: Planned posts never carry a photo. The parent Stop always has `status: "planned"`. No stop detail pop-up is rendered for Planned stops. In the region sidebar, Planned stop tiles are suppressed whenever any Instagram or Substack stop exists in the same region.

---

### Region assignment
Regions are derived dynamically from each stop’s geocoded coordinates by selecting the nearest international airport.

- Each stop belongs to exactly one region.
- Regions are used for grouping and navigation, not as itinerary entries.
- Stop coordinates are the primary source of truth for region assignment.

### Derived effective status

The `status` field on a Stop is the authored value. The view layer computes an effective status per stop and per region:

- A stop's effective status is `"abandoned"` if its stored status is `"planned"` and `date < today_UTC` (today's date in UTC). Otherwise the effective status equals the stored status.
- A region's overall effective status is `"abandoned"` if every stop in the region is abandoned. Otherwise the region's status is computed from its non-abandoned stops as `visited`, `planned`, or `mixed` of those two.
- Fully-abandoned regions are excluded from the route polyline so segments connect across them, but their markers still render on the map.
- Abandoned regions are also skipped when computing the FR-014 "next region" anchor for date-range extension; their own end date is simply their last stop date (no extension).
- Substack stops are excluded from a region's start/end date computation when any non-Substack stop is present (see FR-033). Substack stops still appear within their region; only their dates are ignored for date-range bounds. If a region contains only Substack stops, those dates are used as a fallback.

## Example stop structure

```ts
const parisStop = {
  id: 'paris',
  title: 'Paris',
  caption: 'City of lights and river views',
  date: '2026-06-17',
  coords: { lat: 48.8566, lng: 2.3522 },
  status: 'visited',
  regionCode: 'CDG',
  regionName: 'Paris Region',
  image: '/images/paris.jpg',
  blog: 'The first full day in Paris was filled with art, food, and city walks.',
};
```

## Data usage

- `src/data/itinerary.ts` will export the flat stop data structure.
- `src/components/MapView.tsx` will render markers from stop coordinates and region anchors.
- `src/components/StopDetail.tsx` will render optional images and blog content when present.
- Regions are computed from stop coordinates and the nearest international airport during display.

## Data Sources

### Miscellaneous Adventures (hard-coded trip)

**Source file**: `posts.tsv` (root of repository)  
**Trip title**: Miscellaneous Adventures  
**Stop count**: 23

This trip is sourced from exported Instagram post data. Each row maps to one Stop as follows:

| TSV column | Stop field | Notes |
|---|---|---|
| `id` | `id` | Used as the Stop identifier |
| `instagram_id` | `instagramId` | Optional; retained for reference |
| `shortcode` | `shortcode` | Optional; used to construct Instagram deep-links |
| `media_url` | `image` | Full CDN URL to the post image |
| `caption` | `caption` | Post caption text |
| `timestamp` | `date` | ISO 8601 timestamp; convert to date string |
| `location` | `location` + `coords` | String address geocoded to `{ lat, lng }` |

**Geocoding requirement**: The `location` column is a human-readable address string with no coordinates. Each stop must be geocoded (once, at build time) to populate `coords`. The geocoded values are committed directly into the TypeScript source file — no runtime geocoding API call is made.

**Output file**: `src/data/miscellaneous-adventures.ts`

---

---

## Earth Sandwich 2015

**Source file**: `travelmap-earth-sandwich.csv` (root of repository)
**Trip title**: Earth Sandwich 2015
**Output file**: `src/data/earth-sandwich-2015.ts`
**Stop count**: 82
**Date range**: July 28, 2015 – August 15, 2016

All stops use the Planned post type. Coordinates are pre-geocoded from city names. The CSV column `city` maps to `location`; `country` is embedded in the location string; `date` (M/D/YYYY) is converted to ISO 8601. One data correction applied: "Sofia, Belarus" corrected to Sofia, Bulgaria.

---

## Earth Club Sandwich 2027

**Source file**: `travelmap-earth-club-sandwich.csv` (root of repository)
**Trip title**: Earth Club Sandwich 2027
**Output file**: `src/data/earth-club-sandwich-2027.ts`
**Stop count**: 30
**Date range**: March 26, 2027 – May 12, 2028

All stops use the Planned post type. Some entries list a country or region name rather than a specific city (e.g., "Japan", "Patagonia"); representative city coordinates are used in these cases. One encoding artifact corrected: "Ür&#mqi" normalized to "Ürümqi, China".

---

## Notes

- Optional fields such as `image` and `blog` allow stops to render without breaking when data is missing.
- The flattened region/stop model avoids nested parent/child structures and uses airport-derived regions for high-level grouping.
- `instagramId` and `shortcode` are only present on stops sourced from Instagram; they are not required for manually entered stops.
