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
- **FR-010**: The system MUST support multiple trip itineraries and show the most recent trip by default on page load; visitors MUST be able to switch between trips.
- **FR-011**: The system MUST determine the "active region" of a trip as the last region in sequence that contains at least one visited stop. If all regions are visited or none are visited, no active region is designated.
- **FR-012**: The system MUST render the route line between regions as a solid line for any segment where at least one adjacent region has visited stops, and as a dashed line for segments where both adjacent regions have only planned stops.
- **FR-013**: The system MUST support two stop post types — Instagram (photo, caption, location, date) and Substack (title, subtitle, long-form text). Each type has a distinct data shape and display format.
- **FR-014**: The system MUST calculate a region's date range as: start date = date of the first stop in the region; end date = the later of (date of the last stop in the region) or (one day before the first stop of the next region in the trip sequence).
- **FR-015**: The system MUST enforce that only one region is active at a time in the region view; activating a new region collapses the previously active one and re-centers the map on the newly active region's stops.
- **FR-016**: The system MUST allow visitors to open the stop detail pop-up from any of these entry points: an Instagram photo thumbnail in the trip overview sidebar, an Instagram or Substack content tile in the region sidebar, or a stop marker on the region map.

### Key Entities *(include if feature involves data)*

- **Trip Itinerary**: A named journey composed of an ordered sequence of stops. Multiple itineraries coexist in the site; the most recent by date is shown by default. Each itinerary has a title, description, and an ordered list of stops.
- **Stop**: A single itinerary entry belonging to exactly one region. Each stop has a date, location string, geocoded coordinates, visited/planned status, and a post type (Instagram or Substack).
- **Instagram Post**: A stop post type sourced from an Instagram post. Contains: photo URL, caption text, location string, and timestamp. Identified by Instagram media ID and shortcode.
- **Substack Post**: A stop post type sourced from a Substack article. Contains: title, subtitle, and long-form body text.
- **Region**: A dynamic grouping of nearby stops derived from the nearest international airport. Computed from stop coordinates at build time; not stored as an explicit entity. Characterized by an airport code, region name, country, and reference coordinates. Date range is derived from the region's stops and the subsequent region's start date (see FR-014).

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
- The active region is expanded: its header shows region name and date range, followed by its stop tiles in reverse-chronological order.
- All other regions in the trip appear as collapsed header rows below; clicking a header activates that region (see FR-015).
- Each stop tile shows:
  - Marker icon with a vertical connector line between adjacent tiles.
  - Region name, country, and date.
  - **Instagram stop tile**: small Instagram icon, caption text (up to 3 lines with ellipsis if longer), and a single full-width photo below the caption.
  - **Substack stop tile**: small Substack icon, post title, and a 3-line text preview.

### View 3: Stop Detail Pop-Up

Opens as a modal overlay that dims the background and occupies approximately 80% of the screen width. Entry points are defined in FR-016.

**Overlay dim area**:
- Left side: left-arrow button at vertical mid-point to navigate to the previous stop post.
- Right side: right-arrow button at vertical mid-point to navigate to the next stop post. X button at the top-right to close.

**Main content area**:
- Breadcrumb navigation: Trip / Region / Location · Date.
- **Instagram post layout**: location as heading, caption as subheading, hero image below.
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

## Assumptions

- The initial release is read-only; content editing and posting workflows are out of scope.
- All itinerary and travel content is hard-coded into the site at build time.
- The site is delivered as a static web application without server-side dynamic content.
- Region membership is pre-computed from stop coordinates at build time; no runtime geocoding is performed.
- Content sources are Instagram (photo posts) and Substack (article posts); other content platforms are out of scope for this version.
- The target audience is travelers and their friends and family.
- Mobile responsiveness is expected, but desktop and tablet are the primary target.
- The map component is provided by a third-party mapping service; zoom behavior, map detail levels, and marker rendering are constrained by that service's capabilities.
- The active region concept (FR-011) is only meaningful for trips with a mix of visited and planned regions.
