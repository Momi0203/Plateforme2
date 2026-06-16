/**
 * basemap.js — Sélecteur de fonds de carte (CA-15)
 *
 * Contrôle MapLibre flottant (bottom-right) avec boutons radio pour basculer
 * entre OSM et 3 fonds Esri sans perturber les couches de données.
 */

'use strict';

// ── Catalogue des fonds ───────────────────────────────────────────────────────

const ESRI_BASEMAPS = {
  osm: {
    label:       'OpenStreetMap',
    icon:        'fa-map',
    url:         'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '© <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>',
    maxzoom:     19,
  },
  topo: {
    label:       'ESRI Topographique',
    icon:        'fa-mountain',
    url:         'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Esri',
  },
  imagery: {
    label:       'ESRI Satellite',
    icon:        'fa-satellite',
    url:         'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Esri, DigitalGlobe',
  },
  streets: {
    label:       'ESRI Streets',
    icon:        'fa-road',
    url:         'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Esri',
  },
};

// ── Contrôle MapLibre ─────────────────────────────────────────────────────────

class EsriBasemapControl {

  onAdd(map) {
    this._map    = map;
    this._active = 'osm';

    this._el = document.createElement('div');
    this._el.className = 'maplibregl-ctrl maplibregl-ctrl-group esri-ctrl';

    const radios = Object.entries(ESRI_BASEMAPS).map(([key, bm]) => `
      <label class="esri-ctrl__radio-label">
        <input type="radio" name="basemap-choice" value="${key}" ${key === 'osm' ? 'checked' : ''}>
        ${bm.label}
      </label>`).join('');

    this._el.innerHTML = `
      <button class="esri-ctrl__toggle" title="Changer le fond de carte" aria-label="Fonds de carte">
        <i class="fas fa-layer-group"></i>
      </button>
      <div class="esri-ctrl__menu" role="menu" aria-hidden="true">
        <div class="esri-ctrl__menu-header">Fond de carte</div>
        <div class="esri-ctrl__radio-group">
          ${radios}
        </div>
      </div>
    `;

    const toggle = this._el.querySelector('.esri-ctrl__toggle');
    const menu   = this._el.querySelector('.esri-ctrl__menu');

    // ── Ouvrir / fermer le menu ───────────────────────────────────────────────
    toggle.addEventListener('click', e => {
      e.stopPropagation();
      const open = menu.classList.toggle('esri-ctrl__menu--open');
      menu.setAttribute('aria-hidden', String(!open));
    });

    // ── Sélectionner un fond via radio ────────────────────────────────────────
    this._el.querySelectorAll('input[name="basemap-choice"]').forEach(radio => {
      radio.addEventListener('change', e => {
        e.stopPropagation();
        const key = radio.value;
        _switchBasemap(key);
        this._active = key;

        const bm = ESRI_BASEMAPS[key];
        toggle.innerHTML = `<i class="fas ${bm.icon}"></i>`;
        toggle.title     = bm.label;
      });
    });

    // ── Fermer sur clic extérieur ─────────────────────────────────────────────
    this._closeOnOutside = () => {
      menu.classList.remove('esri-ctrl__menu--open');
      menu.setAttribute('aria-hidden', 'true');
    };
    document.addEventListener('click', this._closeOnOutside);

    return this._el;
  }

  onRemove() {
    document.removeEventListener('click', this._closeOnOutside);
    this._el.remove();
    this._map = null;
  }
}

// ── Changement de fond sans toucher aux couches de données ────────────────────

function _switchBasemap(key) {
  const bm = ESRI_BASEMAPS[key];
  if (!bm) { console.warn(`[basemap] clé inconnue : "${key}"`); return; }

  if (MAP.getLayer('osm-bg'))  MAP.removeLayer('osm-bg');
  if (MAP.getSource('osm'))    MAP.removeSource('osm');

  MAP.addSource('osm', {
    type:        'raster',
    tiles:       [bm.url],
    tileSize:    256,
    maxzoom:     bm.maxzoom ?? 18,
    attribution: bm.attribution,
  });

  const layers   = MAP.getStyle().layers;
  const beforeId = layers.length > 0 ? layers[0].id : undefined;

  if (beforeId) {
    MAP.addLayer({ id: 'osm-bg', type: 'raster', source: 'osm' }, beforeId);
  } else {
    MAP.addLayer({ id: 'osm-bg', type: 'raster', source: 'osm' });
  }

  console.info(`[basemap] → "${bm.label}"`);
}

// ── Enregistrement du contrôle ────────────────────────────────────────────────

MAP.addControl(new EsriBasemapControl(), 'bottom-right');
