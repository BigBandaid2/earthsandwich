# Feature Specification: World Travelogue

**Feature Branch**: `001-world-travelogue`
**Created**: 2026-04-22
**Updated**: 2026-05-08
**Status**: Draft
**Input**: User description: "I am building a travel website that will show the trip itinerary of an upcoming round-the-world trip with roughly 50 major stop. Each stop will have a location, caption, date, image (optional), and long form blog post (optional).

I would like to create a travelogue site that features a world map as a major interactable component, with a sidebar showing itinerary, and expandable components for blurbs, pictures, and travelogue entries. The idea is that there is already an overarching travel plan, and the site will be updated with content throughout the journey. The map can show where the travelers have been so far and where they plan to be in the future. Stops on the trip can have a hierarchical structure, with a high level trip plan showing city to city, and when clicking on a city it zooms into a more detailed city view showing individual sites that have been visited and any pictures or notes associated with them.

There are two types of users who will use the site: One are the travelers themselves, who can update and make adjustments to the itinerary, and post travel content like pictures, short blurbs, and long-from posts. The other is friends and family of the travelers, who can visit the site to see how their travels are going and where they will be. For now, let's just worry about the read-only view of the site and not how to post new content. Assume all content will be hard-coded.

Here is a site online that is already very close to what I am envisioning in presentation format, if you would like to use it as a reference. The main feature it does not have that I want is the ability to designate content as trip level or city level and doing the zoomed in city view. https://clem.travelmap.net/cycling-around-australia"

## Clarifications

### Session 2026-05-01

- Q: Timezone basis for the "is the stop's date in the past?" comparison that derives `abandoned` (FR-028) → A: UTC — the comparison uses the current UTC date so classification is identical for every visitor regardless of timezone.
- Q: Should abandoned stop tiles be suppressed from the region sidebar when the same region also contains Instagram or Substack stops (mirroring FR-018's behavior for planned tiles)? → A: Yes — abandoned tiles follow the same suppression rule as planned tiles (FR-018 extended to abandoned).
- Q: Display order of the trip feed sidebar's three status sections (FR-031)? → A: Visited (top) → Planned (middle) → Abandoned (bottom).
- Q: Visual treatment of abandoned stops and regions (FR-029, FR-030)? → A: Strike-through location/region name + faded grey color + dashed connector dot. Abandoned stops/regions render with NO connector line (vertical or horizontal) joining them to any neighbor — they stand alone in the sidebar list and have no polyline edge on the map.
- Q: For FR-014 region end-date computation, what is the "next region" when the immediate next region is abandoned? → A: Use the next non-abandoned region as the anchor (skip abandoned regions for date-range purposes, matching the route-line skip in FR-030). An abandoned region's own end date is just its last stop date (no extension).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse trip progress on map (Priority: P1)

Travelers and friends/family open the site to see the current round-the-world itinerary, view visited and planned regions on an interactive world map, and use the sidebar to jump to a region.

**Why this priority**: This is the core experience that makes the travelogue useful and engaging for both the travelers and their audience.

**Independent Test**: Open the site and verify the world map is visible, region markers are plotted, and the sidebar lists regions grouped by visited/planned status.

**Acceptance Scenarios**:

1. **Given** the site is loaded, **When** the visitor views the homepage, **Then** the world map shows the overall route with visited and planned regions clearly distinguished, and the active region (if any) is visually called out.
2. **Given** the site is loaded, **When** the visitor reviews the sidebar, **Then** the sidebar displays regions grouped into "Visited" and "Planned" sections with region name, country, and date range for each.

---

### User Story 2 - Explore a region's stops (Priority: P2)

A visitor selects a region from the trip overview to see all stops within that region on a zoomed map, and uses the region sidebar to browse individual stop posts.

**Why this priority**: Region drill-down is the primary path from the high-level trip view to individual travel content, making it the key navigation layer between overview and stop detail.

**Independent Test**: From the trip overview, click "Expand Region →" on any region tile and confirm the map zooms to that region's stops, the sidebar switches to region-level view, and individual stop posts are accessible.

**Acceptance Scenarios**:

1. **Given** the trip overview is displayed, **When** the visitor clicks "Expand Region →" on a region tile, **Then** the map shows only that region's stops and the sidebar shows that region's stop posts.
2. **Given** the region view is displayed, **When** the visitor clicks on a different region's collapsed header in the sidebar, **Then** that region becomes active, the map re-focuses to it, and the previous region collapses.

---

### User Story 3 - Inspect a single stop (Priority: P3)

A visitor opens a stop post and sees its full content: an Instagram post shows the photo and caption, while a Substack post shows the article title and long-form text.

**Why this priority**: Individual stop content is how friends and family connect with the travel story.

**Independent Test**: Click a stop post tile in the region sidebar and confirm the detail pop-up opens with all expected content fields for that post type.

**Acceptance Scenarios**:

1. **Given** a stop is visible in the sidebar, **When** the visitor clicks the stop tile, **Then** the detail pop-up appears showing all available fields for that post type.
2. **Given** a stop has no optional content (no image or no long-form text), **When** the visitor opens the detail pop-up, **Then** the required fields display and the missing optional fields are omitted gracefully.

---

### User Story 4 - View a planned-only itinerary (Priority: P3)

A visitor viewing a trip whose stops have no photo or article content (only location, date, and optional caption) can still see the full route on the map and browse stop tiles in the region view, getting a preview of the journey without rich media.

**Why this priority**: Planned stops are necessary for trips that have a defined itinerary but no published Instagram or Substack content. They provide route context without requiring photos or articles.

**Independent Test**: Load a trip where all stops are of the Planned type. Verify the route appears on the map, planned stop tiles appear in the region sidebar (since no other stop types exist in those regions), and clicking a planned stop does not open a detail pop-up.

**Acceptance Scenarios**:

1. **Given** a region that contains only Planned stops, **When** the visitor drills into that region, **Then** the Planned stop tiles are shown in the region sidebar with location, date, and optional caption.
2. **Given** a region that contains at least one Instagram or Substack stop, **When** the visitor drills into that region, **Then** no Planned stop tiles are shown in the region sidebar.
3. **Given** a visitor clicks a Planned stop marker on the map or a Planned stop tile in the sidebar, **When** the click event fires, **Then** no stop detail pop-up opens.

---

### User Story 5 - See abandoned plans alongside the active itinerary (Priority: P3)

A visitor viewing a trip can see stops that were planned but never visited (their planned date is in the past) called out separately as "abandoned". These stops still appear on the map and in the sidebar so the visitor sees the original intention, but they are visually disconnected from the active route — no line is drawn between an abandoned stop and its neighbors.

**Why this priority**: Real itineraries shift. Plans get dropped — destinations skipped, side trips canceled. Showing abandoned stops preserves a faithful record of what was planned versus what actually happened, without distorting the route line through places the travelers did not go.

**Independent Test**: Load a trip that contains at least one planned stop with a past date. Confirm the stop is labeled as abandoned (its status displays as "abandoned") in the sidebar under a dedicated "Abandoned" section, the stop's region marker still appears on the map, and the route line skips over the abandoned region rather than detouring through it.

**Acceptance Scenarios**:

1. **Given** a trip contains a stop with `status: "planned"` whose date is earlier than today, **When** the trip is rendered, **Then** that stop's effective status is "abandoned" and it is grouped under an "Abandoned" sidebar section separate from "Visited" and "Planned".
2. **Given** an abandoned stop sits sequentially between two non-abandoned stops in the trip, **When** the route line is drawn, **Then** the line connects the two non-abandoned stops directly and does not connect to or pass through the abandoned stop's region.
3. **Given** an abandoned region is shown on the map, **When** the visitor expands the region, **Then** the abandoned stops appear in the region sidebar with their location, date, and optional caption, and (consistent with planned stops) clicking them does not open a stop detail pop-up.

---

> **Data ingestion moved**: All ingestion-related user stories, requirements, and edge cases have been moved to [specs/002-data-ingestion/spec.md](../002-data-ingestion/spec.md).

### Edge Cases

- What happens when a stop has only a caption and date but no image or blog post?
- How does the site behave when the itinerary includes roughly 50 stops and the map becomes dense?
- How does the site display a region that contains a mix of Instagram and Substack posts?
- How does the site handle a stop with a very long caption or article body?
- What does the sidebar show when a trip has no visited stops at all (all planned)?
- How is the active region determined when the last visited region is not the final region in the sequence?
- How is the region end date calculated for the last region in a trip, which has no subsequent region?
- What happens if a trip contains only one region?
- What happens when a visitor opens the stop detail pop-up and navigates past the first or last stop?
- What does the trip overview sidebar show for a region whose stops are all of the Planned type? (No Instagram thumbnails or Substack tiles — just the region header, date range, and Expand button.)
- How does the site behave when a trip spans more than 80 stops across 60+ regions?
- What happens to a region whose stops are a mix of abandoned and non-abandoned? (The region is grouped under whichever non-abandoned status applies; only fully-abandoned regions are hoisted into the "Abandoned" sidebar section, and only fully-abandoned regions are skipped by the route line.)
- What happens to a planned stop whose date is exactly today? (Today is not "in the past" — the stop remains "planned".)
- What happens when a Substack post is dated months after the actual visit? (The Substack stop still appears in its region, but its date does not pull the region's date range forward — see FR-033.)
- What happens when a region contains only Substack stops and no Instagram/Planned/Abandoned stops? (The region falls back to using the Substack dates for its date range, since no other dates are available.)
## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST display an interactive world map showing the full trip route and one region marker per region, distinguishing visually between visited and planned regions.
- **FR-002**: The system MUST include a trip feed sidebar that groups regions into two collapsible sections — "Visited" and "Planned". If all regions in the trip share the same status, only that section is shown.
- **FR-003**: The system MUST provide a stop detail pop-up whose content and layout depend on post type: Instagram posts display location, photo, and caption; Substack posts display title, subtitle, and long-form article body.
- **FR-004**: The system MUST group stops into regions derived from the nearest international airport and show one region marker per region on the world map rather than individual stop markers.
- **FR-005**: The system MUST treat regions as dynamic groupings computed from stop coordinates; they are not explicit itinerary entries and carry no separately stored content.
- **FR-006**: The system MUST allow visitors to navigate from the trip overview to a region-level view by selecting a region tile, where they can browse individual stop posts on a zoomed map.
- **FR-007**: The system MUST render the site as read-only; all content is hard-coded and no visitor input is saved.
- **FR-008**: The system MUST allow visitors to expand and collapse region sections in the trip feed without leaving the current view.
- **FR-009**: The system MUST gracefully handle stops with missing optional content by displaying only the fields that are present.
- **FR-010**: The system MUST support multiple trip itineraries and show the most recent trip by default on page load. The trip selector list MUST display all available itineraries in reverse chronological order, sorted by the date of each trip's earliest stop. Visitors MUST be able to switch between trips by selecting from this list.
- **FR-011**: The system MUST determine the "active region" of a trip as the last region in sequence that contains at least one visited stop. If all regions are visited or none are visited, no active region is designated.
- **FR-012**: The system MUST render the route line between regions as a solid line for any segment where at least one adjacent region has visited stops, and as a dashed line for segments where both adjacent regions have only planned stops.
- **FR-013**: The system MUST support three stop post types — Instagram (photo, caption, location, date), Substack (title, subtitle, long-form text), and Planned (location, date, optional caption, no photo). Each type has a distinct data shape and display format.
- **FR-014**: The system MUST calculate a region's date range as: start date = date of the first non-Substack stop in the region; end date = the later of (date of the last non-Substack stop in the region) or (one day before the first non-Substack stop of the next non-abandoned region in the trip sequence). Abandoned regions are skipped when locating the "next region" anchor (consistent with FR-030's route-line skip). An abandoned region itself receives no end-date extension — its end date is simply the date of its last stop. Substack stop dates are excluded from this computation (see FR-033). If a region contains only Substack stops, its date range falls back to those Substack stops' dates.
- **FR-015**: The system MUST enforce that only one region is active at a time in the region view; activating a new region collapses the previously active one and re-centers the map on the newly active region's stops.
- **FR-016**: The system MUST allow visitors to open the stop detail pop-up from any of these entry points: an Instagram photo thumbnail in the trip overview sidebar, an Instagram or Substack content tile in the region sidebar, or a stop marker on the region map.
- **FR-017**: Planned stops MUST always carry `status: "planned"` and never carry a photo. An optional caption field may provide brief context for the stop.
- **FR-018**: The system MUST suppress Planned and Abandoned stop tiles from the region sidebar when any Instagram or Substack stop exists in the same region. If a region contains only Planned and/or Abandoned stops, those tiles MUST be shown.
- **FR-019**: The system MUST NOT open a stop detail pop-up when a visitor clicks a Planned stop marker or tile; clicking a Planned stop takes no action.
- **FR-020**: The system MUST include hard-coded itinerary data for two additional trips: "Earth Sandwich 2015" (82 stops, July 2015 – August 2016) and "Earth Club Sandwich 2027" (30 stops, March 2027 – May 2028). All stops in both trips use the Planned post type.
- **FR-021**: The trip overview sidebar region tile MUST omit the Instagram thumbnail row and Substack tile row for regions that contain only Planned stops, showing only the region header, date range, and "Expand Region →" button.
- **FR-022**: Both the trip feed sidebar (View 1) and the region sidebar (View 2) MUST be independently scrollable with a visible scrollbar that is clearly distinguishable against the sidebar background.
- **FR-023**: When a region becomes the active region in the region view (either by drilling in from the trip overview or by selecting another region's collapsed header), the region sidebar MUST scroll so that the newly active region's header is positioned as close to the top of the sidebar as possible, keeping its expanded stop list visible below.
- **FR-024**: Both the trip feed sidebar (View 1) and the region sidebar (View 2) MUST share the same fixed pixel width, sized to fit four 60px Instagram thumbnails with 4px gaps plus the connector column and feed padding in a single row. Below the mobile breakpoint (≤768px) the sidebar continues to stack under the map and span full width per existing responsive rules.
- **FR-025**: Instagram images in the region sidebar stop tile (View 2) and in the stop detail pop-up (View 3) MUST render at their original aspect ratio. No fixed crop height or `object-fit: cover` cropping is applied.
- **FR-026**: The stop detail pop-up (View 3) MUST occupy most of the screen height (up to 95vh) and MUST never trigger vertical scrolling caused by the Instagram hero image. If a portrait image would exceed the available vertical space, its rendered width MUST shrink (preserving aspect ratio) until both image and surrounding text fit within the modal without scrolling. Long-form Substack body text MAY still scroll inside the modal.
- **FR-027**: Each trip itinerary MUST have its own shareable URL of the form `#/trip/{tripId}` where `{tripId}` is the trip's stable id (e.g. `earth-sandwich-2015`). On page load the system MUST read this hash and activate the matching trip; if no hash is present or the id is unknown, the default trip (most recent by start date) is shown. Switching trips via the selector MUST update the URL hash, and browser back/forward navigation MUST switch between trips accordingly. The implementation MUST use the URL hash (not History API path routing) so that the site remains a fully static SPA without server-side rewrites.
- **FR-028**: The system MUST recognize a third stop status, "abandoned", in addition to "visited" and "planned". A stop's effective status is derived: any stop authored with `status: "planned"` whose `date` is strictly before the current UTC date (today's date in UTC, computed at render time) is treated as "abandoned". Using UTC ensures every visitor classifies the same stop identically regardless of their local timezone. Stops authored as `"visited"` are never reclassified. The underlying stop data continues to carry only `"visited"` or `"planned"`; the "abandoned" classification is a derived, time-dependent view layer.
- **FR-029**: A region's overall status MUST extend to include "abandoned". A region is "abandoned" if all of its stops are abandoned. A region with any non-abandoned stop retains its previous classification (visited / planned / mixed of those two), with abandoned stops within it ignored for the purpose of choosing visited-vs-planned status.
- **FR-030**: The route line connecting regions MUST skip fully-abandoned regions entirely: the polyline is drawn over the sequence of non-abandoned regions only, so two non-abandoned regions on either side of an abandoned region connect directly to each other. Abandoned region markers MUST still appear on the map (so the visitor sees the abandoned plan), but they are not endpoints of any segment. In the sidebar, abandoned region tiles and abandoned stop tiles MUST omit the vertical connector line that joins adjacent tiles — abandoned items stand visually disconnected from the rest of the itinerary on every surface (map polyline, sidebar connector, region drill-down stop list).
- **FR-031**: The trip feed sidebar MUST add a third collapsible section, "Abandoned", to the existing "Visited" and "Planned" sections. The three sections are rendered in a fixed top-to-bottom order: Visited → Planned → Abandoned. Fully-abandoned regions are listed in the Abandoned section and are excluded from the Visited and Planned sections. Sections that contain no regions for the current trip remain hidden (consistent with FR-002).
- **FR-032**: Abandoned stops MUST follow the same interaction and suppression rules as Planned stops: clicking an abandoned stop marker on the map or an abandoned stop tile in the sidebar MUST NOT open the stop detail pop-up; and abandoned stop tiles MUST be suppressed from the region sidebar whenever any Instagram or Substack stop exists in the same region (per FR-018). When shown, abandoned stop tiles display location, date, and optional caption.
- **FR-033**: The system MUST exclude Substack stop dates from a region's start-date and end-date computation (FR-014) when the region contains any non-Substack stop. Rationale: Substack articles are typically authored after the visit, so their dates represent publication, not presence. The Substack stop itself MUST still appear within the region (on the map and in the region sidebar); only its date is excluded from the date-range bounds. If a region contains only Substack stops, the system falls back to those stops' dates so the region still displays a date range.
> **Ingestion requirements FR-034 to FR-041 moved to [specs/002-data-ingestion/spec.md](../002-data-ingestion/spec.md).**

### Key Entities *(include if feature involves data)*

- **Trip Itinerary**: A named journey composed of an ordered sequence of stops. Multiple itineraries coexist in the site; the most recent by date is shown by default. Each itinerary has a title, description, and an ordered list of stops.
- **Stop**: A single itinerary entry belonging to exactly one region. Each stop has a date, location string, geocoded coordinates, a stored status (visited or planned), and a post type (Instagram, Substack, or Planned). At render time a third effective status, "abandoned", is derived for any planned stop whose date has passed (see FR-028).
- **Instagram Post**: A stop post type sourced from an Instagram post. Always carries `status: "visited"`. Contains: photo URL, caption text, location string, and timestamp. Identified by Instagram media ID and shortcode.
- **Substack Post**: A stop post type sourced from a Substack article. Always carries `status: "visited"`. Contains: title, subtitle, and long-form body text. Note: a Substack stop's `date` represents the article's publication date and is typically later than the actual visit; it is therefore excluded from region date-range computation (see FR-033).
- **Planned Post**: A stop post type representing a planned itinerary entry with no published content. Always carries `status: "planned"`. Contains: location, date, and an optional caption. Has no photo and no detail pop-up.
- **Region**: A dynamic grouping of nearby stops derived from the nearest international airport. Computed from stop coordinates at build time; not stored as an explicit entity. Characterized by an airport code, region name, country, and reference coordinates. Date range is derived from the region's stops and the subsequent region's start date (see FR-014). A region's overall status is one of visited, planned, mixed, or abandoned (see FR-029).
## UI Design

**Wireframe reference**: [specs/001-world-travelogue/wireframes/travelogue-wireframes.svg](specs/001-world-travelogue/wireframes/travelogue-wireframes.svg)

The interface has three distinct views. Views 1 and 2 share a persistent split layout (map canvas + sidebar). View 3 is a modal pop-up overlay over whichever view is current.

### View 1: Trip Overview (Continent-Level Map)

The main landing page. Screen splits into a map canvas (~72% width) on the left and a trip feed sidebar (~28% width) on the right.

**Map canvas**:
- Shows the trip route as a line connecting region markers. Visited segments render as a solid line; planned segments render as a dashed line (see FR-012).
- Each region uses a large filled dot as its marker. The active region uses a teardrop location pin in red.
- Floating card top-left: trip title and hamburger icon. Clicking the hamburger opens a trip selector list.
- Zoom controls anchored bottom-right.
- At this zoom level the map shows city labels and geopolitical boundaries only; road and terrain detail is hidden.

**Trip feed sidebar**:
- Two collapsible sections with headers: "Visited" (above) and "Planned" (below). Sections irrelevant to the current trip are hidden (see FR-002).
- Within each section, region tiles are listed in reverse-chronological order with no border between tiles.
- Each region tile contains:
  - Marker icon matching the map dot, connected to adjacent tiles by a vertical line (solid or dashed, mirroring the route logic).
  - Region name, country, start date, and end date.
  - A horizontal row of up to four Instagram photo thumbnails; if more than four exist, a "+X" overlay appears on the fourth.
  - Up to four Substack post tiles, each showing a small Substack icon, post title, and a 3-line text preview; if more than four exist, a "+X" overlay appears on the fourth.
  - "Expand Region →" pill button at the bottom of the tile.

### View 2: Region-Level Map (Region Drill-Down)

Accessed by selecting "Expand Region →" from the trip overview. Same split layout; map zooms to the selected region.

**Map canvas**:
- Shows full map detail: roads, terrain, waterways, and parks.
- Each stop in the region is shown as a standard dot marker.
- A dashed light-blue route line connects stops in chronological order.
- Floating card top-left: back arrow and "BACK TO TRIP" label.

**Region sidebar**:
- Regions are listed in reverse-chronological order (most recent first), matching the trip overview sidebar ordering.
- The active region is expanded: its header shows region name and date range, followed by its stop tiles in reverse-chronological order.
- All other regions in the trip appear as collapsed header rows above and below the active region; clicking a header activates that region (see FR-015).
- The sidebar scrolls so the active region's header is anchored near the top whenever the active region changes (see FR-023).
- The sidebar uses its own visible scrollbar independent from the map pane (see FR-022).
- Each stop tile shows:
  - Marker icon with a vertical connector line between adjacent tiles.
  - Region name, country, and date.
  - **Instagram stop tile**: small Instagram icon, caption text (up to 3 lines with ellipsis if longer), and the Instagram photo below the caption rendered full-width at its original aspect ratio (square, portrait, or landscape — no cropping; see FR-025).
  - **Substack stop tile**: small Substack icon, post title, and a 3-line text preview.
  - **Planned stop tile**: shown only when the region has no Instagram or Substack stops (see FR-018). Displays location and date; caption shown if present. No clickable action.

### View 3: Stop Detail Pop-Up

Opens as a modal overlay that dims the background and occupies approximately 80% of the screen width and most of the screen height (up to 95vh). Entry points are defined in FR-016.

**Overlay dim area**:
- Left side: left-arrow button at vertical mid-point to navigate to the previous stop post.
- Right side: right-arrow button at vertical mid-point to navigate to the next stop post. X button at the top-right to close.

**Main content area**:
- Breadcrumb navigation: Trip / Region / Location · Date.
- **Instagram post layout**: location as heading, caption as subheading, hero image below rendered at its original aspect ratio. The image is sized to fit within the modal without ever causing vertical scroll — if too tall, its rendered width shrinks to keep the image height within the available space (see FR-026).
- **Substack post layout**: article title as heading, subtitle as subheading, long-form body text with inline section headings below.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Visitors can identify the current trip's route and active region on the map within 3 interactions.
- **SC-002**: The site displays all stops across the world without losing map clarity or sidebar usability.
- **SC-003**: At least 95% of stops display their required location and date metadata.
- **SC-004**: Visitors can navigate from the trip overview to a stop's full detail in no more than two interactions.
- **SC-005**: The site handles stops with missing optional content without layout failure.
- **SC-006**: The map remains legible at trip level by showing region markers rather than individual stop markers.
- **SC-007**: Visitors can switch between multiple trip itineraries without a page reload.
- **SC-008**: All 82 Earth Sandwich 2015 stops and all 30 Earth Club Sandwich 2027 stops are present in the data and render on the map without errors.
- **SC-009**: In any region that mixes Planned stops with Instagram or Substack stops, zero Planned stop tiles appear in the region sidebar.

## Assumptions

- The initial release is read-only; content editing and posting workflows are out of scope.
- All itinerary and travel content is hard-coded into the site at build time.
- The site is delivered as a static web application without server-side dynamic content.
- Region membership is pre-computed from stop coordinates at build time; no runtime geocoding is performed.
- Content sources are Instagram (photo posts), Substack (article posts), and Planned (itinerary entries with no rich content). Other content platforms are out of scope for this version.
- The Earth Sandwich 2015 trip (July 2015 – August 2016) is a completed trip represented entirely with Planned stops, as no Instagram or Substack content has been attached to those itinerary entries.
- The Earth Club Sandwich 2027 trip (March 2027 – May 2028) is a future trip represented entirely with Planned stops.
- Planned stop coordinates are pre-geocoded at build time using well-known city coordinates; no runtime geocoding is performed.
- The "Sofia, Belarus" entry in the Earth Sandwich 2015 CSV is a data error; the correct location is Sofia, Bulgaria.
- The target audience is travelers and their friends and family.
- Mobile responsiveness is expected, but desktop and tablet are the primary target.
- The map component is provided by a third-party mapping service; zoom behavior, map detail levels, and marker rendering are constrained by that service's capabilities.
- The active region concept (FR-011) is only meaningful for trips with a mix of visited and planned regions.
- Data ingestion, database, backend API, and containerization assumptions are documented in [specs/002-data-ingestion/spec.md](../002-data-ingestion/spec.md).
