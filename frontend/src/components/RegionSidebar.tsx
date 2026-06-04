import { useEffect, useRef } from 'react';
import type { RegionGroup } from '../utils/regionUtils';
import { formatDateRange, formatDate, getEffectiveStopStatus } from '../utils/regionUtils';
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
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const activeAccordionRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!activeRegionCode) return;
    const container = scrollContainerRef.current;
    const target = activeAccordionRef.current;
    if (!container || !target) return;
    const offset = target.offsetTop - container.offsetTop;
    container.scrollTo({ top: offset, behavior: 'smooth' });
  }, [activeRegionCode]);

  return (
    <div className="region-sidebar" ref={scrollContainerRef}>
      {[...regionGroups].reverse().map((group) => {
        const isActive = group.region.code === activeRegionCode;
        return (
          <div
            key={group.region.code}
            className={`region-accordion ${isActive ? 'expanded' : 'collapsed'}`}
            ref={isActive ? activeAccordionRef : undefined}
          >
            <button
              type="button"
              className="region-accordion-header"
              onClick={() => onSelectRegion(group.region.code)}
              aria-expanded={isActive}
            >
              <div className="accordion-header-dot-col">
                <div className={`connector-dot ${group.overallStatus === 'abandoned' ? 'abandoned' : group.overallStatus === 'planned' ? 'planned' : 'visited'}`} />
              </div>
              <div className="accordion-header-text">
                <strong>{group.region.name}</strong>
                <span className="accordion-meta">{group.region.country} · {formatDateRange(group.startDate, group.endDate)}</span>
              </div>
              <span className="accordion-chevron" aria-hidden="true">{isActive ? '▲' : '▼'}</span>
            </button>

            {isActive && (() => {
              // FR-018 + FR-032: suppress planned and abandoned tiles when
              // any Instagram or Substack stop exists in the same region.
              const hasRichStop = group.stops.some(
                (s) => s.post.type === 'instagram' || s.post.type === 'substack'
              );
              const visibleStops = hasRichStop
                ? group.stops.filter((s) => s.post.type !== 'planned')
                : group.stops;
              const orderedIds = visibleStops.map((s) => s.id);
              const reversed = [...visibleStops].reverse();
              return (
                <div className="region-stop-list">
                  {reversed.map((stop, idx, arr) => {
                    const next = arr[idx + 1];
                    const nextIsAbandoned = next ? getEffectiveStopStatus(next) === 'abandoned' : false;
                    return (
                      <StopTile
                        key={stop.id}
                        stop={stop}
                        isLast={idx === arr.length - 1}
                        nextIsAbandoned={nextIsAbandoned}
                        onClick={() => {
                          if (stop.post.type === 'planned') return;
                          onOpenStop(stop.id, orderedIds);
                        }}
                      />
                    );
                  })}
                </div>
              );
            })()}
          </div>
        );
      })}
    </div>
  );
}

function StopTile({
  stop,
  isLast,
  nextIsAbandoned = false,
  onClick,
}: {
  stop: Stop;
  isLast: boolean;
  nextIsAbandoned?: boolean;
  onClick: () => void;
}) {
  const effective = getEffectiveStopStatus(stop);
  // FR-030: abandoned stops have no connector line, and the tile immediately
  // above an abandoned stop also omits its line so the abandoned stop sits
  // visually disconnected from its neighbors.
  const showLine = !isLast && effective !== 'abandoned' && !nextIsAbandoned;
  return (
    <div className={`stop-tile ${isLast ? 'last' : ''} ${effective === 'abandoned' ? 'abandoned' : ''}`}>
      <div className="stop-tile-connector">
        <div className={`connector-dot sm ${effective}`} />
        {showLine && <div className="connector-line" />}
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
