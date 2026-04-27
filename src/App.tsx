import { useMemo, useState } from 'react';
import { APIProvider } from '@vis.gl/react-google-maps';
import { miscellaneousAdventures } from './data/miscellaneous-adventures';
import { groupStopsByRegion } from './utils/regionUtils';
import type { Trip } from './data/types';
import WorldMap from './components/MapView';
import TripFeed from './components/Sidebar';
import RegionSidebar from './components/RegionSidebar';
import StopModal from './components/StopDetail';

export type ViewMode = 'trip' | 'region';

const TRIPS: Trip[] = [miscellaneousAdventures];

function App() {
  const [activeTrip, setActiveTrip] = useState<Trip>(TRIPS[0]);
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
  };

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
