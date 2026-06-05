import { useEffect, useMemo } from 'react';
import { Map, AdvancedMarker, useMap, useMapsLibrary } from '@vis.gl/react-google-maps';
import isoCountries from 'i18n-iso-countries';
import enLocale from 'i18n-iso-countries/langs/en.json';
import type { RegionGroup } from '../utils/regionUtils';
import { getActiveRegion, getRoutedGroups, isSegmentSolid } from '../utils/regionUtils';
import type { ViewMode } from '../App';
import type { Stop } from '../data/types';

isoCountries.registerLocale(enLocale);

const MAP_ID = import.meta.env.VITE_GOOGLE_MAPS_MAP_ID as string | undefined;

// --- Arrowhead geometry (FR-049) ---

const DEG = Math.PI / 180;

/** Compass bearing in degrees (0 = N, 90 = E, 180 = S, 270 = W) from A to B. */
function geodesicBearing(
  a: { lat: number; lng: number },
  b: { lat: number; lng: number },
): number {
  const φ1 = a.lat * DEG, φ2 = b.lat * DEG;
  const Δλ = (b.lng - a.lng) * DEG;
  const y = Math.sin(Δλ) * Math.cos(φ2);
  const x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
  return (Math.atan2(y, x) / DEG + 360) % 360;
}

/**
 * Spherical linear interpolation along a great-circle arc.
 * t = 0 → a, t = 1 → b.
 */
function interpolateSlerp(
  a: { lat: number; lng: number },
  b: { lat: number; lng: number },
  t: number,
): { lat: number; lng: number } {
  const φ1 = a.lat * DEG, λ1 = a.lng * DEG;
  const φ2 = b.lat * DEG, λ2 = b.lng * DEG;
  const ax = Math.cos(φ1) * Math.cos(λ1), ay = Math.cos(φ1) * Math.sin(λ1), az = Math.sin(φ1);
  const bx = Math.cos(φ2) * Math.cos(λ2), by = Math.cos(φ2) * Math.sin(λ2), bz = Math.sin(φ2);
  const dot = Math.min(1, Math.max(-1, ax * bx + ay * by + az * bz));
  const Ω = Math.acos(dot);
  if (Ω < 1e-10) return a;
  const sinΩ = Math.sin(Ω);
  const wa = Math.sin((1 - t) * Ω) / sinΩ;
  const wb = Math.sin(t * Ω) / sinΩ;
  const cx = wa * ax + wb * bx, cy = wa * ay + wb * by, cz = wa * az + wb * bz;
  return {
    lat: Math.asin(Math.min(1, Math.max(-1, cz))) / DEG,
    lng: Math.atan2(cy, cx) / DEG,
  };
}

/**
 * SVG arrowhead AdvancedMarker placed 12% from the destination end of a
 * route segment (88% from the start), pointing in the direction of travel.
 * Non-interactive: pointer events are suppressed so it never blocks map clicks.
 */
function SegmentArrow({
  from,
  to,
  color = '#1a73e8',
}: {
  from: { lat: number; lng: number };
  to: { lat: number; lng: number };
  color?: string;
}) {
  const position = useMemo(() => interpolateSlerp(from, to, 0.88), [from, to]);
  const bearing = useMemo(() => geodesicBearing(from, to), [from, to]);

  return (
    <AdvancedMarker position={position}>
      {/* Zero-size container so the SVG is visually centred on the pin point */}
      <div style={{ position: 'relative', width: 0, height: 0, pointerEvents: 'none' }}>
        <svg
          width="14"
          height="14"
          viewBox="0 0 14 14"
          style={{
            position: 'absolute',
            top: '-7px',
            left: '-7px',
            transform: `rotate(${bearing}deg)`,
            transformOrigin: 'center center',
            pointerEvents: 'none',
          }}
        >
          {/* North-pointing triangle; CSS rotation aligns it to segment bearing */}
          <polygon
            points="7,1 13,13 1,13"
            fill={color}
            stroke="white"
            strokeWidth="1"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </AdvancedMarker>
  );
}

// --- Flag pin marker (FR-046, trip overview) ---

// Aliases for names the backend uses that don't match i18n-iso-countries' English names.
const COUNTRY_ALIASES: Record<string, string> = {
  'Micronesia': 'FM', // package name is "Micronesia, Federated States of"
};

/**
 * Flag pin for trip-overview region markers (FR-046).
 * Uses flagcdn.com to serve actual flag images — works on all platforms
 * including Windows where flag emoji renders as text codes.
 * The flex column centres the staff under the flag image so AdvancedMarker's
 * bottom-centre anchor falls at the staff base (the map pin point).
 * Abandoned regions appear faded; the active region scales up with a glow.
 */
function FlagPin({
  country,
  isActive,
  isAbandoned,
}: {
  country: string;
  isActive: boolean;
  isAbandoned: boolean;
}) {
  const iso2 = COUNTRY_ALIASES[country] ?? isoCountries.getAlpha2Code(country, 'en') ?? undefined;
  const scale = isActive ? 1.3 : isAbandoned ? 0.85 : 1.0;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        cursor: 'pointer',
        opacity: isAbandoned ? 0.45 : 1,
        transform: `scale(${scale})`,
        transformOrigin: '50% 100%',
        ...(isActive ? { filter: 'drop-shadow(0 0 4px rgba(249,115,22,0.8))' } : {}),
      }}
    >
      {iso2 ? (
        <img
          src={`https://flagcdn.com/w20/${iso2.toLowerCase()}.png`}
          alt={country}
          style={{
            display: 'block',
            width: '22px',
            height: '14px',
            objectFit: 'cover',
            border: '0.5px solid rgba(0,0,0,0.2)',
            borderRadius: '1px',
          }}
        />
      ) : (
        <div style={{ width: '22px', height: '14px', backgroundColor: '#9aa0a6', borderRadius: '1px' }} />
      )}
      {/* Staff — centred by the flex container */}
      <div
        style={{
          width: '2px',
          height: '10px',
          backgroundColor: isAbandoned ? '#94a3b8' : isActive ? '#ea580c' : '#374151',
          borderRadius: '0 0 1px 1px',
        }}
      />
    </div>
  );
}

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

// Pushpin marker for region drill-down stops (FR-046).
// Circle head + triangular needle; colour-coded by status; scales + glows when open.
// Structured as a flex column so AdvancedMarker's bottom-centre anchor falls at
// the needle tip (the map pin point).
function PushPin({ isOpen, isVisited }: { isOpen: boolean; isVisited: boolean }) {
  const headColor = isOpen ? '#f97316' : isVisited ? '#ea4335' : '#9aa0a6';
  const borderColor = isOpen ? '#c2410c' : isVisited ? '#c5221f' : '#6b7280';
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        transform: isOpen ? 'scale(1.25)' : undefined,
        transformOrigin: '50% 100%',
        filter: isOpen
          ? 'drop-shadow(0 0 4px rgba(249,115,22,0.7))'
          : 'drop-shadow(0 1px 3px rgba(0,0,0,0.4))',
      }}
    >
      <div
        style={{
          width: '16px',
          height: '16px',
          borderRadius: '50%',
          backgroundColor: headColor,
          border: `2.5px solid ${borderColor}`,
        }}
      />
      <div
        style={{
          width: 0,
          height: 0,
          borderLeft: '5px solid transparent',
          borderRight: '5px solid transparent',
          borderTop: `7px solid ${headColor}`,
          marginTop: '-1px',
        }}
      />
    </div>
  );
}

// Custom map marker for region view: photo thumbnail with pointer tip (FR-046).
// Falls back to a pushpin when no image is available.
function StopMarker({ stop, isOpen }: { stop: Stop; isOpen: boolean }) {
  const images = getStopImages(stop);
  const isVisited = stop.status === 'visited';

  if (images.length === 0) {
    return <PushPin isOpen={isOpen} isVisited={isVisited} />;
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
          const color = solid ? '#1a73e8' : '#70757a';
          return (
            <MapPolyline
              key={`${from.region.code}-${to.region.code}`}
              path={[from.region.coords, to.region.coords]}
              solid={solid}
              strokeColor={color}
              strokeWeight={solid ? 3.5 : 2}
            />
          );
        })}
        {routedGroups.slice(0, -1).map((from, i) => {
          const to = routedGroups[i + 1];
          const solid = isSegmentSolid(from, to);
          return (
            <SegmentArrow
              key={`arrow-${from.region.code}-${to.region.code}`}
              from={from.region.coords}
              to={to.region.coords}
              color={solid ? '#1a73e8' : '#70757a'}
            />
          );
        })}

        {regionGroups.map((group) => {
          const isActive = activeRegion?.region.code === group.region.code;
          const isAbandoned = group.overallStatus === 'abandoned';
          // const isVisited = group.overallStatus === 'visited' || group.overallStatus === 'mixed';
          // // Abandoned regions render as a faded grey pin; visited as red; planned as default grey.
          // const background = isAbandoned ? '#cbd5e1' : isVisited ? '#ea4335' : '#9aa0a6';
          // const borderColor = isAbandoned ? '#94a3b8' : isVisited ? '#c5221f' : '#6b7280';
          return (
            <AdvancedMarker
              key={group.region.code}
              position={group.region.coords}
              title={`${group.region.name}, ${group.region.country}${isAbandoned ? ' (abandoned)' : ''}`}
              onClick={() => onSelectRegion(group.region.code)}
            >
              <FlagPin
                country={group.region.country}
                isActive={isActive}
                isAbandoned={isAbandoned}
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

        {group.stops.slice(0, -1).map((stop, i) => (
          <SegmentArrow
            key={`arrow-${stop.id}-${group.stops[i + 1].id}`}
            from={stop.coords}
            to={group.stops[i + 1].coords}
            color="#1a73e8"
          />
        ))}

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
