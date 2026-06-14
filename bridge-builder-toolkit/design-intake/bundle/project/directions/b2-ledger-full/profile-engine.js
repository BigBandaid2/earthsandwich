/* Ledger "Data profile" playground — shared engine.
   Context-free: a profile knows its DATASET only — never whether it is a pile
   or a target, nor which bridge project embeds it. The host supplies that role.

   Expects window.DATASET = {
     id, lsKey,                 // dataset id + localStorage namespace
     kind: 'files'|'relational',
     unitsLabel,                // 'files' | 'tables'
     unitCount,                 // 6 files / 3 tables
     DEFAULT: { objects, nodes, flags, sources, tables, edits: [] },
     SAMPLES, OVERVIEW,
     promptHeader               // first line of the copy-out prompt
   }
   Node: hard  = { kind:'hard', name, desc, from:[...], fields:[], keys:[], hidden }
         implied = { kind:'implied', name, desc, base, anchors:[...], hidden }
   Field row: { f, type, distinct, missing, mem, top, obs, ev, edited, pk, skey, fk, llm, ign }
*/
(function () {
  'use strict';
  var DS = window.DATASET;
  var REL = DS.kind === 'relational';
  var DEFAULT = DS.DEFAULT, SAMPLES = DS.SAMPLES, OVERVIEW = DS.OVERVIEW;
  var LS_CUR = 'b2pg.' + DS.lsKey + '.cur', LS_SAVES = 'b2pg.' + DS.lsKey + '.saves';
  var state, saves;
  function clone(o) { return JSON.parse(JSON.stringify(o)); }
  try { state = JSON.parse(localStorage.getItem(LS_CUR)) || clone(DEFAULT); } catch (e) { state = clone(DEFAULT); }
  try { saves = JSON.parse(localStorage.getItem(LS_SAVES)) || []; } catch (e) { saves = []; }
  /* migrate states saved before newer field metadata existed */
  (function migrate() {
    if (!state.tables || !state.objects || !state.nodes) { state = clone(DEFAULT); return; }
    Object.keys(state.nodes).forEach(function (k) {
      var n = state.nodes[k];
      if (n.kind === 'hard' && !n.from && n.files) { n.from = n.files; delete n.files; }
    });
    Object.keys(DEFAULT.tables).forEach(function (nid) {
      if (!state.tables[nid]) { state.tables[nid] = clone(DEFAULT.tables[nid]); return; }
      DEFAULT.tables[nid].forEach(function (dr) {
        var r = state.tables[nid].filter(function (x) { return x.f === dr.f; })[0];
        if (!r) return;
        if (typeof r.pk === 'undefined') { r.pk = dr.pk; r.skey = dr.skey; r.fk = dr.fk ? clone(dr.fk) : null; r.llm = dr.llm; }
        if (typeof r.ign === 'undefined') r.ign = false;
      });
    });
  })();

  function persist() { try { localStorage.setItem(LS_CUR, JSON.stringify(state)); } catch (e) {} updateStatus(); }
  function persistSaves() { try { localStorage.setItem(LS_SAVES, JSON.stringify(saves)); } catch (e) {} }
  function log(msg) { state.edits.push(msg); persist(); }
  function nowLabel() { var d = new Date(); return d.toISOString().slice(0, 16).replace('T', ' '); }
  function $(s, c) { return (c || document).querySelector(s); }
  function $all(s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
  function objOf(nodeId) { for (var i = 0; i < state.objects.length; i++) if (state.objects[i].nodes.indexOf(nodeId) > -1) return state.objects[i]; return null; }
  function impliedOf(baseId) { var out = []; for (var k in state.nodes) if (state.nodes[k].kind === 'implied' && state.nodes[k].base === baseId) out.push(k); return out; }
  function parsePct(s) { var m = /(\d+(?:\.\d+)?)%/.exec(s); return m ? parseFloat(m[1]) : (String(s) === '0' ? 0 : 100); }
  function keyRank(r) { return r.pk ? 0 : (r.fk ? 1 : (r.skey ? 2 : 3)); }

  /* ============ status + host hooks ============ */
  var statepill = document.getElementById('statepill');
  function updateStatus() {
    var n = state.edits.length;
    statepill.innerHTML = n === 0 ? 'LLM original' : 'edited · <b>' + n + ' change' + (n > 1 ? 's' : '') + '</b>' + (saves.length ? ' · ' + saves.length + ' saved' : '');
  }
  window.bbEditCount = function () { return state.edits.length; };
  window.bbPrompt = buildPrompt;

  /* ============ nodes & objects ============ */
  var objectsEl = document.getElementById('objects');
  function renderLineage() {
    var hard = 0, impl = 0;
    for (var k in state.nodes) { if (state.nodes[k].kind === 'hard') hard++; else impl++; }
    document.getElementById('lineage').innerHTML =
      '<span><b>' + DS.unitCount + '</b> ' + DS.unitsLabel + ' <span class="cap">' + (REL ? 'introspected schema' : 'raw deposits') + '</span></span><span class="arr">→</span>' +
      '<span><b>' + hard + '</b> nodes <span class="cap">' + (REL ? 'deterministic · one per table' : 'deterministic · shared signature') + '</span></span><span class="arr">→</span>' +
      '<span><b>' + impl + '</b> implied <span class="cap">LLM-inferred, no ' + (REL ? 'table' : 'file') + '</span></span><span class="arr">→</span>' +
      '<span><b>' + state.objects.length + '</b> objects <span class="cap">real-world entity</span></span>';
  }
  function nodeCard(nid) {
    var n = state.nodes[nid];
    var d = document.createElement('div');
    d.className = 'nodecard' + (n.hidden ? ' ignored' : '');
    d.draggable = true; d.setAttribute('data-node', nid);
    var fields = n.kind === 'hard' ? n.fields : (state.nodes[n.base] ? state.nodes[n.base].fields.filter(function (f) { return n.anchors.indexOf(f) > -1; }) : n.anchors);
    var sig = fields.map(function (f) { return (n.kind === 'hard' && n.keys.indexOf(f) > -1) ? '<span class="key">' + esc(f) + '</span>' : esc(f); }).join(' · ');
    var prov = n.kind === 'hard'
      ? n.from.map(function (f) { return (REL ? 'table <b>' : 'from <b>') + esc(f) + '</b>'; }).join('<br>')
      : 'implied from node <b>' + esc(state.nodes[n.base] ? state.nodes[n.base].name : '?') + '</b> · anchored by <b>' + n.anchors.join(', ') + '</b>';
    var unitTag = n.kind === 'hard' ? (REL ? 'table' : n.from.length + ' file' + (n.from.length > 1 ? 's' : '')) : 'no ' + (REL ? 'table' : 'table');
    d.innerHTML =
      '<div class="ncard-top"><span class="ncard-dot ' + n.kind + '"></span><span class="ncard-name">' + esc(n.name) + '</span>' +
      (n.kind === 'implied' ? '<span class="ncard-kind">implied</span>' : '') +
      '<span class="ncard-files">' + unitTag + '</span></div>' +
      '<div class="ncard-desc">' + esc(n.desc) + '</div>' +
      '<div class="ncard-sig">' + sig + '</div>' +
      '<div class="ncard-prov">' + prov + '</div>' +
      '<div class="ncard-foot"><button data-act="detail">Detail</button>' +
      (n.kind === 'hard' ? '<button data-act="fields">Fields</button>' : '<button data-act="base">Base node</button>') +
      '<button class="quiet" data-act="hide">' + (n.hidden ? 'Include' : 'Ignore') + '</button></div>';
    d.addEventListener('dragstart', function (e) { e.dataTransfer.setData('text/plain', nid); d.classList.add('dragging'); });
    d.addEventListener('dragend', function () { d.classList.remove('dragging'); });
    $all('[data-act]', d).forEach(function (b) {
      b.addEventListener('click', function (e) {
        e.stopPropagation();
        var act = b.getAttribute('data-act');
        if (act === 'detail') openNode(nid);
        else if (act === 'fields') openTakeover(nid, 'fields');
        else if (act === 'base') openNode(n.base);
        else if (act === 'hide') { n.hidden = !n.hidden; log((n.hidden ? 'Ignored' : 'Re-included') + ' node "' + n.name + '"'); renderObjects(); }
      });
    });
    return d;
  }
  function renderObjects() {
    objectsEl.innerHTML = '';
    state.objects.forEach(function (o) {
      var g = document.createElement('div');
      g.className = 'objgroup'; g.setAttribute('data-obj', o.id);
      var head = document.createElement('div'); head.className = 'ohead';
      head.innerHTML = '<span class="oname" contenteditable="true" spellcheck="false">' + esc(o.name) + '</span><span class="otag">object</span><span class="ocount">' + o.nodes.length + ' node' + (o.nodes.length !== 1 ? 's' : '') + '</span><button class="odel" type="button">✕ delete object</button>';
      var desc = document.createElement('p'); desc.className = 'odesc'; desc.contentEditable = 'true'; desc.spellcheck = false; desc.textContent = o.desc;
      var cards = document.createElement('div'); cards.className = 'nodecards';
      o.nodes.forEach(function (nid) { if (state.nodes[nid]) cards.appendChild(nodeCard(nid)); });
      if (!o.nodes.length) { var e = document.createElement('div'); e.style.cssText = 'padding:18px 0; font:italic 12px Georgia,serif; color:var(--ink-3);'; e.textContent = 'No nodes — drag one here, or delete this object.'; cards.appendChild(e); }
      $('.oname', head).addEventListener('blur', function () {
        var v = this.textContent.trim() || o.name;
        if (v !== o.name) { log('Renamed object "' + o.name + '" → "' + v + '"'); o.name = v; persist(); }
        this.textContent = o.name;
      });
      desc.addEventListener('blur', function () {
        var v = desc.textContent.trim();
        if (v !== o.desc) { o.desc = v; log('Edited description of object "' + o.name + '"'); }
      });
      $('.odel', head).addEventListener('click', function () {
        if (o.nodes.length) {
          var dest = state.objects.filter(function (x) { return x.id !== o.id; })[0];
          if (dest) { dest.nodes = dest.nodes.concat(o.nodes); }
        }
        state.objects = state.objects.filter(function (x) { return x.id !== o.id; });
        log('Deleted object "' + o.name + '"' + (o.nodes.length && state.objects.length ? ' (nodes moved to "' + state.objects[0].name + '")' : ''));
        renderObjects();
      });
      cards.addEventListener('dragover', function (e) { e.preventDefault(); cards.classList.add('dragover'); });
      cards.addEventListener('dragleave', function () { cards.classList.remove('dragover'); });
      cards.addEventListener('drop', function (e) {
        e.preventDefault(); cards.classList.remove('dragover');
        var nid = e.dataTransfer.getData('text/plain');
        var from = objOf(nid);
        if (!nid || !state.nodes[nid] || !from || from.id === o.id) return;
        from.nodes = from.nodes.filter(function (x) { return x !== nid; });
        o.nodes.push(nid);
        log('Moved node "' + state.nodes[nid].name + '" from object "' + from.name + '" to "' + o.name + '"');
        renderObjects();
      });
      g.appendChild(head); g.appendChild(desc); g.appendChild(cards);
      objectsEl.appendChild(g);
    });
    renderLineage(); renderGraph(); persist();
  }
  document.getElementById('new-obj').addEventListener('click', function () {
    state.objects.push({ id: 'o-' + Date.now(), name: 'New object', desc: 'Describe what real-world thing this object is, and why.', nodes: [] });
    log('Created object "New object"');
    renderObjects();
  });
  function renderGraph() {
    $all('[data-gnode]').forEach(function (g) {
      var n = state.nodes[g.getAttribute('data-gnode')];
      if (!n) { g.classList.add('off'); return; }
      g.classList.toggle('off', !!n.hidden);
      $('.nlabel', g).textContent = n.name;
    });
  }

  /* ============ node detail modal ============ */
  var curNode = null;
  function openNode(nid) {
    curNode = nid;
    var n = state.nodes[nid];
    $('#nd-title').textContent = (n.kind === 'implied' ? 'Implied node — ' : 'Node — ') + n.name;
    var prov = $('#nd-prov'); prov.className = 'prov ' + (n.kind === 'implied' ? 'llm' : 'baseline');
    prov.textContent = n.kind === 'implied' ? 'LLM-inferred' : 'deterministic';
    var b = $('#nd-body'), html = '';
    var nameLocked = n.kind === 'hard' && REL;
    html += '<div class="m-row"><label class="mlbl">Name ' + (nameLocked ? '<span style="color:var(--prov-baseline); text-transform:none; letter-spacing:0;">— deterministic, the table name</span>' : '<span style="color:var(--prov-llm); text-transform:none; letter-spacing:0;">— LLM-inferred, editable</span>') + '</label><input type="text" id="nd-name" value="' + esc(n.name) + '"' + (nameLocked ? ' readonly' : '') + '></div>';
    html += '<div class="m-row"><label class="mlbl">Description</label><textarea id="nd-desc">' + esc(n.desc) + '</textarea></div>';
    html += '<div class="m-row"><label class="mlbl">Member of object</label><select id="nd-obj">' + state.objects.map(function (o) { return '<option value="' + o.id + '"' + (objOf(nid) && objOf(nid).id === o.id ? ' selected' : '') + '>' + esc(o.name) + '</option>'; }).join('') + '</select></div>';
    if (n.kind === 'hard') {
      html += '<div class="m-row"><label class="mlbl">Provenance — deterministic</label><div class="mnote" style="margin:0; font-family:var(--mono); font-style:normal; font-size:12px; color:var(--ink-2);">' + n.from.map(esc).join('<br>') + '</div><p class="mnote">' + (REL ? 'One node per table — the schema is the fact.' : 'Every file sharing this ' + n.fields.length + '-field signature folds into this node. Signature and membership are facts, not inferences.') + '</p></div>';
      var imps = impliedOf(nid);
      html += '<div class="m-row"><label class="mlbl">Implied nodes derived from this node</label><ul class="impl-list" id="nd-impl">' +
        (imps.length ? imps.map(function (iid) { var im = state.nodes[iid]; return '<li><span>' + esc(im.name) + '</span><span class="anch">anchors: ' + im.anchors.join(', ') + '</span><span class="ia"><button data-iedit="' + iid + '">Edit</button><button class="quiet" data-idel="' + iid + '">Delete</button></span></li>'; }).join('') : '<li style="color:var(--ink-3); font-style:italic; font-family:var(--serif);">none yet</li>') +
        '</ul><button class="tbtn" id="nd-newimpl" type="button" style="margin-top:10px;">＋ New implied node</button><p class="mnote">An implied node is an entity this node\'s fields describe without a ' + (REL ? 'table' : 'table') + ' of its own — always anchored by one or more of its fields.</p></div>';
    } else {
      html += '<div class="m-row"><label class="mlbl">Base node</label><div class="mnote" style="margin:0;">Derived from <button class="tbtn" id="nd-gobase" type="button" style="margin-left:6px;">' + esc(state.nodes[n.base] ? state.nodes[n.base].name : '?') + ' →</button></div></div>';
      html += '<div class="m-row"><label class="mlbl">Anchor fields <span style="text-transform:none; letter-spacing:0;">— comma-separated, from the base node</span></label><input type="text" id="nd-anchors" value="' + n.anchors.join(', ') + '"><p class="mnote">Available on ' + esc(state.nodes[n.base] ? state.nodes[n.base].name : '?') + ': ' + (state.nodes[n.base] ? state.nodes[n.base].fields.join(' · ') : '') + '</p></div>';
    }
    b.innerHTML = html;
    var f = $('#nd-foot');
    f.innerHTML = (n.kind === 'hard' ? '<button class="tbtn" id="nd-fields" type="button">Full field detail →</button>' : '<button class="tbtn" id="nd-delete" type="button" style="border-color:var(--bad-rule); color:var(--bad);">Delete implied node</button>') +
      '<span class="spacer"></span><button class="tbtn" id="nd-hide" type="button">' + (n.hidden ? 'Include in profiling' : 'Ignore in profiling') + '</button><button class="tbtn amber" id="nd-done" type="button">Done</button>';
    if (n.kind === 'hard') {
      $('#nd-fields').addEventListener('click', function () { commitNode(); closeModals(); openTakeover(nid, 'fields'); });
      $('#nd-newimpl').addEventListener('click', function () {
        var iid = 'n-impl-' + Date.now();
        state.nodes[iid] = { kind: 'implied', name: 'new_implied', desc: 'Describe the implied entity.', base: nid, anchors: [n.fields[0]], hidden: false };
        objOf(nid).nodes.push(iid);
        log('Created implied node from "' + n.name + '"');
        renderObjects(); openNode(iid);
      });
      $all('[data-iedit]', b).forEach(function (x) { x.addEventListener('click', function () { openNode(x.getAttribute('data-iedit')); }); });
      $all('[data-idel]', b).forEach(function (x) {
        x.addEventListener('click', function () {
          var iid = x.getAttribute('data-idel'), im = state.nodes[iid];
          var o = objOf(iid); if (o) o.nodes = o.nodes.filter(function (y) { return y !== iid; });
          delete state.nodes[iid];
          log('Deleted implied node "' + im.name + '"');
          renderObjects(); openNode(nid);
        });
      });
    } else {
      $('#nd-gobase').addEventListener('click', function () { commitNode(); openNode(n.base); });
      $('#nd-delete').addEventListener('click', function () {
        var o = objOf(nid); if (o) o.nodes = o.nodes.filter(function (y) { return y !== nid; });
        delete state.nodes[nid];
        log('Deleted implied node "' + n.name + '"');
        renderObjects(); closeModals();
      });
    }
    $('#nd-hide').addEventListener('click', function () { n.hidden = !n.hidden; log((n.hidden ? 'Ignored' : 'Re-included') + ' node "' + n.name + '"'); renderObjects(); openNode(nid); });
    $('#nd-done').addEventListener('click', function () { commitNode(); closeModals(); });
    $('#m-node').classList.add('open');
  }
  function commitNode() {
    if (!curNode || !state.nodes[curNode]) return;
    var n = state.nodes[curNode];
    var nm = $('#nd-name'), ds = $('#nd-desc'), ob = $('#nd-obj'), an = $('#nd-anchors');
    if (nm && !nm.readOnly && nm.value.trim() && nm.value.trim() !== n.name) { log('Renamed node "' + n.name + '" → "' + nm.value.trim() + '"'); n.name = nm.value.trim(); }
    if (ds && ds.value.trim() !== n.desc) { n.desc = ds.value.trim(); log('Edited description of node "' + n.name + '"'); }
    if (ob) {
      var cur = objOf(curNode);
      if (cur && ob.value !== cur.id) {
        var dest = state.objects.filter(function (o) { return o.id === ob.value; })[0];
        if (dest) {
          cur.nodes = cur.nodes.filter(function (x) { return x !== curNode; });
          dest.nodes.push(curNode);
          log('Moved node "' + n.name + '" from object "' + cur.name + '" to "' + dest.name + '"');
        }
      }
    }
    if (an && n.kind === 'implied') {
      var v = an.value.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
      if (v.join() !== n.anchors.join()) { n.anchors = v; log('Changed anchors of implied node "' + n.name + '" to ' + v.join(', ')); }
    }
    renderObjects();
  }

  /* ============ flags ============ */
  function renderFlags() {
    var ul = document.getElementById('flaglist');
    ul.innerHTML = '';
    var live = state.flags.filter(function (f) { return !f.dismissed; });
    if (!live.length) { ul.innerHTML = '<li style="display:block; font:italic 12.5px Georgia,serif; color:var(--ink-3);">No open flags — all dismissed or commented.</li>'; }
    live.forEach(function (f) {
      var li = document.createElement('li');
      li.innerHTML = '<span class="rref">' + esc(f.ref) + ' <span class="flagchip' + (f.ext ? ' ext' : '') + '" style="margin-left:8px;">' + esc(f.chip) + '</span></span>' +
        '<span class="ract"><button data-fc="' + f.id + '">' + (f.comment ? 'Edit comment' : 'Comment') + '</button><button class="quiet" data-fd="' + f.id + '">Dismiss</button></span>' +
        '<span class="rwhy">' + esc(f.why) + '</span>' +
        (f.comment ? '<span class="rsaved"><b>your comment ·</b> ' + esc(f.comment) + '</span>' : '');
      ul.appendChild(li);
      $('[data-fc]', li).addEventListener('click', function () {
        if ($('.rcomment', li)) return;
        var w = document.createElement('span'); w.className = 'rcomment';
        w.innerHTML = '<textarea placeholder="Why this is (or isn\'t) a problem — carried into the re-profile prompt…">' + esc(f.comment) + '</textarea><button class="tbtn amber" type="button">Save</button>';
        li.appendChild(w);
        $('textarea', w).focus();
        $('button', w).addEventListener('click', function () {
          var v = $('textarea', w).value.trim();
          f.comment = v;
          log('Commented on flag ' + f.ref.split(' ')[0] + ': "' + v.slice(0, 60) + (v.length > 60 ? '…' : '') + '"');
          renderFlags();
        });
      });
      $('[data-fd]', li).addEventListener('click', function () {
        f.dismissed = true;
        log('Dismissed flag: ' + f.ref);
        renderFlags();
      });
    });
    persist();
  }

  /* ============ tables section ============ */
  var curTable = Object.keys(DEFAULT.tables)[0], tblFilter = '';
  function renderTblBar() {
    var bar = document.getElementById('tbl-bar');
    bar.innerHTML = '';
    Object.keys(state.tables).forEach(function (nid) {
      if (!state.nodes[nid]) return;
      var n = state.nodes[nid];
      var btn = document.createElement('button');
      btn.type = 'button'; btn.className = 'ttab' + (nid === curTable ? ' on' : '');
      btn.innerHTML = esc(n.name) + ' <span class="cnt">' + state.tables[nid].length + (n.hidden ? ' · ignored' : '') + '</span>';
      btn.addEventListener('click', function () { curTable = nid; tblFilter = ''; renderTables(); });
      bar.appendChild(btn);
    });
    var fl = document.createElement('input');
    fl.className = 'tfilter'; fl.placeholder = 'filter fields…'; fl.value = tblFilter;
    fl.addEventListener('input', function () { tblFilter = fl.value; renderTblBody(); });
    bar.appendChild(fl);
  }
  function renderTblBody() {
    var rows = state.tables[curTable] || [];
    var vis = rows.filter(function (r) { return !tblFilter || r.f.toLowerCase().indexOf(tblFilter.toLowerCase()) > -1; });
    var w = document.getElementById('tbl-wrap');
    w.innerHTML = '<table class="atable"><thead><tr>' +
      '<th class="bsrc">Field<span class="src">' + (REL ? 'schema baseline' : 'ydata baseline') + '</span></th><th class="bsrc">Type<span class="src">baseline</span></th>' +
      '<th class="bsrc">Distinct<span class="src">ydata</span></th><th class="bsrc">Missing<span class="src">ydata</span></th>' +
      '<th class="lsrc">AI observation &amp; evidence<span class="src">LLM-extended · editable</span></th></tr></thead><tbody>' +
      vis.map(function (r) {
        var tags = '';
        if (r.pk) tags += '<span class="ktag pk">PK</span>';
        if (r.fk && state.nodes[r.fk.node]) tags += '<span class="ktag fk">FK→' + esc(state.nodes[r.fk.node].name) + '</span>';
        if (r.llm) tags += '<span class="ktag llm">LLM</span>';
        if (r.ign) tags += '<span class="ktag ign">ignored</span>';
        return '<tr' + (r.ign ? ' class="ignrow"' : '') + '><td class="field">' + esc(r.f) + tags + '</td><td class="t">' + esc(r.type) + '</td><td class="num">' + esc(r.distinct) + '</td>' +
          '<td class="num">' + (r.missing.indexOf('·') > -1 ? '<span class="warnv">' + esc(r.missing) + '</span>' : esc(r.missing)) + '</td>' +
          '<td class="obs">' + esc(r.obs) + (r.edited ? '<span class="edited">edited</span>' : '') + '<span class="ev">evidence: ' + esc(r.ev) + '</span></td></tr>';
      }).join('') + '</tbody></table>';
    var note = document.getElementById('tbl-note');
    note.innerHTML = 'showing ' + vis.length + ' of ' + rows.length + ' fields · table = node "' + esc(state.nodes[curTable] ? state.nodes[curTable].name : '?') + '" · ';
    var btn = document.createElement('button');
    btn.type = 'button'; btn.textContent = 'Open table detail →';
    btn.addEventListener('click', function () { openTakeover(curTable, 'fields'); });
    note.appendChild(btn);
  }
  function renderTables() { renderTblBar(); renderTblBody(); }

  /* ============ table-detail takeover ============ */
  var tk = document.getElementById('tk');
  var tkNode = null, tkTab = 'fields', tkFilter = '', tkSort = 'order', tkSel = {};
  function openTakeover(nid, tab) {
    tkNode = nid; tkTab = tab || 'fields'; tkFilter = ''; tkSort = 'order'; tkSel = {};
    $('#tk-filter').value = ''; $('#tk-sort').value = 'order';
    clearWarn();
    tk.classList.add('open'); document.body.classList.add('tk-lock');
    renderTk();
  }
  function closeTakeover() {
    tk.classList.remove('open'); document.body.classList.remove('tk-lock');
    clearWarn(); renderTables(); renderObjects(); syncPkFlags();
  }
  $('#tk-close').addEventListener('click', closeTakeover);
  $('#tk-node').addEventListener('click', function () { if (tkNode) openNode(tkNode); });
  $all('[data-tktab]').forEach(function (b) { b.addEventListener('click', function () { tkTab = b.getAttribute('data-tktab'); renderTk(); }); });
  $('#tk-filter').addEventListener('input', function () { tkFilter = this.value; renderTkBody(); });
  $('#tk-sort').addEventListener('change', function () { tkSort = this.value; renderTkBody(); });
  $('#tk-dl').addEventListener('click', function () {
    var s = SAMPLES[tkNode]; if (!s) return;
    var tsv = s.map(function (r) { return r.join('\t'); }).join('\n');
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([tsv], { type: 'text/tab-separated-values' }));
    a.download = (state.nodes[tkNode] ? state.nodes[tkNode].name : 'node') + '.sample.tsv';
    document.body.appendChild(a); a.click(); a.remove();
    log('Downloaded raw sample data for node "' + state.nodes[tkNode].name + '"');
  });
  function clearWarn() { var w = $('#tk-warn'); if (w) w.innerHTML = ''; }
  function warn(msg, confirmLabel, onConfirm, info) {
    var w = $('#tk-warn');
    w.innerHTML = '<div class="tk-warnbar' + (info ? ' info' : '') + '"><span>' + msg + '</span><span class="wbtns">' +
      (onConfirm ? '<button class="tbtn amber" id="tw-ok" type="button">' + confirmLabel + '</button>' : '') +
      '<button class="tbtn" id="tw-no" type="button">' + (onConfirm ? 'Cancel' : 'Dismiss') + '</button></span></div>';
    if (onConfirm) $('#tw-ok').addEventListener('click', function () { clearWarn(); onConfirm(); });
    $('#tw-no').addEventListener('click', clearWarn);
    $('.tk-body', tk).scrollTop = 0;
  }
  function renderTk() {
    var n = state.nodes[tkNode]; if (!n) return;
    var rows = state.tables[tkNode] || [];
    var ov = OVERVIEW[tkNode] || { obs: '—', missing: 0, dup: 0, mem: '—' };
    $('#tk-title').textContent = 'Table — ' + n.name;
    $('#tk-meta').textContent = rows.length + ' fields · ' + ov.obs + ' sampled rows' + (n.from ? ' · ' + n.from.join(' + ') : '');
    $all('[data-tktab]').forEach(function (b) { b.classList.toggle('on', b.getAttribute('data-tktab') === tkTab); });
    renderTkBody();
  }
  function renderTkBody() {
    var rows = state.tables[tkNode] || [];
    var c = $('#tk-content');
    renderBatch();
    if (tkTab === 'overview') {
      var ov = OVERVIEW[tkNode] || {};
      var pk = rows.filter(function (r) { return r.pk; }).map(function (r) { return r.f; });
      var fks = rows.filter(function (r) { return r.fk; });
      var ign = rows.filter(function (r) { return r.ign; }).map(function (r) { return r.f; });
      var alerts = rows.filter(function (r) { return r.missing.indexOf('·') > -1; }).length + (pk.length ? 0 : 1);
      c.innerHTML = '<div class="tk-duo"><div><p class="blk-title">Dataset statistics</p><table class="tk-stat">' +
        '<tr><td class="k">Number of fields</td><td class="v">' + rows.length + '</td></tr>' +
        '<tr><td class="k">Sampled observations</td><td class="v">' + ov.obs + '</td></tr>' +
        '<tr><td class="k">Missing cells</td><td class="v">' + ov.missing + '</td></tr>' +
        '<tr><td class="k">Duplicate rows</td><td class="v">' + ov.dup + '</td></tr>' +
        '<tr><td class="k">Size in memory</td><td class="v">' + ov.mem + '</td></tr>' +
        '<tr><td class="k">Alerts</td><td class="v">' + alerts + '</td></tr></table></div>' +
        '<div><p class="blk-title">Variable types</p><table class="tk-stat"><tr><td class="k">Text</td><td class="v">' + rows.filter(function (r) { return !/INTEGER|REAL/.test(r.type); }).length + '</td></tr><tr><td class="k">Numeric</td><td class="v">' + rows.filter(function (r) { return /INTEGER|REAL/.test(r.type); }).length + '</td></tr></table>' +
        '<p class="blk-title">Keys</p><table class="tk-stat">' +
        '<tr><td class="k">Primary key</td><td class="v">' + (pk.join(' + ') || '— none (flagged)') + '</td></tr>' +
        fks.map(function (r) { return '<tr><td class="k">Foreign key</td><td class="v">' + esc(r.f) + ' → ' + esc(state.nodes[r.fk.node] ? state.nodes[r.fk.node].name : '?') + '.' + esc(r.fk.field) + '</td></tr>'; }).join('') +
        '<tr><td class="k">Searchable</td><td class="v">' + (rows.filter(function (r) { return r.skey; }).map(function (r) { return r.f; }).join(', ') || '—') + '</td></tr>' +
        '<tr><td class="k">Ignored fields</td><td class="v">' + (ign.join(', ') || '—') + '</td></tr></table></div></div>';
      return;
    }
    var idx = rows.map(function (r, i) { return i; });
    if (tkFilter) idx = idx.filter(function (i) { return rows[i].f.toLowerCase().indexOf(tkFilter.toLowerCase()) > -1; });
    if (tkSort === 'name') idx.sort(function (a, b) { return rows[a].f < rows[b].f ? -1 : 1; });
    else if (tkSort === 'distinct') idx.sort(function (a, b) { return parsePct(rows[b].distinct) - parsePct(rows[a].distinct); });
    else if (tkSort === 'missing') idx.sort(function (a, b) { return parsePct(rows[b].missing) - parsePct(rows[a].missing); });
    else if (tkSort === 'keys') idx.sort(function (a, b) { return keyRank(rows[a]) - keyRank(rows[b]); });
    var html = '<div class="tk-row head"><span></span><span>Field<span class="src b">baseline</span></span><span>Statistics<span class="src b">ydata baseline</span></span><span>Keys &amp; status<span class="src l">LLM-guessed · editable</span></span><span>AI observation &amp; evidence<span class="src l">LLM-extended · editable</span></span></div>';
    html += idx.map(function (i) {
      var r = rows[i];
      var fkSel = '';
      if (r.fk) {
        var others = Object.keys(state.nodes).filter(function (k) { return k !== tkNode && state.nodes[k].kind === 'hard'; });
        fkSel = '<span class="fkjoin"><select data-fknode="' + i + '">' + others.map(function (k) { return '<option value="' + k + '"' + (k === r.fk.node ? ' selected' : '') + '>' + esc(state.nodes[k].name) + '</option>'; }).join('') + '</select>' +
          '<select data-fkfield="' + i + '">' + (state.nodes[r.fk.node] ? state.nodes[r.fk.node].fields : []).map(function (f) { return '<option' + (f === r.fk.field ? ' selected' : '') + '>' + esc(f) + '</option>'; }).join('') + '</select></span>';
      }
      return '<div class="tk-row' + (r.ign ? ' ignored' : '') + '"><span><input type="checkbox" class="fsel" data-sel="' + i + '"' + (tkSel[i] ? ' checked' : '') + '></span>' +
        '<span><span class="fname">' + esc(r.f) + '</span><span class="ftype">' + esc(r.type) + (r.edited ? ' · <span style="color:var(--warn);">edited</span>' : '') + '</span></span>' +
        '<span class="fstats">distinct <b>' + esc(r.distinct) + '</b><br>missing <b>' + esc(r.missing) + '</b><br>memory <b>' + esc(r.mem) + '</b><br>top <b>' + esc(r.top) + '</b></span>' +
        '<span class="tk-keys">' +
        '<label><input type="checkbox" data-pk="' + i + '"' + (r.pk ? ' checked' : '') + '> primary key</label>' +
        '<label><input type="checkbox" data-sk="' + i + '"' + (r.skey ? ' checked' : '') + '> searchable key</label>' +
        '<label><input type="checkbox" data-fk="' + i + '"' + (r.fk ? ' checked' : '') + '> foreign key</label>' + fkSel +
        '<label><input type="checkbox" data-llm="' + i + '"' + (r.llm ? ' checked' : '') + '> LLM-inferred field</label>' +
        '<label class="dim"><input type="checkbox" data-ign="' + i + '"' + (r.ign ? ' checked' : '') + '> ignore field</label>' +
        '</span>' +
        '<span><textarea data-obs="' + i + '">' + esc(r.obs) + '</textarea><textarea class="ev" data-ev="' + i + '">' + esc(r.ev) + '</textarea></span></div>';
    }).join('');
    c.innerHTML = html;
    wireTkRows(rows);
  }
  function wireTkRows(rows) {
    var c = $('#tk-content');
    $all('[data-sel]', c).forEach(function (cb) { cb.addEventListener('change', function () { var i = +cb.getAttribute('data-sel'); if (cb.checked) tkSel[i] = true; else delete tkSel[i]; renderBatch(); }); });
    $all('[data-pk]', c).forEach(function (cb) {
      cb.addEventListener('change', function () {
        var i = +cb.getAttribute('data-pk'), r = rows[i], n = state.nodes[tkNode];
        cb.checked = r.pk;
        if (r.pk) {
          warn('Unset primary key <b>' + esc(r.f) + '</b>? Node “' + esc(n.name) + '” will be left with no primary key and flagged.', 'Unset primary key', function () {
            r.pk = false; log('Unset primary key on node "' + n.name + '"'); syncPkFlags(); renderTkBody();
          });
        } else {
          var cur = rows.filter(function (x) { return x.pk; }).map(function (x) { return x.f; });
          var dup = parsePct(r.distinct) < 100 || r.missing !== '0';
          var msg = cur.length ? 'Replace current primary key <b>' + esc(cur.join(' + ')) + '</b> with <b>' + esc(r.f) + '</b>?' : 'Set <b>' + esc(r.f) + '</b> as primary key?';
          if (dup) msg += ' <span style="color:var(--bad);">Warning: ' + esc(r.f) + ' is not fully distinct/present (' + esc(r.distinct) + ' distinct · ' + esc(r.missing) + ' missing) — loading will dedup &amp; truncate every record duplicating or missing it in the sample snapshot.</span>';
          warn(msg, 'Set primary key', function () {
            rows.forEach(function (x) { x.pk = false; });
            r.pk = true;
            log('Set primary key ' + r.f + ' on node "' + n.name + '"' + (cur.length ? ' (was ' + cur.join('+') + ')' : ''));
            syncPkFlags(); renderTkBody();
          });
        }
      });
    });
    $all('[data-sk]', c).forEach(function (cb) { cb.addEventListener('change', function () { var i = +cb.getAttribute('data-sk'), r = rows[i]; r.skey = cb.checked; log((r.skey ? 'Marked' : 'Unmarked') + ' ' + state.nodes[tkNode].name + '.' + r.f + ' as searchable key'); }); });
    $all('[data-fk]', c).forEach(function (cb) {
      cb.addEventListener('change', function () {
        var i = +cb.getAttribute('data-fk'), r = rows[i], n = state.nodes[tkNode];
        if (r.fk) {
          cb.checked = true;
          var tgt = (state.nodes[r.fk.node] ? state.nodes[r.fk.node].name : '?') + '.' + r.fk.field;
          warn('Remove foreign key <b>' + esc(n.name) + '.' + esc(r.f) + ' → ' + esc(tgt) + '</b>? This join will no longer be offered downstream.', 'Remove foreign key', function () {
            r.fk = null; log('Removed foreign key ' + n.name + '.' + r.f + ' → ' + tgt); renderTkBody();
          });
        } else {
          var guess = null;
          Object.keys(state.nodes).forEach(function (k) { if (!guess && k !== tkNode && state.nodes[k].kind === 'hard' && state.nodes[k].fields.indexOf(r.f) > -1) guess = { node: k, field: r.f }; });
          if (!guess) {
            var other = Object.keys(state.nodes).filter(function (k) { return k !== tkNode && state.nodes[k].kind === 'hard'; })[0];
            if (!other) return;
            guess = { node: other, field: state.nodes[other].fields[0] };
          }
          r.fk = guess;
          log('Marked ' + n.name + '.' + r.f + ' as foreign key → ' + state.nodes[guess.node].name + '.' + guess.field);
          renderTkBody();
        }
      });
    });
    $all('[data-fknode]', c).forEach(function (s) { s.addEventListener('change', function () { var i = +s.getAttribute('data-fknode'), r = rows[i]; r.fk.node = s.value; r.fk.field = state.nodes[s.value].fields[0]; log('Repointed foreign key ' + state.nodes[tkNode].name + '.' + r.f + ' → ' + state.nodes[s.value].name + '.' + r.fk.field); renderTkBody(); }); });
    $all('[data-fkfield]', c).forEach(function (s) { s.addEventListener('change', function () { var i = +s.getAttribute('data-fkfield'), r = rows[i]; r.fk.field = s.value; log('Repointed foreign key ' + state.nodes[tkNode].name + '.' + r.f + ' → ' + state.nodes[r.fk.node].name + '.' + s.value); }); });
    $all('[data-llm]', c).forEach(function (cb) { cb.addEventListener('change', function () { var i = +cb.getAttribute('data-llm'), r = rows[i]; r.llm = cb.checked; log((r.llm ? 'Marked' : 'Unmarked') + ' ' + state.nodes[tkNode].name + '.' + r.f + ' as LLM-inferred'); }); });
    $all('[data-ign]', c).forEach(function (cb) { cb.addEventListener('change', function () { var i = +cb.getAttribute('data-ign'), r = rows[i]; r.ign = cb.checked; log((r.ign ? 'Ignored' : 'Re-included') + ' field ' + state.nodes[tkNode].name + '.' + r.f); renderTkBody(); }); });
    $all('[data-obs]', c).forEach(function (t) { t.addEventListener('blur', function () { var r = rows[+t.getAttribute('data-obs')]; if (t.value.trim() !== r.obs) { r.obs = t.value.trim(); r.edited = true; log('Edited observation for ' + state.nodes[tkNode].name + '.' + r.f); } }); });
    $all('[data-ev]', c).forEach(function (t) { t.addEventListener('blur', function () { var r = rows[+t.getAttribute('data-ev')]; if (t.value.trim() !== r.ev) { r.ev = t.value.trim(); r.edited = true; log('Edited evidence for ' + state.nodes[tkNode].name + '.' + r.f); } }); });
  }
  function renderBatch() {
    var keys = Object.keys(tkSel);
    var b = $('#tk-batch');
    if (!keys.length || tkTab !== 'fields') { b.innerHTML = ''; return; }
    b.innerHTML = '<span class="bsel">' + keys.length + ' selected</span><button class="tbtn" id="tb-impl" type="button">Create implied node</button><button class="tbtn" id="tb-cpk" type="button">Create composite primary key</button>';
    $('#tb-impl').addEventListener('click', function () {
      var rows = state.tables[tkNode];
      var anchors = keys.map(function (i) { return rows[+i].f; });
      var iid = 'n-impl-' + Date.now();
      state.nodes[iid] = { kind: 'implied', name: 'implied_' + anchors[0], desc: 'Implied entity anchored by ' + anchors.join(', ') + ' — rename and describe it.', base: tkNode, anchors: anchors, hidden: false };
      objOf(tkNode).nodes.push(iid);
      log('Created implied node "implied_' + anchors[0] + '" from ' + state.nodes[tkNode].name + ' (anchors: ' + anchors.join(', ') + ')');
      tkSel = {};
      renderTkBody();
      warn('Implied node <b>implied_' + esc(anchors[0]) + '</b> created in object “' + esc(objOf(iid).name) + '” — rename and describe it from its node card.', null, null, true);
    });
    $('#tb-cpk').addEventListener('click', function () {
      var rows = state.tables[tkNode];
      var fields = keys.map(function (i) { return rows[+i].f; });
      var cur = rows.filter(function (x) { return x.pk; }).map(function (x) { return x.f; });
      var anyDup = keys.some(function (i) { return parsePct(rows[+i].distinct) < 100 || rows[+i].missing !== '0'; });
      var msg = 'Create composite primary key <b>(' + esc(fields.join(' + ')) + ')</b>' + (cur.length ? ', replacing <b>' + esc(cur.join(' + ')) + '</b>' : '') + '?';
      if (anyDup) msg += ' <span style="color:var(--bad);">Warning: not every part is fully distinct/present — the composite must be unique as a tuple or records will dedup &amp; truncate.</span>';
      warn(msg, 'Create composite key', function () {
        rows.forEach(function (x) { x.pk = false; });
        keys.forEach(function (i) { rows[+i].pk = true; });
        log('Created composite primary key (' + fields.join(' + ') + ') on node "' + state.nodes[tkNode].name + '"' + (cur.length ? ' (was ' + cur.join('+') + ')' : ''));
        tkSel = {}; syncPkFlags(); renderTkBody();
      });
    });
  }
  function syncPkFlags() {
    Object.keys(state.tables).forEach(function (nid) {
      var n = state.nodes[nid]; if (!n) return;
      var has = state.tables[nid].some(function (r) { return r.pk; });
      var fid = 'nopk-' + nid;
      var existing = state.flags.filter(function (f) { return f.id === fid; })[0];
      if (!has && !existing) state.flags.push({ id: fid, ref: 'node ' + n.name, chip: 'no primary key', ext: true, why: 'No field is marked primary key — records cannot be idempotently re-loaded. Pick one (or a composite) in the table detail.', comment: '', dismissed: false });
      if (has && existing) state.flags = state.flags.filter(function (f) { return f.id !== fid; });
    });
    renderFlags();
  }

  /* ============ sources ============ */
  function renderSources() {
    var ul = document.getElementById('srcrows');
    ul.innerHTML = '';
    state.sources.forEach(function (s) {
      var li = document.createElement('li');
      li.className = s.excluded ? 'off' : '';
      li.innerHTML = '<span><span class="sname">' + esc(s.name) + '</span><span class="surl">' + esc(s.url) + '</span>' + (s.added ? ' <span class="prov llm" style="margin-left:8px;">user-added</span>' : '') + '</span>' +
        '<span class="sact"><button data-sx="' + s.id + '">' + (s.excluded ? 'Include' : 'Exclude') + '</button>' + (s.added ? '<button class="quiet" data-sr="' + s.id + '">Remove</button>' : '') + '</span>' +
        '<span class="suse">' + esc(s.use) + '</span>';
      ul.appendChild(li);
      $('[data-sx]', li).addEventListener('click', function () {
        s.excluded = !s.excluded;
        log((s.excluded ? 'Excluded' : 'Re-included') + ' source "' + s.name + '"');
        renderSources();
      });
      var rm = $('[data-sr]', li);
      if (rm) rm.addEventListener('click', function () {
        state.sources = state.sources.filter(function (x) { return x.id !== s.id; });
        log('Removed source "' + s.name + '"');
        renderSources();
      });
    });
    persist();
  }
  document.getElementById('src-add').addEventListener('click', function () {
    var inp = document.getElementById('src-url'), v = inp.value.trim();
    if (!v) { inp.focus(); return; }
    var name = v.replace(/^https?:\/\//, '').split('/')[0];
    state.sources.push({ id: 's' + Date.now(), name: name, url: v, use: 'User-supplied reference — will be consulted on the next re-profile.', excluded: false, added: true });
    log('Added source link "' + name + '"');
    inp.value = '';
    renderSources();
  });
  document.getElementById('src-upload').addEventListener('click', function () { document.getElementById('src-file').click(); });
  document.getElementById('src-file').addEventListener('change', function () {
    var f = this.files && this.files[0]; if (!f) return;
    state.sources.push({ id: 's' + Date.now(), name: f.name, url: 'uploaded file · ' + Math.round(f.size / 1024) + ' KB', use: 'User-uploaded reference document — will be consulted on the next re-profile.', excluded: false, added: true });
    log('Uploaded source file "' + f.name + '"');
    this.value = '';
    renderSources();
  });

  /* ============ save states ============ */
  var saveBtn = document.getElementById('save-btn'), saveDd = document.getElementById('save-dd');
  function renderSaves() {
    var w = document.getElementById('save-items');
    var items = '<button class="dd-item" data-restore="-1"><span>LLM original</span><span class="when">' + DS.snapshotLabel + '</span></button>';
    saves.forEach(function (s, i) {
      items += '<button class="dd-item" data-restore="' + i + '"><span>' + esc(s.label) + ' · ' + s.n + ' edit' + (s.n !== 1 ? 's' : '') + '</span><span class="when">' + esc(s.ts) + '</span></button>';
    });
    w.innerHTML = items;
    $all('[data-restore]', w).forEach(function (b) {
      b.addEventListener('click', function () {
        var i = +b.getAttribute('data-restore');
        state = i === -1 ? clone(DEFAULT) : JSON.parse(saves[i].snap);
        persist();
        renderObjects(); syncPkFlags(); renderTables(); renderSources();
        saveDd.classList.remove('open');
      });
    });
  }
  saveBtn.addEventListener('click', function () {
    if (saveDd.classList.contains('open')) { saveDd.classList.remove('open'); return; }
    if (state.edits.length) {
      saves.push({ ts: nowLabel(), label: 'save ' + (saves.length + 1), n: state.edits.length, snap: JSON.stringify(state) });
      persistSaves();
    }
    renderSaves();
    saveDd.classList.add('open');
    updateStatus();
  });

  /* ============ prompt ============ */
  function buildPrompt() {
    var L = [];
    L.push(DS.promptHeader);
    L.push('Human-reviewed playground state' + (saves.length ? ' · ' + saves.length + ' saved state(s)' : '') + ' · ' + state.edits.length + ' edit(s) since LLM original.');
    L.push('');
    L.push('## Objects & nodes (human-reviewed)');
    state.objects.forEach(function (o) {
      L.push('- Object "' + o.name + '" — ' + o.desc);
      o.nodes.forEach(function (nid) {
        var n = state.nodes[nid]; if (!n) return;
        if (n.kind === 'hard') {
          L.push('  - node ' + n.name + (n.hidden ? ' [IGNORED]' : '') + ' (deterministic; ' + (REL ? 'table' : 'files') + ': ' + n.from.join(', ') + ') fields: ' + n.fields.join(', '));
          var rows = state.tables[nid] || [];
          var pk = rows.filter(function (r) { return r.pk; }).map(function (r) { return r.f; });
          var fks = rows.filter(function (r) { return r.fk; }).map(function (r) { return r.f + '→' + (state.nodes[r.fk.node] ? state.nodes[r.fk.node].name : '?') + '.' + r.fk.field; });
          var sk = rows.filter(function (r) { return r.skey; }).map(function (r) { return r.f; });
          var lm = rows.filter(function (r) { return r.llm; }).map(function (r) { return r.f; });
          var ig = rows.filter(function (r) { return r.ign; }).map(function (r) { return r.f; });
          L.push('    keys: pk=' + (pk.join('+') || 'NONE') + (fks.length ? '; fk: ' + fks.join(', ') : '') + (sk.length ? '; searchable: ' + sk.join(', ') : '') + (lm.length ? '; llm-inferred fields: ' + lm.join(', ') : '') + (ig.length ? '; IGNORED FIELDS: ' + ig.join(', ') : ''));
        }
        else L.push('  - node ' + n.name + (n.hidden ? ' [IGNORED]' : '') + ' (implied from ' + (state.nodes[n.base] ? state.nodes[n.base].name : '?') + '; anchors: ' + n.anchors.join(', ') + ') — ' + n.desc);
      });
    });
    L.push('');
    L.push('## Flagged references');
    state.flags.forEach(function (f) {
      L.push('- ' + f.ref + ' [' + f.chip + ']' + (f.dismissed ? ' [DISMISSED by reviewer]' : '') + (f.comment ? ' [reviewer comment: ' + f.comment + ']' : ''));
    });
    L.push('');
    L.push('## Public-knowledge sources');
    state.sources.forEach(function (s) {
      L.push('- ' + s.name + ' (' + s.url + ')' + (s.excluded ? ' [EXCLUDED by reviewer]' : '') + (s.added ? ' [added by reviewer]' : '') + ' — ' + s.use);
    });
    var ed = [];
    for (var nid in state.tables) state.tables[nid].forEach(function (r) { if (r.edited) ed.push('- ' + (state.nodes[nid] ? state.nodes[nid].name : nid) + '.' + r.f + ': "' + r.obs + '" (evidence: ' + r.ev + ')'); });
    if (ed.length) { L.push(''); L.push('## Reviewer-edited field observations'); L = L.concat(ed); }
    if (state.edits.length) {
      L.push(''); L.push('## Human edit log (chronological)');
      state.edits.forEach(function (e, i) { L.push((i + 1) + '. ' + e); });
    }
    L.push('');
    L.push('Goal: with this feedback incorporated, the next re-profile should one-shot a profile that requires no further edits.');
    return L.join('\n');
  }
  var copyBtn = document.getElementById('copy-btn'), copyPop = document.getElementById('copy-pop'), copyTa = document.getElementById('copy-payload');
  copyBtn.addEventListener('click', function () {
    copyTa.value = buildPrompt();
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(copyTa.value).then(function () {
        copyBtn.classList.add('copied'); copyBtn.textContent = 'Copied';
        setTimeout(function () { copyBtn.classList.remove('copied'); copyBtn.textContent = 'Copy out a prompt'; }, 1600);
      }, function () { copyPop.classList.add('open'); copyTa.focus(); copyTa.select(); });
    } else { copyPop.classList.add('open'); copyTa.focus(); copyTa.select(); }
  });

  /* ============ chrome ============ */
  function closeModals() { $all('.modal-overlay.open').forEach(function (m) { m.classList.remove('open'); }); }
  $all('[data-close]').forEach(function (b) { b.addEventListener('click', function () { if (b.closest('#m-node')) commitNode(); closeModals(); }); });
  $all('.modal-overlay').forEach(function (m) { m.addEventListener('click', function (e) { if (e.target === m) { if (m.id === 'm-node') commitNode(); closeModals(); } }); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      if ($('.modal-overlay.open')) { commitNode(); closeModals(); return; }
      saveDd.classList.remove('open'); copyPop.classList.remove('open');
      if (tk.classList.contains('open')) closeTakeover();
    }
  });
  document.addEventListener('click', function (e) {
    if (saveDd.classList.contains('open') && !saveDd.contains(e.target) && e.target !== saveBtn) saveDd.classList.remove('open');
    if (copyPop.classList.contains('open') && !copyPop.contains(e.target) && e.target !== copyBtn) copyPop.classList.remove('open');
  });
  var tabs = $all('.pg-tabs a');
  tabs.forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      var el = $(a.getAttribute('href'));
      if (el) document.scrollingElement.scrollTop = el.offsetTop - 60;
    });
  });
  var secs = ['s1', 's2', 's3', 's4'].map(function (id) { return document.getElementById(id); });
  function onScroll() {
    var y = document.scrollingElement.scrollTop + 90, cur = 0;
    secs.forEach(function (s, i) { if (s && s.offsetTop <= y) cur = i; });
    tabs.forEach(function (a, i) { a.classList.toggle('on', i === cur); });
  }
  document.addEventListener('scroll', onScroll, { passive: true });

  /* ============ boot ============ */
  renderObjects(); syncPkFlags(); renderTables(); renderSources(); updateStatus(); onScroll();
})();
