import type { RegionGroup } from '../utils/regionUtils';
import { equirectangularProject, getActiveRegion, isSegmentSolid } from '../utils/regionUtils';
import type { ViewMode } from '../App';

interface WorldMapProps {
  regionGroups: RegionGroup[];
  viewMode: ViewMode;
  activeRegionCode: string | null;
  openStopId: string | null;
  onSelectRegion: (regionCode: string) => void;
  onOpenStop: (stopId: string, contextStopIds: string[]) => void;
}

function WorldMap({
  regionGroups,
  viewMode,
  activeRegionCode,
  openStopId,
  onSelectRegion,
  onOpenStop,
}: WorldMapProps) {
  const activeRegion = getActiveRegion(regionGroups);
  const activeGroup = regionGroups.find((g) => g.region.code === activeRegionCode) ?? null;

  if (viewMode === 'region' && activeGroup) {
    return <RegionMap group={activeGroup} openStopId={openStopId} onOpenStop={onOpenStop} />;
  }

  return (
    <TripMap
      regionGroups={regionGroups}
      activeRegion={activeRegion}
      onSelectRegion={onSelectRegion}
    />
  );
}

// Trip overview map: region markers connected by route line
function TripMap({
  regionGroups,
  activeRegion,
  onSelectRegion,
}: {
  regionGroups: RegionGroup[];
  activeRegion: RegionGroup | null;
  onSelectRegion: (code: string) => void;
}) {
  const routeSegments = regionGroups.slice(0, -1).map((from, i) => {
    const to = regionGroups[i + 1];
    const p1 = equirectangularProject(from.region.coords);
    const p2 = equirectangularProject(to.region.coords);
    return { p1, p2, solid: isSegmentSolid(from, to), key: `${from.region.code}-${to.region.code}` };
  });

  return (
    <div className="map-canvas map-canvas-trip" aria-label="World trip overview map">
      <svg className="map-svg" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        {routeSegments.map((seg) => (
          <line
            key={seg.key}
            x1={seg.p1.x}
            y1={seg.p1.y}
            x2={seg.p2.x}
            y2={seg.p2.y}
            className={`route-segment ${seg.solid ? 'solid' : 'dashed'}`}
            strokeDasharray={seg.solid ? undefined : '0.8 0.6'}
          />
        ))}
      </svg>

      {regionGroups.map((group) => {
        const { x, y } = equirectangularProject(group.region.coords);
        const isActive = activeRegion?.region.code === group.region.code;
        const isVisited = group.overallStatus !== 'planned';

        return (
          <button
            key={group.region.code}
            type="button"
            className={`region-marker ${isVisited ? 'visited' : 'planned'} ${isActive ? 'active-region' : ''}`}
            style={{ left: `${x}%`, top: `${y}%` }}
            aria-label={`${group.region.name}, ${group.region.country}`}
            onClick={() => onSelectRegion(group.region.code)}
          >
            {isActive && <span className="active-pin" aria-hidden="true">📍</span>}
            <span className="region-marker-label">{group.region.name}</span>
          </button>
        );
      })}
    </div>
  );
}

// Region drill-down map: stop markers connected by light dashed route
function RegionMap({
  group,
  openStopId,
  onOpenStop,
}: {
  group: RegionGroup;
  openStopId: string | null;
  onOpenStop: (stopId: string, contextStopIds: string[]) => void;
}) {
  const stopIds = group.stops.map((s) => s.id);

  // Compute bounding box to center the region view
  const lats = group.stops.map((s) => s.coords.lat);
  const lngs = group.stops.map((s) => s.coords.lng);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);

  // Padding in degrees
  const padLat = Math.max((maxLat - minLat) * 0.3, 0.5);
  const padLng = Math.max((maxLng - minLng) * 0.3, 0.5);

  const viewMinLat = minLat - padLat;
  const viewMaxLat = maxLat + padLat;
  const viewMinLng = minLng - padLng;
  const viewMaxLng = maxLng + padLng;

  const projectLocal = (coords: { lat: number; lng: number }) => {
    const x = ((coords.lng - viewMinLng) / (viewMaxLng - viewMinLng)) * 100;
    const y = ((viewMaxLat - coords.lat) / (viewMaxLat - viewMinLat)) * 100;
    return { x, y };
  };

  const routePoints = group.stops
    .map((s) => {
      const { x, y } = projectLocal(s.coords);
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <div className="map-canvas map-canvas-region" aria-label={`${group.region.name} region map`}>
      <svg className="map-svg" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <polyline
          points={routePoints}
          className="region-route-line"
          fill="none"
          stroke="#93c5fd"
          strokeWidth="0.8"
          strokeDasharray="1.5 1"
        />
      </svg>

      {group.stops.map((stop) => {
        const { x, y } = projectLocal(stop.coords);
        const isOpen = stop.id === openStopId;

        return (
          <button
            key={stop.id}
            type="button"
            className={`stop-marker ${stop.status} ${isOpen ? 'open' : ''}`}
            style={{ left: `${x}%`, top: `${y}%` }}
            aria-label={stop.location}
            onClick={() => onOpenStop(stop.id, stopIds)}
          >
            <span className="stop-marker-label">{stop.location.split(',')[0]}</span>
          </button>
        );
      })}
    </div>
  );
}

export default WorldMap;
