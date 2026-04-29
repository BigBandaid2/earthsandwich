import { useEffect, useMemo } from 'react';
import { Map, AdvancedMarker, Pin, useMap, useMapsLibrary } from '@vis.gl/react-google-maps';
import type { RegionGroup } from '../utils/regionUtils';
import { getActiveRegion, isSegmentSolid } from '../utils/regionUtils';
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

  return (
    <div className="map-canvas map-canvas-trip" aria-label="World trip overview map">
      <Map
        mapId={MAP_ID}
        defaultCenter={{ lat: 20, lng: -30 }}
        defaultZoom={2}
        gestureHandling="greedy"
        style={{ width: '100%', height: '100%' }}
      >
        <FitBounds coords={regionCoords} padding={80} />

        {regionGroups.slice(0, -1).map((from, i) => {
          const to = regionGroups[i + 1];
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
          const isVisited = group.overallStatus !== 'planned';
          return (
            <AdvancedMarker
              key={group.region.code}
              position={group.region.coords}
              title={`${group.region.name}, ${group.region.country}`}
              onClick={() => onSelectRegion(group.region.code)}
            >
              <Pin
                background={isVisited ? '#ea4335' : '#9aa0a6'}
                borderColor={isVisited ? '#c5221f' : '#6b7280'}
                glyphColor="#ffffff"
                scale={isActive ? 1.3 : 1.0}
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
