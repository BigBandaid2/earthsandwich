import { useState, useEffect } from 'react';
import type { Stop } from '../data/types';
import type { RegionGroup } from '../utils/regionUtils';
import { formatDate } from '../utils/regionUtils';
import isoCountries from 'i18n-iso-countries';
import enLocale from 'i18n-iso-countries/langs/en.json';

isoCountries.registerLocale(enLocale);

const COUNTRY_ALIASES: Record<string, string> = { 'Micronesia': 'FM' };
function isoForCountry(country: string): string | undefined {
  return (COUNTRY_ALIASES[country] ?? isoCountries.getAlpha2Code(country, 'en'))?.toLowerCase();
}

interface StopModalProps {
  stop: Stop;
  stopList: string[];
  allStops: Stop[];
  regionGroups: RegionGroup[];
  onClose: () => void;
  onNav: (direction: 'prev' | 'next') => void;
}

export default function StopModal({ stop, stopList, regionGroups, onClose, onNav }: StopModalProps) {
  const idx = stopList.indexOf(stop.id);
  const hasPrev = idx > 0;
  const hasNext = idx < stopList.length - 1;

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      else if (e.key === 'ArrowLeft' && hasPrev) onNav('prev');
      else if (e.key === 'ArrowRight' && hasNext) onNav('next');
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [hasPrev, hasNext, onClose, onNav]);

  const regionGroup = regionGroups.find((g) => g.region.code === stop.regionCode);
  const iso = regionGroup ? isoForCountry(regionGroup.region.country) : undefined;
  const tripName = 'Earth Club Sandwich';
  const regionName = regionGroup?.region.name ?? stop.regionCode;
  const dateStr = formatDate(stop.date);

  const isInstagram = stop.post.type === 'instagram';
  const isSubstack = stop.post.type === 'substack';
  const topLayout = false; // default side layout

  return (
    <div className="pd-overlay" role="dialog" aria-modal="true" aria-label="Post detail">
      <div className="pd-dim" onClick={onClose} />

      <button
        type="button"
        className="pd-stopnav prev"
        disabled={!hasPrev}
        onClick={() => onNav('prev')}
        aria-label="Previous post"
      >
        ‹
      </button>

      <div
        className={`pd-card${topLayout ? ' is-top' : ''}`}
        data-kind={isInstagram ? 'instagram' : isSubstack ? 'substack' : 'planned'}
        data-layout={topLayout ? 'top' : 'side'}
      >
        <button className="pd-close" onClick={onClose} aria-label="Close">✕</button>

        {isInstagram && (
          <>
            <InstaMedia stop={stop} />
            <InstaBody
              stop={stop}
              iso={iso}
              tripName={tripName}
              regionName={regionName}
              dateStr={dateStr}
            />
          </>
        )}

        {isSubstack && (
          <>
            <DispatchCover
              stop={stop}
              regionName={regionName}
              dateStr={dateStr}
            />
            <DispatchBody
              stop={stop}
              iso={iso}
              tripName={tripName}
              regionName={regionName}
              dateStr={dateStr}
            />
          </>
        )}

        {!isInstagram && !isSubstack && (
          <PlannedView stop={stop} regionName={regionName} dateStr={dateStr} />
        )}
      </div>

      <button
        type="button"
        className="pd-stopnav next"
        disabled={!hasNext}
        onClick={() => onNav('next')}
        aria-label="Next post"
      >
        ›
      </button>
    </div>
  );
}

// ── Instagram media panel ──
function InstaMedia({ stop }: { stop: Stop }) {
  const post = stop.post.type === 'instagram' ? stop.post : null;
  if (!post) return null;

  // Single image — treat as a one-image "carousel"
  const [idx, setIdx] = useState(0);
  useEffect(() => { setIdx(0); }, [stop.id]);
  const images = [post.image].filter(Boolean);
  const n = images.length;

  return (
    <div className="pd-media">
      <div className="pd-photo">
        {images[idx] ? (
          <div className="frame">
            <img
              src={images[idx]}
              alt={post.caption.slice(0, 80)}
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).style.display = 'none';
              }}
            />
          </div>
        ) : (
          <div className="frame" style={{ background: 'var(--surface-sunk)' }} />
        )}
      </div>
      <span className="loc">📍 {stop.location.split(',')[0]}</span>
      {n > 1 && (
        <>
          <span className="count">{idx + 1} / {n}</span>
          <button className="pd-arrow prev" onClick={() => setIdx((v) => (v - 1 + n) % n)} aria-label="Previous photo">‹</button>
          <button className="pd-arrow next" onClick={() => setIdx((v) => (v + 1) % n)} aria-label="Next photo">›</button>
          <div className="pd-dots">
            {images.map((_, k) => <i key={k} className={k === idx ? 'on' : ''} />)}
          </div>
        </>
      )}
    </div>
  );
}

// ── Instagram body panel ──
function InstaBody({
  stop, iso, tripName, regionName, dateStr,
}: {
  stop: Stop; iso?: string; tripName: string; regionName: string; dateStr: string;
}) {
  const post = stop.post.type === 'instagram' ? stop.post : null;
  if (!post) return null;

  const igUrl = post.shortcode ? `https://www.instagram.com/p/${post.shortcode}/` : null;

  return (
    <div className="pd-body">
      <div className="pd-crumb">
        {iso && <img className="flag" src={`https://flagcdn.com/${iso}.svg`} alt="" />}
        <span>{tripName}</span>
        <span className="sep">/</span>
        <span className="region">{regionName}</span>
      </div>

      <div className="pd-daterow">
        <span className="pd-date">{dateStr}</span>
      </div>

      <div className="pd-kicker">Snapshot</div>
      <h2 className="pd-title">{stop.location.split(',')[0]}</h2>
      <p className="pd-caption">{post.caption}</p>

      <span className="pd-stamp" aria-hidden="true">
        <span className="r">★ VISITED ★</span>
        <span className="p">{regionName}</span>
        <span className="r">{dateStr.toUpperCase()}</span>
      </span>

      <div className="pd-foot">
        <div className="pd-source">
          <span className="badge ig" aria-hidden="true">◉</span>
          <span className="handle">@earthsandwich</span>
        </div>
        {igUrl
          ? <a className="pd-extlink" href={igUrl} target="_blank" rel="noopener noreferrer">On Instagram ↗</a>
          : <span className="pd-extlink is-soon">On Instagram</span>}
      </div>
    </div>
  );
}

// ── Substack side cover ──
function DispatchCover({
  stop, regionName, dateStr,
}: {
  stop: Stop; regionName: string; dateStr: string;
}) {
  const post = stop.post.type === 'substack' ? stop.post : null;
  if (!post) return null;

  const year = dateStr.match(/\d{4}/)?.[0] ?? '';
  const noCover = true; // real data has no cover image yet → typographic fallback

  return (
    <div className={`pd-cover${noCover ? ' is-empty' : ''}`}>
      <div className="masthead">
        <span>The Dispatch</span>
        <span className="ln" />
        <span>No. —</span>
      </div>
      <div className="cover-stamp" aria-hidden="true">
        <span className="s1">EST.</span>
        <span className="big">{regionName.slice(0, 3).toUpperCase()}</span>
        <span className="s2">{year}</span>
      </div>
      {!noCover && (
        <span className="pd-cover-slot" aria-hidden="true">
          <span className="ic">⌖</span>
          <span>cover photo loads here</span>
        </span>
      )}
      <div className="cover-title">{post.title}</div>
    </div>
  );
}

// ── Substack body panel ──
function DispatchBody({
  stop, iso, tripName, regionName, dateStr,
}: {
  stop: Stop; iso?: string; tripName: string; regionName: string; dateStr: string;
}) {
  const post = stop.post.type === 'substack' ? stop.post : null;
  if (!post) return null;

  const paragraphs = post.body
    ? post.body.split('\n\n').filter(Boolean)
    : [];

  return (
    <div className="pd-body">
      <div className="pd-crumb">
        {iso && <img className="flag" src={`https://flagcdn.com/${iso}.svg`} alt="" />}
        <span>{tripName}</span>
        <span className="sep">/</span>
        <span className="region">{regionName}</span>
      </div>

      <div className="pd-kicker">Field Dispatch</div>

      <div className="pd-daterow">
        <span className="pd-date">{dateStr}</span>
        <span className="pd-meta">{stop.location.split(',')[0]}</span>
      </div>

      <h2 className="pd-title">{post.title}</h2>
      {post.subtitle && <p className="pd-dek">{post.subtitle}</p>}

      <div className="pd-divider" />

      <div className="pd-prose">
        {paragraphs.map((para, i) => (
          <p key={i}>{para}</p>
        ))}
      </div>

      <div className="pd-end">
        <span className="pd-end-rule" />
        <div className="pd-end-row">
          <span className="pd-byline">
            <span className="badge-s">S</span>
            A dispatch by @earthsandwich
          </span>
          <span className="pd-extlink is-soon">Also on Substack</span>
        </div>
      </div>
    </div>
  );
}

// ── Planned stop view ──
function PlannedView({
  stop, regionName, dateStr,
}: {
  stop: Stop; regionName: string; dateStr: string;
}) {
  return (
    <div className="pd-body">
      <div className="pd-kicker">Planned Stop</div>
      <h2 className="pd-title">{stop.location.split(',')[0]}</h2>
      <div className="pd-daterow">
        <span className="pd-date">{dateStr}</span>
      </div>
      {stop.post.type === 'planned' && stop.post.caption && (
        <p className="pd-caption">{stop.post.caption}</p>
      )}
      <div className="pd-foot">
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--ink-faint)' }}>
          {regionName} — coming soon
        </span>
      </div>
    </div>
  );
}
