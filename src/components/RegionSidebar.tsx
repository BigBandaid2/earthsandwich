import type { RegionGroup } from '../utils/regionUtils';
import { formatDateRange, formatDate } from '../utils/regionUtils';
import type { Stop, InstagramPost, SubstackPost, PlannedPost } from '../data/types';

interface RegionSidebarProps {
  regionGroups: RegionGroup[];
  activeRegionCode: string | null;
  onSelectRegion: (regionCode: string) => void;
  onOpenStop: (stopId: string, contextStopIds: string[]) => void;
}

function RegionSidebar({
  regionGroups,
  activeRegionCode,
  onSelectRegion,
  onOpenStop,
}: RegionSidebarProps) {
  return (
    <div className="region-sidebar">
      {regionGroups.map((group) => {
        const isActive = group.region.code === activeRegionCode;
        return (
          <div key={group.region.code} className={`region-accordion ${isActive ? 'expanded' : 'collapsed'}`}>
            <button
              type="button"
              className="region-accordion-header"
              onClick={() => onSelectRegion(group.region.code)}
              aria-expanded={isActive}
            >
              <div className="accordion-header-dot-col">
                <div className={`connector-dot ${group.overallStatus !== 'planned' ? 'visited' : 'planned'}`} />
              </div>
              <div className="accordion-header-text">
                <strong>{group.region.name}</strong>
                <span className="accordion-meta">{group.region.country} · {formatDateRange(group.startDate, group.endDate)}</span>
              </div>
              <span className="accordion-chevron" aria-hidden="true">{isActive ? '▲' : '▼'}</span>
            </button>

            {isActive && (
              <div className="region-stop-list">
                {[...group.stops].reverse().map((stop, idx, arr) => (
                  <StopTile
                    key={stop.id}
                    stop={stop}
                    isLast={idx === arr.length - 1}
                    onClick={() => onOpenStop(stop.id, group.stops.map((s) => s.id))}
                  />
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function StopTile({ stop, isLast, onClick }: { stop: Stop; isLast: boolean; onClick: () => void }) {
  return (
    <div className={`stop-tile ${isLast ? 'last' : ''}`}>
      <div className="stop-tile-connector">
        <div className={`connector-dot sm ${stop.status}`} />
        {!isLast && <div className="connector-line" />}
      </div>
      <button type="button" className="stop-tile-content" onClick={onClick}>
        <div className="stop-tile-meta">
          <span className="stop-tile-location">{stop.location.split(',')[0]}</span>
          <span className="stop-tile-date">{formatDate(stop.date)}</span>
        </div>
        {stop.post.type === 'instagram' ? (
          <InstagramTileContent post={stop.post} />
        ) : stop.post.type === 'substack' ? (
          <SubstackTileContent post={stop.post} />
        ) : (
          <PlannedTileContent post={stop.post} />
        )}
      </button>
    </div>
  );
}

function InstagramTileContent({ post }: { post: InstagramPost }) {
  return (
    <div className="stop-tile-instagram">
      <div className="stop-tile-ig-header">
        <span className="ig-icon" aria-hidden="true">📸</span>
        <p className="stop-tile-caption">{post.caption}</p>
      </div>
      <img
        src={post.image}
        alt={post.caption.slice(0, 80)}
        className="stop-tile-photo"
        onError={(e) => {
          (e.currentTarget as HTMLImageElement).parentElement!.style.display = 'none';
        }}
      />
    </div>
  );
}

function SubstackTileContent({ post }: { post: SubstackPost }) {
  return (
    <div className="stop-tile-substack">
      <span className="substack-icon-sm" aria-hidden="true">📝</span>
      <div>
        <strong className="stop-tile-article-title">{post.title}</strong>
        {post.subtitle && <p className="stop-tile-article-preview">{post.subtitle}</p>}
        {post.body && (
          <p className="stop-tile-article-preview">{post.body.slice(0, 120)}{post.body.length > 120 ? '…' : ''}</p>
        )}
      </div>
    </div>
  );
}

function PlannedTileContent({ post }: { post: PlannedPost }) {
  return (
    <div className="stop-tile-planned">
      {post.caption && <p className="stop-tile-caption">{post.caption}</p>}
    </div>
  );
}

export default RegionSidebar;
