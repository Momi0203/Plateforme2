/**
 * layers.js — Chargement et contrôle de visibilité des couches GeoJSON.
 *
 * Cycle de vie d'une couche :
 *   1re activation  → fetch GeoJSON + addSource + addLayer (layout.visibility selon DEFAULT_VISIBLE)
 *   coche           → setLayoutProperty('visibility', 'visible')
 *   décoche         → setLayoutProperty('visibility', 'none')   // source conservée en mémoire
 *
 * API publique :
 *   loadLayer(nom, visibility?)  — charge (si absent) et applique la visibilité
 *   hideLayer(nom)               — masque sans décharger
 *
 * Dépend de map.js (window.MAP, window.MAP_READY).
 * Reçoit la liste des couches via window.onCouchesRendered(couches) depuis map.js.
 */

'use strict';


// ── Utilitaires géométriques (bbox d'une feature) ─────────────────────────────

// Préfixe _lyr : table.js déclare aussi _flatCoords — les scripts classiques
// partagent le scope window, le fichier chargé en dernier écrase l'homonyme.
function _lyrFlatCoords(geom) {
  if (!geom) return [];
  if (geom.type === 'Point') return [geom.coordinates];
  if (geom.type === 'GeometryCollection') return (geom.geometries || []).flatMap(_lyrFlatCoords);
  const src = geom.coordinates;
  if (!src) return [];
  return src.flat(Infinity).reduce((a, _, i, arr) =>
    i % 2 === 0 ? [...a, [arr[i], arr[i + 1]]] : a, []);
}

function _bboxOfFeature(geom) {
  const coords = _lyrFlatCoords(geom);
  if (!coords.length) return null;
  const lons = coords.map(c => c[0]);
  const lats = coords.map(c => c[1]);
  const pad = (geom.type === 'Point') ? 0.015 : 0;
  return [
    [Math.min(...lons) - pad, Math.min(...lats) - pad],
    [Math.max(...lons) + pad, Math.max(...lats) + pad],
  ];
}

// ── Visibilité initiale ───────────────────────────────────────────────────────

// Couches visibles au démarrage ; toutes les autres démarrent masquées.
const DEFAULT_VISIBLE = new Set(['provinces', 'communes']);

// ── Calage (ordre de superposition z) ─────────────────────────────────────────
//
// Ordre du HAUT (index 0, dessiné au-dessus) vers le BAS (au plancher, juste
// au-dessus du fond OSM). Les ouvrages ponctuels/linéaires du diagnostic restent
// au-dessus, les grands polygones administratifs au fond. Chaque couche est
// insérée à sa place via `beforeId` quel que soit l'ordre d'activation des cases.
const STACK_ORDER = [
  'seuils', 'murs_protection', 'troncons_seguias', 'barrages', 'khettaras',
  'forages_puits', 'prises_locales', 'perimetres', 'reseau_hydrographique',
  'stations_pluvio', 'stations_hydro', 'stations_clim',
  'bassins_versants', 'communes', 'provinces',
];

// Surcouches qui doivent rester AU-DESSUS de toutes les couches de données
// (surlignage de sélection — selection.js). La 1re présente sert d'ancre haute.
const _OVERLAY_ANCHORS = ['lyr-sel-fill', 'lyr-sel-line', 'lyr-sel-circle'];

// Renvoie l'id du layer devant lequel insérer la couche `nom` (MapLibre place
// l'ajout SOUS ce `beforeId`) pour respecter STACK_ORDER, ou undefined → sommet.
function _stackBeforeId(nom) {
  const idx = STACK_ORDER.indexOf(nom);
  if (idx === -1) return undefined;
  // Couche chargée la plus proche AU-DESSUS (index plus petit) → insérer dessous.
  for (let i = idx - 1; i >= 0; i--) {
    const above = STACK_ORDER[i];
    if (LOADED_LAYERS.has(above) && MAP.getLayer(`lyr-${above}`)) return `lyr-${above}`;
  }
  // Aucune couche de données au-dessus → rester sous les surcouches de sélection.
  for (const a of _OVERLAY_ANCHORS) if (MAP.getLayer(a)) return a;
  return undefined;   // sommet de la pile
}

// ── Couleurs par groupe ───────────────────────────────────────────────────────

const GROUP_COLORS = {
  'Administratif': '#e67e22',   // orange
  'Hydrologie':    '#2980b9',   // bleu
  'Diagnostic':    '#c0392b',   // rouge
};
const COLOR_FALLBACK = '#7f8c8d';

// Exposé pour export.js (construction de la légende PDF)
window.LAYER_GROUP_COLORS  = GROUP_COLORS;
window.LAYER_COLOR_FALLBACK = COLOR_FALLBACK;

// ── État ──────────────────────────────────────────────────────────────────────

// Couches dont source + layer MapLibre ont été créés.
const LOADED_LAYERS = new Set();
window.LOADED_LAYERS = LOADED_LAYERS;

// Couches dont le chargement initial est en cours (verrou anti-doublon).
const _LOADING = new Set();

// Hooks post-chargement indexés par nom de couche.
// Enregistrés par couches_styles.js (ou tout autre module) avant loadLayer().
window.LAYER_POST_LOAD = {};

// Métadonnées (groupe, geom_type, label…) indexées par nom de couche.
// Exposé sur window pour que symbologie.js puisse y accéder.
window.COUCHES_META = {};

// ── Calcul de la couleur ──────────────────────────────────────────────────────

function _colorFor(nom) {
  const meta = window.COUCHES_META[nom] ?? {};
  return GROUP_COLORS[meta.groupe] ?? COLOR_FALLBACK;
}

// ── Paint par type de layer ───────────────────────────────────────────────────

function _paintFor(nom, layerType) {
  const color = _colorFor(nom);

  if (layerType === 'circle') {
    return {
      'circle-color':        color,
      'circle-radius':       5,
      'circle-stroke-color': '#ffffff',
      'circle-stroke-width': 1,
    };
  }
  if (layerType === 'line') {
    return {
      'line-color': color,
      'line-width': 1,
    };
  }
  // fill (Polygon)
  return {
    'fill-color':         color,
    'fill-opacity':       0.3,
    'fill-outline-color': color,
  };
}

// ── Conversion type géométrique → type layer MapLibre ────────────────────────

function _geomToLayerType(geomType = '') {
  const g = geomType.toLowerCase();
  if (g.includes('polygon'))    return 'fill';
  if (g.includes('linestring')) return 'line';
  return 'circle';   // Point, Geometry, inconnu → cercle
}

// ── Chargement GeoJSON paginé ─────────────────────────────────────────────────
// L'API /carte/api/couche/<nom>/ plafonne chaque réponse (limit max = 2000).
// On enchaîne les pages (offset) jusqu'à tout récupérer → la carte affiche
// TOUTES les entités, même pour les grosses couches (ex. réseau hydro = 1207).

const _PAGE_SIZE = 2000;   // doit rester ≤ au plafond serveur (api_views.py)

async function _fetchCoucheGeoJSON(nom) {
  let offset = 0;
  let all    = null;

  for (;;) {
    const resp = await fetch(`/carte/api/couche/${nom}/?limit=${_PAGE_SIZE}&offset=${offset}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status} — ${resp.statusText}`);
    const page  = await resp.json();
    const feats = page.features ?? [];

    if (!all) all = page;
    else      all.features.push(...feats);

    if (feats.length < _PAGE_SIZE) break;   // dernière page atteinte
    offset += _PAGE_SIZE;
  }
  return all;
}

// ── loadLayer ─────────────────────────────────────────────────────────────────

async function loadLayer(nom, visibility = 'visible') {
  await window.MAP_READY;

  // ── Couche déjà chargée : juste changer la visibilité ────────────────────
  if (LOADED_LAYERS.has(nom)) {
    _setCoucheVisibility(nom, visibility);
    _syncCheckbox(nom, visibility === 'visible');
    return;
  }

  // ── Chargement en cours : attendre qu'il se termine puis réappliquer ─────
  if (_LOADING.has(nom)) {
    const wait = () => new Promise(r => setTimeout(r, 80));
    let tries = 0;
    while (_LOADING.has(nom) && tries++ < 30) await wait();
    // Après attente le layer est (normalement) dans LOADED_LAYERS
    if (LOADED_LAYERS.has(nom)) {
      _setCoucheVisibility(nom, visibility);
      _syncCheckbox(nom, visibility === 'visible');
    }
    return;
  }

  // ── Nouveau chargement ────────────────────────────────────────────────────
  _LOADING.add(nom);
  try {
    const geojson = await _fetchCoucheGeoJSON(nom);

    const firstGeomType = geojson.features?.[0]?.geometry?.type ?? 'Point';
    const layerType     = _geomToLayerType(firstGeomType);

    // Calage z : insérer tous les sous-layers de la couche devant la même ancre.
    const beforeId = _stackBeforeId(nom);

    // Rendu fidèle des contours détaillés (sinon MapLibre/geojson-vt les affiche
    // « en marches d'escalier ») :
    //   tolerance: 0  → pas de simplification Douglas-Peucker (défaut 0.375)
    //   maxzoom:  24  → tuiles fines à tous les zooms (pas de sur-zoom d'une tuile
    //                   grossière qui quantifie la géométrie sur une grille visible)
    MAP.addSource(`src-${nom}`, { type: 'geojson', data: geojson, tolerance: 0, maxzoom: 24 });
    MAP.addLayer({
      id:     `lyr-${nom}`,
      type:   layerType,
      source: `src-${nom}`,
      layout: { visibility },
      paint:  _paintFor(nom, layerType),
    }, beforeId);

    // BUG-L5 — layer fantôme contour pour les polygones (fill-outline-width n'existe pas en MapLibre)
    if (layerType === 'fill') {
      MAP.addLayer({
        id:     `lyr-${nom}-outline`,
        type:   'line',
        source: `src-${nom}`,
        layout: { visibility },
        paint: {
          'line-color': _colorFor(nom),
          'line-width': 1,
        },
      }, beforeId);

      // Label au centre du polygone — nom de l'entité (placé au centroïde par MapLibre).
      // Champ : label_field exposé par l'API (défaut = 1er champ déclaré = le « nom »).
      const labelField = window.COUCHES_META[nom]?.label_field
                      || window.COUCHES_META[nom]?.fields?.[0];
      if (labelField) {
        MAP.addLayer({
          id:     `lyr-${nom}-label`,
          type:   'symbol',
          source: `src-${nom}`,
          minzoom: 7,
          layout: {
            visibility,
            'text-field':         ['to-string', ['coalesce', ['get', labelField], '']],
            'text-font':          ['Open Sans Regular', 'Noto Sans Regular'],
            'text-size':          12,
            'text-max-width':     8,
            'symbol-placement':   'point',
            'text-allow-overlap': false,
          },
          paint: {
            'text-color':      '#1A1A2E',
            'text-halo-color': '#ffffff',
            'text-halo-width': 1.4,
          },
        }, beforeId);
      }
    }

    MAP.on('mouseenter', `lyr-${nom}`, () => { MAP.getCanvas().style.cursor = 'pointer'; });
    MAP.on('mouseleave', `lyr-${nom}`, () => { MAP.getCanvas().style.cursor = ''; });

    // Double-clic → contextmenu.js gère via 'carte:dblclick-feature'
    MAP.on('dblclick', `lyr-${nom}`, e => {
      e.preventDefault();
      const feat = e.features?.[0];
      if (!feat) return;
      document.dispatchEvent(new CustomEvent('carte:dblclick-feature', {
        detail: { layerName: nom, feature: feat },
      }));
    });

    LOADED_LAYERS.add(nom);
    _syncCheckbox(nom, visibility === 'visible');

    // Synchroniser la couleur du dot avec la couleur réelle du layer MapLibre
    const _dotEl = document.querySelector(`input[data-couche="${nom}"]`)
      ?.closest('.couche-row')?.querySelector('.couche-dot');
    if (_dotEl) _dotEl.style.background = _colorFor(nom);

    if (typeof window.LAYER_POST_LOAD[nom] === 'function') {
      window.LAYER_POST_LOAD[nom](nom).catch(err =>
        console.warn(`[layers] post-load "${nom}" :`, err)
      );
    }

    const n = geojson.features?.length ?? 0;
    console.info(`[layers] "${nom}" chargé (${visibility}) — ${n} entité${n > 1 ? 's' : ''}`);

  } catch (err) {
    console.error(`[layers] loadLayer("${nom}") :`, err);
    _syncCheckbox(nom, false);
  } finally {
    _LOADING.delete(nom);
  }
}

// ── hideLayer ─────────────────────────────────────────────────────────────────

function hideLayer(nom) {
  if (!LOADED_LAYERS.has(nom)) return;
  _setCoucheVisibility(nom, 'none');
  _syncCheckbox(nom, false);
  console.info(`[layers] "${nom}" masqué`);
}

// ── Synchronisation des cases à cocher ───────────────────────────────────────

function _syncCheckbox(nom, checked) {
  const cb = document.querySelector(`input[data-couche="${nom}"]`);
  if (cb) cb.checked = checked;
}

// Applique une visibilité ('visible' | 'none') à tous les sous-layers d'une
// couche : fond, contour fantôme (-outline) et label de polygone (-label).
function _setCoucheVisibility(nom, vis) {
  for (const suffix of ['', '-outline', '-label']) {
    const id = `lyr-${nom}${suffix}`;
    if (MAP.getLayer(id)) MAP.setLayoutProperty(id, 'visibility', vis);
  }
}

// ── Callback déclenché par map.js après le rendu du panneau ──────────────────

window.onCouchesRendered = function (couches) {
  // Stocker les métadonnées pour _colorFor et _paintFor
  window.COUCHES_META = {};
  for (const c of couches) window.COUCHES_META[c.nom] = c;

  // Resynchroniser les cases des couches éventuellement déjà chargées
  for (const nom of LOADED_LAYERS) {
    const visible = MAP.getLayoutProperty(`lyr-${nom}`, 'visibility') !== 'none';
    _syncCheckbox(nom, visible);
  }

  // Pré-charger uniquement les couches visibles par défaut.
  // Les autres sont chargées à la demande (clic sur la case) pour éviter
  // 13 requêtes GeoJSON inutiles au démarrage et les conditions de course.
  for (const c of couches) {
    if (DEFAULT_VISIBLE.has(c.nom)) loadLayer(c.nom, 'visible');
  }
};

// ── Écoute des cases à cocher (délégation — #couches-liste est statique) ─────

document.getElementById('couches-liste').addEventListener('change', e => {
  const cb = e.target.closest('input[data-couche]');
  if (!cb) return;
  const nom = cb.dataset.couche;
  if (cb.checked) {
    window.couche_active = nom;
    loadLayer(nom, 'visible');
    document.dispatchEvent(new CustomEvent('carte:coucheActive', { detail: { couche: nom } }));
  } else {
    hideLayer(nom);
  }
});

// ── BUG-L4-B — Bouton Centrer (zoom vers l'emprise de la couche) ──────────────

document.getElementById('couches-liste').addEventListener('click', async e => {
  const btn = e.target.closest('.couche-center-btn');
  if (!btn) return;
  const nom = btn.dataset.couche;
  try {
    const resp = await fetch(`/carte/api/couche/${nom}/extent/`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    if (data.bbox) {
      MAP.fitBounds(
        [[data.bbox[0], data.bbox[1]], [data.bbox[2], data.bbox[3]]],
        { padding: 40 }
      );
    }
  } catch (err) {
    console.warn(`[layers] extent "${nom}" :`, err);
  }
});

// ── BUG-L4-B — Bouton Isoler (afficher uniquement cette couche) ───────────────

let _isolatedLayer = null;

document.getElementById('couches-liste').addEventListener('click', e => {
  const btn = e.target.closest('.couche-isoler-btn');
  if (!btn) return;
  const nom = btn.dataset.couche;

  if (_isolatedLayer === nom) { _restoreIsolation(); return; }

  // Masquer toutes les couches chargées sauf la cible
  for (const loaded of LOADED_LAYERS) {
    if (loaded === nom) continue;
    _setCoucheVisibility(loaded, 'none');
    _syncCheckbox(loaded, false);
  }

  // Assurer la visibilité de la couche cible
  if (!LOADED_LAYERS.has(nom)) {
    loadLayer(nom, 'visible');
  } else {
    _setCoucheVisibility(nom, 'visible');
    _syncCheckbox(nom, true);
  }

  _isolatedLayer = nom;
  document.querySelectorAll('.couche-isoler-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  // Afficher la bannière
  const banner = document.getElementById('carte-isolation-banner');
  const label  = document.getElementById('carte-isolation-label');
  if (banner && label) {
    label.textContent = window.COUCHES_META?.[nom]?.label ?? nom;
    banner.style.display = '';
  }
});

function _restoreIsolation() {
  _isolatedLayer = null;
  // Restaurer la visibilité selon les cases à cocher
  for (const nom of LOADED_LAYERS) {
    const cb  = document.querySelector(`input[data-couche="${nom}"]`);
    const vis = cb?.checked ? 'visible' : 'none';
    _setCoucheVisibility(nom, vis);
  }
  document.querySelectorAll('.couche-isoler-btn').forEach(b => b.classList.remove('active'));
  const banner = document.getElementById('carte-isolation-banner');
  if (banner) banner.style.display = 'none';
}

document.getElementById('btn-isolation-reset')?.addEventListener('click', _restoreIsolation);
