/**
 * map.js — Initialisation MapLibre GL + chargement de la liste des couches.
 *
 * Expose window.MAP pour les autres modules (layers.js, query.js, tools.js…).
 * Dépend de maplibre-gl chargé avant ce script.
 */

'use strict';

// ── Configuration ─────────────────────────────────────────────────────────────

const CARTE_CENTER = [-4.7, 32.7];  // Midelt / Tafilalet
const CARTE_ZOOM   = 9;

const GEOM_DOT_CLASS = {
  Polygon:    'geom-polygon',
  LineString: 'geom-linestring',
  Point:      'geom-point',
  Geometry:   'geom-geometry',
};

// ── Initialisation de la carte ────────────────────────────────────────────────

window.MAP = new maplibregl.Map({
  container: 'map',
  // Requis pour capturer la carte en PNG (compositeur Layout) — sans cela
  // canvas.toDataURL() renvoie une image vide sur un contexte WebGL.
  preserveDrawingBuffer: true,
  style: {
    version: 8,
    // Serveur de glyphes (polices) — requis pour les labels texte des couches.
    glyphs: 'https://fonts.openmaptiles.org/{fontstack}/{range}.pbf',
    sources: {
      osm: {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        maxzoom: 19,
        attribution:
          '© <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>',
      },
    },
    layers: [{ id: 'osm-bg', type: 'raster', source: 'osm' }],
  },
  center: CARTE_CENTER,
  zoom: CARTE_ZOOM,
});

MAP.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');
MAP.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-left');

// Promesse résolue quand le style MapLibre est prêt (utile dans layers.js)
window.MAP_READY = new Promise(resolve => MAP.on('load', resolve));

// ── Chargement des couches depuis l'API ───────────────────────────────────────

async function chargerListeCouches() {
  const container = document.getElementById('couches-liste');

  try {
    const resp = await fetch('/carte/api/couches/');
    if (!resp.ok) throw new Error(`HTTP ${resp.status} — ${resp.statusText}`);
    const couches = await resp.json();
    _renderListeCouches(couches, container);
  } catch (err) {
    container.innerHTML = `
      <div class="couches-error">
        <i class="fas fa-exclamation-triangle"></i>
        Impossible de charger les couches.<br>
        <small>${err.message}</small>
      </div>`;
    console.error('[carte] chargerListeCouches :', err);
  }
}

function _renderListeCouches(couches, container) {
  if (!couches.length) {
    container.innerHTML = '<p class="couches-loading">Aucune couche disponible.</p>';
    return;
  }

  // Grouper par attribut "groupe"
  const groupes = {};
  for (const c of couches) {
    if (!groupes[c.groupe]) groupes[c.groupe] = [];
    groupes[c.groupe].push(c);
  }

  container.innerHTML = Object.entries(groupes)
    .map(([groupe, liste]) => {
      const lignes = liste.map(_coucheRowHtml).join('');
      return `
        <details class="couche-groupe" open>
          <summary>${groupe} <small>(${liste.length})</small></summary>
          <ul class="couche-liste">${lignes}</ul>
        </details>`;
    })
    .join('');

  // Notifier layers.js que le panneau est prêt — transmet la liste complète des couches
  if (typeof window.onCouchesRendered === 'function') window.onCouchesRendered(couches);
}

// Gabarit d'une ligne couche du panneau gauche. Exposé pour l'injection
// dynamique d'un groupe (box « Couches » → outils-couches.js).
//   c.reseau_tete : true → couche réseau « intersection-only » (jamais chargée
//   en entier) : pas de case à cocher, bouton « Réseau du BV » au lieu du
//   multicritère.
function _coucheRowHtml(c) {
  const dotClass = GEOM_DOT_CLASS[c.geom_type] ?? 'geom-geometry';
  const champsTip = (c.fields && c.fields.length)
    ? `Champs : ${c.fields.join(', ')}`
    : 'Aucun champ déclaré';

  if (c.reseau_tete) {
    return `
      <li class="couche-row">
        <label class="couche-item" title="${champsTip}">
          <span class="couche-dot ${dotClass}" aria-hidden="true"></span>
          <span class="couche-label" style="margin-left:4px">${c.label}</span>
        </label>
        <button class="couche-action-btn couche-inter-btn" data-couche="${c.nom}"
                title="Réseau du BV : afficher ce réseau clippé à un bassin versant"
                tabindex="-1" aria-label="Réseau du BV pour ${c.label}">
          <i class="fas fa-diagram-project"></i>
        </button>
      </li>`;
  }

  return `
    <li class="couche-row">
      <label class="couche-item" title="${champsTip}">
        <span class="couche-dot ${dotClass}" aria-hidden="true"></span>
        <input type="checkbox" data-couche="${c.nom}" data-geom="${c.geom_type}">
        <span class="couche-label">${c.label}</span>
      </label>
      <button class="couche-style-btn" data-couche="${c.nom}"
              title="Symbologie" tabindex="-1" aria-label="Ouvrir la symbologie de ${c.label}">
        <i class="fas fa-palette"></i>
      </button>
      <button class="couche-action-btn couche-filter-btn" data-couche="${c.nom}"
              title="Requête : filtrer les entités de cette couche sur la carte"
              tabindex="-1" aria-label="Requête sur ${c.label}">
        <i class="fas fa-filter"></i>
      </button>
      <button class="couche-action-btn couche-multi-btn" data-couche="${c.nom}"
              title="Requête multicritère sur cette couche"
              tabindex="-1" aria-label="Requête multicritère sur ${c.label}">
        <i class="fas fa-sliders-h"></i>
      </button>
      <button class="couche-action-btn couche-select-btn" data-couche="${c.nom}"
              title="Sélection d'entités sur cette couche"
              tabindex="-1" aria-label="Sélection sur ${c.label}">
        <i class="fas fa-mouse-pointer"></i>
      </button>
      <button class="couche-action-btn couche-center-btn" data-couche="${c.nom}"
              title="Centrer la carte sur cette couche" tabindex="-1">
        <i class="fas fa-expand-arrows-alt"></i>
      </button>
      <button class="couche-action-btn couche-isoler-btn" data-couche="${c.nom}"
              title="Afficher uniquement cette couche" tabindex="-1">
        <i class="fas fa-eye"></i>
      </button>
    </li>`;
}
window.coucheRowHtml = _coucheRowHtml;

// ── Onglets du panneau outils ─────────────────────────────────────────────────

function _initOnglets() {
  document.querySelectorAll('.outil-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.outil-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const tabId = `tab-${btn.dataset.tab}`;
      document.querySelectorAll('.outil-contenu').forEach(div => {
        div.style.display = div.id === tabId ? '' : 'none';
      });
    });
  });
}

// ── Lancement ─────────────────────────────────────────────────────────────────

_initOnglets();
chargerListeCouches();       // indépendant du chargement des tuiles OSM

MAP.on('load', () => {
  console.info('[carte] MapLibre prêt — centre :', CARTE_CENTER, '— zoom :', CARTE_ZOOM);
});
