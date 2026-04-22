import type { Stop, Itinerary } from '../data/types';
import MapView from '../components/MapView';
import Sidebar from '../components/Sidebar';
import StopDetail from '../components/StopDetail';
import CityDetail from '../components/CityDetail';

interface HomePageProps {
  itinerary: Itinerary;
  cityViewId: string | null;
  selectedStop: Stop | null;
  cityViewStop: Stop | null;
  onSelectStop: (stopId: string) => void;
  onSelectCity: (stopId: string) => void;
  onExitCityView: () => void;
}

function HomePage({
  itinerary,
  cityViewId,
  selectedStop,
  cityViewStop,
  onSelectStop,
  onSelectCity,
  onExitCityView,
}: HomePageProps) {
  const topLevelStops = itinerary.stops;
  const cityChildren = cityViewStop?.children ?? [];

  const mapStops = cityViewId ? [cityViewStop!, ...cityChildren] : topLevelStops;

  return (
    <main className="homepage">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">World Travelogue</p>
          <h1>Follow the around-the-world itinerary and explore city highlights.</h1>
          <p>
            The map shows where the travelers have been and where they're heading next. Click an itinerary item to open stop details or zoom into city-level discoveries.
          </p>
        </div>
        <div className="stats-panel">
          <div>
            <span>Total major stops</span>
            <strong>{topLevelStops.length}</strong>
          </div>
          <div>
            <span>City drilldown</span>
            <strong>{cityChildren.length}</strong>
          </div>
        </div>
      </section>

      <section className="content-grid">
        <aside className="sidebar-panel">
          <Sidebar
            stops={topLevelStops}
            cityViewId={cityViewId}
            cityChildren={cityChildren}
            selectedStopId={selectedStop?.id ?? null}
            onSelectStop={onSelectStop}
            onSelectCity={onSelectCity}
            onExitCityView={onExitCityView}
          />
        </aside>

        <section className="map-panel">
          <MapView
            stops={mapStops}
            selectedStopId={selectedStop?.id ?? null}
            cityViewId={cityViewId}
            topLevelStops={topLevelStops}
            onSelectStop={onSelectStop}
          />
        </section>

        <aside className="detail-panel">
          <StopDetail selectedStop={selectedStop} />
          {cityViewId && cityViewStop ? (
            <CityDetail
              city={cityViewStop}
              selectedChildId={selectedStop?.id ?? null}
              onSelectStop={onSelectStop}
            />
          ) : null}
        </aside>
      </section>
    </main>
  );
}

export default HomePage;
