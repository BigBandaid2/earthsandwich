import type { Stop } from '../data/types';
import type { RegionGroup } from '../utils/regionUtils';
import { formatDate } from '../utils/regionUtils';

interface StopModalProps {
  stop: Stop;
  stopList: string[];
  allStops: Stop[];
  regionGroups: RegionGroup[];
  onClose: () => void;
  onNav: (direction: 'prev' | 'next') => void;
}

function StopModal({ stop, stopList, regionGroups, onClose, onNav }: StopModalProps) {
  const idx = stopList.indexOf(stop.id);
  const canPrev = idx > 0;
  const canNext = idx < stopList.length - 1;

  const regionGroup = regionGroups.find((g) => g.region.code === stop.regionCode);

  const igUrl =
    stop.post.type === 'instagram'
      ? `https://www.instagram.com/p/${stop.post.shortcode}/`
      : null;

  const breadcrumb = [
    regionGroup?.region.name ?? stop.regionCode,
    stop.location.split(',')[0],
    formatDate(stop.date),
  ];

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="Stop detail">
      <div className="modal-dim" onClick={onClose} />

      <button
        type="button"
        className="modal-nav-btn modal-nav-prev"
        onClick={() => onNav('prev')}
        disabled={!canPrev}
        aria-label="Previous stop"
      >
        ‹
      </button>

      <div className="modal-content">
        <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close">
          ✕
        </button>

        <nav className="modal-breadcrumb" aria-label="Breadcrumb">
          {breadcrumb.map((crumb, i) => (
            <span key={i}>
              {i > 0 && <span className="breadcrumb-sep"> / </span>}
              {i === 2 && igUrl ? (
                <a href={igUrl} target="_blank" rel="noopener noreferrer" className="breadcrumb-ig-link">{crumb}</a>
              ) : crumb}
            </span>
          ))}
        </nav>

        {stop.post.type === 'instagram' ? (
          <InstagramPostView stop={stop} igUrl={igUrl!} />
        ) : (
          <SubstackPostView stop={stop} />
        )}
      </div>

      <button
        type="button"
        className="modal-nav-btn modal-nav-next"
        onClick={() => onNav('next')}
        disabled={!canNext}
        aria-label="Next stop"
      >
        ›
      </button>
    </div>
  );
}

function InstagramPostView({ stop, igUrl }: { stop: Stop; igUrl: string }) {
  if (stop.post.type !== 'instagram') return null;
  const post = stop.post;

  return (
    <article className="post-instagram">
      <h1 className="post-heading">{stop.location}</h1>
      <p className="post-subheading">{post.caption}</p>
      <a href={igUrl} target="_blank" rel="noopener noreferrer" className="post-hero-link">
        <img
          src={post.image}
          alt={post.caption.slice(0, 80)}
          className="post-hero-image"
          onError={(e) => {
            (e.currentTarget as HTMLImageElement).parentElement!.parentElement!.insertAdjacentHTML(
              'beforeend',
              '<p class="image-unavailable">Image no longer available</p>'
            );
            (e.currentTarget as HTMLImageElement).parentElement!.style.display = 'none';
          }}
        />
      </a>
    </article>
  );
}

function SubstackPostView({ stop }: { stop: Stop }) {
  if (stop.post.type !== 'substack') return null;
  const post = stop.post;

  return (
    <article className="post-substack">
      <h1 className="post-heading">{post.title}</h1>
      {post.subtitle && <p className="post-subheading">{post.subtitle}</p>}
      <div className="post-body">
        {post.body.split('\n\n').map((para, i) => (
          <p key={i}>{para}</p>
        ))}
      </div>
    </article>
  );
}

export default StopModal;
