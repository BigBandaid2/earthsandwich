# Earth Sandwich Travelogue

A static Vite React travelogue website for a round-the-world itinerary. The application renders a read-only map experience with itinerary stops, optional city drilldown, and expandable travel detail panels.

## Run locally

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Preview

```bash
npm run preview
```

## Notes

- All itinerary content is hard-coded in `src/data/itinerary.ts`.
- The project is designed as a static site with no database or server-side rendering.
- The world map experience is planned to use the Google Maps JavaScript API, with future geocoding via Google Location Search.
