import { useEffect, useMemo, useRef } from 'react';
import { MarkerClusterer } from '@googlemaps/markerclusterer';
import { Map, AdvancedMarker, useMap, useMapsLibrary } from '@vis.gl/react-google-maps';
import isoCountries from 'i18n-iso-countries';
import enLocale from 'i18n-iso-countries/langs/en.json';
import type { RegionGroup } from '../utils/regionUtils';
import { getActiveRegion, getRoutedGroups, isSegmentSolid } from '../utils/regionUtils';
import type { ViewMode } from '../App';
import type { Stop } from '../data/types';
import postmarkMapStyle from '../styles/postmark-map-style';

isoCountries.registerLocale(enLocale);

const MAP_ID = import.meta.env.VITE_GOOGLE_MAPS_MAP_ID as string | undefined;
const TRIP_MAP_ID = (import.meta.env.VITE_GOOGLE_MAPS_TRIP_MAP_ID as string | undefined) ?? MAP_ID;

const COUNTRY_ALIASES: Record<string, string> = {
  'Micronesia': 'FM',
};

function getCountryIso2(country: string): string | undefined {
  return COUNTRY_ALIASES[country] ?? isoCountries.getAlpha2Code(country, 'en') ?? undefined;
}

// Postmark-styled flag pin: a pole with a banner at the top containing the flag.
// Structured as a flex column so AdvancedMarker's bottom-centre anchor falls at the
// base dot (the geo-anchor point).
function FlagPin({
  country,
  isActive,
  isPlanned,
  isAbandoned,
}: {
  country: string;
  isActive: boolean;
  isPlanned: boolean;
  isAbandoned: boolean;
}) {
  const iso2 = getCountryIso2(country)?.toLowerCase();

  return (
    <span
      className={`tg-flag${isActive ? ' is-open' : ''}${isPlanned ? ' planned' : ''}${isAbandoned ? ' abandoned' : ''}`}
      style={{ position: 'relative', display: 'inline-block' }}
    >
      <span className="tg-flag-pole" aria-hidden="true" />
      <span className="tg-flag-base" aria-hidden="true" />
      <span className="tg-flag-banner">
        {iso2 ? (
          <img
            className="tg-flag-img"
            src={`https://flagcdn.com/${iso2}.svg`}
            alt={country}
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).style.display = 'none';
            }}
          />
        ) : (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '8px' }}>
            {country.slice(0, 2).toUpperCase()}
          </span>
        )}
      </span>
      {isActive && <span className="tg-flag-name">{country}</span>}
    </span>
  );
}

// Imperative version of FlagPin for use inside MarkerClusterer.
function createFlagPinElement(
  country: string,
  isActive: boolean,
  isPlanned: boolean,
  isAbandoned: boolean,
): HTMLElement {
  const iso2 = getCountryIso2(country)?.toLowerCase();

  const root = document.createElement('span');
  root.className = `tg-flag${isActive ? ' is-open' : ''}${isPlanned ? ' planned' : ''}${isAbandoned ? ' abandoned' : ''}`;
  root.style.cssText = 'position:relative;display:inline-block';

  const pole = document.createElement('span');
  pole.className = 'tg-flag-pole';
  pole.setAttribute('aria-hidden', 'true');

  const base = document.createElement('span');
  base.className = 'tg-flag-base';
  base.setAttribute('aria-hidden', 'true');

  const banner = document.createElement('span');
  banner.className = 'tg-flag-banner';

  if (iso2) {
    const img = document.createElement('img');
    img.className = 'tg-flag-img';
    img.src = `https://flagcdn.com/${iso2}.svg`;
    img.alt = country;
    img.onerror = () => { img.style.display = 'none'; };
    banner.appendChild(img);
  } else {
    banner.textContent = country.slice(0, 2).toUpperCase();
  }

  root.appendChild(pole);
  root.appendChild(base);
  root.appendChild(banner);
  return root;
}

interface WorldMapProps {
  regionGroups: RegionGroup[];
  viewMode: ViewMode;
  activeRegionCode: string | null;
  openStopId: string | null;
  onSelectRegion: (regionCode: string) => void;
  onOpenStop: (stopId: string, contextStopIds: string[]) => void;
  onClusterClick: (regionCodes: string[]) => void;
}

// Geodesic polyline with Postmark route styling.
function MapPolyline({
  path,
  solid,
}: {
  path: Array<{ lat: number; lng: number }>;
  solid: boolean;
}) {
  const map = useMap();
  const mapsLib = useMapsLibrary('maps');
  const ROUTE_COLOR = '#C5402A';

  useEffect(() => {
    if (!map || !mapsLib) return;

    const polyline = new mapsLib.Polyline({
      map,
      path,
      geodesic: true,
      ...(solid
        ? {
            strokeColor: ROUTE_COLOR,
            strokeOpacity: 1.0,
            strokeWeight: 2.4,
            icons: [
              {
                icon: {
                  path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
                  scale: 3,
                  fillColor: ROUTE_COLOR,
                  fillOpacity: 1,
                  strokeWeight: 0,
                },
                offset: '50%',
              },
            ],
          }
        : {
            strokeOpacity: 0,
            icons: [
              {
                icon: {
                  path: 'M 0,-1 0,1',
                  strokeOpacity: 0.45,
                  strokeWeight: 2.4,
                  strokeColor: ROUTE_COLOR,
                  scale: 2.4,
                },
                offset: '0',
                repeat: '10px',
              },
            ],
          }),
    });

    return () => polyline.setMap(null);
  }, [map, mapsLib, path, solid]);

  return null;
}

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

function PushPin({ isOpen, isVisited }: { isOpen: boolean; isVisited: boolean }) {
  const headColor = isOpen ? '#C5402A' : isVisited ? '#C5402A' : '#B6AC95';
  const borderColor = isOpen ? '#9A2D1B' : isVisited ? '#9A2D1B' : '#A99B82';
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        transform: isOpen ? 'scale(1.25)' : undefined,
        transformOrigin: '50% 100%',
        filter: isOpen ? 'drop-shadow(0 0 4px rgba(197,64,42,0.7))' : 'drop-shadow(0 1px 3px rgba(43,38,32,0.4))',
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
          width: 0, height: 0,
          borderLeft: '5px solid transparent',
          borderRight: '5px solid transparent',
          borderTop: `7px solid ${headColor}`,
          marginTop: '-1px',
        }}
      />
    </div>
  );
}

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
  onClusterClick,
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
      onClusterClick={onClusterClick}
    />
  );
}

function CountryClusterer({
  groups,
  activeRegion,
  onSelectRegion,
  onClusterClick,
}: {
  groups: RegionGroup[];
  activeRegion: RegionGroup | null;
  onSelectRegion: (code: string) => void;
  onClusterClick: (regionCodes: string[]) => void;
}) {
  const map = useMap();
  const markerLib = useMapsLibrary('marker');
  const onSelectRef = useRef(onSelectRegion);
  const onClusterRef = useRef(onClusterClick);
  onSelectRef.current = onSelectRegion;
  onClusterRef.current = onClusterClick;

  useEffect(() => {
    if (!map || !markerLib) return;

    const markerToCode = new WeakMap<object, string>();
    const markerEls = groups.map((group) => {
      const isActive = activeRegion?.region.code === group.region.code;
      const isPlanned = group.overallStatus === 'planned';
      const isAbandoned = group.overallStatus === 'abandoned';
      const marker = new markerLib.AdvancedMarkerElement({
        position: group.region.coords,
        title: group.region.name,
        content: createFlagPinElement(group.region.country, isActive, isPlanned, isAbandoned),
        gmpClickable: true,
      });
      marker.addEventListener('gmp-click', () => onSelectRef.current(group.region.code));
      markerToCode.set(marker, group.region.code);
      return marker;
    });

    const country = groups[0].region.country;
    const clusterer = new MarkerClusterer({
      map,
      markers: markerEls,
      renderer: {
        render({ position }) {
          return new markerLib.AdvancedMarkerElement({
            position,
            content: createFlagPinElement(country, false, false, false),
            gmpClickable: true,
          });
        },
      },
      onClusterClick: (_event, cluster) => {
        if (cluster.bounds) map.fitBounds(cluster.bounds);
        const codes = (cluster.markers ?? [])
          .map((m) => markerToCode.get(m as object))
          .filter((c): c is string => !!c);
        if (codes.length) onClusterRef.current(codes);
      },
    });

    return () => {
      markerEls.forEach((m) => { m.map = null; });
      clusterer.setMap(null);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, markerLib, groups, activeRegion]);

  return null;
}

function TripMap({
  regionGroups,
  activeRegion,
  onSelectRegion,
  onClusterClick,
}: {
  regionGroups: RegionGroup[];
  activeRegion: RegionGroup | null;
  onSelectRegion: (code: string) => void;
  onClusterClick: (regionCodes: string[]) => void;
}) {
  const regionCoords = useMemo(
    () => regionGroups.map((g) => g.region.coords),
    [regionGroups],
  );
  const routedGroups = useMemo(() => getRoutedGroups(regionGroups), [regionGroups]);

  const { indivGroups, countryGroups } = useMemo(() => {
    const byCountry = new globalThis.Map<string, RegionGroup[]>();
    const excluded: RegionGroup[] = [];

    regionGroups.forEach((group) => {
      const iso = getCountryIso2(group.region.country);
      if (!iso) { excluded.push(group); return; }
      const existing = byCountry.get(iso) ?? [];
      byCountry.set(iso, [...existing, group]);
    });

    const indiv = [...excluded];
    const multi: RegionGroup[][] = [];
    byCountry.forEach((groups) => {
      if (groups.length === 1) indiv.push(groups[0]);
      else multi.push(groups);
    });

    return { indivGroups: indiv, countryGroups: multi };
  }, [regionGroups]);

  return (
    <div className="map-canvas map-canvas-trip" aria-label="World trip overview map">
      <Map
        mapId={TRIP_MAP_ID}
        defaultCenter={{ lat: 20, lng: -30 }}
        defaultZoom={2}
        gestureHandling="greedy"
        zoomControl={true}
        disableDefaultUI={true}
        restriction={{ latLngBounds: { north: 85, south: -85, west: -180, east: 180 }, strictBounds: true }}
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
            />
          );
        })}

        {indivGroups.map((group) => {
          const isActive = activeRegion?.region.code === group.region.code;
          const isPlanned = group.overallStatus === 'planned';
          const isAbandoned = group.overallStatus === 'abandoned';
          return (
            <AdvancedMarker
              key={group.region.code}
              position={group.region.coords}
              title={group.region.name}
              onClick={() => onSelectRegion(group.region.code)}
            >
              <FlagPin
                country={group.region.country}
                isActive={isActive}
                isPlanned={isPlanned}
                isAbandoned={isAbandoned}
              />
            </AdvancedMarker>
          );
        })}

        {countryGroups.map((groups) => (
          <CountryClusterer
            key={`cluster-${groups[0].region.country}`}
            groups={groups}
            activeRegion={activeRegion}
            onSelectRegion={onSelectRegion}
            onClusterClick={onClusterClick}
          />
        ))}
      </Map>
    </div>
  );
}

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
        disableDefaultUI={true}
        style={{ width: '100%', height: '100%' }}
        styles={postmarkMapStyle}
      >
        <FitBounds coords={stopCoords} padding={60} />

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
