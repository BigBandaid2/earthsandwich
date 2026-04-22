import { useMemo, useState } from 'react';
import HomePage from './pages/HomePage';
import { itinerary } from './data/itinerary';
import type { Stop } from './data/types';

function App() {
  const [selectedStopId, setSelectedStopId] = useState<string | null>(null);
  const [cityViewId, setCityViewId] = useState<string | null>(null);

  const allStops = useMemo(() => {
    const stops: Stop[] = [...itinerary.stops];
    for (const stop of itinerary.stops) {
      if (stop.children) {
        stops.push(...stop.children);
      }
    }
    return stops;
  }, []);

  const selectedStop = useMemo(
    () => allStops.find((stop) => stop.id === selectedStopId) ?? null,
    [allStops, selectedStopId]
  );

  const cityViewStop = useMemo(
    () => itinerary.stops.find((stop) => stop.id === cityViewId) ?? null,
    [cityViewId]
  );

  const handleSelectStop = (stopId: string) => {
    setSelectedStopId(stopId);
    const stop = itinerary.stops.find((item) => item.id === stopId);
    if (stop?.type === 'city') {
      setCityViewId(stopId);
    }
  };

  const handleSelectCity = (stopId: string) => {
    const stop = itinerary.stops.find((item) => item.id === stopId);
    if (stop?.type === 'city') {
      setCityViewId(stopId);
      setSelectedStopId(stopId);
    } else {
      setSelectedStopId(stopId);
    }
  };

  const handleExitCityView = () => {
    setCityViewId(null);
    setSelectedStopId(null);
  };

  return (
    <div className="app-shell">
      <HomePage
        itinerary={itinerary}
        cityViewId={cityViewId}
        selectedStop={selectedStop}
        cityViewStop={cityViewStop}
        onSelectStop={handleSelectStop}
        onSelectCity={handleSelectCity}
        onExitCityView={handleExitCityView}
      />
    </div>
  );
}

export default App;
