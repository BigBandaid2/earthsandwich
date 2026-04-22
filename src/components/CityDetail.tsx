import type { Stop } from '../data/types';

interface CityDetailProps {
  city: Stop;
  selectedChildId: string | null;
  onSelectStop: (stopId: string) => void;
}

function CityDetail({ city, selectedChildId, onSelectStop }: CityDetailProps) {
  if (!city.children || city.children.length === 0) {
    return null;
  }

  return (
    <section className="city-detail">
      <h3>City details for {city.title}</h3>
      <p>{city.caption}</p>
      <ul className="city-detail-list">
        {city.children.map((child) => (
          <li key={child.id}>
            <button
              type="button"
              className={`city-child ${child.id === selectedChildId ? 'active' : ''}`}
              onClick={() => onSelectStop(child.id)}
              aria-pressed={child.id === selectedChildId}
            >
              <strong>{child.title}</strong>
              <span>{child.caption}</span>
              <span>{child.date}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default CityDetail;
