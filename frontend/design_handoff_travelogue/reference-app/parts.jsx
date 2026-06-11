// Travelogue App — components + mount. Postmark direction.
const { useState } = React;
const D = window.TGDATA;

// striped placeholder for a thumbnail
function stripe(hue) {
  return `repeating-linear-gradient(135deg, hsl(${hue} 30% 64%) 0 9px, hsl(${hue} 34% 56%) 9px 18px)`;
}
function duotone(hue) {
  return `linear-gradient(150deg, hsl(${hue} 42% 66%), hsl(${(hue + 38) % 360} 38% 46%))`;
}

// ── Flag pin ───────────────────────────────────────────────
function FlagPin({ r, onClick }) {
  const cls = 'tg-flag' + (r.open ? ' is-open' : '') + (r.status === 'planned' ? ' planned' : '');
  return (
    <span className={cls} style={{ left: r.x + '%', top: r.y + '%' }}>
      <span className="tg-flag-pole" aria-hidden="true" />
      <span className="tg-flag-base" aria-hidden="true" />
      <span className="tg-flag-banner" onClick={onClick} title={r.name}>
        <img className="tg-flag-img" src={'https://flagcdn.com/' + r.iso + '.svg'} alt=""
          onError={(e) => { e.currentTarget.style.display = 'none'; e.currentTarget.parentElement.textContent = r.iso.toUpperCase(); }} />
      </span>
      {r.open && <span className="tg-flag-name">{r.name}</span>}
    </span>
  );
}

// small satellite flags to evoke per-stop clustering
const SAT = [ [2.4, -1.6], [-2.6, 1.4], [3.4, 2.2], [-1.8, -2.4] ];
function Satellites({ r }) {
  if (r.status === 'planned') return null;
  const n = Math.min(r.stopCount - 1, 4);
  const out = [];
  for (let i = 0; i < n; i++) {
    const [dx, dy] = SAT[i];
    out.push(
      <span key={i} className="tg-flag" style={{ left: (r.x + dx) + '%', top: (r.y + dy) + '%', height: '20px', zIndex: 2, opacity: 0.92 }}>
        <span className="tg-flag-pole" aria-hidden="true" />
        <span className="tg-flag-base" aria-hidden="true" />
        <span className="tg-flag-banner" style={{ width: '17px', height: '12px' }}>
          <img className="tg-flag-img" src={'https://flagcdn.com/' + r.iso + '.svg'} alt=""
            onError={(e) => { e.currentTarget.style.display = 'none'; }} />
        </span>
      </span>
    );
  }
  return <>{out}</>;
}

// ── Route: solid directional line + arrowheads, dashed planned leg ──
function RouteLayer({ regions }) {
  const solid = regions.filter((r) => r.status !== 'planned');
  const solidD = solid.map((r, i) => (i ? 'L' : 'M') + r.x + ',' + r.y).join(' ');
  const planned = regions.find((r) => r.status === 'planned');
  const lastSolid = solid[solid.length - 1];
  const dashedD = planned ? `M${lastSolid.x},${lastSolid.y} L${planned.x},${planned.y}` : null;

  const arrows = [];
  for (let i = 1; i < solid.length; i++) {
    const a = solid[i - 1], b = solid[i];
    arrows.push({ key: i, mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2, ang: Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI });
  }
  return (
    <div className="tg-routelayer" aria-hidden="true">
      <svg className="tg-route" viewBox="0 0 100 100" preserveAspectRatio="none">
        {dashedD && <path className="tg-route-planned" d={dashedD} />}
        <path className="tg-route-main" d={solidD} />
      </svg>
      {arrows.map((ar) => (
        <span key={ar.key} className="tg-arrow" style={{ left: ar.mx + '%', top: ar.my + '%', '--a': ar.ang + 'deg' }}>
          <span className="tg-arrow-head" />
        </span>
      ))}
    </div>
  );
}

// ── Region tile ───────────────────────────────────────────
function RegionTile({ r, last, onPhoto, onDispatch }) {
  return (
    <div className={'tg-tile ' + r.status}>
      <div className="tg-tile-rail">
        <span className={'tg-dot ' + r.status} />
        {!last && <span className="tg-rail-line" />}
      </div>
      <div className="tg-tile-body">
        <div className="tg-tile-head">
          <h3 className="tg-tile-name">{r.name}</h3>
          <span className="tg-tile-date">{r.dates}</span>
        </div>
        <div className="tg-tile-country">{r.country}</div>
        {r.photos.length > 0 && (
          <div className="tg-strip">
            {r.photos.map((p, i) => (
              <button key={i} className="tg-photo" onClick={() => onPhoto(r, i)} aria-label={p.location}>
                <span className="tg-photo-img" style={{ background: stripe(p.hue) }} />
              </button>
            ))}
            {r.extra ? <span className="tg-strip-more">+{r.extra}</span> : null}
          </div>
        )}
        {r.dispatch && (
          <button type="button" className="tg-dispatch" onClick={() => onDispatch(r)}>
            <span className="tg-dispatch-badge">S</span>
            <span className="tg-dispatch-txt"><b>Dispatch</b> · {r.dispatch.readMins} min read</span>
            <span className="tg-dispatch-arr">→</span>
          </button>
        )}
        {r.note && <p className={'tg-note' + (r.status === 'planned' ? ' planned' : '')}>{r.note}</p>}
        {r.status !== 'planned' && <button className="tg-btn tg-btn-ghost">Open region</button>}
      </div>
    </div>
  );
}

// ── Stop modal removed: app now uses the shared PostDetail (detail.jsx) ──

// Build a flat, ordered list of normalized posts from the trip's regions.
// Each region contributes its Instagram photos, then its Substack dispatch.
function buildPosts() {
  const posts = [];
  const index = {}; // lookup keys → post position
  D.regions.forEach((r) => {
    r.photos.forEach((p, i) => {
      const n = p.count || 1;
      const images = [];
      for (let k = 0; k < n; k++) images.push((p.hue + k * 26) % 360);
      index[r.code + '-p' + i] = posts.length;
      posts.push({
        kind: 'instagram', trip: D.trip.name, region: r.name, iso: r.iso,
        date: r.dates, stampDate: r.dates.toUpperCase(), handle: '@earthsandwich',
        location: p.location, caption: p.caption, images,
      });
    });
    if (r.dispatch) {
      const d = r.dispatch;
      index[r.code + '-d'] = posts.length;
      posts.push({
        kind: 'substack', trip: D.trip.name, region: r.name, iso: r.iso,
        date: r.dates, no: d.no, readMins: d.readMins, handle: '@earthsandwich',
        hue: d.hue, stampCode: r.code, stampYear: (r.dates.match(/\d{4}/) || [''])[0],
        location: d.location, title: d.title, coverLine: d.title, dek: d.dek, body: d.body,
      });
    }
  });
  return { posts, index };
}

// ── App ───────────────────────────────────────────────────
function App() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [open, setOpen] = useState(null); // post index or null

  const { posts, index } = React.useMemo(buildPosts, []);
  const PostDetail = window.PostDetail;

  const openPhoto = (region, i) => {
    const pi = index[region.code + '-p' + i];
    if (pi != null) setOpen(pi);
  };
  const openDispatch = (region) => {
    const pi = index[region.code + '-d'];
    if (pi != null) setOpen(pi);
  };
  const openRegionFirst = (region) => {
    if (index[region.code + '-d'] != null) return openDispatch(region);
    if (region.photos.length) return openPhoto(region, 0);
  };

  return (
    <div className="tg-app">
      {/* Map */}
      <div className="tg-map">
        <span className="tg-map-grid" aria-hidden="true" />
        <span className="tg-map-coord">restyled Google map · stop by stop</span>
        <div className="tg-postmark" aria-hidden="true">
          <div className="tg-postmark-ring">
            <span className="tg-postmark-top">PAR AVION</span>
            <span className="tg-postmark-star">✶</span>
            <span className="tg-postmark-bot">VIA AIR MAIL</span>
          </div>
          <span className="tg-cancel" /><span className="tg-cancel" /><span className="tg-cancel" />
        </div>
        <RouteLayer regions={D.regions} />
        {D.regions.map((r) => <Satellites key={'s' + r.code} r={r} />)}
        {D.regions.map((r) => <FlagPin key={r.code} r={r} onClick={() => openRegionFirst(r)} />)}

        <div className="tg-tripbar">
          <button className="tg-burger" aria-label="Trips" onClick={() => setMenuOpen((v) => !v)}>≡</button>
          <span className="tg-tripbar-title">{D.trip.name}</span>
          <span className="tg-tripbar-count">{D.trip.stops} stops</span>
          {menuOpen && (
            <div className="tg-tripmenu">
              {D.trips.map((t) => (
                <button key={t.id} className={'tg-tripmenu-item' + (t.active ? ' active' : '')} onClick={() => setMenuOpen(false)}>
                  <span className="tg-tripmenu-name">{t.name}</span>
                  <span className="tg-tripmenu-meta">{t.meta}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Sidebar */}
      <aside className="tg-feed">
        <div className="tg-feed-head">
          <div className="eyebrow">A collection of adventures</div>
          <h1 className="tg-feed-title">{D.trip.name}</h1>
          <div className="tg-feed-sub"><span className="script">{D.trip.blurb}</span> stop by stop</div>
          <div className="tg-feed-meta">
            <span><b>{D.trip.visited}</b> visited</span><span className="tg-feed-meta-dot" />
            <span><b>{D.trip.planned}</b> planned</span><span className="tg-feed-meta-dot" />
            <span><b>{D.trip.countries}</b> countries</span>
          </div>
        </div>
        <div className="tg-feed-scroll">
          <div className="tg-feed-section">Itinerary</div>
          {D.regions.map((r, i) => (
            <RegionTile key={r.code} r={r} last={i === D.regions.length - 1} onPhoto={openPhoto} onDispatch={openDispatch} />
          ))}
        </div>
      </aside>

      {open !== null && PostDetail && (
        <PostDetail
          post={posts[open]}
          onClose={() => setOpen(null)}
          onPrev={() => setOpen((i) => Math.max(0, i - 1))}
          onNext={() => setOpen((i) => Math.min(posts.length - 1, i + 1))}
          hasPrev={open > 0}
          hasNext={open < posts.length - 1}
        />
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
