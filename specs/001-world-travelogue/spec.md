# Feature Specification: World Travelogue

**Feature Branch**: `001-world-travelogue`
**Created**: 2026-04-22
**Status**: Draft
**Input**: User description: "I am building a travel website that will show the trip itinerary of an upcoming round-the-world trip with roughly 50 major stop. Each stop will have a location, caption, date, image (optional), and long form blog post (optional).

I would like to create a travelogue site that features a world map as a major interactable component, with a sidebar showing itinerary, and expandable components for blurbs, pictures, and travelogue entries. The idea is that there is already an overarching travel plan, and the site will be updated with content throughout the journey. The map can show where the travelers have been so far and where they plan to be in the future. Stops on the trip can have a hierarchical structure, with a high level trip plan showing city to city, and when clicking on a city it zooms into a more detailed city view showing individual sites that have been visited and any pictures or notes associated with them.

There are two types of users who will use the site: One are the travelers themselves, who can update and make adjustments to the itinerary, and post travel content like pictures, short blurbs, and long-from posts. The other is friends and family of the travelers, who can visit the site to see how their travels are going and where they will be. For now, let's just worry about the read-only view of the site and not how to post new content. Assume all content will be hard-coded.

Here is a site online that is already very close to what I am envisioning in presentation format, if you would like to use it as a reference. The main feature it does not have that I want is the ability to designate content as trip level or city level and doing the zoomed in city view. https://clem.travelmap.net/cycling-around-australia"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse trip progress on map (Priority: P1)

Travelers and friends/family open the site to see the current round-the-world itinerary, view visited and planned stops on an interactive world map, and use the sidebar to jump to a stop.

**Why this priority**: This is the core experience that makes the travelogue useful and engaging for both the travelers and their audience.

**Independent Test**: Open the site and verify the world map is visible, stops are plotted, and the sidebar lists major trip stops.

**Acceptance Scenarios**:

1. **Given** the site is loaded, **When** the visitor views the homepage, **Then** the world map shows the overall route with visited and planned stops clearly distinguished.
2. **Given** the site is loaded, **When** the visitor reviews the sidebar, **Then** the sidebar displays the itinerary with location name, caption, and date for each major stop.

---

### User Story 2 - Explore region clusters on zoomed-out map (Priority: P2)

A visitor zooms out on the map and sees nearby stops clustered by dynamically derived regions, where each region is based on the nearest international airport.

**Why this priority**: Region clustering keeps the itinerary legible at continental or country level while preserving the full stop list.

**Independent Test**: Zoom the map out and verify region clusters appear; select a region to see the stops it contains.

**Acceptance Scenarios**:

1. **Given** the visitor is viewing the map at a zoomed-out level, **When** nearby stops are close together, **Then** the stops are grouped into region clusters derived from the nearest international airport.
2. **Given** a region cluster is visible, **When** the visitor selects it, **Then** the interface reveals the stops assigned to that region without altering the underlying flat itinerary.

---

### User Story 3 - Inspect a single stop (Priority: P3)

A visitor clicks on a stop in the itinerary or on the map and sees its details, including location, caption, date, optional image, and optional travelogue entry.

**Why this priority**: Detailed stop summaries are how friends and family connect with the travel story.

**Independent Test**: Click a stop in the itinerary or on the map and confirm the stop detail panel appears with the required fields.

**Acceptance Scenarios**:

1. **Given** a stop is displayed, **When** the visitor selects that stop, **Then** the detail view shows location, caption, date, and any image or long-form blog text available.
2. **Given** a stop has no image or blog post, **When** the visitor opens the detail view, **Then** the page still shows the required fields and gracefully omits the missing optional content.

---

### Edge Cases

- What happens when a stop has only a caption and date but no image or blog post?
- How does the site behave when the itinerary includes roughly 50 stops and the map becomes dense?
- How does the site display a region cluster with multiple stops sharing the same nearest international airport?
- How does the site handle a stop with a very long blog post or caption text?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST display a world map with the round-the-world route and all major stops plotted, distinguishing between visited and planned stops.
- **FR-002**: The system MUST include a sidebar itinerary listing all major stops with location, caption, and date.
- **FR-003**: The system MUST provide a detail view for each stop that includes location, caption, date, optional image, and optional long-form blog content.
- **FR-004**: The system MUST support region clustering derived from each stop’s nearest international airport when the map is zoomed out.
- **FR-005**: The system MUST treat regions as dynamic groupings, not explicit itinerary stops; every stop must belong to one region based on geocoded coordinates.
- **FR-006**: The system MUST allow visitors to select a region cluster and inspect the stops assigned to that region.
- **FR-007**: The system MUST render the site as read-only content for this version, with all itinerary and travel content hard-coded.
- **FR-008**: The system MUST allow visitors to expand or collapse blurbs, pictures, and travelogue entries without requiring content editing.
- **FR-009**: The system MUST gracefully handle stops missing optional images or blog posts by displaying only available content.

### Key Entities *(include if feature involves data)*

- **Trip Itinerary**: Represents the round-the-world journey as a flat sequence of major stops.
- **Stop**: Represents a single itinerary entry with location, caption, date, optional image, optional long-form blog, visited/planned status, and region membership.
- **Region**: Represents a dynamic grouping of nearby stops derived from the nearest international airport; regions are used for clustering on the map and navigation, but are not stored as explicit itinerary entries.
- **Content Panel**: Represents expandable/display components for blurbs, pictures, and long-form journal entries.

## UI Design

**Wireframe reference**: [specs/001-world-travelogue/wireframes/travelogue-wireframes.svg](specs/001-world-travelogue/wireframes/travelogue-wireframes.svg)

The interface has three distinct views that visitors navigate between. Views 1 and 2 share a persistent split layout (map canvas + sidebar); View 3 is a full-page reading layout.

### View 1: Trip Overview (Continent-Level Map)

The main landing page. The screen is split into a map canvas (approximately 72% width) and a chronological trip feed sidebar (approximately 28% width).

**Map canvas**:
- Displays the complete round-the-world route as a dashed line connecting all region markers
- Region markers use a filled gold star for visited regions, an outlined star for planned regions, and a red pulsing circle for the current location
- Floating card in the top-left: trip title with a hamburger menu and share button
- Floating legend in the bottom-left: identifies visited, current, and upcoming marker styles
- Zoom controls (+/−) anchored to the bottom-right

**Trip feed sidebar**:
- Header shows the trip name label, current day counter (e.g., "Day 18 of 60"), and a live status indicator
- Body is a scrollable, reverse-chronological feed; each entry shows:
  - Marker icon (filled gold star for visited, red dot for current)
  - Region or city name and date
  - 1–2 line caption
  - Horizontal strip of photo thumbnails with an overflow count badge (e.g., "+5")
  - "Explore city →" pill button that navigates to the region-level view
- The current stop is labeled "Current stop" and distinguished with a red dot

### View 2: Region-Level Map (City/Region Drill-Down)

Accessed by selecting "Explore city →" from the trip overview. The same split layout is retained but the map is zoomed to show a single region at street level.

**Map canvas**:
- Shows street grid, waterways, and park areas for spatial context
- Stops in the region are represented by numbered circle pins (1, 2, 3…):
  - Visited stops: filled red circles
  - Planned stops: dashed outlined circles
- A dashed red line traces the route between visited stops in order
- Floating card in the top-left: back arrow, "BACK TO TRIP" label, and region/city name
- Bottom-left legend: visited count and planned count for this region

**Region sidebar**:
- Header shows the city/region name, date range, "X of Y sites" progress, and a red horizontal progress bar
- Each stop entry shows sequence number, name, date, caption, and a photo thumbnail strip
- The most recent or current stop is highlighted with a warm-tinted card and a "TODAY" badge; it includes a "Read full entry →" link
- Upcoming planned stops appear below a divider in a muted visual style

### View 3: Stop Detail / Full Post

Accessed by selecting "Read full entry →" from the region view. Full-page reading layout with no map canvas.

**Top navigation bar**:
- Left: "← Back to map" link returning to the trip overview
- Center: trip title
- Right: current day counter

**Main content column** (~61% of page width, centered):
- Breadcrumb navigation showing Trip / Region / Post title
- Article title and subtitle/tagline
- Author name, date, estimated read time, and location label
- Full-width hero image with caption
- Long-form blog body with inline section headings and side-by-side inline image pairs

**Right sidebar** (~15% of page width):
- "MORE FROM [REGION]" section: 2–3 related stop cards, each with thumbnail, title, and read time
- "ON THE MAP" mini-map thumbnail pinpointing the stop's location within the region

**Bottom navigation**:
- Previous stop card (← PREVIOUS) and next stop card (NEXT →), each showing the stop title and date

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Visitors can identify the current itinerary and route on the map within 3 interactions.
- **SC-002**: The site displays at least 50 major stops across the world without losing map clarity or itinerary access.
- **SC-003**: At least 95% of major stops show required location, caption, and date metadata.
- **SC-004**: Visitors can use region clustering and then open a stop detail with no more than two navigation actions.
- **SC-005**: The site shows optional images or blog entries when present and handles missing optional content without layout failure.
- **SC-006**: The map remains legible at country/continental zoom levels through region-based clustering.

## Assumptions

- The initial release is read-only and does not include content editing or posting workflows.
- All itinerary and travel content is hard-coded into the site.
- The site will be delivered as a static web application without server-side dynamic content.
- Region membership is derived dynamically from each stop’s geocoded coordinates and the nearest international airport.
- The target audience is travelers and their friends/family who need a visual and narrative summary of the journey.
- Mobile responsiveness is expected, but the primary focus is the interactive map and itinerary experience on desktop and tablet screens.
