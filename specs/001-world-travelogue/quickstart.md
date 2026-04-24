# Quickstart: World Travelogue

## Setup

1. Install project dependencies:

```bash
npm install
```

2. Start the local development server:

```bash
npm run dev
```

## Run locally

Open the local development URL shown in the terminal, typically `http://localhost:5173`.

## Build for production

```bash
npm run build
```

## Preview the production build

```bash
npm run preview
```

## Notes

- All itinerary content is hard-coded in `src/data/itinerary.ts`.
- The interactive world map is planned to use the Google Maps JavaScript API in `src/components/MapView.tsx`.
- `src/components/Sidebar.tsx` and `src/components/StopDetail.tsx` provide itinerary and stop detail interactions.
- Future geocoding may leverage Google Location Search for stop lookup and location search features.
- Use `specs/001-world-travelogue/data-model.md` for the data shape and `specs/001-world-travelogue/research.md` for design decisions.
