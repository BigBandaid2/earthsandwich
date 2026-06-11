// Travelogue — PostDetail component (postcard spread). Postmark direction.
// Renders an Instagram photo post OR a Substack dispatch from a normalized
// `post` object. Exported to window for the app + showcase to mount.
(function () {
  const { useState, useEffect } = React;

  function img(hue) { return `linear-gradient(150deg, hsl(${hue} 44% 64%), hsl(${(hue + 36) % 360} 40% 44%))`; }
  function flagSrc(iso) { return 'https://flagcdn.com/' + iso + '.svg'; }

  // ── Instagram body ──
  function InstaBody({ post }) {
    return (
      <div className="pd-body">
        <div className="pd-crumb">
          <img className="flag" src={flagSrc(post.iso)} alt="" />
          <span>{post.trip}</span><span className="sep">/</span><span className="region">{post.region}</span>
        </div>
        <div className="pd-daterow">
          <span className="pd-date">{post.date}</span>
        </div>
        <div className="pd-kicker">Snapshot</div>
        <h2 className="pd-title">{post.location}</h2>
        <p className="pd-caption">{post.caption}</p>

        <span className="pd-stamp" aria-hidden="true">
          <span className="r">★ VISITED ★</span>
          <span className="p">{post.region}</span>
          <span className="r">{post.stampDate}</span>
        </span>

        <div className="pd-foot">
          <div className="pd-source">
            <span className="badge ig">◉</span>
            <span className="handle">{post.handle}</span>
          </div>
          {post.url
            ? <a className="pd-extlink" href={post.url} target="_blank" rel="noopener noreferrer">On Instagram ↗</a>
            : <span className="pd-extlink is-soon">On Instagram</span>}
        </div>
      </div>
    );
  }

  // ── Substack body ──
  function DispatchBody({ post, hideTitle }) {
    return (
      <div className="pd-body">
        <div className="pd-crumb">
          <img className="flag" src={flagSrc(post.iso)} alt="" />
          <span>{post.trip}</span><span className="sep">/</span><span className="region">{post.region}</span>
        </div>
        <div className="pd-kicker">Field Dispatch · No. {post.no}</div>
        <div className="pd-daterow">
          <span className="pd-date">{post.date}</span>
          <span className="pd-meta">{post.readMins} min read · {post.location}</span>
        </div>
        {!hideTitle && <h2 className="pd-title">{post.title}</h2>}
        {post.dek && <p className="pd-dek">{post.dek}</p>}
        <div className="pd-divider" />
        <div className="pd-prose">
          {post.body.map((b, i) => {
            if (typeof b === 'string') return <p key={i}>{b}</p>;
            if (b.sub) return <h3 className="pd-sub" key={i}>{b.sub}</h3>;
            if (b.quote) return <blockquote className="pd-quote" key={i}>{b.quote}</blockquote>;
            return null;
          })}
          <div className="pd-end">
            <span className="pd-end-rule" aria-hidden="true" />
            <div className="pd-end-row">
              <span className="pd-byline"><span className="badge-s">S</span>A dispatch by {post.handle}</span>
              {post.url
                ? <a className="pd-extlink" href={post.url} target="_blank" rel="noopener noreferrer">Open on Substack ↗</a>
                : <span className="pd-extlink is-soon">Also on Substack</span>}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── Substack cover as a horizontal top banner (alt layout) ──
  function DispatchBanner({ post }) {
    const empty = !!post.noCover;
    return (
      <div className={'pd-banner' + (empty ? ' is-empty' : '')} style={empty ? undefined : { background: img(post.hue) }}>
        <div className="masthead"><span>The Dispatch</span><span className="ln" /><span>No. {post.no}</span></div>
        <div className="cover-stamp" aria-hidden="true"><span className="s1">EST.</span><span className="big">{post.stampCode || '★'}</span><span className="s2">{post.stampYear || ''}</span></div>
        <h2 className="pd-banner-title">{post.title}</h2>
      </div>
    );
  }

  // ── Media panels ──
  function InstaMedia({ post }) {
    const [i, setI] = useState(0);
    const n = post.images.length;
    useEffect(() => { setI(0); }, [post]);
    const go = (d) => setI((v) => (v + d + n) % n);
    return (
      <div className="pd-media">
        <div className="pd-photo">
          <span className="frame" style={{ backgroundImage: img(post.images[i]) }} />
        </div>
        {n > 1 && <span className="count">{i + 1} / {n}</span>}
        <span className="loc">📍 {post.location}</span>
        {n > 1 && (
          <>
            <button className="pd-arrow prev" onClick={() => go(-1)} aria-label="Previous photo">‹</button>
            <button className="pd-arrow next" onClick={() => go(1)} aria-label="Next photo">›</button>
            <div className="pd-dots">{post.images.map((_, k) => <i key={k} className={k === i ? 'on' : ''} />)}</div>
          </>
        )}
      </div>
    );
  }

  function DispatchCover({ post }) {
    const empty = !!post.noCover;
    return (
      <div className={'pd-cover' + (empty ? ' is-empty' : '')} style={empty ? undefined : { background: img(post.hue) }}>
        <div className="masthead"><span>The Dispatch</span><span className="ln" /><span>No. {post.no}</span></div>
        <div className="cover-stamp" aria-hidden="true"><span className="s1">EST.</span><span className="big">{post.stampCode || '★'}</span><span className="s2">{post.stampYear || ''}</span></div>
        {!empty && (
          <span className="pd-cover-slot" aria-hidden="true">
            <span className="ic">⌖</span>
            <span>cover photo loads here</span>
          </span>
        )}
        <div className="cover-title">{post.coverLine || post.title}</div>
      </div>
    );
  }

  // ── Frame ──
  function PostDetail({ post, onClose, onPrev, onNext, hasPrev, hasNext, embedded }) {
    useEffect(() => {
      if (embedded) return;
      const k = (e) => {
        if (e.key === 'Escape') onClose && onClose();
        else if (e.key === 'ArrowLeft' && hasPrev) onPrev && onPrev();
        else if (e.key === 'ArrowRight' && hasNext) onNext && onNext();
      };
      window.addEventListener('keydown', k);
      return () => window.removeEventListener('keydown', k);
    }, [post, hasPrev, hasNext, embedded]);

    const isSub = post.kind === 'substack';
    const topLayout = isSub && post.layout === 'top';
    const card = (
      <div
        className={'pd-card' + (embedded ? ' is-embedded' : '') + (topLayout ? ' is-top' : '')}
        data-kind={post.kind}
        data-layout={topLayout ? 'top' : 'side'}
      >
        <button className="pd-close" onClick={onClose} aria-label="Close">✕</button>
        {topLayout
          ? <React.Fragment><DispatchBanner post={post} /><DispatchBody post={post} hideTitle /></React.Fragment>
          : isSub
            ? <React.Fragment><DispatchCover post={post} /><DispatchBody post={post} /></React.Fragment>
            : <React.Fragment><InstaMedia post={post} /><InstaBody post={post} /></React.Fragment>}
      </div>
    );

    if (embedded) return card;

    return (
      <div className="pd-overlay" role="dialog" aria-modal="true">
        <div className="pd-dim" onClick={onClose} />
        <button className="pd-stopnav prev" disabled={!hasPrev} onClick={onPrev} aria-label="Previous stop">‹</button>
        {card}
        <button className="pd-stopnav next" disabled={!hasNext} onClick={onNext} aria-label="Next stop">›</button>
      </div>
    );
  }

  window.PostDetail = PostDetail;
})();
