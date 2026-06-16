/**
 * drilldown.js — Double-clic / drill-down (§5.1.6)
 *
 * Province    → zoom emprise + communes filtrées (GET ?pks=)
 * Seuil       → BassinVersant polygone + ReseauHydrographique classifié grid_code
 * PriseLocale → même logique BV via PriseLocale.bassin_versant
 * Barrage     → même logique BV via BarrageRetenue.bassin_versant
 *
 * Couches drill-down ajoutées en dehors du gestionnaire de couches normal
 * (sources/layers MapLibre temporaires préfixées "dd-").
 * ESC ou clic sur le bouton ✕ du badge efface tout.
 *
 * Dépend de :
 *   map.js   → window.MAP, window.MAP_READY
 *   query.js → requeteSimple(), getCsrf()  (chargé avant ce fichier)
 */

'use strict';

// ── Style réseau hydrographique par grid_code (§5.1.6) ───────────────────────

const DD_RESEAU_PAINT = {
  'line-width': [
    'interpolate', ['linear'], ['get', 'grid_code'],
    1, 1,   // petit affluent  → 1 px
    5, 3,   // cours moyen     → 3 px
    9, 6,   // cours principal → 6 px
  ],
  'line-color': [
    'interpolate', ['linear'], ['get', 'grid_code'],
    1, '#a8d5f5',   // bleu clair
    5, '#4a90d9',   // bleu moyen
    9, '#1a4f8a',   // bleu foncé
  ],
  'line-opacity': 0.92,
};

// ── État ──────────────────────────────────────────────────────────────────────

const _dd = {
  layerIds:      [],  // ids MapLibre des layers temporaires
  sourceIds:     [],  // ids des sources temporaires
  hiddenLayers:  [],  // [{id}] couches normales masquées pour la durée du drill-down
};

// ── Gestion des couches temporaires ──────────────────────────────────────────

function _ddClearAll() {
  for (const id of [..._dd.layerIds].reverse()) {
    if (MAP.getLayer(id)) MAP.removeLayer(id);
  }
  for (const id of _dd.sourceIds) {
    if (MAP.getSource(id)) MAP.removeSource(id);
  }
  _dd.layerIds  = [];
  _dd.sourceIds = [];

  // Rétablir les couches normales masquées
  for (const { id } of _dd.hiddenLayers) {
    if (MAP.getLayer(id)) MAP.setLayoutProperty(id, 'visibility', 'visible');
  }
  _dd.hiddenLayers = [];

  _ddHideBadge();
}

/** Masque une couche normale pendant le drill-down. */
function _ddHideLayer(id) {
  if (!MAP.getLayer(id)) return;
  const prev = MAP.getLayoutProperty(id, 'visibility');
  if (prev !== 'none') {
    MAP.setLayoutProperty(id, 'visibility', 'none');
    _dd.hiddenLayers.push({ id });
  }
}

/** Ajoute une source GeoJSON temporaire. */
function _ddAddSource(id, geojson) {
  if (MAP.getSource(id)) MAP.removeSource(id);
  MAP.addSource(id, { type: 'geojson', data: geojson, tolerance: 0, maxzoom: 24 });  // pas de simplification / tuiles fines
  _dd.sourceIds.push(id);
}

/** Ajoute un layer MapLibre temporaire. */
function _ddAddLayer(spec) {
  if (MAP.getLayer(spec.id)) MAP.removeLayer(spec.id);
  MAP.addLayer(spec);
  _dd.layerIds.push(spec.id);
}

// ── Badge de notification ─────────────────────────────────────────────────────

function _ddShowBadge(texte) {
  let badge = document.getElementById('dd-badge');
  if (!badge) {
    badge = document.createElement('div');
    badge.id        = 'dd-badge';
    badge.className = 'dd-badge';
    document.getElementById('zone-carte')?.appendChild(badge);
  }

  // Reconstruire proprement sans innerHTML non sécurisé
  badge.textContent = '';

  const icon = document.createElement('i');
  icon.className = 'fas fa-layer-group';
  badge.appendChild(icon);

  const msg = document.createElement('span');
  msg.textContent = ' ' + texte + ' ';
  badge.appendChild(msg);

  const kbd = document.createElement('kbd');
  kbd.textContent = 'Échap';
  badge.appendChild(kbd);

  const btn = document.createElement('button');
  btn.title       = 'Fermer le drill-down';
  btn.textContent = '✕';
  btn.addEventListener('click', _ddClearAll);
  badge.appendChild(btn);

  badge.style.display = 'flex';
}

function _ddHideBadge() {
  const badge = document.getElementById('dd-badge');
  if (badge) badge.style.display = 'none';
}

// ── Helpers géométriques ──────────────────────────────────────────────────────

function _ddBbox(geometry) {
  if (!geometry?.coordinates) return null;
  const pts = _ddFlatCoords(geometry);
  if (!pts.length) return null;
  let [xMin, yMin, xMax, yMax] = [Infinity, Infinity, -Infinity, -Infinity];
  for (const [x, y] of pts) {
    if (x < xMin) xMin = x; if (x > xMax) xMax = x;
    if (y < yMin) yMin = y; if (y > yMax) yMax = y;
  }
  return isFinite(xMin) ? [xMin, yMin, xMax, yMax] : null;
}

function _ddCollectionBbox(geojson) {
  const features = geojson.features ?? [];
  let [xMin, yMin, xMax, yMax] = [Infinity, Infinity, -Infinity, -Infinity];
  for (const f of features) {
    const b = _ddBbox(f.geometry);
    if (!b) continue;
    if (b[0] < xMin) xMin = b[0]; if (b[2] > xMax) xMax = b[2];
    if (b[1] < yMin) yMin = b[1]; if (b[3] > yMax) yMax = b[3];
  }
  return isFinite(xMin) ? [xMin, yMin, xMax, yMax] : null;
}

function _ddFlatCoords(geom) {
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

function _ddZoom(bbox, opts = {}) {
  if (!bbox) return;
  MAP.fitBounds([[bbox[0], bbox[1]], [bbox[2], bbox[3]]], {
    padding: 60, duration: 800, maxZoom: 14, ...opts,
  });
}

// ── Province → Communes filtrées (§5.1.6 ligne 1) ────────────────────────────

async function _ddProvinceToCommuneS(feature) {
  const provincePk = Number(feature.id ?? feature.properties?.pk);
  if (!provincePk) return;

  console.info(`[drilldown] Province ${provincePk} → communes`);

  try {
    // 1. requete_simple → PKs des communes appartenant à cette province
    const res = await requeteSimple('communes', 'province', '=', provincePk);
    if (!res?.pks?.length) {
      console.warn('[drilldown] aucune commune pour la province', provincePk);
      return;
    }

    // 2. GeoJSON filtré sur ces PKs
    const resp = await fetch(`/carte/api/couche/communes/?pks=${res.pks.join(',')}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const geojson = await resp.json();
    if (!geojson.features?.length) return;

    // 3. Masquer la couche communes normale, afficher la sélection
    _ddClearAll();
    _ddHideLayer('lyr-communes');

    _ddAddSource('src-dd-communes', geojson);
    _ddAddLayer({
      id:     'lyr-dd-communes-fill',
      type:   'fill',
      source: 'src-dd-communes',
      paint:  { 'fill-color': '#e67e22', 'fill-opacity': 0.42, 'fill-outline-color': '#c0542a' },
    });
    _ddAddLayer({
      id:     'lyr-dd-communes-line',
      type:   'line',
      source: 'src-dd-communes',
      paint:  { 'line-color': '#c0542a', 'line-width': 1.5 },
    });

    // 4. Zoom sur l'emprise de la province
    const bbox = _ddBbox(feature.geometry);
    _ddZoom(bbox);

    _ddShowBadge(`${res.pks.length} commune(s) — Province #${provincePk}`);
  } catch (err) {
    console.error('[drilldown] Province → Communes :', err);
  }
}

// ── Seuil / PriseLocale / Barrage → BV + Réseau hydro (§5.1.6 lignes 2-3) ───

async function _ddOuvrageToBvReseau(feature, nomCouche) {
  const bvPk = feature.properties?.bassin_versant;
  if (!bvPk) {
    console.warn(`[drilldown] ${nomCouche} #${feature.id} — pas de bassin_versant`);
    return;
  }

  console.info(`[drilldown] ${nomCouche} #${feature.id} → BV ${bvPk} + réseau`);

  try {
    // 1. Polygone du BV — geojson_entite
    const bvResp = await fetch(`/carte/api/couche/bassins_versants/${bvPk}/`);
    if (!bvResp.ok) throw new Error(`BV HTTP ${bvResp.status}`);
    const bvGj = await bvResp.json();
    if (!bvGj.features?.length) throw new Error('BV GeoJSON vide');

    // 2. Bbox du BV → filtre réseau hydrographique
    const bbox = _ddCollectionBbox(bvGj);
    if (!bbox) throw new Error('bbox BV invalide');

    // 3. Réseau hydrographique dans la bbox
    const reseauResp = await fetch(
      `/carte/api/couche/reseau_hydrographique/?bbox=${bbox.join(',')}&limit=2000`
    );
    if (!reseauResp.ok) throw new Error(`Réseau HTTP ${reseauResp.status}`);
    const reseauGj = await reseauResp.json();

    // 4. Afficher les couches
    _ddClearAll();

    // BV : remplissage léger + contour
    _ddAddSource('src-dd-bv', bvGj);
    _ddAddLayer({
      id:     'lyr-dd-bv-fill',
      type:   'fill',
      source: 'src-dd-bv',
      paint:  { 'fill-color': '#2980b9', 'fill-opacity': 0.18 },
    });
    _ddAddLayer({
      id:     'lyr-dd-bv-border',
      type:   'line',
      source: 'src-dd-bv',
      paint:  { 'line-color': '#1a5f9a', 'line-width': 2.2 },
    });

    // Réseau hydrographique classifié par grid_code
    const nbTroncons = reseauGj.features?.length ?? 0;
    if (nbTroncons) {
      _ddAddSource('src-dd-reseau', reseauGj);
      _ddAddLayer({
        id:     'lyr-dd-reseau',
        type:   'line',
        source: 'src-dd-reseau',
        paint:  DD_RESEAU_PAINT,
      });
    }

    // 5. Zoom sur le BV
    _ddZoom(bbox);

    _ddShowBadge(`BV #${bvPk} — ${nbTroncons} tronçon(s) hydrographique(s)`);
  } catch (err) {
    console.error('[drilldown] OuvrageToBvReseau :', err);
  }
}

// ── Initialisation des handlers dblclick ─────────────────────────────────────

async function _initDrilldown() {
  await window.MAP_READY;

  // Province → Communes filtrées + zoom
  MAP.on('dblclick', 'lyr-provinces', (e) => {
    e.preventDefault();
    const f = MAP.queryRenderedFeatures(e.point, { layers: ['lyr-provinces'] })[0];
    if (f) _ddProvinceToCommuneS(f);
  });

  // Seuil → BV + Réseau
  MAP.on('dblclick', 'lyr-seuils', (e) => {
    e.preventDefault();
    const f = MAP.queryRenderedFeatures(e.point, { layers: ['lyr-seuils'] })[0];
    if (f) _ddOuvrageToBvReseau(f, 'seuils');
  });

  // Prise locale → BV + Réseau
  MAP.on('dblclick', 'lyr-prises_locales', (e) => {
    e.preventDefault();
    const f = MAP.queryRenderedFeatures(e.point, { layers: ['lyr-prises_locales'] })[0];
    if (f) _ddOuvrageToBvReseau(f, 'prises_locales');
  });

  // Barrage collinaire → BV + Réseau
  MAP.on('dblclick', 'lyr-barrages', (e) => {
    e.preventDefault();
    const f = MAP.queryRenderedFeatures(e.point, { layers: ['lyr-barrages'] })[0];
    if (f) _ddOuvrageToBvReseau(f, 'barrages');
  });

  // Touche Échap → quitter le mode drill-down
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && _dd.layerIds.length) _ddClearAll();
  });

  console.info('[drilldown] handlers dblclick enregistrés');
}

// ── Init ──────────────────────────────────────────────────────────────────────

_initDrilldown();
