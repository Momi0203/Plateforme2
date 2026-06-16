/**
 * table.js — Onglet Tableau attributaire (§5.2.3)
 *
 * TA-01  Pagination 50/100/200 lignes par page
 * TA-03  Tri ascendant/descendant par clic sur en-tête
 * TA-05  Surlignage jaune des lignes dans selection_active
 * TA-06  Clic ligne → zoom + sélection sur la carte
 * TA-09  Export CSV (tout ou sélection) via POST /carte/api/export/csv/
 * §6     Synchronisation bidirectionnelle avec la carte
 *
 * Dépend de :
 *   map.js       → window.MAP
 *   selection.js → window.selection_active, window.applySelectionFromPks
 *                  window.onSelectionChange (hook exposé ici, appelé par selection.js)
 *   query.js     → getCsrf()
 *   layers.js    → window.onCoucheActiveChange (hook exposé ici)
 */

'use strict';

// ── État interne ──────────────────────────────────────────────────────────────

const _ta = {
  couche:       null,
  data:         [],    // [{pk, props, geom}]
  sortCol:      null,
  sortAsc:      true,
  page:         0,
  pageSize:     50,
  exportChamps: null,  // null = toutes les colonnes ; sinon tableau de noms (TA-13)
};

// ── Onglets centraux (Carte | Tableau | Dashboard | Layout) ───────────────────

function _initCentraleTabs() {
  document.querySelectorAll('.centrale-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      _switchTab(btn.dataset.ctab);
    });
  });
}

function _switchTab(ctab) {
  document.querySelectorAll('.centrale-tab').forEach(b => {
    b.classList.toggle('active', b.dataset.ctab === ctab);
  });
  const zCarte     = document.getElementById('zone-carte');
  const zTableau   = document.getElementById('zone-tableau');
  const zDashboard = document.getElementById('zone-dashboard');
  const zLayout    = document.getElementById('zone-layout');
  if (zCarte)     zCarte.style.display     = ctab === 'carte'     ? '' : 'none';
  if (zTableau)   zTableau.style.display   = ctab === 'tableau'   ? '' : 'none';
  if (zDashboard) zDashboard.style.display = ctab === 'dashboard' ? '' : 'none';
  if (zLayout)    zLayout.style.display    = ctab === 'layout'    ? '' : 'none';

  if (ctab === 'carte' && window.MAP) setTimeout(() => window.MAP.resize(), 50);
  if (ctab === 'layout') document.dispatchEvent(new CustomEvent('carte:layoutOpen'));

  document.dispatchEvent(new CustomEvent('carte:tabSwitch', { detail: { tab: ctab } }));
}

// ── Chargement des données ────────────────────────────────────────────────────

async function chargerTableau(couche) {
  if (!couche) { _viderTableau(); return; }

  _ta.couche  = couche;
  _ta.page    = 0;
  _ta.sortCol = null;
  _ta.sortAsc = true;
  _ta.data    = [];

  const gc = document.getElementById('ta-grid-container');
  if (!gc) return;

  gc.innerHTML = `<div class="ta-placeholder">
    <i class="fas fa-spinner fa-spin"></i>
    <span>Chargement de « ${_escHtml(couche)} »…</span>
  </div>`;

  _updateFooter(0, 0);
  _updatePagination(0);

  const lbl = document.getElementById('ta-couche-label');
  if (lbl) lbl.textContent = couche;

  try {
    const resp = await fetch(`/carte/api/couche/${couche}/?limit=2000`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status} — ${resp.statusText}`);
    const geojson = await resp.json();

    _ta.data = (geojson.features ?? []).map(f => ({
      pk:   f.id ?? f.properties?.pk,
      props: f.properties ?? {},
      geom:  f.geometry,
    }));

    _renderGrid();
  } catch (err) {
    if (gc) gc.innerHTML = `<div class="ta-placeholder">
      <i class="fas fa-exclamation-triangle"></i>
      <span>Erreur : ${_escHtml(err.message)}</span>
    </div>`;
    console.error('[tableau] chargerTableau :', err);
  }
}

function _viderTableau() {
  _ta.couche = null;
  _ta.data   = [];
  const gc = document.getElementById('ta-grid-container');
  if (gc) gc.innerHTML = `<div class="ta-placeholder">
    <i class="fas fa-table"></i>
    <span>Activez une couche dans le panneau gauche<br>pour afficher ses attributs.</span>
  </div>`;
  _updateFooter(0, 0);
  _updatePagination(0);
  const lbl = document.getElementById('ta-couche-label');
  if (lbl) lbl.textContent = '';
}

// ── Rendu de la grille ────────────────────────────────────────────────────────

function _renderGrid() {
  const gc = document.getElementById('ta-grid-container');
  if (!gc) return;

  const { data, sortCol, sortAsc, page, pageSize } = _ta;

  if (!data.length) {
    gc.innerHTML = `<div class="ta-placeholder">
      <i class="fas fa-inbox"></i>
      <span>Aucune donnée pour cette couche.</span>
    </div>`;
    _updateFooter(0, 0);
    _updatePagination(0);
    return;
  }

  // Colonnes (pk en premier, puis toutes les propriétés)
  const cols = ['pk', ...Object.keys(data[0].props)];

  // Tri (TA-03)
  let rows = [...data];
  if (sortCol) {
    rows.sort((a, b) => {
      const va = sortCol === 'pk' ? a.pk : (a.props[sortCol] ?? '');
      const vb = sortCol === 'pk' ? b.pk : (b.props[sortCol] ?? '');
      if (va == null) return sortAsc ? 1 : -1;
      if (vb == null) return sortAsc ? -1 : 1;
      const cmp = String(va).localeCompare(String(vb), 'fr', { numeric: true });
      return sortAsc ? cmp : -cmp;
    });
  }

  // Pagination (TA-01)
  const total    = rows.length;
  const start    = page * pageSize;
  const pageRows = rows.slice(start, start + pageSize);

  // PKs sélectionnés (TA-05)
  const selSet = new Set((window.selection_active ?? []).map(Number));

  // En-têtes
  const thead = cols.map(c => {
    const sorted   = c === sortCol;
    const sortIcon = sorted ? (sortAsc ? ' ↑' : ' ↓') : '';
    return `<th class="ta-th${sorted ? ' ta-sorted' : ''}" data-col="${_escAttr(c)}">${_escHtml(c)}<span class="ta-sort-icon">${sortIcon}</span></th>`;
  }).join('');

  // Lignes
  const tbody = pageRows.map(row => {
    const pk      = Number(row.pk);
    const selAttr = selSet.has(pk) ? ' class="ta-row-sel"' : '';
    const cells   = cols.map(c => {
      const raw = c === 'pk' ? row.pk : (row.props[c] ?? '');
      const txt = raw !== null && raw !== undefined ? String(raw) : '';
      return `<td title="${_escAttr(txt)}">${_escHtml(txt)}</td>`;
    }).join('');
    return `<tr${selAttr} data-pk="${_escAttr(String(row.pk))}">${cells}</tr>`;
  }).join('');

  gc.innerHTML = `<table class="ta-table">
    <thead><tr>${thead}</tr></thead>
    <tbody>${tbody}</tbody>
  </table>`;

  // Tri au clic sur l'en-tête (TA-03)
  gc.querySelectorAll('.ta-th').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.col;
      if (_ta.sortCol === col) {
        _ta.sortAsc = !_ta.sortAsc;
      } else {
        _ta.sortCol = col;
        _ta.sortAsc = true;
      }
      _renderGrid();
    });
  });

  // Clic sur une ligne → zoom + sélection (TA-06)
  gc.querySelectorAll('tbody tr[data-pk]').forEach(tr => {
    tr.addEventListener('click', () => _onRowClick(Number(tr.dataset.pk)));
  });

  // Scroll vers la première ligne surlignée
  const firstSel = gc.querySelector('tr.ta-row-sel');
  if (firstSel) firstSel.scrollIntoView({ block: 'nearest' });

  _updateFooter(selSet.size, total);
  _updatePagination(total);
}

// ── Clic sur une ligne (TA-06) ────────────────────────────────────────────────

function _onRowClick(pk) {
  const row = _ta.data.find(r => Number(r.pk) === pk);
  if (!row) return;

  // Mettre à jour la sélection cartographique
  if (typeof window.applySelectionFromPks === 'function') {
    window.applySelectionFromPks(_ta.couche, [pk]);
  }

  // Zoomer sur l'entité via sa géométrie GeoJSON
  if (row.geom && window.MAP) {
    const bbox = _geomBbox(row.geom);
    if (bbox) {
      window.MAP.fitBounds(
        [[bbox[0], bbox[1]], [bbox[2], bbox[3]]],
        { padding: 60, maxZoom: 16, duration: 600 },
      );
    }
  }

  // Basculer sur l'onglet Carte pour que l'utilisateur voie le zoom
  _switchTab('carte');

  // ── FEATURE-C2 : Charger les ouvrages associés si périmètre sélectionné ──
  if (_ta.couche === 'perimetres') {
    _loadOuvragesPanel(pk);
  }
}

// ── FEATURE-C2 — Sous-panneau ouvrages d'un périmètre ────────────────────────

const _OUVRAGE_TYPES = ['seuils', 'murs_protection', 'troncons_seguias', 'barrages', 'khettaras', 'forages_puits', 'prises_locales'];
const _OUVRAGE_LABELS = {
  seuils: 'Seuils', murs_protection: 'Murs', troncons_seguias: 'Séguias',
  barrages: 'Barrages', khettaras: 'Khettaras', forages_puits: 'Forages', prises_locales: 'Prises',
};

let _ouvCache = {}; // {pk: {type: data}}
let _ouvPk    = null;
let _ouvTab   = 'seuils';

async function _loadOuvragesPanel(pk) {
  const panel = document.getElementById('ta-ouvrages-panel');
  if (!panel) return;

  _ouvPk = pk;
  _ouvCache = {};
  panel.style.display = '';

  panel.innerHTML = `
    <div class="ta-ouv-header">
      <span class="ta-ouv-title"><i class="fas fa-layer-group"></i> Ouvrages associés — Périmètre #${pk}</span>
      <button class="ta-btn" id="ta-ouv-close" style="padding:2px 6px;font-size:10px">✕</button>
    </div>
    <div class="ta-ouv-tabs">
      ${_OUVRAGE_TYPES.map(t => `<button class="ta-ouv-tab${t === _ouvTab ? ' active' : ''}" data-ouv="${t}">${_OUVRAGE_LABELS[t]} <span class="ta-ouv-count" id="ta-ouv-count-${t}"></span></button>`).join('')}
    </div>
    <div class="ta-ouv-body" id="ta-ouv-body"><p style="color:#aaa;font-size:11px"><i class="fas fa-spinner fa-spin"></i> Chargement…</p></div>`;

  document.getElementById('ta-ouv-close')?.addEventListener('click', () => {
    panel.style.display = 'none';
    panel.innerHTML = '';
    _ouvPk = null;
  });

  panel.querySelectorAll('.ta-ouv-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      panel.querySelectorAll('.ta-ouv-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      _ouvTab = btn.dataset.ouv;
      _showOuvrageTab(_ouvTab);
    });
  });

  // Pré-charger le premier onglet
  await _fetchOuvrageType(pk, _ouvTab);
  _showOuvrageTab(_ouvTab);

  // Charger les autres en arrière-plan (juste les counts)
  _OUVRAGE_TYPES.filter(t => t !== _ouvTab).forEach(t => {
    _fetchOuvrageType(pk, t).then(() => {
      const cnt = _ouvCache[t]?.count ?? 0;
      const el  = document.getElementById(`ta-ouv-count-${t}`);
      if (el) el.textContent = cnt ? `(${cnt})` : '';
    });
  });
}

async function _fetchOuvrageType(pk, type) {
  if (_ouvCache[type]) return _ouvCache[type];
  try {
    const resp = await fetch(`/carte/api/perimetre/${pk}/ouvrages/${type}/`);
    const data = await resp.json();
    _ouvCache[type] = data;
    const el = document.getElementById(`ta-ouv-count-${type}`);
    if (el) el.textContent = data.count ? `(${data.count})` : '';
    return data;
  } catch { _ouvCache[type] = { count: 0, fields: [], ouvrages: [] }; return _ouvCache[type]; }
}

function _showOuvrageTab(type) {
  const body = document.getElementById('ta-ouv-body');
  if (!body) return;
  const data = _ouvCache[type];
  if (!data) { body.innerHTML = `<p style="color:#aaa;font-size:11px"><i class="fas fa-spinner fa-spin"></i> Chargement…</p>`; return; }
  if (!data.count) { body.innerHTML = `<p style="color:#aaa;font-size:11px;padding:6px">Aucun ${_OUVRAGE_LABELS[type].toLowerCase()} associé.</p>`; return; }
  const cols   = data.fields;
  const header = cols.map(c => `<th>${c}</th>`).join('');
  const rows   = data.ouvrages.map(row =>
    `<tr>${cols.map(c => `<td>${row[c] ?? ''}</td>`).join('')}</tr>`
  ).join('');
  body.innerHTML = `
    <table class="ta-ouv-mini-table">
      <thead><tr>${header}</tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

// ── Pagination ────────────────────────────────────────────────────────────────

function _updatePagination(total) {
  const { pageSize, page } = _ta;
  const nbPages = Math.ceil(total / pageSize) || 1;
  const infoEl  = document.getElementById('ta-page-info');
  const btnsEl  = document.getElementById('ta-page-btns');
  if (!infoEl || !btnsEl) return;

  if (total) {
    const s = page * pageSize + 1;
    const e = Math.min((page + 1) * pageSize, total);
    infoEl.textContent = `${s}–${e} sur ${total}`;
  } else {
    infoEl.textContent = '';
  }

  // Boutons de navigation (fenêtre glissante de 7 numéros max)
  const parts = [];
  parts.push(`<button class="ta-page-btn" id="ta-btn-prev"${page === 0 ? ' disabled' : ''}>‹</button>`);

  const MAX = 7;
  let pStart = Math.max(0, page - 3);
  let pEnd   = Math.min(nbPages - 1, pStart + MAX - 1);
  if (pEnd - pStart < MAX - 1) pStart = Math.max(0, pEnd - MAX + 1);

  if (pStart > 0)       parts.push(`<button class="ta-page-num" data-p="0">1</button>`);
  if (pStart > 1)       parts.push(`<span class="ta-page-ellipsis">…</span>`);

  for (let p = pStart; p <= pEnd; p++) {
    parts.push(`<button class="ta-page-num${p === page ? ' active' : ''}" data-p="${p}">${p + 1}</button>`);
  }

  if (pEnd < nbPages - 2) parts.push(`<span class="ta-page-ellipsis">…</span>`);
  if (pEnd < nbPages - 1) parts.push(`<button class="ta-page-num" data-p="${nbPages - 1}">${nbPages}</button>`);

  parts.push(`<button class="ta-page-btn" id="ta-btn-next"${page >= nbPages - 1 ? ' disabled' : ''}>›</button>`);
  btnsEl.innerHTML = parts.join('');

  btnsEl.querySelector('#ta-btn-prev')?.addEventListener('click', () => {
    if (_ta.page > 0) { _ta.page--; _renderGrid(); }
  });
  btnsEl.querySelector('#ta-btn-next')?.addEventListener('click', () => {
    if (_ta.page < nbPages - 1) { _ta.page++; _renderGrid(); }
  });
  btnsEl.querySelectorAll('.ta-page-num').forEach(btn => {
    btn.addEventListener('click', () => {
      _ta.page = parseInt(btn.dataset.p, 10);
      _renderGrid();
    });
  });
}

// ── Pied de tableau ───────────────────────────────────────────────────────────

function _updateFooter(nbSel, total) {
  const totalEl = document.getElementById('ta-footer-total');
  const selEl   = document.getElementById('ta-footer-sel');
  if (totalEl) totalEl.textContent = total ? `Total : ${total} entité${total > 1 ? 's' : ''}` : '';
  if (selEl)   selEl.textContent   = nbSel > 0 ? `• ${nbSel} sélectionnée${nbSel > 1 ? 's' : ''}` : '';
}

// ── Export (TA-09 CSV / TA-10 Excel / TA-12 sél vs tout / TA-13 colonnes) ────

function _exportBody(selOnly) {
  const pks   = selOnly ? (window.selection_active ?? []) : null;
  const champs = _ta.exportChamps;
  return {
    couche: _ta.couche,
    ...(pks?.length      ? { pks }    : {}),
    ...(champs?.length   ? { champs } : {}),
  };
}

async function _doExport(endpoint, filename) {
  try {
    const resp = await fetch(endpoint, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body:    JSON.stringify(_exportBody(filename.includes('_selection'))),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status} — ${resp.statusText}`);
    const blob = await resp.blob();
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), { href: url, download: filename });
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error('[tableau] export :', err);
    alert(`Export échoué : ${err.message}`);
  }
}

function _exportCsv(selOnly) {
  if (!_ta.couche) return;
  const suffix = selOnly ? '_selection' : '';
  _doExport('/carte/api/export/csv/', `${_ta.couche}${suffix}.csv`);
}

function _exportExcel(selOnly) {
  if (!_ta.couche) return;
  const suffix = selOnly ? '_selection' : '';
  _doExport('/carte/api/export/excel/', `${_ta.couche}${suffix}.xlsx`);
}

// ── Sélecteur de colonnes (TA-13) ─────────────────────────────────────────────

function _allCols() {
  if (!_ta.data.length) return [];
  return ['pk', ...Object.keys(_ta.data[0].props)];
}

function _openColPicker() {
  if (!_ta.data.length) { alert('Chargez une couche avant de choisir les colonnes.'); return; }

  const cols    = _allCols();
  const active  = new Set(_ta.exportChamps ?? cols);
  let   picker  = document.getElementById('ta-col-picker');

  // ── Construire / reconstruire le contenu ──────────────────────────────────
  picker.innerHTML = `
    <div class="ta-cp-header">
      <span>Colonnes à exporter</span>
      <button id="ta-cp-close" class="ta-cp-close-btn" title="Fermer">✕</button>
    </div>
    <div class="ta-cp-body">
      <label class="ta-cp-all">
        <input type="checkbox" id="ta-cp-select-all" ${active.size === cols.length ? 'checked' : ''}>
        <strong>Tout sélectionner</strong>
      </label>
      <hr class="ta-cp-sep">
      <div class="ta-cp-list">
        ${cols.map(c => `
          <label class="ta-cp-item">
            <input type="checkbox" value="${_escAttr(c)}" ${active.has(c) ? 'checked' : ''}>
            ${_escHtml(c)}
          </label>`).join('')}
      </div>
    </div>
    <div class="ta-cp-footer">
      <button id="ta-cp-ok" class="ta-btn ta-btn--primary">Appliquer</button>
      <button id="ta-cp-reset" class="ta-btn">Tout</button>
    </div>`;

  picker.style.display = 'block';

  // "Tout sélectionner"
  const allCb = picker.querySelector('#ta-cp-select-all');
  allCb.addEventListener('change', () => {
    picker.querySelectorAll('.ta-cp-list input[type=checkbox]')
      .forEach(cb => { cb.checked = allCb.checked; });
  });

  // Sync "Tout sélectionner" si on coche/décoche individuellement
  picker.querySelectorAll('.ta-cp-list input[type=checkbox]').forEach(cb => {
    cb.addEventListener('change', () => {
      const all = picker.querySelectorAll('.ta-cp-list input[type=checkbox]');
      allCb.checked = [...all].every(c => c.checked);
    });
  });

  // Appliquer
  picker.querySelector('#ta-cp-ok').addEventListener('click', () => {
    const checked = [...picker.querySelectorAll('.ta-cp-list input[type=checkbox]:checked')]
      .map(cb => cb.value);
    _ta.exportChamps = checked.length && checked.length < cols.length ? checked : null;
    _updateColBtnLabel();
    picker.style.display = 'none';
  });

  // Réinitialiser (toutes)
  picker.querySelector('#ta-cp-reset').addEventListener('click', () => {
    _ta.exportChamps = null;
    _updateColBtnLabel();
    picker.style.display = 'none';
  });

  picker.querySelector('#ta-cp-close').addEventListener('click', () => {
    picker.style.display = 'none';
  });
}

function _updateColBtnLabel() {
  const btn = document.getElementById('btn-ta-cols');
  if (!btn) return;
  const n = _ta.exportChamps?.length ?? _allCols().length;
  btn.innerHTML = `<i class="fas fa-columns"></i> Colonnes (${n})`;
}

// ── Synchronisation bidirectionnelle (§6) ─────────────────────────────────────

// Carte → Tableau : re-surligner les lignes quand la sélection change (TA-05)
document.addEventListener('carte:selectionChange', () => {
  if (_ta.data.length) _renderGrid();
});

// Couche active change → recharger le tableau si l'onglet est visible
document.addEventListener('carte:coucheActive', e => {
  const couche = e.detail?.couche;
  if (!couche) return;

  _ta.couche       = couche;
  _ta.data         = [];
  _ta.page         = 0;
  _ta.sortCol      = null;
  _ta.exportChamps = null;  // reset sélection colonnes à chaque changement de couche

  const lbl = document.getElementById('ta-couche-label');
  if (lbl) lbl.textContent = couche;

  const zoneTab = document.getElementById('zone-tableau');
  if (zoneTab && zoneTab.style.display !== 'none') {
    chargerTableau(couche);
  }
});

// Lazy-load quand on bascule sur l'onglet Tableau
document.addEventListener('carte:tabSwitch', e => {
  if (e.detail?.tab === 'tableau' && _ta.couche && !_ta.data.length) {
    chargerTableau(_ta.couche);
  }
});

// ── Helpers ───────────────────────────────────────────────────────────────────

function _escHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function _escAttr(s) { return _escHtml(s); }

function _geomBbox(geom) {
  if (!geom?.coordinates) return null;
  const flat = _flatCoords(geom);
  if (!flat.length) return null;
  let [minX, minY, maxX, maxY] = [Infinity, Infinity, -Infinity, -Infinity];
  for (const [x, y] of flat) {
    if (x < minX) minX = x; if (x > maxX) maxX = x;
    if (y < minY) minY = y; if (y > maxY) maxY = y;
  }
  return [minX, minY, maxX, maxY];
}

function _flatCoords(geom) {
  const c = geom.coordinates;
  switch (geom.type) {
    case 'Point':           return [c];
    case 'LineString':      return c;
    case 'Polygon':         return c.flat();
    case 'MultiPoint':      return c;
    case 'MultiLineString': return c.flat();
    case 'MultiPolygon':    return c.flat(2);
    default:                return [];
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────

(function init() {
  _initCentraleTabs();

  // Sélecteur de taille de page (TA-01)
  document.getElementById('ta-select-pagesize')?.addEventListener('change', e => {
    _ta.pageSize = parseInt(e.target.value, 10);
    _ta.page     = 0;
    _renderGrid();
  });

  // Export CSV (TA-09 / TA-12)
  document.getElementById('btn-ta-export-sel')?.addEventListener('click', () => _exportCsv(true));
  document.getElementById('btn-ta-export-all')?.addEventListener('click', () => _exportCsv(false));

  // Export Excel (TA-10 / TA-12)
  document.getElementById('btn-ta-xls-sel')?.addEventListener('click', () => _exportExcel(true));
  document.getElementById('btn-ta-xls-all')?.addEventListener('click', () => _exportExcel(false));

  // Sélecteur de colonnes (TA-13)
  document.getElementById('btn-ta-cols')?.addEventListener('click', e => {
    e.stopPropagation();
    const picker = document.getElementById('ta-col-picker');
    if (picker.style.display !== 'none') {
      picker.style.display = 'none';
    } else {
      _openColPicker();
    }
  });

  // Ferme le picker si clic hors
  document.addEventListener('click', e => {
    const picker = document.getElementById('ta-col-picker');
    const btn    = document.getElementById('btn-ta-cols');
    if (!picker || picker.style.display === 'none') return;
    if (!picker.contains(e.target) && e.target !== btn) picker.style.display = 'none';
  });
})();
