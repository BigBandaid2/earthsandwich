import type { Stop } from '../data/types';

interface SidebarProps {
  stops: Stop[];
  cityViewId: string | null;
  cityChildren: Stop[];
  selectedStopId: string | null;
  onSelectStop: (stopId: string) => void;
  onSelectCity: (stopId: string) => void;
  onExitCityView: () => void;
}

function Sidebar({
  stops,
  cityViewId,
  cityChildren,
  selectedStopId,
  onSelectStop,
  onSelectCity,
  onExitCityView,
}: SidebarProps) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>Itinerary</h2>
        {cityViewId ? (
          <button type="button" className="secondary-button" onClick={onExitCityView}>
            Back to world route
          </button>
        ) : null}
      </div>
      <ul className="stop-list">
        {stops.map((stop) => (
          <li key={stop.id}>
            <button
              type="button"
              className={`stop-item ${stop.id === selectedStopId ? 'active' : ''}`}
              onClick={() => (stop.type === 'city' ? onSelectCity(stop.id) : onSelectStop(stop.id))}
              aria-pressed={stop.id === selectedStopId}
            >
              <span className="stop-title">{stop.title}</span>
              <span className="stop-meta">{stop.caption}</span>
              <span className="stop-date">{stop.date}</span>
            </button>
            {cityViewId === stop.id && cityChildren.length > 0 ? (
              <ul className="child-list">
                {cityChildren.map((child) => (
                  <li key={child.id}>
                    <button
                      type="button"
                      className={`child-item ${child.id === selectedStopId ? 'active' : ''}`}
                      onClick={() => onSelectStop(child.id)}
                      aria-pressed={child.id === selectedStopId}
                    >
                      {child.title}
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Sidebar;
