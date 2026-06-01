import { useEffect, useMemo } from 'react';
import { Map, AdvancedMarker, Pin, useMap, useMapsLibrary } from '@vis.gl/react-google-maps';
import type { RegionGroup } from '../utils/regionUtils';
import { getActiveRegion, getRoutedGroups, isSegmentSolid } from '../utils/regionUtils';
import type { ViewMode } from '../App';
import type { Stop } from '../data/types';

const MAP_ID = import.meta.env.VITE_GOOGLE_MAPS_MAP_ID as string | undefined;

interface WorldMapProps {
  regionGroups: RegionGroup[];
  viewMode: ViewMode;
  activeRegionCode: string | null;
  openStopId: string | null;
  onSelectRegion: (regionCode: string) => void;
  onOpenStop: (stopId: string, contextStopIds: string[]) => void;
}

// Renders a geodesic polyline. Solid or dashed, using the imperative Maps API.
function MapPolyline({
  path,
  solid,
  strokeColor,
  strokeWeight = 2.5,
}: {
  path: Array<{ lat: number; lng: number }>;
  solid: boolean;
  strokeColor: string;
  strokeWeight?: number;
}) {
  const map = useMap();
  const mapsLib = useMapsLibrary('maps');

  useEffect(() => {
    if (!map || !mapsLib) return;

    const polyline = new mapsLib.Polyline({
      map,
      path,
      geodesic: true,
      ...(solid
        ? { strokeColor, strokeOpacity: 1.0, strokeWeight }
        : {
            strokeOpacity: 0,
            icons: [
              {
                icon: {
                  path: 'M 0,-1 0,1',
                  strokeOpacity: 1,
                  strokeWeight: 2,
                  strokeColor,
                  scale: strokeWeight,
                },
                offset: '0',
                repeat: '12px',
              },
            ],
          }),
    });

    return () => polyline.setMap(null);
  }, [map, mapsLib, path, solid, strokeColor, strokeWeight]);

  return null;
}

// Fits the map viewport to a set of coordinates once the map and library are ready.
function FitBounds({
  coords,
  padding = 60,
}: {
  coords: Array<{ lat: number; lng: number }>;
  padding?: number;
}) {
  const map = useMap();
  const mapsLib = useMapsLibrary('maps');

  useEffect(() => {
    if (!map || !mapsLib || coords.length === 0) return;
    if (coords.length === 1) {
      map.setCenter(coords[0]);
      map.setZoom(12);
      return;
    }
    const bounds = new google.maps.LatLngBounds();
    coords.forEach((c) => bounds.extend(c));
    map.fitBounds(bounds, padding);
    const listener = google.maps.event.addListenerOnce(map, 'idle', () => {
      const z = map.getZoom();
      if (typeof z === 'number') map.setZoom(z + 0.4);
    });
    return () => google.maps.event.removeListener(listener);
  }, [map, mapsLib, coords, padding]);

  return null;
}

function getStopImages(stop: Stop): string[] {
  if (stop.post.type === 'instagram' && stop.post.image) return [stop.post.image];
  return [];
}

// Custom map marker for region view: photo thumbnail with pointer tip.
// Falls back to a Pin when no image is available.
function StopMarker({ stop, isOpen }: { stop: Stop; isOpen: boolean }) {
  const images = getStopImages(stop);
  const isVisited = stop.status === 'visited';

  if (images.length === 0) {
    return (
      <Pin
        background={isOpen ? '#f97316' : isVisited ? '#ea4335' : '#9aa0a6'}
        borderColor={isOpen ? '#ea580c' : isVisited ? '#c5221f' : '#6b7280'}
        glyphColor="#ffffff"
        scale={isOpen ? 1.1 : 0.8}
      />
    );
  }

  const extra = images.length - 1;
  return (
    <div className={`stop-thumb${isOpen ? ' stop-thumb--open' : ''}`}>
      <div className="stop-thumb-stack">
        {extra > 0 && <div className="stop-thumb-back" />}
        <div className="stop-thumb-front">
          <img src={images[0]} alt={stop.location} className="stop-thumb-img" />
          {extra > 0 && <span className="stop-thumb-count">+{extra}</span>}
        </div>
      </div>
      <div className="stop-thumb-tip" />
    </div>
  );
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
    return (
      <RegionMap group={activeGroup} openStopId={openStopId} onOpenStop={onOpenStop} />
    );
  }

  return (
    <TripMap
      regionGroups={regionGroups}
      activeRegion={activeRegion}
      onSelectRegion={onSelectRegion}
    />
  );
}

// Trip overview: world map with region markers and route line.
function TripMap({
  regionGroups,
  activeRegion,
  onSelectRegion,
}: {
  regionGroups: RegionGroup[];
  activeRegion: RegionGroup | null;
  onSelectRegion: (code: string) => void;
}) {
  const regionCoords = useMemo(
    () => regionGroups.map((g) => g.region.coords),
    [regionGroups],
  );
  // FR-030: route line skips fully-abandoned regions, connecting the
  // non-abandoned regions on either side directly to each other.
  const routedGroups = useMemo(() => getRoutedGroups(regionGroups), [regionGroups]);

  return (
    <div className="map-canvas map-canvas-trip" aria-label="World trip overview map">
      <Map
        mapId={MAP_ID}
        defaultCenter={{ lat: 20, lng: -30 }}
        defaultZoom={2}
        gestureHandling="greedy"
        zoomControl={true}
        style={{ width: '100%', height: '100%' }}
      >
        <FitBounds coords={regionCoords} padding={80} />

        {routedGroups.slice(0, -1).map((from, i) => {
          const to = routedGroups[i + 1];
          const solid = isSegmentSolid(from, to);
          return (
            <MapPolyline
              key={`${from.region.code}-${to.region.code}`}
              path={[from.region.coords, to.region.coords]}
              solid={solid}
              strokeColor={solid ? '#1a73e8' : '#70757a'}
            strokeWeight={solid ? 3.5 : 2}
            />
          );
        })}

        {regionGroups.map((group) => {
          const isActive = activeRegion?.region.code === group.region.code;
          const isAbandoned = group.overallStatus === 'abandoned';
          const isVisited = group.overallStatus === 'visited' || group.overallStatus === 'mixed';
          // Abandoned regions render as a faded grey pin; visited as red; planned as default grey.
          const background = isAbandoned ? '#cbd5e1' : isVisited ? '#ea4335' : '#9aa0a6';
          const borderColor = isAbandoned ? '#94a3b8' : isVisited ? '#c5221f' : '#6b7280';
          return (
            <AdvancedMarker
              key={group.region.code}
              position={group.region.coords}
              title={`${group.region.name}, ${group.region.country}${isAbandoned ? ' (abandoned)' : ''}`}
              onClick={() => onSelectRegion(group.region.code)}
            >
              <Pin
                background={background}
                borderColor={borderColor}
                glyphColor="#ffffff"
                scale={isActive ? 1.3 : isAbandoned ? 0.85 : 1.0}
              />
            </AdvancedMarker>
          );
        })}
      </Map>
    </div>
  );
}

// Region drill-down: zoomed map with individual stop markers.
function RegionMap({
  group,
  openStopId,
  onOpenStop,
}: {
  group: RegionGroup;
  openStopId: string | null;
  onOpenStop: (stopId: string, contextStopIds: string[]) => void;
}) {
  const stopCoords = useMemo(() => group.stops.map((s) => s.coords), [group.stops]);
  const stopIds = useMemo(() => group.stops.map((s) => s.id), [group.stops]);

  return (
    <div className="map-canvas map-canvas-region" aria-label={`${group.region.name} region map`}>
      <Map
        mapId={MAP_ID}
        defaultCenter={group.region.coords}
        defaultZoom={12}
        gestureHandling="greedy"
        zoomControl={true}
        style={{ width: '100%', height: '100%' }}
      >
        <FitBounds coords={stopCoords} padding={60} />

        <MapPolyline
          path={stopCoords}
          solid={false}
          strokeColor="#1a73e8"
          strokeWeight={2.5}
        />

        {group.stops.map((stop) => {
          const isOpen = stop.id === openStopId;
          return (
            <AdvancedMarker
              key={stop.id}
              position={stop.coords}
              title={stop.location}
              onClick={() => onOpenStop(stop.id, stopIds)}
            >
              <StopMarker stop={stop} isOpen={isOpen} />
            </AdvancedMarker>
          );
        })}
      </Map>
    </div>
  );
}

export default WorldMap;
