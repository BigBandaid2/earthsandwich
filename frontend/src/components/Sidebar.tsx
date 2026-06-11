import type { RegionGroup } from '../utils/regionUtils';
import { formatDateRange } from '../utils/regionUtils';
import type { Trip, InstagramPost, SubstackPost } from '../data/types';

interface TripFeedProps {
  regionGroups: RegionGroup[];
  trip: Trip;
  onExpandRegion: (regionCode: string) => void;
  onOpenStop: (stopId: string, contextStopIds: string[]) => void;
}

// Counts for the header stat row
function tripStats(regionGroups: RegionGroup[], trip: Trip) {
  const visited = trip.stops.filter((s) => s.status === 'visited').length;
  const planned = trip.stops.filter((s) => s.status === 'planned').length;
  const countries = new Set(regionGroups.map((g) => g.region.country)).size;
  return { visited, planned, countries };
}

function TripFeed({ regionGroups, trip, onExpandRegion, onOpenStop }: TripFeedProps) {
  const stats = tripStats(regionGroups, trip);

  return (
    <div className="tg-feed">
      <div className="tg-feed-head">
        <div className="eyebrow">A collection of adventures</div>
        <h1 className="tg-feed-title">{trip.title}</h1>
        <div className="tg-feed-sub">
          <span className="script">stop by stop</span>
        </div>
        <div className="tg-feed-meta">
          <span><b>{stats.visited}</b> visited</span>
          <span className="tg-feed-meta-dot" />
          <span><b>{stats.planned}</b> planned</span>
          <span className="tg-feed-meta-dot" />
          <span><b>{stats.countries}</b> countries</span>
        </div>
      </div>

      <div className="tg-feed-scroll">
        <div className="tg-feed-section">Itinerary</div>
        {regionGroups.map((group, i) => (
          <RegionTile
            key={group.region.code}
            group={group}
            isLast={i === regionGroups.length - 1}
            onExpand={() => onExpandRegion(group.region.code)}
            onOpenStop={onOpenStop}
          />
        ))}
      </div>
    </div>
  );
}

interface RegionTileProps {
  group: RegionGroup;
  isLast: boolean;
  onExpand: () => void;
  onOpenStop: (stopId: string, contextStopIds: string[]) => void;
}

function RegionTile({ group, isLast, onExpand, onOpenStop }: RegionTileProps) {
  const allStopIds = group.stops.map((s) => s.id);
  const instagramStops = group.stops.filter((s) => s.post.type === 'instagram');
  const substackStops = group.stops.filter((s) => s.post.type === 'substack');

  const MAX_PHOTOS = 4;
  const visiblePhotos = instagramStops.slice(0, MAX_PHOTOS);
  const extraPhotos = instagramStops.length > MAX_PHOTOS ? instagramStops.length - MAX_PHOTOS : 0;

  // First substack stop becomes the dispatch chip
  const dispatch = substackStops.length > 0 ? substackStops[0] : null;

  // The region note is the trip description if available
  const status = group.overallStatus === 'abandoned' ? 'abandoned'
    : group.overallStatus === 'planned' ? 'planned'
    : 'visited';

  const dotStatus = group.overallStatus === 'mixed' ? 'visited' : group.overallStatus;

  return (
    <div className={`tg-tile ${status}`}>
      <div className="tg-tile-rail">
        <span className={`tg-dot ${dotStatus}`} />
        {!isLast && <span className="tg-rail-line" />}
      </div>

      <div className="tg-tile-body">
        <div className="tg-tile-head">
          <h3 className="tg-tile-name">{group.region.name}</h3>
          <span className="tg-tile-date">{formatDateRange(group.startDate, group.endDate)}</span>
        </div>
        <div className="tg-tile-country">{group.region.country}</div>

        {visiblePhotos.length > 0 && (
          <div className="tg-strip">
            {visiblePhotos.map((stop) => {
              const post = stop.post as InstagramPost;
              return (
                <button
                  key={stop.id}
                  type="button"
                  className="tg-photo"
                  onClick={() => onOpenStop(stop.id, allStopIds)}
                  aria-label={post.caption.slice(0, 60)}
                >
                  <img
                    src={post.image}
                    alt={post.caption.slice(0, 60)}
                    className="tg-photo-img"
                    onError={(e) => {
                      const btn = (e.currentTarget as HTMLImageElement).closest('.tg-photo');
                      if (btn) (btn as HTMLElement).style.display = 'none';
                    }}
                  />
                </button>
              );
            })}
            {extraPhotos > 0 && <span className="tg-strip-more">+{extraPhotos}</span>}
          </div>
        )}

        {dispatch && (
          <button
            type="button"
            className="tg-dispatch"
            onClick={() => onOpenStop(dispatch.id, allStopIds)}
          >
            <span className="tg-dispatch-badge">S</span>
            <span className="tg-dispatch-txt">
              <b>Dispatch</b>
              {(dispatch.post as SubstackPost).title
                ? ` · ${(dispatch.post as SubstackPost).title.slice(0, 40)}${(dispatch.post as SubstackPost).title.length > 40 ? '…' : ''}`
                : ''}
            </span>
            <span className="tg-dispatch-arr">→</span>
          </button>
        )}

        {status !== 'planned' && (
          <button type="button" className="tg-btn tg-btn-ghost" onClick={onExpand}>
            Open region
          </button>
        )}
      </div>
    </div>
  );
}

export default TripFeed;
