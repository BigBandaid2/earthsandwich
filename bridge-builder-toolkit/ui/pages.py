"""Server-rendered HTML layer for the guided Web UI — b2-ledger redesign (FR-179/184).

A persistent left-rail app-shell (workspace nav + per-project nav) in the warm
"paper / serif / amber" system from the Claude Design handoff. Vanilla HTML via
``html.escape``; no template engine, no external assets. The CSS is ported
verbatim from the design's `style.css`.
"""
from __future__ import annotations

import html
import json
from urllib.parse import quote

from common.config import BridgeProject

# --- design system, ported from design-intake/bundle/.../b2-ledger-full/style.css ---
_CSS = """
:root{color-scheme:dark;--paper:#171512;--paper-deep:#11100d;--rail:#131109;--rail-bg:#131110;--ink:#eae6dd;--ink-2:#aaa291;--ink-3:#7c7464;--rule:#2f2b23;--rule-soft:#262219;--accent:#d3a35a;--accent-dim:#4f3f25;--ok:#97c9a4;--warn:#d9b36c;--bad:#dd8d95;--bad-rule:#54323a;--ok-rule:#2c4434;--serif:Georgia,"Times New Roman",serif;--sans:system-ui,sans-serif;--mono:ui-monospace,"Cascadia Mono",Menlo,Consolas,monospace;}
html.light{color-scheme:light;--paper:#f5f1e8;--paper-deep:#ece7da;--rail-bg:#efeadd;--ink:#2b261d;--ink-2:#6d6555;--ink-3:#98907e;--rule:#d8d0bd;--rule-soft:#e3dccb;--accent:#a3712a;--accent-dim:#d4bb90;--ok:#3e7d52;--warn:#92702c;--bad:#b04a56;--bad-rule:#ddb3b8;--ok-rule:#b9d2bf;}
*{box-sizing:border-box;}
body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.6 var(--sans);}
.shell{display:grid;grid-template-columns:232px minmax(0,1fr);min-height:100vh;}
aside.rail{background:var(--rail-bg);border-right:1px solid var(--rule);padding:26px 22px;display:flex;flex-direction:column;gap:0;position:sticky;top:0;height:100vh;overflow-y:auto;}
.rail .wordmark{font:400 19px/1.2 var(--serif);color:var(--ink);text-decoration:none;display:block;padding-bottom:18px;border-bottom:1px solid var(--rule);}
.rail .wordmark i{font-style:italic;color:var(--accent);}
.rail .navgroup{padding:18px 0 4px;}
.rail .navgroup+.navgroup{border-top:1px solid var(--rule-soft);margin-top:14px;}
.rail .navgroup .gtitle{font:400 12px/1 var(--serif);font-style:italic;color:var(--ink-3);margin:0 0 10px;}
.rail .navgroup .gtitle.proj{font:600 10px/1.5 var(--sans);font-style:normal;letter-spacing:.13em;text-transform:uppercase;color:var(--ink-2);overflow-wrap:anywhere;}
.rail nav{display:flex;flex-direction:column;gap:1px;}
.rail nav a,.rail nav span.navitem{display:flex;align-items:baseline;gap:8px;font:600 10.5px/1.5 var(--sans);letter-spacing:.13em;text-transform:uppercase;color:var(--ink-3);text-decoration:none;padding:7px 0 7px 12px;border-left:1px solid transparent;}
.rail nav a:hover{color:var(--accent);}
.rail nav a.here{color:var(--ink);border-left-color:var(--accent);}
.rail nav span.navitem.soon{color:var(--ink-3);opacity:.5;}
.rail nav span.navitem .mini{font:400 11px/1.2 var(--serif);font-style:italic;letter-spacing:.02em;text-transform:none;color:var(--ink-3);}
.rail .railfoot{margin-top:auto;padding-top:16px;border-top:1px solid var(--rule-soft);font:400 11.5px/1.6 var(--serif);font-style:italic;color:var(--ink-3);}
main.content{padding:30px 42px 80px;min-width:0;}
.pagetitle{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;margin:0 0 4px;padding-bottom:14px;border-bottom:1px solid var(--rule);}
.pagetitle h1{margin:0;font:400 28px/1.2 var(--serif);letter-spacing:-.01em;}
.pagetitle .sub{font:12px/1.5 var(--mono);color:var(--ink-3);}
.pagetitle .right{margin-left:auto;display:flex;align-items:baseline;gap:14px;}
.pagetitle .right a{font:600 10.5px/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--accent);text-decoration:none;border-bottom:1px solid var(--accent-dim);padding-bottom:2px;}
.lede{color:var(--ink-2);font-size:14px;max-width:70ch;margin:12px 0 0;}
section.sheet{border-top:1px solid var(--rule);margin-top:30px;padding-top:14px;}
section.sheet.first{border-top:none;margin-top:22px;padding-top:0;}
.sheet-head{display:flex;align-items:baseline;gap:12px;margin-bottom:16px;}
.sheet-head .no{font:400 13px/1 var(--serif);font-style:italic;color:var(--accent);min-width:26px;}
.sheet-head h2{margin:0;font:600 11px/1.5 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--ink-2);flex:1;}
.sheet-head a.action{font:600 10.5px/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--accent);text-decoration:none;border-bottom:1px solid var(--accent-dim);padding-bottom:2px;}
.status{display:inline-flex;align-items:center;gap:8px;font:600 10.5px/1 var(--sans);letter-spacing:.13em;text-transform:uppercase;}
.status .tick{font-size:12px;}
.status.ok{color:var(--ok);}.status.warn{color:var(--warn);}.status.bad{color:var(--bad);}.status.dim{color:var(--ink-3);}
.report{margin:0;font:12.5px/1.9 var(--mono);color:var(--ink);overflow-x:auto;}
.confirms{display:flex;gap:40px;flex-wrap:wrap;align-items:baseline;}
.confirm{display:flex;align-items:baseline;gap:11px;}
.confirm .tick{font:12px/1 var(--mono);}
.confirm .what{font:600 10.5px/1.5 var(--sans);letter-spacing:.13em;text-transform:uppercase;}
.confirm.ok .tick,.confirm.ok .what{color:var(--ok);}
.confirm.bad .tick,.confirm.bad .what{color:var(--bad);}
.confirm .where{font:12px/1.5 var(--mono);color:var(--ink-3);}
.cmd{display:flex;align-items:stretch;gap:12px;max-width:880px;}
.cmd pre{flex:1;margin:0;padding:13px 16px;background:var(--paper-deep);border:1px solid var(--rule);border-left:2px solid var(--accent);font:13px/1.5 var(--mono);color:var(--ink);overflow-x:auto;white-space:pre;}
button.copy{padding:0 18px;border:1px solid var(--rule);background:transparent;color:var(--ink-2);font:600 10.5px/1 var(--sans);letter-spacing:.13em;text-transform:uppercase;cursor:pointer;}
button.copy:hover{border-color:var(--accent);color:var(--accent);}
button.copy.copied{border-color:var(--ok);color:var(--ok);}
.alts{margin-top:18px;max-width:880px;}
.alts-title{font:400 12px/1 var(--serif);font-style:italic;color:var(--ink-3);margin-bottom:10px;}
.alt{display:flex;align-items:baseline;gap:12px;padding:6px 0;border-top:1px solid var(--rule-soft);}
.alt code{flex:1;font:12px/1.6 var(--mono);color:var(--ink-2);overflow-x:auto;white-space:pre;}
.note{font:400 12.5px/1.6 var(--serif);font-style:italic;color:var(--ink-3);margin-top:14px;max-width:64ch;}
.track{list-style:none;margin:0;padding:0;max-width:880px;}
.track>li{display:grid;grid-template-columns:26px minmax(0,1fr) auto;align-items:baseline;gap:0 14px;padding:16px 0;border-top:1px solid var(--rule-soft);}
.track>li:first-child{border-top:none;}
.track .tn{font:400 13px/1.3 var(--serif);font-style:italic;color:var(--ink-3);}
.track .tbody{min-width:0;}
.track .tname{font:400 17px/1.3 var(--serif);color:var(--ink);}
.track .tname a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--accent-dim);}
.track .tdesc{font:12.5px/1.6 var(--mono);color:var(--ink-3);margin-top:5px;}
.track .tdesc .auto{color:var(--ok);}
.track .tstate{justify-self:end;white-space:nowrap;font:600 10px/1.5 var(--sans);letter-spacing:.13em;text-transform:uppercase;}
.track>li.done .tstate{color:var(--ok);}
.track>li.review .tstate,.track>li.review .tn{color:var(--accent);}
.track>li.pending .tname,.track>li.pending .tstate{color:var(--ink-3);}
.toc-meta{margin-top:14px;padding-top:10px;border-top:1px solid var(--rule-soft);font:11.5px/1.6 var(--mono);color:var(--ink-3);display:flex;gap:26px;flex-wrap:wrap;}
.toc-meta b{color:var(--ink-2);font-weight:500;}
.flash{margin-top:20px;padding:10px 0;border-top:1px solid;border-bottom:1px solid;font:400 13px/1.5 var(--serif);font-style:italic;}
.flash.ok{color:var(--ok);border-color:var(--ok-rule);}
.flash.bad{color:var(--bad);border-color:var(--bad-rule);}
table.list{width:100%;border-collapse:collapse;}
table.list th{text-align:left;font:600 10px/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);padding:8px 24px 8px 0;border-bottom:1px solid var(--rule);}
table.list td{padding:14px 24px 14px 0;border-bottom:1px solid var(--rule-soft);font-size:13.5px;vertical-align:baseline;}
table.list td:last-child,table.list th:last-child{padding-right:0;}
table.list td.mono{font:12.5px/1.6 var(--mono);color:var(--ink-2);}
table.list a.proj{font:400 16px/1.3 var(--serif);color:var(--ink);text-decoration:none;border-bottom:1px solid var(--accent-dim);}
table.list a.proj:hover{color:var(--accent);border-bottom-color:var(--accent);}
.tree{display:flex;flex-direction:column;max-width:880px;}
.tree a.row{display:flex;align-items:baseline;gap:12px;padding:9px 0;border-bottom:1px solid var(--rule-soft);text-decoration:none;font:13px/1.5 var(--mono);color:var(--ink);}
.tree a.row:hover{color:var(--accent);}
.tree a.row .meta{margin-left:auto;font:400 12px/1.4 var(--serif);font-style:italic;color:var(--ink-3);}
.tree a.row.up{color:var(--ink-3);border-bottom:none;}
a{color:var(--accent);}
.muted{color:var(--ink-3);}
code.inline{font:12px/1 var(--mono);color:var(--ink-2);}
.duo{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0 56px;align-items:start;}
@media (max-width:1100px){.duo{grid-template-columns:1fr;}}
.report{margin:0;font:12.5px/1.9 var(--mono);color:var(--ink);overflow-x:auto;}
/* forms */
.formgrid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0 56px;align-items:start;max-width:1100px;}
@media (max-width:1100px){.formgrid{grid-template-columns:1fr;}}
form .field{margin-bottom:24px;min-width:0;}
label.lbl{display:block;font:600 10.5px/1.5 var(--sans);letter-spacing:.13em;text-transform:uppercase;color:var(--ink-2);margin-bottom:7px;}
label.lbl .hint{text-transform:none;letter-spacing:.02em;font:400 12px/1.4 var(--serif);font-style:italic;color:var(--ink-3);}
input[type=text],input[type=password]{width:100%;padding:9px 2px;border:0;border-bottom:1px solid var(--rule);background:transparent;color:var(--ink);font:14px/1.4 var(--mono);}
input[type=text]::placeholder,input[type=password]::placeholder{color:var(--ink-3);opacity:.65;}
input[type=text]:focus,input[type=password]:focus{outline:none;border-bottom-color:var(--accent);}
button.btn{padding:11px 26px;border:1px solid var(--accent);background:transparent;color:var(--accent);font:600 11px/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;cursor:pointer;}
button.btn:hover{background:rgba(211,163,90,.1);}
button.btn.secondary{border-color:var(--rule);color:var(--ink-2);}
button.btn.secondary:hover{border-color:var(--ink-3);color:var(--ink);background:transparent;}
button.btn.danger{border-color:var(--bad-rule);color:var(--bad);}
button.btn.danger:hover{background:rgba(221,141,149,.08);}
button.btn:disabled{opacity:.4;cursor:not-allowed;}
/* new-project controls */
.slug{margin-top:8px;font:12px/1.5 var(--mono);color:var(--ink-3);}
.slug b{color:var(--accent);font-weight:400;}
.slug.taken,.slug.taken b{color:var(--bad);}
textarea.block{width:100%;min-height:132px;resize:vertical;background:var(--paper-deep);border:1px solid var(--rule);color:var(--ink);padding:11px 13px;font:13px/1.65 var(--mono);}
textarea.block::placeholder{color:var(--ink-3);opacity:.7;}
textarea.block:focus{outline:none;border-color:var(--accent);}
.counter{display:flex;justify-content:space-between;gap:12px;margin-top:6px;font:11.5px/1.5 var(--mono);color:var(--ink-3);}
.counter .hintnote{font:400 12px/1.5 var(--serif);font-style:italic;}
.counter .count.over{color:var(--bad);}
select.line{width:100%;padding:9px 2px;border:0;border-bottom:1px solid var(--rule);background:transparent;color:var(--ink);font:14px/1.4 var(--mono);appearance:none;-webkit-appearance:none;cursor:pointer;background-image:linear-gradient(45deg,transparent 50%,var(--ink-3) 50%),linear-gradient(135deg,var(--ink-3) 50%,transparent 50%);background-position:right 9px center,right 4px center;background-size:5px 5px,5px 5px;background-repeat:no-repeat;}
select.line:focus{outline:none;border-bottom-color:var(--accent);}
select.line option{background:var(--paper-deep);color:var(--ink);}
.conngrid{display:grid;grid-template-columns:2fr 1fr;gap:0 28px;}
.conngrid .span2{grid-column:1 / -1;}
@media (max-width:720px){.conngrid{grid-template-columns:1fr;}}
.seg{display:inline-flex;border:1px solid var(--rule);}
.seg label{position:relative;}
.seg input{position:absolute;opacity:0;pointer-events:none;}
.seg span{display:block;padding:7px 14px;cursor:pointer;font:600 10px/1.4 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--ink-3);border-right:1px solid var(--rule);}
.seg label:last-child span{border-right:none;}
.seg input:checked + span{background:rgba(211,163,90,.12);color:var(--accent);}
.seg label:hover span{color:var(--ink);}
.specrow{display:flex;align-items:flex-end;gap:22px;flex-wrap:wrap;}
.specrow .num{width:110px;}
input[type=number].line{width:100%;padding:9px 2px;border:0;border-bottom:1px solid var(--rule);background:transparent;color:var(--ink);font:14px/1.4 var(--mono);}
input[type=number].line:focus{outline:none;border-bottom-color:var(--accent);}
.checkline{display:flex;align-items:center;gap:10px;font-size:13.5px;color:var(--ink-2);}
.checkline input{accent-color:var(--accent);width:15px;height:15px;}
.filelist{margin:4px 0 14px;}
.filelist .checkline{padding:7px 0;border-bottom:1px solid var(--rule-soft);font:12.5px/1.5 var(--mono);}
.filelist.validated .checkline{align-items:baseline;gap:12px;padding:10px 0;}
.fmeta{margin-left:auto;display:flex;align-items:baseline;gap:14px;white-space:nowrap;}
.fmeta .dims{font:12px/1.4 var(--mono);color:var(--ink-2);}
.tbadge{font:600 9px/1.5 var(--sans);letter-spacing:.13em;text-transform:uppercase;padding:2px 7px;border:1px solid;border-radius:3px;}
.tbadge.ok{color:var(--ok);border-color:var(--ok-rule);}
.tbadge.bad{color:var(--bad);border-color:var(--bad-rule);}
.checkline.rejected{color:var(--ink-3);}
.checkline.rejected .name{text-decoration:line-through;text-decoration-color:var(--bad);}
.checkline.rejected .reason{font:400 12px/1.4 var(--serif);font-style:italic;color:var(--bad);}
.checkline.rejected input{visibility:hidden;}
.testline{display:flex;align-items:center;gap:16px;margin-top:4px;flex-wrap:wrap;}
.testresult{font:600 10.5px/1.5 var(--sans);letter-spacing:.1em;text-transform:uppercase;display:none;align-items:center;gap:8px;}
.testresult .tick{font-size:12px;}
.testresult.ok{color:var(--ok);display:inline-flex;}
.testresult.bad{color:var(--bad);display:inline-flex;}
.testresult.testing{color:var(--ink-3);display:inline-flex;}
.gate{display:flex;flex-direction:column;gap:8px;margin-bottom:18px;}
.gate .gline{display:flex;align-items:baseline;gap:10px;font:13px/1.5 var(--sans);color:var(--ink-3);}
.gate .gline .mark{font:12px/1 var(--mono);width:16px;}
.gate .gline.met{color:var(--ink-2);}
.gate .gline.met .mark{color:var(--ok);}
.gate .gline.unmet .mark{color:var(--ink-3);}
/* multi-directory pile sources */
.srclist{display:flex;flex-direction:column;gap:0;}
.srcrow{padding:14px 0;border-top:1px solid var(--rule-soft);display:grid;grid-template-columns:1fr auto auto;gap:6px 14px;align-items:center;}
.srcrow:first-child{border-top:none;}
.srcrow input.spath{width:100%;padding:8px 2px;border:0;border-bottom:1px solid var(--rule);background:transparent;color:var(--ink);font:14px/1.4 var(--mono);}
.srcrow input.spath:focus{outline:none;border-bottom-color:var(--accent);}
.srcrow .skind{display:inline-flex;align-items:baseline;gap:8px;}
.srcrow .srcrm{background:none;border:none;color:var(--ink-3);font:11px/1 var(--sans);letter-spacing:.1em;text-transform:uppercase;cursor:pointer;}
.srcrow .srcrm:hover{color:var(--bad);}
.kindtag{font:600 9px/1.5 var(--sans);letter-spacing:.13em;text-transform:uppercase;padding:2px 7px;border:1px solid;border-radius:3px;}
.kindtag.data{color:#86cfc4;border-color:var(--ok-rule);}
.kindtag.media{color:#c4a4e8;border-color:var(--accent-dim);}
.hbtn{display:inline-flex;align-items:center;gap:7px;padding:7px 14px;border:1px solid var(--rule);background:transparent;color:var(--ink-2);font:600 10px/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;cursor:pointer;text-decoration:none;}
.hbtn:hover{border-color:var(--accent);color:var(--accent);}
.addsrc{margin-top:14px;}
.mediasum{border:1px solid var(--rule-soft);background:var(--paper-deep);padding:14px 18px 16px;display:flex;flex-wrap:wrap;gap:8px 32px;align-items:baseline;}
.mediasum .big{font:400 18px/1.2 var(--serif);color:var(--ink);}
.mediasum .kv{font:12px/1.6 var(--mono);color:var(--ink-2);}
.mediasum .note{flex-basis:100%;font:400 12px/1.6 var(--serif);font-style:italic;color:var(--ink-3);margin-top:2px;}
.grouphead{display:flex;align-items:baseline;gap:10px;margin:14px 0 6px;}
.grouphead .gpath{font:12px/1.5 var(--mono);color:var(--ink-2);}
.grouphead .selall{margin-left:auto;display:flex;gap:14px;}
.grouphead .selall a{font:600 9.5px/1 var(--sans);letter-spacing:.11em;text-transform:uppercase;color:var(--accent);text-decoration:none;}
.grouphead .selall a:hover{text-decoration:underline;}
/* sticky section toolbar */
.view-toolbar{position:sticky;top:0;z-index:9;background:var(--rail-bg);border-bottom:1px solid var(--rule);margin:0 -42px;padding:0 42px;display:flex;align-items:stretch;gap:2px;min-height:44px;}
.view-toolbar a{display:inline-flex;align-items:center;gap:8px;font:600 10px/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--ink-3);text-decoration:none;padding:0 14px;border-bottom:2px solid transparent;}
.view-toolbar a:hover{color:var(--accent);}
.view-toolbar a.on{color:var(--ink);border-bottom-color:var(--accent);}
/* collapsible danger / details */
details.fold{margin-top:36px;}
details.fold>summary{list-style:none;cursor:pointer;display:flex;align-items:baseline;gap:12px;padding:12px 0;border-top:1px solid var(--rule);font:600 11px/1.5 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);}
details.fold>summary::-webkit-details-marker{display:none;}
details.fold>summary .chev{font:12px/1 var(--mono);color:var(--ink-3);transition:transform .2s;}
details.fold[open]>summary .chev{transform:rotate(90deg);}
details.fold>summary:hover{color:var(--ink-2);}
details.fold>summary .sumnote{margin-left:auto;font:400 12px/1.4 var(--serif);font-style:italic;color:var(--ink-3);text-transform:none;letter-spacing:0;}
details.fold.danger[open]>summary{color:var(--bad);border-top-color:var(--bad-rule);}
details.fold.danger[open]>summary .chev{color:var(--bad);}
.foldbody{padding:18px 22px 22px;border:1px solid var(--bad-rule);border-top:none;}
/* directory-browser modal */
.modal-overlay{position:fixed;inset:0;z-index:50;background:rgba(8,7,5,.66);display:none;align-items:center;justify-content:center;padding:24px;}
.modal-overlay.open{display:flex;}
.modal{width:100%;max-width:560px;background:var(--paper);border:1px solid var(--rule);box-shadow:0 24px 60px rgba(0,0,0,.5);}
.modal .m-head{display:flex;align-items:baseline;gap:12px;padding:20px 24px 14px;border-bottom:1px solid var(--rule);}
.modal .m-head h3{margin:0;font:400 20px/1.2 var(--serif);}
.modal .m-head .mclose{margin-left:auto;background:none;border:none;color:var(--ink-3);font:18px/1 var(--mono);cursor:pointer;padding:0;}
.modal .m-head .mclose:hover{color:var(--accent);}
.modal .m-body{padding:18px 24px 24px;}
.modal .mfp{font:12px/1.6 var(--mono);color:var(--ink-3);margin:0 0 12px;overflow-wrap:anywhere;}
.modal .mfp b{color:var(--accent);font-weight:400;}
.dirtree{border:1px solid var(--rule-soft);background:var(--paper-deep);max-height:320px;overflow:auto;padding:8px 0;margin-bottom:16px;}
.dirtree .drow{display:flex;align-items:baseline;gap:9px;padding:7px 14px;font:13px/1.4 var(--mono);color:var(--ink-2);cursor:pointer;}
.dirtree .drow:hover{background:rgba(211,163,90,.06);color:var(--ink);}
.dirtree .drow .ic{color:var(--ink-3);}
.dirtree .drow .cnt{margin-left:auto;font:11px/1.4 var(--mono);color:var(--ink-3);}
"""

_DIR_MODAL = (
    '<div class="modal-overlay" id="dirmodal"><div class="modal">'
    '<div class="m-head"><h3>Choose a directory</h3><button class="mclose" type="button" id="dm-close">×</button></div>'
    '<div class="m-body"><p class="mfp">current: <b id="dm-path">—</b></p>'
    '<div class="dirtree" id="dm-tree"></div>'
    '<button class="btn" type="button" id="dm-select">Select this directory</button></div></div></div>'
)

_THEME_JS = (
    "<script>if(new URLSearchParams(location.search).get('theme')==='light')"
    "{document.documentElement.classList.add('light');}</script>"
)

#: per-project nav: (label, route-suffix or None when not yet built, key)
_PROJECT_NAV = [
    ("Dashboard", "", "dashboard"),
    ("Project details", "edit", "details"),
    ("Pile profile", None, "pile"),
    ("Target profile", None, "target"),
    ("Bridge synthesis", None, "synthesis"),
    ("Final bundle", None, "bundle"),
]


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def project_url(slug: str, *suffix: str) -> str:
    path = "/projects/" + quote(slug, safe="")
    if suffix:
        path += "/" + "/".join(suffix)
    return path


def _rail(nav_project: dict | None, active: str) -> str:
    projects_here = ' class="here"' if active == "projects" else ""
    workspace = [f'<a{projects_here} href="/projects">Projects</a>']
    if active == "new":
        workspace.append('<a class="here" href="/projects/new">New project</a>')
    parts = [
        '<aside class="rail">',
        '<a class="wordmark" href="/projects">bridge<i>_builder</i></a>',
        '<div class="navgroup"><p class="gtitle">workspace</p>',
        f'<nav>{"".join(workspace)}</nav></div>',
    ]
    if nav_project:
        slug = nav_project["slug"]
        items = []
        for label, suffix, key in _PROJECT_NAV:
            here = ' class="here"' if key == active else ""
            if suffix is None:
                items.append(f'<span class="navitem soon">{_e(label)}</span>')
            else:
                href = project_url(slug, suffix) if suffix else project_url(slug)
                items.append(f'<a{here} href="{href}">{_e(label)}</a>')
        parts.append(
            f'<div class="navgroup"><p class="gtitle proj">{_e(nav_project["name"])}</p>'
            f'<nav>{"".join(items)}</nav></div>'
        )
    parts.append('<div class="railfoot">Local, single operator. The UI guides; stages run via the CLI.</div>')
    parts.append("</aside>")
    return "".join(parts)


def layout(
    title: str,
    body: str,
    *,
    page_sub: str = "",
    page_actions_html: str = "",
    lede: str = "",
    nav_project: dict | None = None,
    active: str = "",
    autorefresh: bool = False,
) -> str:
    refresh = "<script>setTimeout(function(){location.reload();},5000);</script>" if autorefresh else ""
    sub = f'<span class="sub">{_e(page_sub)}</span>' if page_sub else ""
    actions = f'<span class="right">{page_actions_html}</span>' if page_actions_html else ""
    lede_html = f'<p class="lede">{_e(lede)}</p>' if lede else ""
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_e(title)} — bridge_builder</title>\n"
        f"<style>{_CSS}</style>\n{_THEME_JS}\n</head>\n<body>\n"
        f'<div class="shell">\n{_rail(nav_project, active)}\n<main class="content">\n'
        f'<div class="pagetitle"><h1>{_e(title)}</h1>{sub}{actions}</div>\n{lede_html}\n'
        + body
        + f"\n</main>\n</div>\n{refresh}</body>\n</html>\n"
    )


def _validation_badge(project: BridgeProject) -> str:
    v = project.validation
    if not (v.pile_readable and v.target_reachable):
        return '<span class="status bad"><span class="tick">●</span>invalid</span>'
    label = "valid · oracle run" if v.oracle_can_run else "valid · oracle skip"
    klass = "ok" if v.oracle_can_run else "warn"
    return f'<span class="status {klass}"><span class="tick">●</span>{label}</span>'


def render_project_list(projects: list[BridgeProject]) -> str:
    if projects:
        rows = "".join(
            f'<tr><td><a class="proj" href="{project_url(p.slug)}">{_e(p.slug)}</a></td>'
            f'<td class="mono">{_e(p.pile.describe())}</td>'
            f'<td class="mono">{_e(p.target.describe())}</td>'
            f"<td>{_validation_badge(p)}</td></tr>"
            for p in projects
        )
        table = (
            '<table class="list"><thead><tr>'
            '<th style="width:30%">Project</th><th style="width:30%">Pile</th>'
            '<th style="width:24%">Target</th><th>Status</th></tr></thead>'
            f"<tbody>{rows}</tbody></table>"
            '<p class="note">Connections are stored per project in a gitignored '
            "<code class=\"inline\">.secrets</code> file — passwords never appear here or in project.yml.</p>"
        )
    else:
        table = '<p class="lede">No projects yet. <a href="/projects/new">Create one →</a></p>'
    n = len(projects)
    body = f'<section class="sheet first" style="margin-top:28px;">{table}</section>'
    return layout(
        "Bridge projects", body, active="projects",
        page_sub=f"{n} project{'' if n == 1 else 's'}",
        page_actions_html='<a href="/projects/new">+ New project</a>',
        lede="Validated bridge specifications between a pile and a relational target.",
    )


def render_message(title: str, message: str, *, error: bool = False) -> str:
    klass = "bad" if error else "ok"
    body = f'<div class="flash {klass}">{_e(message)}</div><p class="note"><a href="/projects">← back to projects</a></p>'
    return layout(title, body, active="projects")


_COPY_JS = (
    "<script>document.querySelectorAll('button.copy').forEach(function(b){"
    "b.addEventListener('click',function(){navigator.clipboard.writeText(b.getAttribute('data-cmd')).then(function(){"
    "var t=b.textContent;b.classList.add('copied');b.textContent='Copied';"
    "setTimeout(function(){b.classList.remove('copied');b.textContent=t;},1200);});});});</script>"
)


# Shared client logic for the New / Edit forms. TAKEN, MODE, SOURCES, listed are
# injected by _form_js(); everything else is portable from the design's new.html.
_FORM_JS_BODY = r"""
var pileKind=PILE_KIND,targetKind=TARGET_KIND;
var pileFileOk=false,pileDbOk=(MODE==='edit'&&pileKind==='relational');
var targetDbOk=(MODE==='edit'&&targetKind==='relational'),targetFileOk=(MODE==='edit'&&targetKind==='file');
var state={nameOk:MODE==='edit',pileOk:false,targetOk:false};
function $(id){return document.getElementById(id);}
function slugify(s){return s.toLowerCase().trim().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');}
function detectKind(p){return /media|img|image|photo|video|assets/i.test(p)?'media':'data';}

var nameEl=$('b-name'),slugVal=$('slug-val'),slugLine=$('slug-line');
function refreshName(){
  if(MODE==='edit'||!nameEl||!slugLine){return;}
  var slug=slugify(nameEl.value);
  if(!slug){slugVal.textContent='—';slugLine.classList.remove('taken');slugLine.firstChild.textContent='slug: ';state.nameOk=false;}
  else if(TAKEN.indexOf(slug)!==-1){slugVal.textContent=slug;slugLine.classList.add('taken');slugLine.firstChild.textContent='slug taken — delete the existing project first: ';state.nameOk=false;}
  else{slugVal.textContent=slug;slugLine.classList.remove('taken');slugLine.firstChild.textContent='slug: ';state.nameOk=true;}
  refreshGate();
}
if(nameEl&&MODE!=='edit')nameEl.addEventListener('input',refreshName);
var descEl=$('b-desc'),descCount=$('desc-count');
if(descEl)descEl.addEventListener('input',function(){var n=descEl.value.length;descCount.textContent=n+' / 4000';descCount.classList.toggle('over',n>=4000);});

/* ===== endpoint kind toggles ===== */
document.querySelectorAll('input[name="pile_kind"]').forEach(function(r){r.addEventListener('change',function(){if(!r.checked)return;pileKind=r.value;$('pile-file').style.display=(pileKind==='file')?'':'none';$('pile-db').style.display=(pileKind==='relational')?'':'none';recompute();});});
document.querySelectorAll('input[name="target_kind"]').forEach(function(r){r.addEventListener('change',function(){if(!r.checked)return;targetKind=r.value;$('target-db').style.display=(targetKind==='relational')?'':'none';$('target-file').style.display=(targetKind==='file')?'':'none';recompute();});});

/* ===== pile (file): multi-directory sources ===== */
var srclist=$('srclist'),filesField=$('files-field'),fileGroups=$('filegroups'),rejectNote=$('reject-note');
function renderSources(){
  srclist.innerHTML='';
  SOURCES.forEach(function(s,si){
    var kind=s.kind||detectKind(s.path);
    var row=document.createElement('div');row.className='srcrow';
    row.innerHTML='<input class="spath" data-si="'+si+'" value="'+(s.path||'')+'" placeholder="../path/to/directory">'+
      '<button class="hbtn" type="button" data-browse="'+si+'">Browse…</button>'+
      '<span class="skind"><span class="kindtag '+kind+'">'+kind+'</span>'+
      (SOURCES.length>1?'<button class="srcrm" type="button" data-si="'+si+'">remove</button>':'')+'</span>';
    srclist.appendChild(row);
  });
  srclist.querySelectorAll('input.spath').forEach(function(inp){inp.addEventListener('input',function(){var si=+inp.getAttribute('data-si');SOURCES[si].path=inp.value;SOURCES[si].kind=detectKind(inp.value);var tag=inp.parentNode.querySelector('.kindtag');tag.className='kindtag '+SOURCES[si].kind;tag.textContent=SOURCES[si].kind;});});
  srclist.querySelectorAll('[data-browse]').forEach(function(b){b.addEventListener('click',function(){openBrowserSource(+b.getAttribute('data-browse'));});});
  srclist.querySelectorAll('.srcrm').forEach(function(b){b.addEventListener('click',function(){SOURCES.splice(+b.getAttribute('data-si'),1);renderSources();if(listed)renderFiles();});});
}
if($('add-src'))$('add-src').addEventListener('click',function(){SOURCES.push({path:'',kind:'data',files:[]});renderSources();});

/* ===== directory-browser modal (shared by pile sources + file target) ===== */
var dlg=$('dirmodal'),dmTree=$('dm-tree'),dmPath=$('dm-path'),browseMode=null,curRel='';
function openBrowserSource(si){browseMode={type:'source',si:si};loadDir(SOURCES[si].path||'');if(dlg)dlg.classList.add('open');}
function openBrowserInput(el){browseMode={type:'input',el:el};loadDir(el.value||'');if(dlg)dlg.classList.add('open');}
function closeBrowser(){if(dlg)dlg.classList.remove('open');browseMode=null;}
function loadDir(path){
  fetch('/fs?path='+encodeURIComponent(path)).then(function(r){return r.json();}).then(function(d){
    curRel=d.rel;dmPath.textContent=d.abs;dmTree.innerHTML='';
    if(d.parentRel!==null&&d.parentRel!==undefined){var up=document.createElement('div');up.className='drow';up.innerHTML='<span class="ic">↑</span>.. <span class="cnt">up one level</span>';up.addEventListener('click',function(){loadDir(d.parentRel);});dmTree.appendChild(up);}
    d.entries.forEach(function(e){var row=document.createElement('div');row.className='drow';
      row.innerHTML='<span class="ic">▸</span>'+e.name+'<span class="cnt">'+(e.kind==='media'?e.media+' media':e.data+' data')+'</span>';
      row.addEventListener('click',function(){loadDir(e.rel);});dmTree.appendChild(row);});
    if(!d.entries.length){var none=document.createElement('div');none.className='drow';none.style.cursor='default';none.innerHTML='<span class="ic">·</span>no sub-directories';dmTree.appendChild(none);}
  }).catch(function(){dmTree.innerHTML='<div class="drow">could not read directory</div>';});
}
if($('dm-close'))$('dm-close').addEventListener('click',closeBrowser);
if(dlg)dlg.addEventListener('click',function(e){if(e.target===dlg)closeBrowser();});
if($('dm-select'))$('dm-select').addEventListener('click',function(){
  if(browseMode&&curRel){
    if(browseMode.type==='source'){SOURCES[browseMode.si].path=curRel;SOURCES[browseMode.si].kind=detectKind(curRel);renderSources();if(listed)renderFiles();}
    else{browseMode.el.value=curRel;targetFileOk=false;if($('tf-result')){$('tf-result').className='testresult';$('tf-result').innerHTML='';}recompute();}
  }
  closeBrowser();
});

function renderFiles(){
  fileGroups.innerHTML='';var anyRejected=false;
  SOURCES.forEach(function(s,si){
    var kind=s.kind||detectKind(s.path);
    var head=document.createElement('div');head.className='grouphead';
    head.innerHTML='<span class="gpath">'+(s.path||'(unnamed directory)')+'</span><span class="kindtag '+kind+'">'+kind+'</span>'+
      (kind!=='media'&&(s.files||[]).length?'<span class="selall"><a href="#" data-sel="'+si+':1">Select all</a><a href="#" data-sel="'+si+':0">Unselect all</a></span>':'');
    fileGroups.appendChild(head);
    if(kind==='media'){
      var m=s.media||{total:0,types:'—',size:'—',ref:'—'};
      var sum=document.createElement('div');sum.className='mediasum';
      sum.innerHTML='<span class="big">'+m.total+' media files</span><span class="kv">'+m.types+' · '+m.size+'</span><span class="kv">referenced by '+m.ref+'</span>'+
        '<span class="note">Media is catalogued, not ingested — no per-file selection. Only files correlated to sampled pile rows are fetched at profile time; remote stores (e.g. S3) are accessed on demand.</span>';
      fileGroups.appendChild(sum);return;
    }
    var list=document.createElement('div');list.className='filelist validated';
    (s.files||[]).forEach(function(f){
      var rowEl=document.createElement('label');
      if(f.valid){rowEl.className='checkline';
        rowEl.innerHTML='<input type="checkbox" '+(f.checked?'checked':'')+'> <span class="name">'+f.name+'</span><span class="fmeta"><span class="dims">'+f.rows+' rows × '+f.cols+' cols</span><span class="tbadge ok">valid '+String(f.fmt||'').toUpperCase()+'</span></span>';
        rowEl.querySelector('input').addEventListener('change',function(e){f.checked=e.target.checked;refreshPile();});
      }else{anyRejected=true;rowEl.className='checkline rejected';
        rowEl.innerHTML='<input type="checkbox" disabled> <span class="name">'+f.name+'</span><span class="fmeta"><span class="reason">'+f.reason+'</span><span class="tbadge bad">rejected</span></span>';
      }
      list.appendChild(rowEl);
    });
    fileGroups.appendChild(list);
  });
  fileGroups.querySelectorAll('[data-sel]').forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();var p=a.getAttribute('data-sel').split(':');var s=SOURCES[+p[0]],on=p[1]==='1';(s.files||[]).forEach(function(f){if(f.valid)f.checked=on;});renderFiles();});});
  rejectNote.style.display=anyRejected?'':'none';
  if(filesField)filesField.style.display='';
  refreshPile();
}
function refreshPile(){pileFileOk=SOURCES.some(function(s){return (s.files||[]).some(function(f){return f.valid&&f.checked;});});recompute();}

var listBtn=$('list-btn');
if(listBtn)listBtn.addEventListener('click',function(){
  var payload=SOURCES.map(function(s){return {path:s.path,kind:s.kind||detectKind(s.path)};});
  listBtn.disabled=true;listBtn.textContent='Validating…';
  var body=new FormData();body.append('sources_json',JSON.stringify(payload));
  fetch('/projects/list-files',{method:'POST',body:body}).then(function(r){return r.json();}).then(function(data){
    data.forEach(function(res,i){if(!SOURCES[i])return;SOURCES[i].kind=res.kind;
      if(res.kind==='media'){delete SOURCES[i].files;SOURCES[i].media=res.media;}
      else{var prev={};(SOURCES[i].files||[]).forEach(function(f){prev[f.name]=f.checked;});
        SOURCES[i].files=res.files.map(function(f){f.checked=f.valid&&(prev[f.name]!==undefined?prev[f.name]:true);return f;});}
    });
    listed=true;listBtn.textContent='Re-list & validate files';listBtn.disabled=false;renderSources();renderFiles();
  }).catch(function(){listBtn.textContent='List & validate files';listBtn.disabled=false;});
});

/* ===== sample spec (applies to whichever pile source) ===== */
var specN=$('b-spec-n'),specResolved=$('spec-resolved');
function refreshSpec(){if(!specN)return;var mode=document.querySelector('input[name="specmode"]:checked').value;specResolved.textContent=mode+':'+(parseInt(specN.value,10)||0);}
document.querySelectorAll('input[name="specmode"]').forEach(function(r){r.addEventListener('change',refreshSpec);});
if(specN)specN.addEventListener('input',refreshSpec);

/* ===== relational endpoint test (generic, idp = 'p' pile | 't' target) ===== */
function connTest(idp,onDone){
  var r=$(idp+'-test-result');
  var c={engine:$(idp+'-engine').value,host:$(idp+'-host').value,port:$(idp+'-port').value,database:$(idp+'-db').value,user:$(idp+'-user').value,password:$(idp+'-pw').value};
  if(!(c.host.trim()&&c.database.trim()&&c.user.trim()&&(MODE==='edit'||c.password.trim()))){r.className='testresult bad';r.innerHTML='<span class="tick">✕</span>Fill host, database, user'+(MODE==='edit'?'':' and password')+' first';onDone(false);return;}
  r.className='testresult testing';r.innerHTML='<span class="tick">◴</span>Testing…';onDone(false);
  var body=new FormData();Object.keys(c).forEach(function(k){body.append(k,c[k]);});
  fetch('/projects/test-connection',{method:'POST',body:body}).then(function(x){return x.json();}).then(function(d){
    if(d.reachable){r.className='testresult ok';r.innerHTML='<span class="tick">●</span>'+(d.oracle?'Reachable · read + insert + delete confirmed':'Reachable · read confirmed');onDone(true);}
    else{r.className='testresult bad';r.innerHTML='<span class="tick">✕</span>'+(d.note||'unreachable');onDone(false);}
  }).catch(function(){r.className='testresult bad';r.innerHTML='<span class="tick">✕</span>test failed';onDone(false);});
}
function wireConn(idp,setOk){
  var btn=$(idp+'-test-btn');if(btn)btn.addEventListener('click',function(){connTest(idp,function(ok){setOk(ok);recompute();});});
  [idp+'-engine',idp+'-host',idp+'-port',idp+'-db',idp+'-user',idp+'-pw'].forEach(function(id){var el=$(id);if(el)el.addEventListener('input',function(){setOk(MODE==='edit'&&id!==idp+'-pw'?undefined:false);if($(idp+'-test-result')){$(idp+'-test-result').className='testresult';$(idp+'-test-result').innerHTML='';}recompute();});});
}
wireConn('p',function(v){if(v!==undefined)pileDbOk=v;});
wireConn('t',function(v){if(v!==undefined)targetDbOk=v;});

/* ===== file target: writable directory check ===== */
var tfBrowse=$('tf-browse'),tfCheck=$('tf-check'),tfPath=$('tf-path');
if(tfBrowse)tfBrowse.addEventListener('click',function(){openBrowserInput(tfPath);});
if(tfPath)tfPath.addEventListener('input',function(){if(targetFileOk){targetFileOk=false;$('tf-result').className='testresult';$('tf-result').innerHTML='';recompute();}});
if(tfCheck)tfCheck.addEventListener('click',function(){
  var p=(tfPath.value||'').trim(),r=$('tf-result');
  if(!p){r.className='testresult bad';r.innerHTML='<span class="tick">✕</span>Enter a directory path';targetFileOk=false;recompute();return;}
  r.className='testresult testing';r.innerHTML='<span class="tick">◴</span>Checking…';targetFileOk=false;recompute();
  var body=new FormData();body.append('path',p);
  fetch('/projects/test-dir',{method:'POST',body:body}).then(function(x){return x.json();}).then(function(d){
    if(d.writable){r.className='testresult ok';r.innerHTML='<span class="tick">●</span>'+(d.exists?'Directory writable':'Will be created · writable');targetFileOk=true;}
    else{r.className='testresult bad';r.innerHTML='<span class="tick">✕</span>'+(d.note||'not writable');targetFileOk=false;}
    recompute();
  }).catch(function(){r.className='testresult bad';r.innerHTML='<span class="tick">✕</span>check failed';targetFileOk=false;recompute();});
});

/* ===== gate ===== */
var createBtn=$('create-btn'),gate=$('gate');
function recompute(){
  state.pileOk=(pileKind==='file')?pileFileOk:pileDbOk;
  state.targetOk=(targetKind==='relational')?targetDbOk:targetFileOk;
  refreshGate();
}
function setGate(id,ok,doneText,todoText){var el=$(id);if(!el)return;el.classList.toggle('met',ok);el.classList.toggle('unmet',!ok);el.querySelector('.mark').textContent=ok?'●':'○';el.querySelector('span:last-child').textContent=ok?doneText:todoText;}
function refreshGate(){
  if(gate){setGate('g-name',state.nameOk,'Slug “'+slugVal.textContent+'” is available','Project name is set and its slug is free');
    setGate('g-pile',state.pileOk,pileKind==='file'?'Valid data file(s) selected':'Pile database reachable',pileKind==='file'?'At least one valid data file is selected':'Pile database tested and reachable');
    setGate('g-target',state.targetOk,targetKind==='relational'?'Target connection reachable':'Output directory writable',targetKind==='relational'?'Target connection tested and reachable':'Output directory checked and writable');
    createBtn.disabled=!(state.nameOk&&state.pileOk&&state.targetOk);}
}
$('pform').addEventListener('submit',function(){
  var payload=SOURCES.map(function(s){var o={path:s.path,kind:s.kind||detectKind(s.path)};if(o.kind==='data'){o.files=(s.files||[]).filter(function(f){return f.valid&&f.checked;}).map(function(f){return f.name;});}return o;});
  $('sources_json').value=JSON.stringify(payload);
  if(specN)$('sample').value=document.querySelector('input[name="specmode"]:checked').value+':'+(parseInt(specN.value,10)||0);
});

/* ===== section toolbar scrollspy ===== */
var vtLinks=Array.prototype.slice.call(document.querySelectorAll('#vt a'));
vtLinks.forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();var el=document.querySelector(a.getAttribute('href'));if(el)document.scrollingElement.scrollTop=el.offsetTop-64;});});
var vtSecs=['sec-i','sec-ii','sec-iii','sec-iv'].map(function(id){return document.getElementById(id);});
function vtSpy(){var y=document.scrollingElement.scrollTop+100,cur=0;vtSecs.forEach(function(s,i){if(s&&s.offsetTop<=y)cur=i;});vtLinks.forEach(function(a,i){a.classList.toggle('on',i===cur);});}
document.addEventListener('scroll',vtSpy,{passive:true});

renderSources();if(listed)renderFiles();refreshName();refreshSpec();recompute();vtSpy();
"""


def _cmd_block(primary: str, alternates: list[str]) -> str:
    block = (
        '<div class="cmd"><pre>' + _e(primary) + "</pre>"
        f'<button class="copy" type="button" data-cmd="{_e(primary)}">Copy</button></div>'
    )
    if alternates:
        rows = "".join(
            f'<div class="alt"><code>{_e(a)}</code>'
            f'<button class="copy mini" type="button" data-cmd="{_e(a)}">Copy</button></div>'
            for a in alternates
        )
        block += f'<div class="alts"><div class="alts-title">or, instead</div>{rows}</div>'
    return block


# --- Dashboard (T061) ---------------------------------------------------------

_TRACK_STAGES = ("Pile profiling", "Target profiling", "Synthesize bridge", "Final bundle")


def _next_step_track(status, *, validation_ok: bool) -> str:
    done = [
        True,                                            # 1. project created
        status.pile_profiled,
        status.target_profiled,
        status.mapping_iterations > 0,
        status.bundle_present,
    ]
    descs = [
        "Project created — connections validated",
        "ydata baseline + analyst playground over the sampled pile",
        "schema profile + ER diagram + candidate-table ranking",
        "oracle + review loops produce the bridge mapping",
        "packaged spec — available once synthesis passes the oracle",
    ]
    names = ["Project created", *_TRACK_STAGES]
    current = next((i for i, d in enumerate(done) if not d), len(done)) if validation_ok else None
    items = []
    for i, name in enumerate(names):
        if done[i]:
            klass, state_label = "done", "Done"
        elif i == current:
            klass, state_label = "review", "Next"
        else:
            klass, state_label = "pending", "—"
        items.append(
            f'<li class="{klass}"><span class="tn">{i + 1}</span>'
            f'<div class="tbody"><div class="tname">{_e(name)}</div>'
            f'<div class="tdesc">{_e(descs[i])}</div></div>'
            f'<span class="tstate">{state_label}</span></li>'
        )
    meta = (
        f'<div class="toc-meta"><span>data-profiling iterations <b>{status.profiling_iterations}</b></span>'
        f'<span>bridge-mapping iterations <b>{status.mapping_iterations}</b></span></div>'
    )
    return f'<ol class="track">{"".join(items)}</ol>{meta}'


def render_dashboard(project, status, primary, alternates, *, flash=None, error=None) -> str:  # noqa: ANN001
    v = project.validation
    validation_ok = v.pile_readable and v.target_reachable
    nav_project = {"slug": project.slug, "name": project.name}

    flash_html = ""
    if error:
        flash_html = f'<div class="flash bad">{_e(error)}</div>'
    elif flash:
        flash_html = f'<div class="flash ok">{_e(flash)}</div>'
    locked = getattr(status, "lock_live_owner", None) is not None
    if locked:
        flash_html = (
            f'<div class="flash bad">operation in progress (PID {status.lock_live_owner}) — '
            "mutations are refused while it runs; this view auto-refreshes.</div>" + flash_html
        )

    # i. Connection — collapsed confirmations linking to Project details.
    n_files = len(project.pile.data_files())
    pile_confirm = (
        f'<div class="confirm ok"><span class="tick">●</span><span class="what">Pile valid</span>'
        f'<span class="where">{n_files} data file{"" if n_files == 1 else "s"} readable</span></div>'
        if v.pile_readable else
        '<div class="confirm bad"><span class="tick">●</span><span class="what">Pile invalid</span>'
        '<span class="where">no readable data files</span></div>'
    )
    if v.target_reachable:
        where = "read · insert · delete confirmed" if v.oracle_can_run else "read confirmed · no insert/delete (oracle skips)"
        target_confirm = (
            f'<div class="confirm ok"><span class="tick">●</span><span class="what">Target valid</span>'
            f'<span class="where">{where}</span></div>'
        )
    else:
        target_confirm = (
            '<div class="confirm bad"><span class="tick">●</span><span class="what">Target unreachable</span>'
            '<span class="where">re-validate in Project details</span></div>'
        )
    when = f'<div class="confirm"><span class="where">validated {_e(v.validated_at)}</span></div>' if v.validated_at else ""
    connection = (
        '<section class="sheet first"><div class="sheet-head"><span class="no">i.</span><h2>Connection</h2>'
        f'<a class="action" href="{project_url(project.slug, "edit")}">Connection report</a></div>'
        f'<div class="confirms">{pile_confirm}{target_confirm}{when}</div></section>'
    )

    # ii. Suggested next step — guidance-only progress tracker + copyable CLI.
    intro = (
        '<p class="note" style="margin-top:0;">Re-validate the connection before profiling can continue.</p>'
        if not validation_ok else ""
    )
    next_step = (
        '<section class="sheet"><div class="sheet-head"><span class="no">ii.</span><h2>Suggested next step</h2></div>'
        f'{intro}{_next_step_track(status, validation_ok=validation_ok)}'
        f'<div style="margin-top:22px;">{_cmd_block(primary, alternates)}</div>'
        '<p class="note">The UI guides; stages run via the CLI. Copy the command above into your terminal.</p></section>'
    )

    # iii. Artifacts.
    artifacts = (
        '<section class="sheet"><div class="sheet-head"><span class="no">iii.</span><h2>Artifacts</h2>'
        f'<a class="action" href="{project_url(project.slug, "artifacts")}">Browse folder</a></div>'
        f'<p class="note">Profiling and mapping artifacts — including the analysis playgrounds — live in the project '
        f'folder ({status.profiling_iterations} data-profiling iteration'
        f'{"" if status.profiling_iterations == 1 else "s"} so far). Re-profiling and synthesis commands are issued from the CLI.</p></section>'
    )

    first_dir = project.pile.directories[0].path if project.pile.directories else project.pile.describe()
    body = flash_html + connection + next_step + artifacts + _COPY_JS
    return layout(
        project.slug, body,
        page_sub=f"{first_dir} → {project.target.describe()}",
        page_actions_html=_validation_badge(project),
        nav_project=nav_project, active="dashboard", autorefresh=locked,
    )


# --- New / Edit project form (T062 / T063) ------------------------------------

_VIEW_TOOLBAR = (
    '<nav class="view-toolbar" id="vt">'
    '<a href="#sec-i" class="on">i. Identity</a><a href="#sec-ii">ii. Pile source</a>'
    '<a href="#sec-iii">iii. Target</a><a href="#sec-iv">iv. {last}</a></nav>'
)

_HINT = 'style="font:400 12px/1.4 Georgia,serif;font-style:italic;color:var(--ink-3);"'

_ENGINE_OPTS = (("postgresql", "PostgreSQL"), ("mysql", "MySQL / MariaDB"), ("mssql", "SQL Server"))


def _cv(conn) -> dict:  # noqa: ANN001
    """Connection field values for prefill (credential-free)."""
    if conn is not None:
        return {"engine": conn.engine, "host": conn.host, "port": str(conn.port),
                "database": conn.database, "user": conn.user}
    return {"engine": "postgresql", "host": "", "port": "5432", "database": "", "user": ""}


def _kind_toggle(name: str, current: str, options: list[tuple[str, str]]) -> str:
    radios = "".join(
        f'<label><input type="radio" name="{name}" value="{v}"{" checked" if v == current else ""}>'
        f"<span>{_e(lbl)}</span></label>"
        for v, lbl in options
    )
    return f'<div class="field" style="margin-bottom:18px;"><div class="seg" role="radiogroup">{radios}</div></div>'


def _conn_block(idp: str, name_prefix: str, cv: dict, *, edit: bool) -> str:
    """A relational-connection grid (engine/host/port/db/user/pw) + Test button.

    ``idp`` namespaces the element ids (``p`` pile, ``t`` target); ``name_prefix``
    namespaces the form field names (``pile_`` for pile, ``""`` for target).
    """
    opts = "".join(
        f'<option value="{val}"{" selected" if cv["engine"] == val else ""}>{lbl}</option>'
        for val, lbl in _ENGINE_OPTS
    )
    pw_hint = (
        '<span class="hint">— leave blank to keep the stored credential; required only if you change the connection</span>'
        if edit else '<span class="hint">— stored only in the gitignored .secrets, never shown again</span>'
    )
    pw_ph = "•••••• (unchanged)" if edit else "••••••••••"
    return (
        '<div class="conngrid">'
        f'<div class="field span2" style="max-width:300px;"><label class="lbl" for="{idp}-engine">Engine</label>'
        f'<select class="line" id="{idp}-engine" name="{name_prefix}engine">{opts}</select></div>'
        f'<div class="field"><label class="lbl" for="{idp}-host">Host</label>'
        f'<input type="text" id="{idp}-host" name="{name_prefix}host" value="{_e(cv["host"])}" placeholder="db.internal.local"></div>'
        f'<div class="field"><label class="lbl" for="{idp}-port">Port</label>'
        f'<input type="text" id="{idp}-port" name="{name_prefix}port" value="{_e(cv["port"])}"></div>'
        f'<div class="field span2"><label class="lbl" for="{idp}-db">Database</label>'
        f'<input type="text" id="{idp}-db" name="{name_prefix}database" value="{_e(cv["database"])}" placeholder="travelogue"></div>'
        f'<div class="field"><label class="lbl" for="{idp}-user">User</label>'
        f'<input type="text" id="{idp}-user" name="{name_prefix}user" value="{_e(cv["user"])}" placeholder="bridge_writer"></div>'
        f'<div class="field"><label class="lbl" for="{idp}-pw">Password {pw_hint}</label>'
        f'<input type="password" id="{idp}-pw" name="{name_prefix}password" placeholder="{pw_ph}"></div>'
        f'</div><div class="testline"><button class="btn secondary" type="button" id="{idp}-test-btn">Test connection</button>'
        f'<span class="testresult" id="{idp}-test-result"></span></div>'
    )


def _pile_section(*, kind: str, cv: dict, edit: bool) -> str:
    file_disp = "" if kind == "file" else "display:none;"
    db_disp = "" if kind == "relational" else "display:none;"
    file_block = (
        '<div class="field"><label class="lbl">Directories <span class="hint">— e.g. extracted tables plus a media folder</span></label>'
        '<div class="srclist" id="srclist"></div>'
        '<button class="btn secondary addsrc" type="button" id="add-src">+ Add directory</button>'
        '<div class="testline" style="margin-top:14px;"><button class="btn secondary" type="button" id="list-btn">List &amp; validate files</button>'
        f'<span class="muted" id="list-note" {_HINT}>Data files (TSV, CSV, JSON…) are validated as tables; media directories are catalogued, not ingested.</span></div></div>'
        '<div class="field" id="files-field" style="display:none;"><label class="lbl">Files <span class="hint">— selection is frozen to an explicit list</span></label>'
        '<div id="filegroups"></div>'
        '<p class="note" id="reject-note" style="display:none;">Files that don\'t parse as a valid table can\'t be selected. Fix or remove them in the directory, then re-list.</p></div>'
    )
    db_block = (
        '<p class="note" style="margin-top:0;margin-bottom:14px;">Read access is enough — the database\'s tables become the pile\'s source rows.</p>'
        + _conn_block("p", "pile_", cv, edit=edit)
    )
    spec = (
        '<div class="field" style="margin-bottom:0;margin-top:10px;"><label class="lbl">Pile sample spec <span class="hint">— how rows are drawn for profiling; overridable per run</span></label>'
        '<div class="specrow"><div class="seg" role="radiogroup" aria-label="Sample mode">'
        '<label><input type="radio" name="specmode" value="head"><span>Head only</span></label>'
        '<label><input type="radio" name="specmode" value="random"><span>Random only</span></label>'
        '<label><input type="radio" name="specmode" value="head+random" checked><span>Head + random</span></label></div>'
        '<div class="num"><label class="lbl" for="b-spec-n" style="margin-bottom:4px;">Rows</label>'
        '<input type="number" class="line" id="b-spec-n" value="200" min="1" max="100000" step="50"></div>'
        '<div class="slug" style="margin:0;">resolves to <b id="spec-resolved">head+random:200</b></div></div></div>'
    )
    return (
        '<section class="sheet" id="sec-ii"><div class="sheet-head"><span class="no">ii.</span><h2>Pile source</h2>'
        f'<span class="hint" {_HINT}>where the content to bridge comes from — a set of files, or a database</span></div>'
        + _kind_toggle("pile_kind", kind, [("file", "File directories"), ("relational", "Relational database")])
        + f'<div id="pile-file" style="{file_disp}">{file_block}</div>'
        + f'<div id="pile-db" style="{db_disp}">{db_block}</div>'
        + spec + "</section>"
    )


def _target_section(*, kind: str, cv: dict, path: str, edit: bool) -> str:
    db_disp = "" if kind == "relational" else "display:none;"
    file_disp = "" if kind == "file" else "display:none;"
    db_block = (
        _conn_block("t", "", cv, edit=edit)
        + '<p class="note">Credentials are stored with the project in a gitignored <code class="inline">.secrets</code> '
        "file so later stages can reach the target — write-scoped and never shown again after saving.</p>"
    )
    file_block = (
        '<div class="field"><label class="lbl">Output directory <span class="hint">— where the future bridge writes; validated as a writable directory</span></label>'
        '<div class="srcrow" style="border-top:none;padding-top:0;">'
        f'<input class="spath" id="tf-path" name="target_path" value="{_e(path or "")}" placeholder="../path/to/output">'
        '<button class="hbtn" type="button" id="tf-browse">Browse…</button>'
        '<span class="skind"><span class="kindtag data">dir</span></span></div>'
        '<div class="testline" style="margin-top:14px;"><button class="btn secondary" type="button" id="tf-check">Check directory</button>'
        '<span class="testresult" id="tf-result"></span></div>'
        '<p class="note">A file target is validated as a writable directory. The oracle insert/delete loop applies only to relational targets.</p></div>'
    )
    return (
        '<section class="sheet" id="sec-iii"><div class="sheet-head"><span class="no">iii.</span><h2>Target</h2>'
        f'<span class="hint" {_HINT}>the destination the future bridge writes into — a database, or a directory</span></div>'
        + _kind_toggle("target_kind", kind, [("relational", "Relational database"), ("file", "File directory")])
        + f'<div id="target-db" style="{db_disp}">{db_block}</div>'
        + f'<div id="target-file" style="{file_disp}">{file_block}</div>'
        + "</section>"
    )


def _form_js(*, mode: str, taken: list[str], sources: list, slug: str, listed: bool,
             pile_kind: str, target_kind: str) -> str:
    return (
        "<script>(function(){"
        f"var TAKEN={json.dumps(taken)};var MODE={json.dumps(mode)};var SOURCES={json.dumps(sources)};"
        f"var listed={'true' if listed else 'false'};"
        f"var PILE_KIND={json.dumps(pile_kind)};var TARGET_KIND={json.dumps(target_kind)};"
        + _FORM_JS_BODY + "})();</script>"
    )


def render_create_form(*, existing_slugs=None, error=None, values=None, sources=None) -> str:  # noqa: ANN001
    values = values or {}
    sources = sources if sources is not None else [{"path": "", "kind": "data", "files": []}]
    pile_kind = values.get("pile_kind", "file")
    target_kind = values.get("target_kind", "relational")
    pile_cv = {"engine": values.get("pile_engine", "postgresql"), "host": values.get("pile_host", ""),
               "port": values.get("pile_port", "5432"), "database": values.get("pile_database", ""),
               "user": values.get("pile_user", "")}
    target_cv = {"engine": values.get("engine", "postgresql"), "host": values.get("host", ""),
                 "port": values.get("port", "5432"), "database": values.get("database", ""),
                 "user": values.get("user", "")}
    flash_html = f'<div class="flash bad">{_e(error)}</div>' if error else ""
    identity = (
        '<section class="sheet first" id="sec-i" style="margin-top:26px;"><div class="sheet-head"><span class="no">i.</span><h2>Identity</h2></div>'
        '<div class="formgrid"><div><div class="field" style="margin-bottom:18px;">'
        '<label class="lbl" for="b-name">Project name</label>'
        f'<input type="text" id="b-name" name="name" value="{_e(values.get("name", ""))}" placeholder="IG pile → travelogue">'
        '<div class="slug" id="slug-line">slug: <b id="slug-val">—</b></div></div></div>'
        '<div><div class="field" style="margin-bottom:0;">'
        '<label class="lbl" for="b-desc">Description &amp; intent <span class="hint">— markdown; gives later synthesis stages context</span></label>'
        f'<textarea class="block" id="b-desc" name="description" maxlength="4000" placeholder="## Goal&#10;What this bridge is for…">{_e(values.get("description", ""))}</textarea>'
        '<div class="counter"><span class="hintnote">Carried into bridge synthesis &amp; the final spec package.</span>'
        '<span class="count" id="desc-count">0 / 4000</span></div></div></div></div></section>'
    )
    create = (
        '<section class="sheet" id="sec-iv"><div class="sheet-head"><span class="no">iv.</span><h2>Create</h2></div>'
        '<div class="gate" id="gate">'
        '<div class="gline unmet" id="g-name"><span class="mark">○</span><span>Project name is set and its slug is free</span></div>'
        '<div class="gline unmet" id="g-pile"><span class="mark">○</span><span>At least one valid data file is selected</span></div>'
        '<div class="gline unmet" id="g-target"><span class="mark">○</span><span>Target connection tested and reachable</span></div></div>'
        '<button class="btn" type="submit" id="create-btn" disabled>Create project</button>'
        '<p class="note">Each project name produces a unique slug. To reuse a slug, delete the existing project first — this view never overwrites.</p></section>'
    )
    body = (
        flash_html
        + _VIEW_TOOLBAR.format(last="Create")
        + '<form id="pform" method="post" action="/projects" novalidate>'
        + identity
        + _pile_section(kind=pile_kind, cv=pile_cv, edit=False)
        + _target_section(kind=target_kind, cv=target_cv, path=values.get("target_path", ""), edit=False)
        + create
        + '<input type="hidden" name="sources_json" id="sources_json"><input type="hidden" name="sample" id="sample"></form>'
        + _DIR_MODAL
        + _form_js(mode="new", taken=list(existing_slugs or []), sources=sources, slug="", listed=False,
                   pile_kind=pile_kind, target_kind=target_kind)
    )
    return layout("New bridge project", body, active="new")


def render_edit_form(project, *, sources=None, error=None, flash=None) -> str:  # noqa: ANN001
    sources = sources or []
    nav_project = {"slug": project.slug, "name": project.name}
    flash_html = ""
    if error:
        flash_html = f'<div class="flash bad">{_e(error)}</div>'
    elif flash:
        flash_html = f'<div class="flash ok">{_e(flash)}</div>'
    sample = project.pile.sample
    n = len(project.description or "")
    pile_kind = project.pile.kind
    target_kind = project.target.kind
    identity = (
        '<section class="sheet first" id="sec-i" style="margin-top:24px;"><div class="sheet-head"><span class="no">i.</span><h2>Identity</h2></div>'
        '<div class="formgrid"><div><div class="field" style="margin-bottom:18px;">'
        '<label class="lbl" for="b-name">Project name <span class="hint">— immutable; delete &amp; recreate to rename</span></label>'
        f'<input type="text" id="b-name" value="{_e(project.name)}" readonly style="color:var(--ink-2);">'
        f'<div class="slug">slug: <b>{_e(project.slug)}</b></div></div></div>'
        '<div><div class="field" style="margin-bottom:0;">'
        '<label class="lbl" for="b-desc">Description &amp; intent <span class="hint">— markdown; carried into bridge synthesis</span></label>'
        f'<textarea class="block" id="b-desc" name="description" maxlength="4000">{_e(project.description or "")}</textarea>'
        '<div class="counter"><span class="hintnote">Carried into bridge synthesis &amp; the final spec package.</span>'
        f'<span class="count" id="desc-count">{n} / 4000</span></div></div></div></div></section>'
    )
    legacy_note = ""
    if project.target.connection is None and project.target.connection_env:
        legacy_note = (
            f'<div class="flash ok">Legacy env-var connection <code class="inline">{_e(project.target.connection_env)}</code> — '
            "enter the discrete connection and a password below to migrate it to stored credentials.</div>"
        )
    save = (
        '<section class="sheet" id="sec-iv"><div class="sheet-head"><span class="no">iv.</span><h2>Save</h2></div>'
        '<button class="btn" type="submit">Re-validate + save</button>'
        '<p class="note">Validation re-runs against these inputs before anything persists; on failure the prior config is untouched.</p></section>'
    )
    delete_fold = (
        '<details class="fold danger"><summary><span class="chev">▸</span>Delete project<span class="sumnote">rarely needed — irreversible</span></summary>'
        '<div class="foldbody">'
        f'<form id="delete-form" method="post" action="{project_url(project.slug, "delete")}">'
        '<p class="lede" style="margin:0 0 14px;">Type the project slug to confirm deletion. Irreversible — iteration histories, truth baseline and bundle are removed.</p>'
        '<div class="field" style="max-width:380px;margin-bottom:18px;">'
        f'<input type="text" id="confirm-name" name="confirm_name" placeholder="{_e(project.slug)}" autocomplete="off"></div>'
        '<button class="btn danger" id="delete-btn" type="submit" disabled>Delete project</button></form></div></details>'
        "<script>(function(){var ci=document.getElementById('confirm-name'),db=document.getElementById('delete-btn');"
        f"if(!ci)return;ci.addEventListener('input',function(){{db.disabled=ci.value!=={json.dumps(project.slug)};}});}})();</script>"
    )
    body = (
        flash_html + legacy_note
        + _VIEW_TOOLBAR.format(last="Save")
        + f'<form id="pform" method="post" action="{project_url(project.slug, "update")}" novalidate>'
        + identity
        + _pile_section(kind=pile_kind, cv=_cv(project.pile.connection), edit=True)
        + _target_section(kind=target_kind, cv=_cv(project.target.connection), path=project.target.path or "", edit=True)
        + save
        + '<input type="hidden" name="sources_json" id="sources_json"><input type="hidden" name="sample" id="sample"></form>'
        + delete_fold
        + _DIR_MODAL
        + _form_js(mode="edit", taken=[], sources=sources, slug=project.slug, listed=True,
                   pile_kind=pile_kind, target_kind=target_kind)
        + _preselect_sample_js(sample.strategy, sample.size)
    )
    return layout(
        "Project details", body,
        page_sub=f"name is immutable · slug {project.slug}",
        page_actions_html=_validation_badge(project),
        nav_project=nav_project, active="details",
    )


def _preselect_sample_js(strategy: str, size: int) -> str:
    return (
        "<script>(function(){var r=document.querySelector('input[name=\"specmode\"][value='+"
        f"{json.dumps(strategy)}+']');if(r)r.checked=true;var n=document.getElementById('b-spec-n');"
        f"if(n)n.value={int(size)};var sr=document.getElementById('spec-resolved');"
        f"if(sr)sr.textContent={json.dumps(strategy)}+':'+{int(size)};}})();</script>"
    )


# --- Artifacts browser (T064) -------------------------------------------------

def _artifact_meta(name: str, is_dir: bool, size: int) -> str:
    if is_dir:
        return "folder"
    human = _human_bytes(size)
    if name.endswith(".enhanced.html"):
        return f"playground · {human}"
    if name.endswith((".ydata-profile.html", ".er-diagram.svg")):
        return f"raw baseline · {human}"
    return human


def render_artifact_listing(project, relpath, entries) -> str:  # noqa: ANN001
    nav_project = {"slug": project.slug, "name": project.name}
    up_href = project_url(project.slug) if not relpath else project_url(
        project.slug, "artifacts", *relpath.split("/")[:-1]
    ).rstrip("/")
    rows = [f'<a class="row up" href="{up_href}">.. <span class="meta">up one level</span></a>']
    for name, is_dir, size in entries:
        child = f"{relpath}/{name}" if relpath else name
        href = project_url(project.slug, "artifacts", *child.split("/"))
        label = name + ("/" if is_dir else "")
        rows.append(
            f'<a class="row" href="{href}">{_e(label)}<span class="meta">{_e(_artifact_meta(name, is_dir, size))}</span></a>'
        )
    body = f'<section class="sheet first" style="margin-top:26px;"><div class="tree">{"".join(rows)}</div></section>'
    return layout(
        "Artifacts", body,
        page_sub=relpath or "project folder",
        nav_project=nav_project, active="",
    )


def _human_bytes(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"
