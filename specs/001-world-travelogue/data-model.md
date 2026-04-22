# Data Model: World Travelogue

## Core Entities

### Trip Itinerary
Represents the full round-the-world route and includes the major stop sequence.

- `id`: string
- `title`: string
- `description`: string
- `stops`: `Stop[]`

### Stop
Represents a major itinerary entry or city-level element.

- `id`: string
- `type`: `"trip" | "city" | "site"`
- `title`: string
- `caption`: string
- `date`: string
- `coords`: `{ lat: number; lng: number }`
- `status`: `"visited" | "planned"`
- `image?`: string
- `blog?`: string
- `details?`: `string`
- `children?`: `Stop[]`  
  Used for city-level drilldown where a city stop includes nested site-level entries.

### City-Level Drilldown
City stops are hierarchical nodes with a nested `children` array of local sites.

- `type = "city"`
- `children`: `Stop[]`
- `children` entries typically use `type = "site"`

## Example stop structure

```ts
const tokyo: Stop = {
  id: 'tokyo',
  type: 'city',
  title: 'Tokyo',
  caption: 'Arrival in Tokyo and city highlights',
  date: '2026-07-10',
  coords: { lat: 35.6895, lng: 139.6917 },
  status: 'planned',
  image: '/images/tokyo.jpg',
  blog: 'Landing in Tokyo and exploring local culture.',
  children: [
    {
      id: 'sensoji',
      type: 'site',
      title: 'Senso-ji Temple',
      caption: 'Historic temple visit in Asakusa',
      date: '2026-07-11',
      coords: { lat: 35.7148, lng: 139.7967 },
      status: 'planned',
      image: '/images/sensoji.jpg',
      blog: 'A peaceful morning at one of Tokyo’s oldest temples.',
    },
  ],
};
```

## Data usage

- `src/data/itinerary.ts` will export the itinerary data structure.
- `src/components/MapView.tsx` will render markers from the stop coordinate data.
- `src/components/StopDetail.tsx` will render optional images and blog content when present.

## Notes

- Optional fields such as `image` and `blog` allow stops to render without breaking when data is missing.
- The hierarchical `children` field enables zoomed-in city views while keeping the top-level route intact.
