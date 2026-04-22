# Research: World Travelogue

## Decision
Implement the travelogue as a static Vite + React application with hard-coded itinerary data. The map experience will be built using Google Maps platform.

## Rationale
- Vite + React provides a fast developer experience and a clean way to manage interactive UI state for map selection, sidebar navigation, and expandable stop details.
- A static build satisfies the requirement for no databases and hard-coded mock content.
- Google Maps is popular and affordable for small projects without large scale traffic.

## Alternatives considered
- Plain static HTML/CSS/JS without React
  - Rejected because the requested UI behavior and hierarchical interactivity are easier to manage in React.
- SVG lightweight maps
  - Rejected because Google Maps is fine.
- Backend or database-driven content
  - Rejected because the feature explicitly requires no databases and all content should be hard-coded for this version.
- Server-side rendering / dynamic site generation
  - Rejected because the initial scope is a read-only static travelogue.
