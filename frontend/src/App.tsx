import { useEffect, useMemo, useState } from 'react';
import { APIProvider } from '@vis.gl/react-google-maps';
import { groupStopsByRegion } from './utils/regionUtils';
import type { Trip } from './data/types';
import { useTrips } from './hooks/useTrips';
import { useTrip } from './hooks/useTrip';
import { useRegions } from './hooks/useRegions';
import { ErrorBoundary } from 'react-error-boundary';
import WorldMap from './components/MapView';
import TripFeed from './components/Sidebar';
import RegionSidebar from './components/RegionSidebar';
import StopModal from './components/StopDetail';

export type ViewMode = 'trip' | 'region';

// FR-027: Parse `#/trip/{tripId}` from the URL hash; return the matching trip id
// or the first trip's id as the fallback. Returns null when trips haven't loaded yet.
function tripIdFromHash(hash: string, trips: Trip[]): string | null {
  if (trips.length === 0) return null;
  const match = hash.match(/^#\/trip\/([^/?#]+)/);
  if (match) {
    const found = trips.find((t) => t.id === match[1]);
    if (found) return found.id;
  }
  return trips[0].id;
}

function App() {
  const { trips, loading: tripsLoading, error: tripsError } = useTrips();
  const { regions, loading: regionsLoading, error: regionsError } = useRegions();
  const [activeTripId, setActiveTripId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('trip');
  const [activeRegionCode, setActiveRegionCode] = useState<string | null>(null);
  const [openStopId, setOpenStopId] = useState<string | null>(null);
  const [modalStopList, setModalStopList] = useState<string[]>([]);
  const [tripSelectorOpen, setTripSelectorOpen] = useState(false);

  // Resolve the active trip from the URL hash once the trips list loads.
  useEffect(() => {
    if (trips.length === 0 || activeTripId !== null) return;
    const id = tripIdFromHash(window.location.hash, trips);
    if (id) {
      setActiveTripId(id);
      if (!window.location.hash) {
        window.history.replaceState(null, '', `#/trip/${id}`);
      }
    }
  }, [trips, activeTripId]);

  const { trip: activeTrip } = useTrip(activeTripId);

  const regionGroups = useMemo(
    () => (activeTrip ? groupStopsByRegion(activeTrip, regions) : []),
    [activeTrip, regions]
  );

  const openStop = useMemo(
    () => activeTrip?.stops.find((s) => s.id === openStopId) ?? null,
    [activeTrip, openStopId]
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

  // FR-051: primary cluster-click behavior (fitBounds) is handled inside CountryClusterer.
  // This handler exists for future App-level responses (e.g. highlighting clustered regions).
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleClusterClick = (_regionCodes: string[]) => {
    // no-op: zoom-to-separate is handled imperatively by CountryClusterer
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
    setActiveTripId(trip.id);
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
      const nextId = tripIdFromHash(window.location.hash, trips);
      if (nextId && nextId !== activeTripId) {
        setActiveTripId(nextId);
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
  }, [trips, activeTripId]);

  if (tripsLoading || regionsLoading) {
    return (
      <div className="app-shell app-loading">
        <p>Loading…</p>
      </div>
    );
  }

  if (tripsError || regionsError) {
    return (
      <div className="app-shell app-error">
        <p>{tripsError ?? regionsError}</p>
      </div>
    );
  }

  if (trips.length === 0) {
    return (
      <div className="app-shell app-empty">
        <p>No trips are currently available.</p>
      </div>
    );
  }

  if (!activeTrip) {
    return (
      <div className="app-shell app-loading">
        <p>Loading…</p>
      </div>
    );
  }

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
                  {trips.map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      className={`trip-option ${t.id === activeTripId ? 'active' : ''}`}
                      onClick={() => handleSelectTrip(t)}
                    >
                      {t.title}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <ErrorBoundary fallback={<div className="error-boundary-fallback"><p>Something went wrong.</p></div>}>
              <WorldMap
                regionGroups={regionGroups}
                viewMode={viewMode}
                activeRegionCode={activeRegionCode}
                openStopId={openStopId}
                onSelectRegion={handleExpandRegion}
                onOpenStop={handleOpenStop}
                onClusterClick={handleClusterClick}
              />
            </ErrorBoundary>
          </div>

          <div className="sidebar-pane">
            <ErrorBoundary fallback={<div className="error-boundary-fallback"><p>Something went wrong.</p></div>}>
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
            </ErrorBoundary>
          </div>
        </div>

        {openStop && (
          <ErrorBoundary fallback={<div className="error-boundary-fallback"><p>Something went wrong.</p></div>}>
            <StopModal
              stop={openStop}
              stopList={modalStopList}
              allStops={activeTrip.stops}
              regionGroups={regionGroups}
              onClose={handleCloseStop}
              onNav={handleModalNav}
            />
          </ErrorBoundary>
        )}
      </div>
    </APIProvider>
  );
}

export default App;
