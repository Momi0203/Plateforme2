/**
 * dashboard.js — Onglet Dashboard (§5.2.2)
 *
 * DB-01  Histogramme — distribution d'un champ numérique
 * DB-02  Donut — répartition par valeur catégorielle
 * DB-03  Barres — comparaison d'un indicateur par catégorie
 * DB-04  KPI — nb entités, somme, moyenne, min/max
 * DB-08  Clic segment graphique → sélectionne sur la carte
 *
 * Préconfiguration automatique par couche (§5.2.2) :
 *   perimetres, seuils, troncons_seguias, bassins_versants,
 *   reseau_hydrographique, stations_pluvio, stations_hydro,
 *   stations_clim, provinces, communes
 *
 * Sync §6 :
 *   carte:selectionChange → recalcul si scope=selection
 *   carte:coucheActive    → rechargement
 *   carte:tabSwitch       → lazy-load
 *
 * Dépend de :
 *   Chart.js (CDN, window.Chart)
 *   map.js       → window.MAP
 *   selection.js → window.applySelectionFromPks, window.selection_active
 *   layers.js    → window.COUCHES_META
 *   query.js     → getCsrf() (non utilisé directement ici)
 */

'use strict';

// ── Palette ───────────────────────────────────────────────────────────────────

const DB_COLORS = [
  '#f0a500','#2980b9','#27ae60','#e74c3c','#9b59b6',
  '#1abc9c','#e67e22','#3498db','#2ecc71','#e91e63',
  '#795548','#607d8b','#ff9800','#8bc34a','#00bcd4',
];

// ── Préconfiguration par couche — BUG-C3 nettoyée ────────────────────────────

const DB_PRECONFIG = {
  perimetres: [
    { type: 'donut',  champ: 'commune_territoriale',
      titre: 'Répartition par commune' },
    { type: 'histo',  champ: 'superficie_irriguee',
      titre: 'Distribution superficie irriguée (ha)' },
    { type: 'kpi',    champs: ['nombre_beneficiaires', 'superficie_totale', 'superficie_irriguee'],
      titre: 'Indicateurs périmètres' },
    { type: 'barres', champX: 'commune_territoriale', champY: 'nombre_beneficiaires',
      titre: 'Bénéficiaires par commune' },
  ],
  seuils: [
    { type: 'donut',  champ: 'etat_general',   titre: 'État général des seuils' },
    { type: 'donut',  champ: 'type_du_seuil',  titre: 'Types de seuils' },
    { type: 'histo',  champ: 'debit_mobilise', titre: 'Distribution débit mobilisé (m³/s)' },
    { type: 'kpi',    champs: ['debit_mobilise', 'largeur_crete', 'hauteur_seuil'],
      titre: 'Paramètres hydrauliques' },
  ],
  troncons_seguias: [
    { type: 'donut',  champ: 'nature',         titre: 'Nature des matériaux' },
    { type: 'donut',  champ: 'etat_general',   titre: 'État général des tronçons' },
    { type: 'histo',  champ: 'longueur',       titre: 'Distribution longueurs (m)' },
    { type: 'kpi',    champs: ['longueur'],     aggFunc: { longueur: 'sum' },
      titre: 'Linéaire total réseau (m)' },
    { type: 'kpi',    champs: ['efficience_calculee'], aggFunc: { efficience_calculee: 'avg' },
      titre: 'Efficience moyenne (%)' },
  ],
  barrages: [
    { type: 'donut',  champ: 'etat_general',             titre: 'État général des barrages' },
    { type: 'kpi',    champs: ['capacite_retenue', 'apport_moyen_annuel'],
      titre: 'Capacité et apports' },
  ],
  khettaras: [
    { type: 'donut',  champ: 'etat_general',  titre: 'État des khettaras' },
    { type: 'histo',  champ: 'debit_galerie', titre: 'Distribution débits (m³/s)' },
  ],
  forages_puits: [
    { type: 'donut',  champ: 'etat_general',                     titre: 'État des forages' },
    { type: 'kpi',    champs: ['profondeur_forage', 'debit_exploitation'],
      titre: 'Profondeur et débit' },
  ],
  murs_protection: [
    { type: 'donut',  champ: 'etat_general', titre: 'État des murs de protection' },
    { type: 'histo',  champ: 'longueur',     titre: 'Distribution longueurs (m)' },
  ],
  prises_locales: [
    { type: 'donut',  champ: 'etat_general',  titre: 'État des prises locales' },
    { type: 'kpi',    champs: ['debit_derive'], titre: 'Débit dérivé (m³/s)' },
  ],
  bassins_versants: [
    { type: 'barres', champX: 'nom', champY: 'superficie_km2', limit: 20,
      titre: 'Répartition superficie par bassin (km²)' },
    { type: 'barres', champX: 'nom', champY: 'perimetre_km', limit: 20,
      titre: 'Répartition périmètre par bassin (km)' },
    { type: 'multiAxes', champX: 'nom',
      titre: 'Altitudes min et max par bassin',
      axes: { y: { titre: 'Altitude (m)' } },
      series: [
        { champ: 'altitude_min', label: 'Altitude min (m)', axis: 'y', chartType: 'bar' },
        { champ: 'altitude_max', label: 'Altitude max (m)', axis: 'y', chartType: 'bar' },
      ] },
    { type: 'barres', champX: 'nom', champY: 'thalweg_km', limit: 20,
      titre: 'Longueur du thalweg par bassin (km)' },
    { type: 'multiAxes', champX: 'nom',
      titre: 'Précipitation et évapotranspiration par bassin',
      axes: { y: { titre: 'mm/an' } },
      series: [
        { champ: 'precipitations_annuelles_mm',      label: 'Précipitation annuelle (mm)',      axis: 'y', chartType: 'bar' },
        { champ: 'evapotranspiration_annuelle_mm',   label: 'Évapotranspiration annuelle (mm)', axis: 'y', chartType: 'bar' },
      ] },
    { type: 'kpi',
      champs: [
        'superficie_km2', 'perimetre_km', 'altitude_min', 'altitude_max',
        'precipitations_annuelles_mm', 'evapotranspiration_annuelle_mm',
      ],
      aggFunc: {
        superficie_km2: 'sumMax',
        perimetre_km: 'sumMax',
        altitude_min: 'min',
        altitude_max: 'max',
        precipitations_annuelles_mm: 'minMax',
        evapotranspiration_annuelle_mm: 'minMax',
      },
      champLabels: {
        superficie_km2: 'Surface',
        perimetre_km: 'Périmètre',
        altitude_min: 'Altitude minimale',
        altitude_max: 'Altitude maximale',
        precipitations_annuelles_mm: 'Précipitation',
        evapotranspiration_annuelle_mm: 'Évapotranspiration',
      },
      titre: 'Statistiques bassins versants' },
  ],
  reseau_hydrographique: [
    { type: 'donut', champ: 'sorder', titre: 'Répartition par ordre de Strahler' },
  ],
  stations_pluvio: [
    { type: 'barres', champX: 'nom', champY: 'hauteur_moyenne', limit: 20,
      titre: 'Hauteur moyenne par station (mm)' },
    { type: 'multiAxes', champX: 'nom',
      titre: 'Pjmax par période de retour',
      axes: { y: { titre: 'Pjmax (mm)' } },
      series: [
        { champ: 'pjmax_t10',  label: 'Pjmax T10',  axis: 'y', chartType: 'line' },
        { champ: 'pjmax_t20',  label: 'Pjmax T20',  axis: 'y', chartType: 'line' },
        { champ: 'pjmax_t50',  label: 'Pjmax T50',  axis: 'y', chartType: 'line' },
        { champ: 'pjmax_t100', label: 'Pjmax T100', axis: 'y', chartType: 'line' },
      ] },
    { type: 'kpi',
      champs: ['hauteur_moyenne', 'pjmax_t10', 'pjmax_t20', 'pjmax_t50', 'pjmax_t100'],
      aggFunc: {
        hauteur_moyenne: 'minMax',
        pjmax_t10: 'minMax',
        pjmax_t20: 'minMax',
        pjmax_t50: 'minMax',
        pjmax_t100: 'minMax',
      },
      champLabels: {
        hauteur_moyenne: 'Hauteur moyenne',
        pjmax_t10: 'Pjmax T10',
        pjmax_t20: 'Pjmax T20',
        pjmax_t50: 'Pjmax T50',
        pjmax_t100: 'Pjmax T100',
      },
      titre: 'Statistiques pluviométriques' },
  ],
  stations_hydro: [
    { type: 'barres', champX: 'nom', champY: 'superficie_bv_jaugee', limit: 20,
      titre: 'Superficie BV jaugée par station (km²)' },
    { type: 'multiAxes', champX: 'nom',
      titre: 'Qjmax par période de retour',
      axes: { y: { titre: 'Qjmax (m³/s)' } },
      series: [
        { champ: 'qjmax_t10',  label: 'Qjmax T10',  axis: 'y', chartType: 'line' },
        { champ: 'qjmax_t20',  label: 'Qjmax T20',  axis: 'y', chartType: 'line' },
        { champ: 'qjmax_t50',  label: 'Qjmax T50',  axis: 'y', chartType: 'line' },
        { champ: 'qjmax_t100', label: 'Qjmax T100', axis: 'y', chartType: 'line' },
      ] },
    { type: 'kpi',
      champs: ['superficie_bv_jaugee', 'qjmax_t10', 'qjmax_t20', 'qjmax_t50', 'qjmax_t100'],
      aggFunc: {
        superficie_bv_jaugee: 'minMax',
        qjmax_t10: 'minMax',
        qjmax_t20: 'minMax',
        qjmax_t50: 'minMax',
        qjmax_t100: 'minMax',
      },
      champLabels: {
        superficie_bv_jaugee: 'Superficie BV jaugée',
        qjmax_t10: 'Qjmax T10',
        qjmax_t20: 'Qjmax T20',
        qjmax_t50: 'Qjmax T50',
        qjmax_t100: 'Qjmax T100',
      },
      titre: 'Statistiques hydrométriques' },
  ],
  stations_clim: [
    { type: 'monthlySeries', champ: 'temperatures_moyennes',
      titre: 'Températures moyennes mensuelles', valueLabel: 'Température (°C)' },
    { type: 'monthlySeries', champ: 'precipitations_normales',
      titre: 'Précipitations normales mensuelles', valueLabel: 'Précipitation (mm/mois)' },
  ],
  provinces: [
    { type: 'barres', champX: 'nom_fr', champY: 'population_totale', limit: 20,
      titre: 'Répartition population par province' },
    { type: 'barres', champX: 'nom_fr', champY: 'superficie_km2', limit: 20,
      titre: 'Répartition superficie par province (km²)' },
    { type: 'multiAxes', champX: 'nom_fr',
      titre: 'ET0, précipitation et température par province',
      axes: {
        y:  { titre: 'ET0 / Précipitation (mm)' },
        y1: { titre: 'Température (°C)' },
      },
      series: [
        { champ: 'et0_annuelle_mm',     label: 'ET0 annuelle (mm)',           axis: 'y',  chartType: 'bar' },
        { champ: 'precip_annuelle_mm',  label: 'Précipitation annuelle (mm)', axis: 'y',  chartType: 'bar' },
        { champ: 'temp_moy_annuelle_c', label: 'Température moyenne (°C)',    axis: 'y1', chartType: 'line' },
      ] },
    { type: 'kpi',
      champs: ['superficie_km2', 'population_totale', 'et0_annuelle_mm', 'precip_annuelle_mm', 'temp_moy_annuelle_c'],
      aggFunc: {
        superficie_km2: 'sumMax',
        population_totale: 'sumMax',
        et0_annuelle_mm: 'max',
        precip_annuelle_mm: 'max',
        temp_moy_annuelle_c: 'max',
      },
      champLabels: {
        superficie_km2: 'Superficie',
        population_totale: 'Population',
        et0_annuelle_mm: 'ET0',
        precip_annuelle_mm: 'Précipitation',
        temp_moy_annuelle_c: 'Température',
      },
      titre: 'Statistiques provinces' },
  ],
  communes: [
    { type: 'barres', champX: 'nom_fr', champY: 'population_totale', limit: 20,
      titre: 'Répartition population par commune' },
    { type: 'barres', champX: 'nom_fr', champY: 'superficie_km2', limit: 20,
      titre: 'Répartition superficie par commune (km²)' },
    { type: 'donut',  champ: 'province', labelLayer: 'provinces', labelField: 'nom_fr',
      titre: 'Répartition par province' },
    { type: 'barres', champX: 'nom_fr', champY: 'nbr_perimetres_agricoles', limit: 20,
      titre: 'Nombre de périmètres par commune' },
    { type: 'donut',  champ: 'type_commune', titre: 'Répartition par type' },
    { type: 'kpi',
      champs: ['superficie_km2', 'population_totale', 'nbr_perimetres_agricoles'],
      aggFunc: {
        superficie_km2: 'sumMax',
        population_totale: 'sumMax',
        nbr_perimetres_agricoles: 'sumMax',
      },
      champLabels: {
        superficie_km2: 'Superficie',
        population_totale: 'Population',
        nbr_perimetres_agricoles: 'Périmètres',
      },
      titre: 'Statistiques communes' },
  ],
};

// ── État ──────────────────────────────────────────────────────────────────────

const _db = {
  couche:       null,
  data:         [],    // [{pk, props}] — toutes les entités
  scope:        'all', // 'all' | 'selection'
  charts:       [],    // instances Chart.js actives
  lookupLabels: {},
};

// ── API publique ──────────────────────────────────────────────────────────────

async function chargerDashboard(couche) {
  if (!couche) { _showPlaceholder(); return; }

  _db.couche = couche;
  _db.data   = [];
  _db.scope  = 'all';

  _destroyCharts();
  _showLoading();

  // Libellé couche
  const lbl = document.getElementById('db-couche-label');
  if (lbl) lbl.textContent = window.COUCHES_META?.[couche]?.label ?? couche;

  try {
    const resp = await fetch(`/carte/api/couche/${couche}/?limit=2000`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status} — ${resp.statusText}`);
    const geojson = await resp.json();

    _db.data = (geojson.features ?? []).map(f => ({
      pk:    f.id ?? f.properties?.pk,
      props: f.properties ?? {},
    }));

    await _renderDashboard();
  } catch (err) {
    _showError(err.message);
    console.error('[dashboard] chargerDashboard :', err);
  }
}

// ── Jeu de features selon le scope ───────────────────────────────────────────

function _featureSet() {
  if (_db.scope === 'selection') {
    const sel = new Set((window.selection_active ?? []).map(Number));
    if (sel.size) return _db.data.filter(f => sel.has(Number(f.pk)));
  }
  return _db.data;
}

// ── Rendu principal ───────────────────────────────────────────────────────────

async function _renderDashboard() {
  const grid = document.getElementById('db-grid');
  if (!grid) return;

  _destroyCharts();
  grid.innerHTML = '';

  const features = _featureSet();
  const cfgs     = DB_PRECONFIG[_db.couche] ?? _buildGenericConfig(features);

  document.getElementById('db-toolbar').style.display  = '';
  document.getElementById('db-placeholder').style.display = 'none';

  _updateScopeBar();

  for (const cfg of cfgs) {
    const widget = _createWidget(cfg.titre, cfg.type);
    grid.appendChild(widget);
    await _renderWidget(widget, cfg, features);
  }
}

// ── Config générique (couches sans préconfig) — BUG-C3 : exclure les identifiants ──

// Champs à ne jamais proposer comme dimension catégorielle (identifiants uniques)
const _ID_SUFFIXES = ['_id', '_pk', '_code', '_nom', '_ref', '_name'];
function _isIdentifier(key) {
  const k = key.toLowerCase();
  if (['pk', 'id', 'nom', 'code', 'ref', 'name', 'nom_fr'].includes(k)) return true;
  return _ID_SUFFIXES.some(s => k.endsWith(s)) || k.startsWith('id_');
}

// Compte le nombre de valeurs distinctes d'un champ dans le dataset
function _countDistinct(features, key) {
  return new Set(features.map(f => String(f.props[key] ?? ''))).size;
}

function _buildGenericConfig(features) {
  const cfgs = [{ type: 'kpi', champs: [], titre: 'Statistiques générales' }];
  if (!features.length) return cfgs;

  const props = features[0].props;
  for (const [key, val] of Object.entries(props)) {
    if (_isIdentifier(key)) continue;
    const n = parseFloat(val);
    if (!isNaN(n) && isFinite(n)) {
      cfgs.push({ type: 'histo', champ: key, titre: `Distribution — ${key}` });
      break;
    }
  }
  for (const [key, val] of Object.entries(props)) {
    if (_isIdentifier(key)) continue;
    if (typeof val === 'string' && val && _countDistinct(features, key) <= 30) {
      cfgs.push({ type: 'donut', champ: key, titre: `Répartition — ${key}` });
      break;
    }
  }
  return cfgs;
}

// ── Création d'un conteneur widget ───────────────────────────────────────────

function _createWidget(titre, type) {
  const icon = {
    donut:        'fa-chart-pie',
    histo:        'fa-chart-bar',
    barres:       'fa-chart-column',
    multiAxes:    'fa-chart-line',
    monthlySeries:'fa-chart-line',
    kpi:          'fa-tachometer-alt',
  }[type] ?? 'fa-chart-bar';

  const div = document.createElement('div');
  div.className = 'db-widget';
  div.innerHTML = `
    <div class="db-widget-header">
      <i class="fas ${icon}" style="color:var(--c-accent);font-size:11px"></i>
      <span class="db-widget-title">${_esc(titre)}</span>
    </div>
    <div class="db-widget-body">
      ${type === 'kpi' ? '<div class="db-kpi-grid"></div>' : '<canvas></canvas>'}
    </div>`;
  return div;
}

async function _renderWidget(container, cfg, features) {
  switch (cfg.type) {
    case 'donut':        await _renderDonut(container, cfg, features);  break;
    case 'histo':             _renderHisto(container, cfg, features);   break;
    case 'barres':            _renderBarres(container, cfg, features);  break;
    case 'multiAxes':         _renderMultiAxes(container, cfg, features); break;
    case 'monthlySeries':     _renderMonthlySeries(container, cfg, features); break;
    case 'kpi':               _renderKpi(container, cfg, features);     break;
  }
}

async function _loadLayerLabelMap(layer, field) {
  const cacheKey = `${layer}:${field}`;
  if (_db.lookupLabels[cacheKey]) return _db.lookupLabels[cacheKey];

  try {
    const resp = await fetch(
      `/carte/api/couche/${layer}/?fields=${encodeURIComponent(field)}&limit=2000`
    );
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const geojson = await resp.json();
    const labelMap = Object.fromEntries((geojson.features ?? []).map(f => [
      String(f.id ?? f.properties?.pk),
      f.properties?.[field] ?? f.id ?? '',
    ]));
    _db.lookupLabels[cacheKey] = labelMap;
    return labelMap;
  } catch (err) {
    console.warn(`[dashboard] labels "${layer}.${field}" :`, err);
    return {};
  }
}

// ── DB-02 : Donut ─────────────────────────────────────────────────────────────

async function _renderDonut(container, cfg, features) {
  const body = container.querySelector('.db-widget-body');

  // Labels depuis l'API (règle évolutivité §11.3, catégories dynamiques)
  let labelMap = {};
  try {
    const resp = await fetch(`/carte/api/couche/${_db.couche}/champs/${cfg.champ}/valeurs/`);
    if (resp.ok) {
      const { valeurs } = await resp.json();
      labelMap = Object.fromEntries((valeurs ?? []).map(v => [String(v.valeur), v.label]));
    }
  } catch { /* non bloquant */ }

  if (cfg.labelLayer && cfg.labelField) {
    const lookupMap = await _loadLayerLabelMap(cfg.labelLayer, cfg.labelField);
    labelMap = { ...labelMap, ...lookupMap };
  }

  // Comptage par catégorie + groupement des PKs pour DB-08
  const counts    = {};
  const pksByCat  = {};
  for (const f of features) {
    const raw = f.props[cfg.champ];
    const key = (raw !== null && raw !== undefined && raw !== '') ? String(raw) : '(vide)';
    counts[key]   = (counts[key] ?? 0) + 1;
    (pksByCat[key] ??= []).push(Number(f.pk));
  }

  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  if (!entries.length) { _noData(body); return; }

  const labels  = entries.map(([k]) => labelMap[k] ?? k);
  const data    = entries.map(([, v]) => v);
  const rawKeys = entries.map(([k]) => k);
  const total   = data.reduce((a, b) => a + b, 0);

  const canvas = body.querySelector('canvas');
  const chart  = new Chart(canvas.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: DB_COLORS.slice(0, entries.length),
        borderWidth: 2,
        borderColor: '#fff',
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '52%',
      plugins: {
        legend: {
          position: 'right',
          labels: { font: { size: 11 }, padding: 10, boxWidth: 14, usePointStyle: true },
        },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.label} : ${ctx.parsed} (${((ctx.parsed / total) * 100).toFixed(1)} %)`,
          },
        },
      },
      onClick: (_, elements) => {
        if (!elements.length) return;
        _onChartClick(pksByCat[rawKeys[elements[0].index]] ?? []);
      },
    },
  });
  _db.charts.push(chart);
}

// ── DB-01 : Histogramme ───────────────────────────────────────────────────────

function _renderHisto(container, cfg, features) {
  const body = container.querySelector('.db-widget-body');
  const vals  = features
    .map(f => parseFloat(f.props[cfg.champ]))
    .filter(v => !isNaN(v) && isFinite(v));

  if (!vals.length) { _noData(body); return; }

  const min    = Math.min(...vals);
  const max    = Math.max(...vals);
  const range  = max - min || 1;
  const nbBins = Math.min(12, Math.max(4, Math.ceil(Math.sqrt(vals.length))));
  const step   = range / nbBins;

  const bins = Array.from({ length: nbBins }, (_, i) => ({
    lo:    min + i * step,
    hi:    min + (i + 1) * step,
    count: 0,
    pks:   [],
  }));

  for (const f of features) {
    const v  = parseFloat(f.props[cfg.champ]);
    if (isNaN(v) || !isFinite(v)) continue;
    const bi = Math.min(Math.floor((v - min) / step), nbBins - 1);
    bins[bi].count++;
    bins[bi].pks.push(Number(f.pk));
  }

  const fmt = v => (v % 1 === 0) ? String(v) : v.toFixed(2);

  const canvas = body.querySelector('canvas');
  const chart  = new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: {
      labels: bins.map(b => `${fmt(b.lo)}–${fmt(b.hi)}`),
      datasets: [{
        label: 'Entités',
        data: bins.map(b => b.count),
        backgroundColor: 'rgba(41, 128, 185, 0.72)',
        borderColor: 'rgba(29, 100, 155, 1)',
        borderWidth: 1,
        categoryPercentage: 1,
        barPercentage: 0.97,
        borderRadius: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0, font: { size: 11 } } },
        x: { ticks: { font: { size: 10 }, maxRotation: 40, autoSkip: true } },
      },
      onClick: (_, elements) => {
        if (!elements.length) return;
        _onChartClick(bins[elements[0].index].pks);
      },
    },
  });
  _db.charts.push(chart);
}

// ── DB-03 : Barres horizontales ───────────────────────────────────────────────

function _renderBarres(container, cfg, features) {
  const body = container.querySelector('.db-widget-body');

  // Agrégation : group by champX, sum champY (ou count si champY null)
  const groups = {};
  for (const f of features) {
    const key = String(f.props[cfg.champX] ?? '(vide)');
    if (!groups[key]) groups[key] = { pks: [], vals: [] };
    groups[key].pks.push(Number(f.pk));
    if (cfg.champY) {
      const v = parseFloat(f.props[cfg.champY]);
      if (!isNaN(v) && isFinite(v)) groups[key].vals.push(v);
    }
  }

  const entries = Object.entries(groups)
    .map(([label, g]) => ({
      label,
      value: cfg.champY ? g.vals.reduce((a, b) => a + b, 0) : g.pks.length,
      pks:   g.pks,
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, cfg.limit ?? 15);

  if (!entries.length) { _noData(body); return; }

  const canvas = body.querySelector('canvas');
  const chart  = new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: {
      labels: entries.map(e => e.label),
      datasets: [{
        label: cfg.champY ?? 'Nombre',
        data:  entries.map(e => parseFloat(e.value.toFixed(3))),
        backgroundColor: entries.map((_, i) => DB_COLORS[i % DB_COLORS.length]),
        borderWidth: 0,
        borderRadius: 3,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { beginAtZero: true, ticks: { font: { size: 11 } } },
        y: { ticks: { font: { size: 11 } } },
      },
      onClick: (_, elements) => {
        if (!elements.length) return;
        _onChartClick(entries[elements[0].index].pks);
      },
    },
  });
  _db.charts.push(chart);
}

// ── Graphe multi-axes : séries climatiques sur axe primaire / secondaire ──

function _renderMultiAxes(container, cfg, features) {
  const body   = container.querySelector('.db-widget-body');
  const series = cfg.series ?? [];

  const rows = features
    .map(f => ({
      label: String(f.props[cfg.champX] ?? `#${f.pk}`),
      pk:    Number(f.pk),
      props: f.props,
    }))
    .filter(row => series.some(s => {
      const v = parseFloat(row.props[s.champ]);
      return !isNaN(v) && isFinite(v);
    }))
    .sort((a, b) => a.label.localeCompare(b.label, 'fr'));

  if (!rows.length || !series.length) { _noData(body); return; }

  const canvas = body.querySelector('canvas');
  const chart  = new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: {
      labels: rows.map(row => row.label),
      datasets: series.map((s, i) => {
        const color  = DB_COLORS[i % DB_COLORS.length];
        const isLine = s.chartType === 'line';
        return {
          type:            s.chartType ?? 'line',
          label:           s.label ?? s.champ,
          data:            rows.map(row => {
            const v = parseFloat(row.props[s.champ]);
            return !isNaN(v) && isFinite(v) ? v : null;
          }),
          yAxisID:         s.axis ?? 'y',
          borderColor:     color,
          backgroundColor: isLine ? color : _hexToRgba(color, 0.72),
          borderWidth:     isLine ? 2 : 0,
          borderRadius:    isLine ? 0 : 3,
          tension:         isLine ? 0.25 : 0,
          fill:            false,
          pointRadius:     isLine ? 3 : 0,
        };
      }),
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { size: 11 }, padding: 10, boxWidth: 12 },
        },
      },
      scales: {
        x:  { ticks: { font: { size: 10 }, maxRotation: 40, autoSkip: true } },
        y:  {
          beginAtZero: true,
          position: 'left',
          title: { display: !!cfg.axes?.y?.titre, text: cfg.axes?.y?.titre },
          ticks: { font: { size: 11 } },
        },
        y1: {
          position: 'right',
          grid: { drawOnChartArea: false },
          title: { display: !!cfg.axes?.y1?.titre, text: cfg.axes?.y1?.titre },
          ticks: { font: { size: 11 } },
        },
      },
      onClick: (_, elements) => {
        if (!elements.length) return;
        _onChartClick([rows[elements[0].index].pk]);
      },
    },
  });
  _db.charts.push(chart);
}

// ── Séries mensuelles Sep→Aoû (stations_clim) ────────────────────────────────

const MOIS_SEP_AOU = ['Sep','Oct','Nov','Déc','Jan','Fév','Mar','Avr','Mai','Jui','Jul','Aoû'];

function _renderMonthlySeries(container, cfg, features) {
  const body = container.querySelector('.db-widget-body');

  const series = [];
  for (const f of features) {
    const raw = f.props[cfg.champ];
    if (!Array.isArray(raw) || raw.length < 12) continue;
    const vals = raw.slice(0, 12).map(v => {
      const n = parseFloat(v);
      return isNaN(n) ? null : n;
    });
    if (vals.every(v => v === null)) continue;
    series.push({
      label: f.props.nom ?? `Station ${f.pk}`,
      data:  vals,
      pk:    Number(f.pk),
    });
  }

  if (!series.length) { _noData(body); return; }

  const canvas = body.querySelector('canvas');
  const chart  = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: {
      labels: MOIS_SEP_AOU,
      datasets: series.map((s, i) => ({
        label:           s.label,
        data:            s.data,
        borderColor:     DB_COLORS[i % DB_COLORS.length],
        backgroundColor: 'transparent',
        borderWidth:     2,
        tension:         0.3,
        pointRadius:     3,
        fill:            false,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { size: 11 }, padding: 8, boxWidth: 12, usePointStyle: true },
        },
        tooltip: {
          callbacks: {
            label: ctx => {
              const v = ctx.parsed.y;
              const s = v !== null ? v.toFixed(1) : '—';
              return ` ${ctx.dataset.label} : ${s}${cfg.valueLabel ? '  ' + cfg.valueLabel : ''}`;
            },
          },
        },
      },
      scales: {
        x: { ticks: { font: { size: 11 } } },
        y: {
          beginAtZero: false,
          title: { display: !!cfg.valueLabel, text: cfg.valueLabel ?? '' },
          ticks: { font: { size: 11 } },
        },
      },
      onClick: (_, elements) => {
        if (!elements.length) return;
        _onChartClick([series[elements[0].datasetIndex].pk]);
      },
    },
  });
  _db.charts.push(chart);
}

// ── DB-04 : KPI ───────────────────────────────────────────────────────────────

function _renderKpi(container, cfg, features) {
  const kpiEl   = container.querySelector('.db-kpi-grid');
  const aggFunc = cfg.aggFunc ?? {};  // BUG-C3 : support aggFunc par champ
  const labels  = cfg.champLabels ?? {};
  const items   = [{ label: 'Entités', value: features.length.toLocaleString('fr') }];

  for (const champ of cfg.champs ?? []) {
    const vals = features
      .map(f => parseFloat(f.props[champ]))
      .filter(v => !isNaN(v) && isFinite(v));
    if (!vals.length) continue;

    const sum  = vals.reduce((a, b) => a + b, 0);
    const mean = sum / vals.length;
    const fn   = aggFunc[champ];
    const label = labels[champ] ?? champ;

    if (fn === 'sum') {
      items.push({ label: `Σ ${label}`, value: _fmt(sum) });
    } else if (fn === 'avg') {
      items.push({ label: `⌀ ${label}`, value: _fmt(mean) });
    } else if (fn === 'max') {
      items.push({ label: `Max ${label}`, value: _fmt(Math.max(...vals)) });
    } else if (fn === 'sumMax') {
      items.push({ label: `Somme ${label}`, value: _fmt(sum) });
      items.push({ label: `Max ${label}`, value: _fmt(Math.max(...vals)) });
    } else {
      // Comportement par défaut : 4 indicateurs complets
      items.push({ label: `Σ ${label}`,   value: _fmt(sum) });
      items.push({ label: `⌀ ${label}`,   value: _fmt(mean) });
      items.push({ label: `Min ${label}`, value: _fmt(Math.min(...vals)) });
      items.push({ label: `Max ${label}`, value: _fmt(Math.max(...vals)) });
    }
  }

  kpiEl.innerHTML = items.map(it => `
    <div class="db-kpi-card">
      <div class="db-kpi-value">${_esc(String(it.value))}</div>
      <div class="db-kpi-label">${_esc(it.label)}</div>
    </div>`).join('');
}

// ── DB-08 : Clic segment → sélection sur la carte ────────────────────────────

function _onChartClick(pks) {
  if (!pks?.length || !_db.couche) return;
  if (typeof window.applySelectionFromPks === 'function') {
    window.applySelectionFromPks(_db.couche, pks);
  }
  // Basculer sur la Carte pour voir le résultat
  document.querySelectorAll('.centrale-tab').forEach(b => {
    b.classList.toggle('active', b.dataset.ctab === 'carte');
  });
  document.getElementById('zone-carte').style.display     = '';
  document.getElementById('zone-tableau').style.display   = 'none';
  document.getElementById('zone-dashboard').style.display = 'none';
  if (window.MAP) setTimeout(() => window.MAP.resize(), 50);
}

// ── Scope (Tout / Sélection) ──────────────────────────────────────────────────

function _updateScopeBar() {
  const n   = window.selection_active?.length ?? 0;
  const cnt = document.getElementById('db-sel-count');
  if (cnt) cnt.textContent = n;
  document.querySelectorAll('.db-scope-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.scope === _db.scope);
  });
}

// ── Helpers DOM ───────────────────────────────────────────────────────────────

function _destroyCharts() {
  for (const c of _db.charts) {
    try { c.destroy(); } catch {}
  }
  _db.charts = [];
}

function _showLoading() {
  const grid = document.getElementById('db-grid');
  if (grid) grid.innerHTML = `
    <div class="db-loading" style="grid-column:1/-1">
      <i class="fas fa-spinner fa-spin"></i>&nbsp;Chargement…
    </div>`;
  const tb = document.getElementById('db-toolbar');
  if (tb) tb.style.display = '';
  const ph = document.getElementById('db-placeholder');
  if (ph) ph.style.display = 'none';
}

function _showPlaceholder() {
  _destroyCharts();
  const grid = document.getElementById('db-grid');
  if (grid) grid.innerHTML = '';
  const tb = document.getElementById('db-toolbar');
  if (tb) tb.style.display = 'none';
  const ph = document.getElementById('db-placeholder');
  if (ph) ph.style.display = '';
}

function _showError(msg) {
  const grid = document.getElementById('db-grid');
  if (grid) grid.innerHTML = `
    <div class="db-loading" style="grid-column:1/-1;color:var(--c-danger)">
      <i class="fas fa-exclamation-triangle"></i>&nbsp;Erreur : ${_esc(msg)}
    </div>`;
}

function _noData(body) {
  const canvas = body.querySelector('canvas');
  if (canvas) canvas.remove();
  body.insertAdjacentHTML('beforeend',
    '<div class="db-widget-no-data"><i class="fas fa-inbox"></i>&nbsp;Pas de données</div>');
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _hexToRgba(hex, alpha = 1) {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!m) return hex;
  return `rgba(${parseInt(m[1], 16)}, ${parseInt(m[2], 16)}, ${parseInt(m[3], 16)}, ${alpha})`;
}

function _fmt(v) {
  if (Number.isInteger(v)) return v.toLocaleString('fr');
  return v.toLocaleString('fr', { maximumFractionDigits: 2 });
}

function _esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── Synchronisation §6 ────────────────────────────────────────────────────────

// Sélection change → recalcul si scope=selection ou màj compteur
document.addEventListener('carte:selectionChange', () => {
  _updateScopeBar();
  if (_db.scope === 'selection' && _db.data.length) _renderDashboard();
});

// Couche active change → recharger si l'onglet est visible, sinon lazy-mark
document.addEventListener('carte:coucheActive', e => {
  const couche = e.detail?.couche;
  if (!couche) return;
  _db.couche = couche;
  _db.data   = [];
  const zone = document.getElementById('zone-dashboard');
  if (zone && zone.style.display !== 'none') {
    chargerDashboard(couche);
  }
  // else : chargement lazy au prochain carte:tabSwitch
});

// Basculer sur l'onglet Dashboard → charger si pas encore fait
document.addEventListener('carte:tabSwitch', e => {
  if (e.detail?.tab !== 'dashboard') return;
  if (_db.couche && !_db.data.length) {
    chargerDashboard(_db.couche);
  } else if (!_db.couche) {
    _showPlaceholder();
  }
});

// ── Init ──────────────────────────────────────────────────────────────────────

(function init() {
  // Scope toggle (Tout / Sélection)
  document.querySelectorAll('.db-scope-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      _db.scope = btn.dataset.scope;
      _updateScopeBar();
      if (_db.data.length) _renderDashboard();
    });
  });
})();
