import type { Stop } from '../data/types';

interface MapViewProps {
  stops: Stop[];
  topLevelStops: Stop[];
  selectedStopId: string | null;
  cityViewId: string | null;
  onSelectStop: (stopId: string) => void;
}

const projection = (coords: { lat: number; lng: number }) => {
  const x = ((coords.lng + 180) / 360) * 100;
  const y = ((90 - coords.lat) / 180) * 100;
  return { left: `${x}%`, top: `${y}%` };
};

const buildPoints = (points: Stop[]) =>
  points
    .filter((stop) => stop.coords)
    .map((stop) => {
      const { left, top } = projection(stop.coords);
      return `${left},${top}`;
    })
    .join(' ');

const MapView = ({ stops, topLevelStops, selectedStopId, cityViewId, onSelectStop }: MapViewProps) => {
  const pathPoints = buildPoints(stops);
  const topRoutePoints = buildPoints(topLevelStops);

  return (
    <div className="map-view" aria-label="Travel itinerary map">
      <div className="map-legend" aria-hidden="true">
        <span>
          <strong>Legend:</strong>
        </span>
        <span className="legend-dot visited"></span> Visited
        <span className="legend-dot planned"></span> Planned
        <span className="legend-dot selected"></span> Selected
      </div>
      <div className="map-canvas">
        <div className="map-background" />
        <svg className="map-lines" aria-hidden="true">
          <polyline points={topRoutePoints} className="route-line route-line-backdrop" />
          <polyline points={pathPoints} className="route-line route-line-active" />
        </svg>

        {stops.map((stop) => {
          const position = projection(stop.coords);
          const isSelected = stop.id === selectedStopId;
          const markerClass = stop.status === 'visited' ? 'marker visited' : 'marker planned';
          return (
            <button
              key={stop.id}
              type="button"
              className={`${markerClass}${isSelected ? ' selected' : ''}`}
              style={position}
              aria-pressed={isSelected}
              aria-label={`${stop.title}, ${stop.caption}, ${stop.status}`}
              onClick={() => onSelectStop(stop.id)}
            >
              <span className="marker-label">{stop.title}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default MapView;
