/**
 * contextmenu.js — Menu contextuel clic droit sur les entités de la carte.
 *
 * T3 : Zoom vers l'entité
 * T4 : Masque — hiérarchie 1 (Province → Commune → Périmètre → Ouvrages)
 * T5 : Masque — hiérarchie 2 (Bassin Versant → Réseau/Ouvrages/Stations)
 * T6 : Bannière masque actif + réinitialisation
 *
 * Dépend de map.js (window.MAP), layers.js (LOADED_LAYERS, loadLayer,
 * _bboxOfFeature, window.COUCHES_META).
 */

'use strict';

// ── Hiérarchie Masque ─────────────────────────────────────────────────────────

const MASQUE_CHILDREN = {
  provinces: [
    { key: 'communes',        label: 'Communes' },
    { key: 'perimetres',      label: 'Périmètres' },
    { key: 'seuils',          label: 'Seuils' },
    { key: 'murs_protection', label: 'Murs de protection' },
    { key: 'troncons_seguias',label: 'Tronçons séguias' },
    { key: 'barrages',        label: 'Barrages' },
    { key: 'khettaras',       label: 'Khettaras' },
    { key: 'forages_puits',   label: 'Forages / Puits' },
    { key: 'prises_locales',  label: 'Prises locales' },
  ],
  communes: [
    { key: 'perimetres',      label: 'Périmètres' },
    { key: 'seuils',          label: 'Seuils' },
    { key: 'murs_protection', label: 'Murs de protection' },
    { key: 'troncons_seguias',label: 'Tronçons séguias' },
    { key: 'barrages',        label: 'Barrages' },
    { key: 'khettaras',       label: 'Khettaras' },
    { key: 'forages_puits',   label: 'Forages / Puits' },
    { key: 'prises_locales',  label: 'Prises locales' },
  ],
  perimetres: [
    { key: 'seuils',          label: 'Seuils' },
    { key: 'murs_protection', label: 'Murs de protection' },
    { key: 'troncons_seguias',label: 'Tronçons séguias' },
    { key: 'barrages',        label: 'Barrages' },
    { key: 'khettaras',       label: 'Khettaras' },
    { key: 'forages_puits',   label: 'Forages / Puits' },
    { key: 'prises_locales',  label: 'Prises locales' },
  ],
  bassins_versants: [
    { key: 'reseau_hydrographique', label: 'Réseau hydrographique' },
    { key: 'seuils',                label: 'Seuils' },
    { key: 'barrages',              label: 'Barrages' },
    { key: 'prises_locales',        label: 'Prises locales' },
    { key: 'stations_hydro',        label: 'Stations hydrométriques' },
    { key: 'stations_clim',         label: 'Stations climatiques' },
    { key: 'stations_pluvio',       label: 'Stations pluviométriques' },
  ],
};

// ── État interne ──────────────────────────────────────────────────────────────

let _ctxFeature    = null;   // feature MapLibre sur laquelle le menu est ouvert
let _ctxLayerName  = null;   // nom de la couche (ex : 'provinces')
let _activeMasque  = null;   // { couche, pks } filtre actif

const _menu    = document.getElementById('carte-ctx-menu');
const _subMenu = document.getElementById('ctx-masque-sub');

// ── Ouvrir le menu ────────────────────────────────────────────────────────────

function _showMenu(x, y, feature, layerName) {
  _ctxFeature   = feature;
  _ctxLayerName = layerName;

  // En-tête : nom de la couche + nom de l'entité
  const meta        = window.COUCHES_META?.[layerName];
  const couLabel    = meta?.label ?? layerName;
  const entiteNom   = feature.properties?.nom
                   || feature.properties?.nom_fr
                   || feature.properties?.nom_du_seuil
                   || `#${feature.id ?? '?'}`;
  document.getElementById('ctx-layer-name').textContent = `${couLabel} — ${entiteNom}`;

  // Sous-menu Masque
  _buildMasqueSubMenu(layerName);

  // Positionnement (évite de sortir de l'écran)
  _menu.style.display = 'block';
  const mw = _menu.offsetWidth;
  const mh = _menu.offsetHeight;
  const sx = Math.min(x, window.innerWidth  - mw - 8);
  const sy = Math.min(y, window.innerHeight - mh - 8);
  _menu.style.left = `${sx}px`;
  _menu.style.top  = `${sy}px`;
}

function _hideMenu() {
  _menu.style.display = 'none';
  _subMenu.innerHTML  = '';
  _ctxFeature   = null;
  _ctxLayerName = null;
}

// ── Sous-menu Masque ──────────────────────────────────────────────────────────

function _buildMasqueSubMenu(layerName) {
  const children = MASQUE_CHILDREN[layerName];
  _subMenu.innerHTML = '';
  if (!children?.length) {
    const row = document.createElement('div');
    row.className   = 'ctx-item ctx-sub-item';
    row.style.color = 'var(--c-muted)';
    row.style.fontStyle = 'italic';
    row.textContent = 'Aucune couche liée';
    _subMenu.appendChild(row);
    return;
  }
  for (const child of children) {
    const btn = document.createElement('button');
    btn.className   = 'ctx-item ctx-sub-item';
    btn.textContent = child.label;
    btn.addEventListener('click', () => {
      _hideMenu();
      _applyMasque(_ctxLayerName || layerName, _ctxFeature, child.key, child.label);
    });
    _subMenu.appendChild(btn);
  }
}

// ── Action Zoom (T3) ──────────────────────────────────────────────────────────

document.getElementById('ctx-action-zoom').addEventListener('click', () => {
  if (!_ctxFeature) { _hideMenu(); return; }
  const bbox = _bboxOfFeature(_ctxFeature.geometry);
  if (bbox) MAP.fitBounds(bbox, { padding: 60, maxZoom: 16 });
  _hideMenu();
});

// ── Masque — appel API + filtre MapLibre (T4 / T5) ───────────────────────────

async function _applyMasque(parentCouche, feature, childCouche, childLabel) {
  const pk = feature.id ?? feature.properties?.pk ?? feature.properties?.id;
  if (!pk) { console.warn('[masque] pk introuvable sur la feature'); return; }

  const parentMeta = window.COUCHES_META?.[parentCouche];
  const parentNom  = feature.properties?.nom
                  || feature.properties?.nom_fr
                  || `#${pk}`;

  // Appel API backend
  let pks;
  try {
    const resp = await fetch(`/carte/api/masque/${parentCouche}/${pk}/${childCouche}/`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    pks = data.pks ?? [];
  } catch (err) {
    console.error('[masque] erreur API :', err);
    return;
  }

  if (!pks.length) {
    _showMasqueBanner(`Aucune entité trouvée (${childLabel})`, 0);
    return;
  }

  // Charger la couche enfant si besoin, puis attendre qu'elle soit prête
  if (typeof loadLayer === 'function' && !window.LOADED_LAYERS?.has(childCouche)) {
    await new Promise(resolve => {
      const orig = window.LAYER_POST_LOAD?.[childCouche];
      window.LAYER_POST_LOAD = window.LAYER_POST_LOAD || {};
      window.LAYER_POST_LOAD[childCouche] = async (nom) => {
        if (typeof orig === 'function') await orig(nom);
        resolve();
      };
      loadLayer(childCouche, 'visible');
    });
  } else if (typeof loadLayer === 'function') {
    loadLayer(childCouche, 'visible');
  }

  // Appliquer le filtre MapLibre
  // ['id'] accède au top-level id du feature (= pk Django), pas à properties.id
  const numPks  = pks.map(Number);
  const layerId = `lyr-${childCouche}`;
  if (MAP.getLayer(layerId)) {
    const expr = ['in', ['id'], ['literal', numPks]];
    for (const suffix of ['', '-outline', '-label']) {
      const id = `${layerId}${suffix}`;
      if (MAP.getLayer(id)) {
        MAP.setFilter(id, expr);
        MAP.setLayoutProperty(id, 'visibility', 'visible');
      }
    }
  }

  // Mémoriser le masque actif pour la réinitialisation
  _activeMasque = { couche: childCouche, pks };

  // Activer la couche exactement comme un clic utilisateur sur la case
  const cb = document.querySelector(`input[data-couche="${childCouche}"]`);
  if (cb) cb.checked = true;
  window.couche_active = childCouche;
  document.dispatchEvent(new CustomEvent('carte:coucheActive', { detail: { couche: childCouche } }));

  // Bannière
  const childMeta = window.COUCHES_META?.[childCouche];
  const childLabelFull = childMeta?.label ?? childLabel;
  _showMasqueBanner(
    `${childLabelFull} — ${parentNom} (${pks.length} entité${pks.length > 1 ? 's' : ''})`,
    pks.length
  );

  // Zoomer sur les résultats
  try {
    const resp = await fetch(`/carte/api/couche/${childCouche}/extent/?pks=${pks.join(',')}`);
    if (resp.ok) {
      const data = await resp.json();
      if (data.bbox) MAP.fitBounds(
        [[data.bbox[0], data.bbox[1]], [data.bbox[2], data.bbox[3]]],
        { padding: 40 }
      );
    }
  } catch (_) {}
}

// ── Bannière masque actif (T6) ────────────────────────────────────────────────

function _showMasqueBanner(label, count) {
  const banner = document.getElementById('carte-masque-banner');
  const span   = document.getElementById('carte-masque-label');
  if (!banner || !span) return;
  span.textContent = label;
  banner.style.display = '';
}

function _resetMasque() {
  if (!_activeMasque) return;
  const { couche } = _activeMasque;
  const layerId = `lyr-${couche}`;

  for (const suffix of ['', '-outline', '-label']) {
    if (MAP.getLayer(`${layerId}${suffix}`)) MAP.setFilter(`${layerId}${suffix}`, null);
  }
  _activeMasque = null;

  const banner = document.getElementById('carte-masque-banner');
  if (banner) banner.style.display = 'none';
}

document.getElementById('btn-masque-reset')?.addEventListener('click', _resetMasque);

// ── Double-clic → masque automatique sur le premier enfant ────────────────────

document.addEventListener('carte:dblclick-feature', e => {
  const { layerName, feature } = e.detail;
  const children = MASQUE_CHILDREN[layerName];
  if (!children?.length) return;   // couche sans enfants → rien
  _applyMasque(layerName, feature, children[0].key, children[0].label);
});

// ── Listener clic droit sur la carte ─────────────────────────────────────────

MAP_READY.then(() => {
  MAP.on('contextmenu', e => {
    // Récupérer la feature de la couche la plus haute sous le curseur
    const allLayerIds = [...(window.LOADED_LAYERS || [])].map(n => `lyr-${n}`);
    const feats = MAP.queryRenderedFeatures(e.point, { layers: allLayerIds });

    if (!feats.length) { _hideMenu(); return; }

    const feat      = feats[0];
    const layerId   = feat.layer.id;                     // ex: "lyr-provinces"
    const layerName = layerId.replace(/^lyr-/, '')       // ex: "provinces"
                             .replace(/-outline$/, '');

    _showMenu(e.originalEvent.clientX, e.originalEvent.clientY, feat, layerName);

    // Empêcher le menu contextuel natif du navigateur
    e.originalEvent.preventDefault();
  });

  // Fermer sur clic ailleurs
  document.addEventListener('click', e => {
    if (!_menu.contains(e.target)) _hideMenu();
  });
});
