import type { RegionGroup } from '../utils/regionUtils';
import { formatDateRange } from '../utils/regionUtils';
import type { Trip, InstagramPost, Stop } from '../data/types';

interface TripFeedProps {
  regionGroups: RegionGroup[];
  trip: Trip;
  onExpandRegion: (regionCode: string) => void;
  onOpenStop: (stopId: string, contextStopIds: string[]) => void;
}

function TripFeed({ regionGroups, onExpandRegion, onOpenStop }: TripFeedProps) {
  // FR-031: split into Visited / Planned / Abandoned sections. Mixed regions
  // count as visited; fully-abandoned regions get their own section.
  const visited = regionGroups.filter(
    (g) => g.overallStatus === 'visited' || g.overallStatus === 'mixed'
  );
  const planned = regionGroups.filter((g) => g.overallStatus === 'planned');
  const abandoned = regionGroups.filter((g) => g.overallStatus === 'abandoned');

  return (
    <div className="trip-feed">
      {visited.length > 0 && (
        <section className="feed-section">
          <h2 className="feed-section-title">Visited</h2>
          <div className="region-list">
            {[...visited].reverse().map((group, idx, arr) => (
              <RegionTile
                key={group.region.code}
                group={group}
                isLast={idx === arr.length - 1}
                onExpand={() => onExpandRegion(group.region.code)}
                onOpenStop={onOpenStop}
              />
            ))}
          </div>
        </section>
      )}
      {planned.length > 0 && (
        <section className="feed-section">
          <h2 className="feed-section-title">Planned</h2>
          <div className="region-list">
            {[...planned].reverse().map((group, idx, arr) => (
              <RegionTile
                key={group.region.code}
                group={group}
                isLast={idx === arr.length - 1}
                onExpand={() => onExpandRegion(group.region.code)}
                onOpenStop={onOpenStop}
              />
            ))}
          </div>
        </section>
      )}
      {abandoned.length > 0 && (
        <section className="feed-section">
          <h2 className="feed-section-title">Abandoned</h2>
          <div className="region-list">
            {[...abandoned].reverse().map((group, idx, arr) => (
              <RegionTile
                key={group.region.code}
                group={group}
                isLast={idx === arr.length - 1}
                onExpand={() => onExpandRegion(group.region.code)}
                onOpenStop={onOpenStop}
              />
            ))}
          </div>
        </section>
      )}
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
  const visiblePhotos = instagramStops.slice(0, 4);
  const extraPhotos = instagramStops.length > 4 ? instagramStops.length - 4 : 0;
  const visibleSubstack = substackStops.slice(0, 4);
  const extraSubstack = substackStops.length > 4 ? substackStops.length - 4 : 0;

  return (
    <div className={`region-tile ${isLast ? 'last' : ''} ${group.overallStatus === 'abandoned' ? 'abandoned' : ''}`}>
      <div className="region-tile-connector">
        <div className={`connector-dot ${group.overallStatus === 'abandoned' ? 'abandoned' : group.overallStatus === 'planned' ? 'planned' : 'visited'}`} />
        {!isLast && group.overallStatus !== 'abandoned' && <div className="connector-line" />}
      </div>

      <div className="region-tile-content">
        <div className="region-tile-header">
          <strong className="region-name">{group.region.name}</strong>
          <button type="button" className="expand-region-btn inline" onClick={onExpand}>
            Expand →
          </button>
          <span className="region-country">{group.region.country}</span>
          <span className="region-dates">{formatDateRange(group.startDate, group.endDate)}</span>
        </div>

        {visiblePhotos.length > 0 && (
          <div className="photo-strip">
            {visiblePhotos.map((stop, idx) => {
              const post = stop.post as InstagramPost;
              const isLast4 = idx === 3 && extraPhotos > 0;
              return (
                <button
                  key={stop.id}
                  type="button"
                  className="photo-thumb-btn"
                  onClick={() => onOpenStop(stop.id, allStopIds)}
                  aria-label={`View: ${post.caption.slice(0, 60)}`}
                >
                  <img
                    src={post.image}
                    alt={post.caption.slice(0, 60)}
                    className="photo-thumb"
                    onError={(e) => {
                      (e.currentTarget as HTMLImageElement).style.display = 'none';
                    }}
                  />
                  {isLast4 && (
                    <span className="photo-overflow">+{extraPhotos}</span>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {visibleSubstack.length > 0 && (
          <div className="substack-tiles">
            {visibleSubstack.map((stop, idx) => {
              const isLast4 = idx === 3 && extraSubstack > 0;
              return (
                <SubstackTileItem
                  key={stop.id}
                  stop={stop}
                  extra={isLast4 ? extraSubstack : 0}
                  onClick={() => onOpenStop(stop.id, allStopIds)}
                />
              );
            })}
          </div>
        )}

      </div>
    </div>
  );
}

function SubstackTileItem({
  stop,
  extra,
  onClick,
}: {
  stop: Stop;
  extra: number;
  onClick: () => void;
}) {
  if (stop.post.type !== 'substack') return null;
  const post = stop.post;

  return (
    <button type="button" className="substack-tile" onClick={onClick}>
      <span className="substack-icon" aria-hidden="true">📝</span>
      <div className="substack-tile-text">
        <span className="substack-title">{post.title}</span>
        {post.subtitle && <span className="substack-preview">{post.subtitle}</span>}
      </div>
      {extra > 0 && <span className="substack-overflow">+{extra}</span>}
    </button>
  );
}

export default TripFeed;
