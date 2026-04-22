import { useState } from 'react';
import type { Stop } from '../data/types';

interface StopDetailProps {
  selectedStop: Stop | null;
}

function StopDetail({ selectedStop }: StopDetailProps) {
  const [imageOpen, setImageOpen] = useState(true);
  const [blogOpen, setBlogOpen] = useState(true);

  if (!selectedStop) {
    return (
      <section className="stop-detail empty-state">
        <h2>Stop details</h2>
        <p>Select a stop from the itinerary or map to view more information here.</p>
      </section>
    );
  }

  return (
    <section className="stop-detail">
      <div className="stop-detail-header">
        <div>
          <p className="stop-type">{selectedStop.type === 'city' ? 'City stop' : selectedStop.type === 'site' ? 'Site stop' : 'Major stop'}</p>
          <h2>{selectedStop.title}</h2>
          <p className="stop-caption">{selectedStop.caption}</p>
          <p className="stop-date">{selectedStop.date}</p>
        </div>
      </div>

      {selectedStop.image ? (
        <div className="toggle-section">
          <button type="button" className="toggle-button" onClick={() => setImageOpen((prev) => !prev)}>
            {imageOpen ? 'Hide image' : 'Show image'}
          </button>
          {imageOpen ? <img className="stop-image" src={selectedStop.image} alt={selectedStop.title} /> : null}
        </div>
      ) : null}

      <div className="toggle-section">
        <button type="button" className="toggle-button" onClick={() => setBlogOpen((prev) => !prev)}>
          {blogOpen ? 'Hide journal entry' : 'Show journal entry'}
        </button>
        {blogOpen ? (
          <div className="blog-content">
            <p>{selectedStop.blog ?? 'No long-form journal entry available for this stop.'}</p>
          </div>
        ) : null}
      </div>

      {selectedStop.details ? (
        <div className="details-block">
          <h3>Details</h3>
          <p>{selectedStop.details}</p>
        </div>
      ) : null}
    </section>
  );
}

export default StopDetail;
