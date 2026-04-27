import { useEffect, useMemo } from 'react';
import { Map, AdvancedMarker, useMap, useMapsLibrary } from '@vis.gl/react-google-maps';
import type { RegionGroup } from '../utils/regionUtils';
import { getActiveRegion, isSegmentSolid } from '../utils/regionUtils';
import type { ViewMode } from '../App';

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
              strokeColor={solid ? '#60a5fa' : '#94a3b8'}
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
              <div
                className={`gm-region-dot${isVisited ? ' visited' : ' planned'}${isActive ? ' active' : ''}`}
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
          strokeColor="#93c5fd"
          strokeWeight={1.5}
        />

        {group.stops.map((stop) => (
          <AdvancedMarker
            key={stop.id}
            position={stop.coords}
            title={stop.location}
            onClick={() => onOpenStop(stop.id, stopIds)}
          >
            <div
              className={`gm-stop-dot ${stop.status}${stop.id === openStopId ? ' open' : ''}`}
            />
          </AdvancedMarker>
        ))}
      </Map>
    </div>
  );
}

export default WorldMap;
