/**
 * selection.js — Outils de sélection cartographique
 *
 * SEL-01 Sélection rectangulaire (drag + queryRenderedFeatures)
 * SEL-04 Clic sur entité → info-bulle 5 attributs + mise à jour selection_active
 * SEL-06 Compteur en temps réel dans la barre de statut
 * SEL-07 Tout désélectionner / Inverser
 * SEL-08 Surlignage jaune des entités sélectionnées
 *
 * API publique :
 *   window.selection_active           — array de PKs (lecture)
 *   window.applySelectionFromPks(couche, pks) — appelé par query.js après requête API
 *
 * Dépend de :
 *   map.js    → window.MAP, window.MAP_READY
 *   layers.js → window.LOADED_LAYERS
 */

'use strict';

// ── État ──────────────────────────────────────────────────────────────────────

window.selection_active     = [];   // array de PKs (exposé pour les autres modules)
window.selection_par_couche = {};   // { couche: [pks] } — sélection ventilée par couche

let _selFeatures   = [];        // [{id, nom, feature}] — données internes
let _selectionMode = 'click';   // 'click' | 'rect'
let _activePopup   = null;

// ── Source et layers de surlignage (SEL-08) ───────────────────────────────────

const SEL_SRC = 'src-sel';

async function _initHighlight() {
  await window.MAP_READY;

  MAP.addSource(SEL_SRC, {
    type: 'geojson',
    data: { type: 'FeatureCollection', features: [] },
  });

  MAP.addLayer({
    id: 'lyr-sel-fill', type: 'fill', source: SEL_SRC,
    filter: ['==', ['geometry-type'], 'Polygon'],
    paint: { 'fill-color': '#f1c40f', 'fill-opacity': 0.55, 'fill-outline-color': '#e67e22' },
  });

  MAP.addLayer({
    id: 'lyr-sel-line', type: 'line', source: SEL_SRC,
    filter: ['any',
      ['==', ['geometry-type'], 'LineString'],
      ['==', ['geometry-type'], 'MultiLineString'],
    ],
    paint: { 'line-color': '#f1c40f', 'line-width': 3 },
  });

  MAP.addLayer({
    id: 'lyr-sel-circle', type: 'circle', source: SEL_SRC,
    filter: ['==', ['geometry-type'], 'Point'],
    paint: {
      'circle-color': '#f1c40f', 'circle-radius': 9,
      'circle-stroke-color': '#e67e22', 'circle-stroke-width': 2,
    },
  });
}

// ── Synchronisation état → DOM ────────────────────────────────────────────────

// fullPks : si fourni (par applySelectionFromPks), utilise ce tableau pour le
// compteur total plutôt que de le dériver de _selFeatures (viewport seulement).
function _refreshSelection(fullPks, fullCouche) {
  // Highlight (SEL-08)
  const src = MAP.getSource(SEL_SRC);
  if (src) {
    src.setData({ type: 'FeatureCollection', features: _selFeatures.map(s => s.feature) });
  }

  // API publique
  window.selection_active = fullPks != null ? fullPks : _selFeatures.map(s => s.id);

  // Sélection ventilée par couche (outils du panneau droit)
  const parCouche = {};
  if (fullPks != null && fullCouche) {
    parCouche[fullCouche] = fullPks.map(Number);
  } else {
    for (const s of _selFeatures) (parCouche[s.nom] ??= []).push(Number(s.id));
  }
  window.selection_par_couche = parCouche;

  // Compteur (SEL-06)
  const n  = window.selection_active.length;
  const el = document.getElementById('sel-compteur');
  if (el) {
    const s = n !== 1 ? 's' : '';
    el.textContent = n > 0 ? `${n} entite${s} selectionnee${s}` : '';
    el.classList.toggle('sel-compteur--visible', n > 0);
  }

  // Synchronisation Tableau (TA-05) + Dashboard (DB-02/03/04)
  document.dispatchEvent(new CustomEvent('carte:selectionChange'));
}

// ── SEL-04 : Clic sur entité ─────────────────────────────────────────────────

function _onMapClick(e) {
  if (_selectionMode !== 'click') return;

  const layerIds = _scopedLayerIds();
  if (!layerIds.length) return;

  const features = MAP.queryRenderedFeatures(e.point, { layers: layerIds });

  if (!features.length) {
    _clearAll();
    return;
  }

  const f   = features[0];
  const pk  = f.id;
  const nom = f.layer.id.replace(/^lyr-/, '');

  const idx = _selFeatures.findIndex(s => s.id === pk && s.nom === nom);
  if (idx >= 0) {
    // Deja selectionne → deselectioner
    _selFeatures.splice(idx, 1);
  } else {
    // Clic simple → remplace la selection
    _selFeatures = [{ id: pk, nom, feature: f }];
  }

  _refreshSelection();
  _showInfoBulle(f, e.lngLat);
}

function _showInfoBulle(feature, lngLat) {
  if (_activePopup) { _activePopup.remove(); _activePopup = null; }

  const props = feature.properties ?? {};
  const top5 = Object.entries(props)
    .filter(([, v]) => v !== null && v !== undefined && String(v) !== '' && String(v) !== 'null')
    .slice(0, 5);

  if (!top5.length) return;

  const rows = top5
    .map(([k, v]) =>
      `<tr>
         <td style="padding:2px 8px 2px 0;font-weight:600;color:#555;white-space:nowrap">${k}</td>
         <td style="padding:2px 0;color:#222">${v}</td>
       </tr>`)
    .join('');

  _activePopup = new maplibregl.Popup({ maxWidth: '300px', closeButton: true })
    .setLngLat(lngLat)
    .setHTML(
      `<div style="font-size:11px;font-weight:700;color:#b8860b;margin-bottom:4px">
         ${feature.layer?.id?.replace(/^lyr-/, '') ?? ''}
       </div>
       <table style="border-collapse:collapse;font-size:12px;line-height:1.65">${rows}</table>`
    )
    .addTo(MAP);
}

// ── SEL-01 : Selection rectangulaire ─────────────────────────────────────────

let _rectOn    = false;
let _rectStart = null;
let _rectDiv   = null;

function _activerRect() {
  _selectionMode = 'rect';
  document.getElementById('btn-sel-rect')?.classList.add('active');
  MAP.getCanvas().style.cursor = 'crosshair';
  MAP.dragPan.disable();
}

function _desactiverRect() {
  _selectionMode = 'click';
  document.getElementById('btn-sel-rect')?.classList.remove('active');
  MAP.getCanvas().style.cursor = '';
  MAP.dragPan.enable();
  if (_rectDiv) { _rectDiv.remove(); _rectDiv = null; }
  _rectOn    = false;
  _rectStart = null;
}

function _initRectHandlers() {
  const canvas    = MAP.getCanvas();
  const container = MAP.getCanvasContainer();

  canvas.addEventListener('mousedown', e => {
    if (_selectionMode !== 'rect') return;
    e.preventDefault();
    _rectOn    = true;
    _rectStart = [e.offsetX, e.offsetY];

    _rectDiv = document.createElement('div');
    Object.assign(_rectDiv.style, {
      position: 'absolute', border: '2px dashed #f1c40f',
      background: 'rgba(241,196,15,0.12)', pointerEvents: 'none',
      left: e.offsetX + 'px', top: e.offsetY + 'px',
      width: '0', height: '0', zIndex: '999',
    });
    container.appendChild(_rectDiv);
  });

  window.addEventListener('mousemove', e => {
    if (!_rectOn || !_rectDiv || !_rectStart) return;
    const rect = container.getBoundingClientRect();
    const cx = e.clientX - rect.left;
    const cy = e.clientY - rect.top;
    Object.assign(_rectDiv.style, {
      left:   Math.min(cx, _rectStart[0]) + 'px',
      top:    Math.min(cy, _rectStart[1]) + 'px',
      width:  Math.abs(cx - _rectStart[0]) + 'px',
      height: Math.abs(cy - _rectStart[1]) + 'px',
    });
  });

  window.addEventListener('mouseup', e => {
    if (!_rectOn || !_rectStart) return;

    const rect = container.getBoundingClientRect();
    const cx   = e.clientX - rect.left;
    const cy   = e.clientY - rect.top;
    const bbox = [
      [Math.min(_rectStart[0], cx), Math.min(_rectStart[1], cy)],
      [Math.max(_rectStart[0], cx), Math.max(_rectStart[1], cy)],
    ];

    const layerIds = _scopedLayerIds();
    const features = layerIds.length ? MAP.queryRenderedFeatures(bbox, { layers: layerIds }) : [];

    const seen = new Set();
    _selFeatures = features
      .filter(f => {
        const key = `${f.layer.id}::${f.id}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .map(f => ({ id: f.id, nom: f.layer.id.replace(/^lyr-/, ''), feature: f }));

    _refreshSelection();
    _desactiverRect();
  });
}

// ── SEL-07 : Tout deselectioner / Inverser ────────────────────────────────────

function _clearAll() {
  _selFeatures = [];
  if (_activePopup) { _activePopup.remove(); _activePopup = null; }
  _refreshSelection();
}

function _inverser() {
  const layerIds   = _scopedLayerIds();
  const allVisible = layerIds.length ? MAP.queryRenderedFeatures({ layers: layerIds }) : [];

  const selSet = new Set(_selFeatures.map(s => `${s.nom}::${s.id}`));

  const seen = new Set();
  _selFeatures = allVisible
    .filter(f => {
      const nom = f.layer.id.replace(/^lyr-/, '');
      const key = `${nom}::${f.id}`;
      if (selSet.has(key) || seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .map(f => ({ id: f.id, nom: f.layer.id.replace(/^lyr-/, ''), feature: f }));

  _refreshSelection();
}

// ── Navigation des sous-panneaux du panneau gauche ───────────────────────────
// Les onglets ont ete supprimes : les sous-panneaux (requete / multi / selection)
// s'ouvrent uniquement via les boutons par couche, et se ferment par ← retour.

window.showPgPanel = function (tab) {
  document.getElementById('couches-liste').style.display      = 'none';
  document.getElementById('panneau-symbologie').style.display = 'none';
  document.querySelectorAll('[id^="pg-tab-"]').forEach(el => {
    el.style.display = 'none';
  });

  if (tab === 'couches') {
    document.getElementById('couches-liste').style.display = '';
  } else {
    const el = document.getElementById(`pg-tab-${tab}`);
    if (el) el.style.display = 'flex';
  }
};

// Boutons ← retour : retour a la liste des couches + levee du scope de selection
document.querySelectorAll('.pg-back-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    window.SELECTION_SCOPE = null;
    window.showPgPanel('couches');
  });
});

// ── Scope de selection par couche ────────────────────────────────────────────
// Quand non-null, la selection (clic, rectangle, inverser) ne porte que sur
// cette couche. Pose par le bouton .couche-select-btn, leve par ← retour.

window.SELECTION_SCOPE = null;

function _scopedLayerIds() {
  return [...(window.LOADED_LAYERS ?? [])]
    .filter(nom => !window.SELECTION_SCOPE || nom === window.SELECTION_SCOPE)
    .map(nom => `lyr-${nom}`);
}

// Bouton « Sélection » d'une ligne couche → ouvre le sous-panneau scope sur elle
document.getElementById('couches-liste').addEventListener('click', e => {
  const btn = e.target.closest('.couche-select-btn');
  if (!btn) return;
  e.preventDefault();
  e.stopPropagation();

  const nom = btn.dataset.couche;

  // Rendre la couche visible
  const cb = document.querySelector(`input[data-couche="${nom}"]`);
  if (cb && !cb.checked) {
    cb.checked = true;
    cb.dispatchEvent(new Event('change', { bubbles: true }));
  }

  window.SELECTION_SCOPE = nom;
  const lbl = document.getElementById('pg-selection-couche-label');
  if (lbl) lbl.textContent = window.COUCHES_META?.[nom]?.label ?? nom;

  window.showPgPanel('selection');
});

// ── API publique : applique une selection depuis une liste de PKs (query.js) ──

function _applySelectionFromPks(couche, pks) {
  if (!pks?.length) { _clearAll(); return; }

  const pkSet = new Set(pks.map(Number));
  const rendered = MAP.queryRenderedFeatures({ layers: [`lyr-${couche}`] });
  const seen = new Set();

  _selFeatures = rendered
    .filter(f => {
      const id = Number(f.id);
      if (!pkSet.has(id) || seen.has(id)) return false;
      seen.add(id);
      return true;
    })
    .map(f => ({ id: f.id, nom: couche, feature: f }));

  // Passe fullPks pour que le compteur reflète le total API, pas juste le viewport
  _refreshSelection(pks, couche);
}

// ── Init ──────────────────────────────────────────────────────────────────────

(async () => {
  await _initHighlight();
  _initRectHandlers();

  MAP.on('click', _onMapClick);

  document.getElementById('btn-sel-rect')?.addEventListener('click', () => {
    _selectionMode === 'rect' ? _desactiverRect() : _activerRect();
  });
  document.getElementById('btn-sel-deselect')?.addEventListener('click', _clearAll);
  document.getElementById('btn-sel-invert')?.addEventListener('click', _inverser);

  // Expose pour query.js
  window.applySelectionFromPks = _applySelectionFromPks;

  _refreshSelection();
})();
