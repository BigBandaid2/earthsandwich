import { useEffect, useMemo, useState } from 'react';
import { APIProvider } from '@vis.gl/react-google-maps';
import { trips } from './data/itinerary';
import { groupStopsByRegion } from './utils/regionUtils';
import type { Trip } from './data/types';
import WorldMap from './components/MapView';
import TripFeed from './components/Sidebar';
import RegionSidebar from './components/RegionSidebar';
import StopModal from './components/StopDetail';

export type ViewMode = 'trip' | 'region';

function firstStopDate(trip: Trip): string {
  return trip.stops.reduce((min, s) => (s.date < min ? s.date : min), trip.stops[0]?.date ?? '');
}

const TRIPS: Trip[] = [...trips].sort((a, b) =>
  firstStopDate(b).localeCompare(firstStopDate(a))
);

// FR-027: Parse `#/trip/{tripId}` from the URL hash and resolve to a Trip,
// falling back to TRIPS[0] (most recent) when the hash is absent or unknown.
function tripFromHash(hash: string): Trip {
  const match = hash.match(/^#\/trip\/([^/?#]+)/);
  if (match) {
    const found = TRIPS.find((t) => t.id === match[1]);
    if (found) return found;
  }
  return TRIPS[0];
}

function App() {
  const [activeTrip, setActiveTrip] = useState<Trip>(() =>
    typeof window !== 'undefined' ? tripFromHash(window.location.hash) : TRIPS[0]
  );
  const [viewMode, setViewMode] = useState<ViewMode>('trip');
  const [activeRegionCode, setActiveRegionCode] = useState<string | null>(null);
  const [openStopId, setOpenStopId] = useState<string | null>(null);
  const [modalStopList, setModalStopList] = useState<string[]>([]);
  const [tripSelectorOpen, setTripSelectorOpen] = useState(false);

  const regionGroups = useMemo(() => groupStopsByRegion(activeTrip), [activeTrip]);

  const activeGroup = useMemo(
    () => regionGroups.find((g) => g.region.code === activeRegionCode) ?? null,
    [regionGroups, activeRegionCode]
  );

  const openStop = useMemo(
    () => activeTrip.stops.find((s) => s.id === openStopId) ?? null,
    [activeTrip.stops, openStopId]
  );

  const handleExpandRegion = (regionCode: string) => {
    setActiveRegionCode(regionCode);
    setViewMode('region');
  };

  const handleBackToTrip = () => {
    setViewMode('trip');
    setActiveRegionCode(null);
  };

  const handleSelectRegion = (regionCode: string) => {
    setActiveRegionCode(regionCode);
  };

  const handleOpenStop = (stopId: string, contextStopIds: string[]) => {
    setOpenStopId(stopId);
    setModalStopList(contextStopIds);
  };

  const handleCloseStop = () => {
    setOpenStopId(null);
    setModalStopList([]);
  };

  const handleModalNav = (direction: 'prev' | 'next') => {
    if (!openStopId || modalStopList.length === 0) return;
    const idx = modalStopList.indexOf(openStopId);
    if (direction === 'prev' && idx > 0) setOpenStopId(modalStopList[idx - 1]);
    if (direction === 'next' && idx < modalStopList.length - 1) setOpenStopId(modalStopList[idx + 1]);
  };

  const handleSelectTrip = (trip: Trip) => {
    setActiveTrip(trip);
    setViewMode('trip');
    setActiveRegionCode(null);
    setOpenStopId(null);
    setTripSelectorOpen(false);
    const newHash = `#/trip/${trip.id}`;
    if (window.location.hash !== newHash) {
      window.history.pushState(null, '', newHash);
    }
  };

  // FR-027: react to back/forward navigation by re-resolving the hash.
  useEffect(() => {
    const onHashChange = () => {
      const next = tripFromHash(window.location.hash);
      if (next.id !== activeTrip.id) {
        setActiveTrip(next);
        setViewMode('trip');
        setActiveRegionCode(null);
        setOpenStopId(null);
      }
    };
    window.addEventListener('hashchange', onHashChange);
    window.addEventListener('popstate', onHashChange);
    return () => {
      window.removeEventListener('hashchange', onHashChange);
      window.removeEventListener('popstate', onHashChange);
    };
  }, [activeTrip.id]);

  // Keep the URL in sync on first load when no hash was provided.
  useEffect(() => {
    if (!window.location.hash) {
      window.history.replaceState(null, '', `#/trip/${activeTrip.id}`);
    }
  }, [activeTrip.id]);

  return (
    <APIProvider apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? ''}>
    <div className="app-shell">
      <div className="view-layout">
        <div className="map-pane">
          <div className="map-trip-card">
            <button
              type="button"
              className="hamburger-btn"
              aria-label="Open trip selector"
              onClick={() => setTripSelectorOpen((v) => !v)}
            >
              ☰
            </button>
            {viewMode === 'region' ? (
              <button type="button" className="back-btn" onClick={handleBackToTrip}>
                ← BACK TO TRIP
              </button>
            ) : (
              <span className="trip-title-card">{activeTrip.title}</span>
            )}
            {tripSelectorOpen && (
              <div className="trip-selector-dropdown">
                {TRIPS.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    className={`trip-option ${t.id === activeTrip.id ? 'active' : ''}`}
                    onClick={() => handleSelectTrip(t)}
                  >
                    {t.title}
                  </button>
                ))}
              </div>
            )}
          </div>

          <WorldMap
            regionGroups={regionGroups}
            viewMode={viewMode}
            activeRegionCode={activeRegionCode}
            openStopId={openStopId}
            onSelectRegion={handleExpandRegion}
            onOpenStop={handleOpenStop}
          />
        </div>

        <div className="sidebar-pane">
          {viewMode === 'trip' ? (
            <TripFeed
              regionGroups={regionGroups}
              trip={activeTrip}
              onExpandRegion={handleExpandRegion}
              onOpenStop={handleOpenStop}
            />
          ) : (
            <RegionSidebar
              regionGroups={regionGroups}
              activeRegionCode={activeRegionCode}
              onSelectRegion={handleSelectRegion}
              onOpenStop={handleOpenStop}
            />
          )}
        </div>
      </div>

      {openStop && (
        <StopModal
          stop={openStop}
          stopList={modalStopList}
          allStops={activeTrip.stops}
          regionGroups={regionGroups}
          onClose={handleCloseStop}
          onNav={handleModalNav}
        />
      )}
    </div>
    </APIProvider>
  );
}

export default App;
