/**
 * panneau-droit.js — Panneau Analyse + Export (Phase 4 FEATURE-R1)
 *
 * 7 boîtes accordéon : Périmètre / Seuil / Prise locale / Khettara /
 *                      Barrage / Forage / Tronçon séguia
 * Chaque boîte se remplit après sélection d'une entité via carte:selectionChange.
 * §R-IP : Indice de priorité partagé entre tous les ouvrages.
 */
'use strict';

const _MOIS_SEP_AOU = ['Sep','Oct','Nov','Déc','Jan','Fév','Mar','Avr','Mai','Jui','Jul','Aoû'];

// Couche → id de la div body
const _COUCHE_BODY = {
  perimetres:       'body-perimetre',
  seuils:           'body-seuil',
  prises_locales:   'body-prise',
  khettaras:        'body-khettara',
  barrages:         'body-barrage',
  forages_puits:    'body-forage',
  troncons_seguias: 'body-seguia',
};
// Couche → id du <details> accordéon
const _COUCHE_DETAILS = {
  perimetres:       'box-perimetre',
  seuils:           'box-seuil',
  prises_locales:   'box-prise',
  khettaras:        'box-khettara',
  barrages:         'box-barrage',
  forages_puits:    'box-forage',
  troncons_seguias: 'box-seguia',
};

// ── Classe IP ─────────────────────────────────────────────────────────────────

const _IP_CLASS_INFO = {
  1: { label: 'Intervention urgente', color: '#c0392b' },
  2: { label: 'Priorité haute',       color: '#e67e22' },
  3: { label: 'Priorité modérée',     color: '#f1c40f' },
  4: { label: 'À surveiller',         color: '#2ecc71' },
  5: { label: 'Bon état',             color: '#27ae60' },
};

// ── Onglets Analyse / Export ──────────────────────────────────────────────────

function _initPdTabs() {
  document.querySelectorAll('.pd-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.pd-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const tab = btn.dataset.pdTab;
      const analyseSection = document.getElementById('pd-section-analyse');
      const exportSection  = document.getElementById('panneau-droit-export');
      if (analyseSection) analyseSection.style.display = tab === 'analyse' ? '' : 'none';
      if (exportSection)  exportSection.style.display  = tab === 'export'  ? '' : 'none';
    });
  });
}

// ── Gestion de la sélection carte ────────────────────────────────────────────

document.addEventListener('carte:selectionChange', () => {
  const couche = window.couche_active;
  const pks    = window.selection_active || [];
  const bodyId = _COUCHE_BODY[couche];
  if (!bodyId) return;

  // Ouvrir l'accordéon correspondant
  const detailsEl = document.getElementById(_COUCHE_DETAILS[couche]);
  if (detailsEl) detailsEl.open = true;

  // Switcher vers l'onglet Analyse si Export est actif
  const analyseTab = document.querySelector('.pd-tab[data-pd-tab="analyse"]');
  if (analyseTab && !analyseTab.classList.contains('active')) analyseTab.click();

  if (!pks.length) {
    _setBodyPlaceholder(bodyId, 'Aucune entité sélectionnée.');
    return;
  }

  const pk = pks[0];
  switch (couche) {
    case 'perimetres':       _renderPerimetre(bodyId, pk);   break;
    case 'seuils':           _renderSeuil(bodyId, pk);       break;
    case 'prises_locales':   _renderPrise(bodyId, pk);       break;
    case 'khettaras':        _renderKhettara(bodyId, pk);    break;
    case 'barrages':         _renderBarrage(bodyId, pk);     break;
    case 'forages_puits':    _renderForage(bodyId, pk);      break;
    case 'troncons_seguias': _renderSeguia(bodyId, pk);      break;
  }
});

// ── Helpers DOM ───────────────────────────────────────────────────────────────

function _setBodyPlaceholder(bodyId, msg) {
  const el = document.getElementById(bodyId);
  if (el) el.innerHTML = `<p class="pd-placeholder"><i class="fas fa-info-circle"></i><br>${msg}</p>`;
}

function _setBodyLoading(bodyId) {
  const el = document.getElementById(bodyId);
  if (el) el.innerHTML = `<p class="pd-loading"><i class="fas fa-spinner fa-spin"></i> Chargement…</p>`;
}

// ── Fetch helper ─────────────────────────────────────────────────────────────

async function _apiFetch(url) {
  const resp = await fetch(url);
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}));
    throw new Error(data.erreur ?? `HTTP ${resp.status}`);
  }
  return resp.json();
}

// ── BOX-R-P — Périmètre irrigué ──────────────────────────────────────────────

function _renderPerimetre(bodyId, pk) {
  const el = document.getElementById(bodyId);
  if (!el) return;

  el.innerHTML = `
    <div class="pd-tool-group">
      <span class="pd-entity-badge"><i class="fas fa-seedling"></i> Périmètre #${pk}</span>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">P-1</span> Évaluation des besoins en eau</p>
        <a class="pd-btn pd-btn-link" href="/bilan/" target="_blank">
          <i class="fas fa-tachometer-alt"></i> Voir les bilans
        </a>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">P-2</span> Bilan volumétrique</p>
        <div class="pd-btn-group">
          <button class="pd-btn pd-btn-year" data-year="humide">Humide</button>
          <button class="pd-btn pd-btn-year" data-year="normale">Normale</button>
          <button class="pd-btn pd-btn-year" data-year="seche">Sèche</button>
        </div>
        <div id="pd-p2-result-${pk}" class="pd-result"></div>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">P-3</span> Rendement agricole</p>
        <button class="pd-btn" id="pd-p3-btn-${pk}">
          <i class="fas fa-seedling"></i> Calculer
        </button>
        <div id="pd-p3-result-${pk}" class="pd-result"></div>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">P-4</span> Tours d'eau</p>
        <button class="pd-btn" id="pd-p4-btn-${pk}">
          <i class="fas fa-calendar-alt"></i> Afficher
        </button>
        <div id="pd-p4-result-${pk}" class="pd-result"></div>
      </div>
    </div>`;

  // P-2 — Bilan volumétrique
  el.querySelectorAll('.pd-btn-year').forEach(btn => {
    btn.addEventListener('click', async () => {
      const year   = btn.dataset.year;
      const resEl  = document.getElementById(`pd-p2-result-${pk}`);
      if (!resEl) return;
      try {
        const data  = await _apiFetch(`/carte/api/perimetre/${pk}/volume-bilan/`);
        const vol   = data[`volume_annee_${year}`];
        const exc   = data[`volume_excedent_deficit_${year}`];
        const fmtM3 = v => v != null ? (v / 1e6).toFixed(3) + ' Mm³' : '—';
        const color = exc != null ? (exc >= 0 ? '#27ae60' : '#c0392b') : '#888';
        const icon  = exc != null ? (exc >= 0 ? '▲' : '▼') : '';
        resEl.innerHTML = `
          <div class="pd-kpi-row">
            <span class="pd-kpi-label">Volume (${year})</span>
            <span class="pd-kpi-val">${fmtM3(vol)}</span>
          </div>
          <div class="pd-kpi-row">
            <span class="pd-kpi-label">Excédent / Déficit</span>
            <span class="pd-kpi-val" style="color:${color}">${icon} ${fmtM3(exc)}</span>
          </div>`;
      } catch (err) {
        document.getElementById(`pd-p2-result-${pk}`).innerHTML =
          `<p class="pd-error">${err.message}</p>`;
      }
    });
  });

  // P-3 — Rendement
  document.getElementById(`pd-p3-btn-${pk}`)?.addEventListener('click', async () => {
    const resEl = document.getElementById(`pd-p3-result-${pk}`);
    if (!resEl) return;
    try {
      const data = await _apiFetch(`/carte/api/perimetre/${pk}/rendement/`);
      if (!data.assolement?.length) {
        resEl.innerHTML = `<p class="pd-muted">Aucun assolement saisi.</p>`; return;
      }
      const rows = data.assolement.map(a =>
        `<tr><td>${a.culture}</td><td>${a.surface_ha ?? '—'}</td><td>${a.rendement ?? '—'}</td></tr>`
      ).join('');
      resEl.innerHTML = `
        <div class="pd-kpi-row">
          <span class="pd-kpi-label">Rendement pondéré</span>
          <span class="pd-kpi-val">${data.rendement_pondere ?? '—'} qx/ha</span>
        </div>
        <div class="pd-kpi-row">
          <span class="pd-kpi-label">Culture dominante</span>
          <span class="pd-kpi-val">${data.culture_dominante ?? '—'}</span>
        </div>
        <div class="pd-kpi-row">
          <span class="pd-kpi-label">Surface totale</span>
          <span class="pd-kpi-val">${data.total_surface_ha} ha</span>
        </div>
        <table class="pd-mini-table">
          <thead><tr><th>Culture</th><th>Ha</th><th>Rdt</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>`;
    } catch (err) {
      document.getElementById(`pd-p3-result-${pk}`).innerHTML = `<p class="pd-error">${err.message}</p>`;
    }
  });

  // P-4 — Tours d'eau
  document.getElementById(`pd-p4-btn-${pk}`)?.addEventListener('click', async () => {
    const resEl = document.getElementById(`pd-p4-result-${pk}`);
    if (!resEl) return;
    try {
      const data = await _apiFetch(`/carte/api/perimetre/${pk}/tours-eau/`);
      if (!data.count) {
        resEl.innerHTML = `<p class="pd-muted">Aucun tour d'eau enregistré.</p>`; return;
      }
      const rows = data.tours.map(t =>
        `<tr><td>${t.ayant_droit}</td><td>${t.cycle_jours ?? '—'}</td><td>${t.duree_heures ?? '—'}</td></tr>`
      ).join('');
      resEl.innerHTML = `
        <p class="pd-muted">${data.count} ayant${data.count > 1 ? 's' : ''}-droit</p>
        <table class="pd-mini-table">
          <thead><tr><th>Ayant droit</th><th>Cycle (j)</th><th>Durée (h)</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>`;
    } catch (err) {
      document.getElementById(`pd-p4-result-${pk}`).innerHTML = `<p class="pd-error">${err.message}</p>`;
    }
  });
}

// ── Helpers partagés (BV, efficience) ────────────────────────────────────────

function _renderBvCard(bv) {
  return `
    <div class="pd-bv-card">
      <span class="pd-bv-name"><i class="fas fa-map"></i> ${bv.nom}</span>
      <div class="pd-kpi-row"><span class="pd-kpi-label">Surface</span><span class="pd-kpi-val">${bv.surface_km2 ?? '—'} km²</span></div>
      <div class="pd-kpi-row"><span class="pd-kpi-label">Thalweg</span><span class="pd-kpi-val">${bv.thalweg_km ?? '—'} km</span></div>
      <div class="pd-kpi-row"><span class="pd-kpi-label">Z min / max</span><span class="pd-kpi-val">${bv.z_min ?? '—'} / ${bv.z_max ?? '—'} m</span></div>
      ${bv.qcrue_t10  != null ? `<div class="pd-kpi-row"><span class="pd-kpi-label">Q crue T=10</span><span class="pd-kpi-val">${bv.qcrue_t10} m³/s</span></div>` : ''}
      ${bv.qcrue_t100 != null ? `<div class="pd-kpi-row"><span class="pd-kpi-label">Q crue T=100</span><span class="pd-kpi-val">${bv.qcrue_t100} m³/s</span></div>` : ''}
      <a class="pd-link" href="${bv.url_calcul}" target="_blank"><i class="fas fa-external-link-alt"></i> Calcul hydrologique</a>
    </div>`;
}

async function _showBvOnMap(bvGeoJsonUrl) {
  try {
    const feat = await _apiFetch(bvGeoJsonUrl);
    if (!feat.geometry) return;
    const srcId = 'src-bv-highlight';
    const lyrId = 'lyr-bv-highlight';
    if (MAP.getLayer(lyrId)) MAP.removeLayer(lyrId);
    if (MAP.getSource(srcId)) MAP.removeSource(srcId);
    MAP.addSource(srcId, { type: 'geojson', data: feat });
    MAP.addLayer({
      id: lyrId, type: 'fill', source: srcId,
      paint: { 'fill-color': '#2980b9', 'fill-opacity': 0.35, 'fill-outline-color': '#1a5276' },
    });
    // Zoom sur le BV
    const coords = feat.geometry.coordinates?.[0];
    if (coords?.length) {
      const lons = coords.map(c => c[0]);
      const lats = coords.map(c => c[1]);
      MAP.fitBounds([[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]], { padding: 40 });
    }
  } catch (err) {
    console.warn('[panneau-droit] BV highlight :', err);
  }
}

function _renderEfficience(containerId, eff) {
  const container = document.getElementById(containerId);
  if (!container) return;
  if (eff == null) {
    container.innerHTML = `<p class="pd-muted">Efficience non disponible.</p>`; return;
  }
  const pct   = (eff * 100).toFixed(1);
  const color = eff * 100 >= 65 ? 'pd-eff-good' : 'pd-eff-bad';
  container.innerHTML = `
    <div class="pd-progress-bar">
      <div class="pd-progress-fill ${color}" style="width:${pct}%"></div>
    </div>
    <div class="pd-kpi-row">
      <span class="pd-kpi-label">Efficience réseau</span>
      <span class="pd-kpi-val">${pct}%</span>
    </div>
    <p class="pd-muted-sm">Référence nationale : 65%</p>`;
}

function _tryLoadEfficience(containerId, couche, pk) {
  // Lecture depuis les propriétés GeoJSON déjà en cache MapLibre
  if (!window.MAP || !MAP.getLayer(`lyr-${couche}`)) {
    document.getElementById(containerId).innerHTML = `<p class="pd-muted">Efficience non disponible.</p>`;
    return;
  }
  const feats = MAP.querySourceFeatures(`src-${couche}`, { filter: ['==', ['get', 'id'], pk] });
  const eff   = feats[0]?.properties?.efficience_reseaux;
  _renderEfficience(containerId, eff ?? null);
}

// ── BOX-R-S — Seuil hydraulique ──────────────────────────────────────────────

function _renderSeuil(bodyId, pk) {
  const el = document.getElementById(bodyId);
  if (!el) return;
  el.innerHTML = `
    <div class="pd-tool-group">
      <span class="pd-entity-badge"><i class="fas fa-water"></i> Seuil #${pk}</span>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">S-2</span> Apport hydrologique du BV</p>
        <button class="pd-btn" id="s2-btn-${pk}"><i class="fas fa-chart-area"></i> Charger</button>
        <div id="s2-result-${pk}" class="pd-result"></div>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">S-3</span> Délimitation du BV</p>
        <button class="pd-btn" id="s3-btn-${pk}"><i class="fas fa-draw-polygon"></i> Afficher sur carte</button>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">S-4</span> Efficience du réseau</p>
        <div id="s4-result-${pk}" class="pd-result"></div>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">S-5</span> Indice de priorité</p>
        <button class="pd-btn" id="s5-btn-${pk}"><i class="fas fa-exclamation-triangle"></i> Calculer</button>
        <div id="s5-result-${pk}" class="pd-result"></div>
      </div>
    </div>`;

  _tryLoadEfficience(`s4-result-${pk}`, 'seuils', pk);

  document.getElementById(`s2-btn-${pk}`)?.addEventListener('click', async () => {
    const resEl = document.getElementById(`s2-result-${pk}`);
    try {
      const data = await _apiFetch(`/carte/api/seuil/${pk}/bv-apport/`);
      resEl.innerHTML = _renderBvCard(data);
    } catch (err) { resEl.innerHTML = `<p class="pd-error">${err.message}</p>`; }
  });
  document.getElementById(`s3-btn-${pk}`)?.addEventListener('click', () => {
    _showBvOnMap(`/carte/api/seuil/${pk}/bv/`);
  });
  document.getElementById(`s5-btn-${pk}`)?.addEventListener('click', () => {
    _openIPForm(`s5-result-${pk}`, 'seuils');
  });
}

// ── BOX-R-PL — Prise locale ───────────────────────────────────────────────────

function _renderPrise(bodyId, pk) {
  const el = document.getElementById(bodyId);
  if (!el) return;
  el.innerHTML = `
    <div class="pd-tool-group">
      <span class="pd-entity-badge"><i class="fas fa-faucet"></i> Prise #${pk}</span>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">PL-2</span> Apport hydrologique du BV</p>
        <button class="pd-btn" id="pl2-btn-${pk}"><i class="fas fa-chart-area"></i> Charger</button>
        <div id="pl2-result-${pk}" class="pd-result"></div>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">PL-3</span> Délimitation du BV</p>
        <button class="pd-btn" id="pl3-btn-${pk}"><i class="fas fa-draw-polygon"></i> Afficher sur carte</button>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">PL-4</span> Efficience du réseau</p>
        <div id="pl4-result-${pk}" class="pd-result"></div>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">PL-5</span> Indice de priorité</p>
        <button class="pd-btn" id="pl5-btn-${pk}"><i class="fas fa-exclamation-triangle"></i> Calculer</button>
        <div id="pl5-result-${pk}" class="pd-result"></div>
      </div>
    </div>`;

  _tryLoadEfficience(`pl4-result-${pk}`, 'prises_locales', pk);

  document.getElementById(`pl2-btn-${pk}`)?.addEventListener('click', async () => {
    const resEl = document.getElementById(`pl2-result-${pk}`);
    try {
      const data = await _apiFetch(`/carte/api/prise/${pk}/bv-apport/`);
      resEl.innerHTML = _renderBvCard(data);
    } catch (err) { resEl.innerHTML = `<p class="pd-error">${err.message}</p>`; }
  });
  document.getElementById(`pl3-btn-${pk}`)?.addEventListener('click', () => {
    _showBvOnMap(`/carte/api/prise/${pk}/bv/`);
  });
  document.getElementById(`pl5-btn-${pk}`)?.addEventListener('click', () => {
    _openIPForm(`pl5-result-${pk}`, 'prises_locales');
  });
}

// ── BOX-R-K — Khettara ───────────────────────────────────────────────────────

function _renderKhettara(bodyId, pk) {
  const el = document.getElementById(bodyId);
  if (!el) return;
  el.innerHTML = `
    <div class="pd-tool-group">
      <span class="pd-entity-badge"><i class="fas fa-archway"></i> Khettara #${pk}</span>
      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">K-1</span> Indice de priorité</p>
        <button class="pd-btn" id="k1-btn-${pk}"><i class="fas fa-exclamation-triangle"></i> Calculer</button>
        <div id="k1-result-${pk}" class="pd-result"></div>
      </div>
    </div>`;
  document.getElementById(`k1-btn-${pk}`)?.addEventListener('click', () => {
    _openIPForm(`k1-result-${pk}`, 'khettaras');
  });
}

// ── BOX-R-B — Barrage collinaire ─────────────────────────────────────────────

function _renderBarrage(bodyId, pk) {
  const el = document.getElementById(bodyId);
  if (!el) return;
  el.innerHTML = `
    <div class="pd-tool-group">
      <span class="pd-entity-badge"><i class="fas fa-mountain"></i> Barrage #${pk}</span>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">B-1</span> Apports et régime</p>
        <button class="pd-btn" id="b1-btn-${pk}"><i class="fas fa-water"></i> Charger</button>
        <div id="b1-result-${pk}" class="pd-result"></div>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">B-2</span> Apport hydrologique BV</p>
        <button class="pd-btn" id="b2-btn-${pk}"><i class="fas fa-chart-area"></i> Charger</button>
        <div id="b2-result-${pk}" class="pd-result"></div>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">B-3</span> Délimitation du BV</p>
        <button class="pd-btn" id="b3-btn-${pk}"><i class="fas fa-draw-polygon"></i> Afficher sur carte</button>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">B-4</span> Efficience du réseau</p>
        <div id="b4-result-${pk}" class="pd-result"></div>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">B-5</span> Indice de priorité</p>
        <button class="pd-btn" id="b5-btn-${pk}"><i class="fas fa-exclamation-triangle"></i> Calculer</button>
        <div id="b5-result-${pk}" class="pd-result"></div>
      </div>
    </div>`;

  _tryLoadEfficience(`b4-result-${pk}`, 'barrages', pk);

  document.getElementById(`b1-btn-${pk}`)?.addEventListener('click', async () => {
    const resEl = document.getElementById(`b1-result-${pk}`);
    try {
      const data = await _apiFetch(`/carte/api/barrage/${pk}/bv-apport/`);
      let html = `
        <div class="pd-kpi-row"><span class="pd-kpi-label">Capacité retenue</span><span class="pd-kpi-val">${data.capacite_retenue ?? '—'} m³</span></div>
        <div class="pd-kpi-row"><span class="pd-kpi-label">Volume irrigat.</span><span class="pd-kpi-val">${data.volume_attribue_irrigation ?? '—'} m³</span></div>`;
      if (data.apports_mensuels_normale) html += _renderApportsMensuels(data);
      resEl.innerHTML = html;
    } catch (err) { resEl.innerHTML = `<p class="pd-error">${err.message}</p>`; }
  });

  document.getElementById(`b2-btn-${pk}`)?.addEventListener('click', async () => {
    const resEl = document.getElementById(`b2-result-${pk}`);
    try {
      const data = await _apiFetch(`/carte/api/barrage/${pk}/bv-apport/`);
      if (data.bv) resEl.innerHTML = _renderBvCard(data.bv);
      else resEl.innerHTML = `<p class="pd-muted">Aucun BV lié.</p>`;
    } catch (err) { resEl.innerHTML = `<p class="pd-error">${err.message}</p>`; }
  });

  document.getElementById(`b3-btn-${pk}`)?.addEventListener('click', () => {
    _showBvOnMap(`/carte/api/barrage/${pk}/bv/`);
  });
  document.getElementById(`b5-btn-${pk}`)?.addEventListener('click', () => {
    _openIPForm(`b5-result-${pk}`, 'barrages');
  });
}

function _renderApportsMensuels(data) {
  const rows = _MOIS_SEP_AOU.map((m, i) => {
    const fmt = v => v != null ? Number(v).toLocaleString('fr') : '—';
    return `<tr>
      <td>${m}</td>
      <td>${fmt(data.apports_mensuels_humide?.[i])}</td>
      <td>${fmt(data.apports_mensuels_normale?.[i])}</td>
      <td>${fmt(data.apports_mensuels_seche?.[i])}</td>
    </tr>`;
  }).join('');
  return `
    <p class="pd-muted-sm" style="margin-top:8px">Apports mensuels (m³)</p>
    <table class="pd-mini-table">
      <thead><tr><th>Mois</th><th>Hum.</th><th>Norm.</th><th>Sèche</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

// ── BOX-R-F — Forage / Puits ─────────────────────────────────────────────────

function _renderForage(bodyId, pk) {
  const el = document.getElementById(bodyId);
  if (!el) return;
  el.innerHTML = `
    <div class="pd-tool-group">
      <span class="pd-entity-badge"><i class="fas fa-tint"></i> Forage #${pk}</span>
      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">F-1</span> Indice de priorité</p>
        <button class="pd-btn" id="f1-btn-${pk}"><i class="fas fa-exclamation-triangle"></i> Calculer</button>
        <div id="f1-result-${pk}" class="pd-result"></div>
      </div>
    </div>`;
  document.getElementById(`f1-btn-${pk}`)?.addEventListener('click', () => {
    _openIPForm(`f1-result-${pk}`, 'forages_puits');
  });
}

// ── BOX-R-T — Tronçon séguia ─────────────────────────────────────────────────

function _renderSeguia(bodyId, pk) {
  const el = document.getElementById(bodyId);
  if (!el) return;
  el.innerHTML = `
    <div class="pd-tool-group">
      <span class="pd-entity-badge"><i class="fas fa-stream"></i> Tronçon #${pk}</span>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">T-1</span> Débit Manning-Strickler</p>
        <div class="pd-params">
          <label class="pd-param-label">n Manning <span class="pd-param-hint">(béton 0.013, terre 0.025)</span></label>
          <input id="t1-n-${pk}" type="number" step="0.001" min="0.001" max="0.5"
                 placeholder="auto selon nature" class="pd-input">
          <label class="pd-param-label">Pente S (m/m)</label>
          <input id="t1-s-${pk}" type="number" step="0.0001" min="0.00001" value="0.001" class="pd-input">
        </div>
        <button class="pd-btn" id="t1-btn-${pk}"><i class="fas fa-calculator"></i> Calculer</button>
        <div id="t1-result-${pk}" class="pd-result"></div>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">T-2</span> Rendement hydraulique</p>
        <button class="pd-btn" id="t2-btn-${pk}"><i class="fas fa-percent"></i> Calculer</button>
        <div id="t2-result-${pk}" class="pd-result"></div>
      </div>

      <div class="pd-tool">
        <p class="pd-tool-title"><span class="pd-tool-num">T-3</span> Indice de priorité</p>
        <button class="pd-btn" id="t3-btn-${pk}"><i class="fas fa-exclamation-triangle"></i> Calculer</button>
        <div id="t3-result-${pk}" class="pd-result"></div>
      </div>
    </div>`;

  // T-1 — Manning
  document.getElementById(`t1-btn-${pk}`)?.addEventListener('click', async () => {
    const resEl = document.getElementById(`t1-result-${pk}`);
    if (!resEl) return;
    const nVal  = document.getElementById(`t1-n-${pk}`)?.value;
    const pente = parseFloat(document.getElementById(`t1-s-${pk}`)?.value || '0.001');
    const body  = { pks: [pk], pente };
    if (nVal) body.n_manning = parseFloat(nVal);
    try {
      const resp = await fetch('/carte/api/outils/manning/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
        body: JSON.stringify(body),
      });
      const data = await resp.json();
      const r = data.resultats?.[0];
      if (!r) throw new Error(data.erreur ?? 'Aucun résultat');
      resEl.innerHTML = `
        <div class="pd-kpi-row"><span class="pd-kpi-label">Q calculé</span><span class="pd-kpi-val">${r.debit_calcule?.toFixed(4)} m³/s</span></div>
        <div class="pd-kpi-row"><span class="pd-kpi-label">n utilisé</span><span class="pd-kpi-val">${r.n_utilise}</span></div>
        <div class="pd-kpi-row"><span class="pd-kpi-label">Forme section</span><span class="pd-kpi-val">${r.forme ?? '—'}</span></div>`;
    } catch (err) { resEl.innerHTML = `<p class="pd-error">${err.message}</p>`; }
  });

  // T-2 — Efficience
  document.getElementById(`t2-btn-${pk}`)?.addEventListener('click', async () => {
    const resEl = document.getElementById(`t2-result-${pk}`);
    if (!resEl) return;
    try {
      const resp = await fetch('/carte/api/outils/efficience/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
        body: JSON.stringify({ pks: [pk] }),
      });
      const data = await resp.json();
      const r = data.resultats?.[0];
      if (!r) throw new Error(data.erreurs?.[0]?.erreur ?? 'Aucun résultat');
      const pct = r.efficience_pourcent?.toFixed(1);
      const colorClass = parseFloat(pct) >= 65 ? 'pd-eff-good' : 'pd-eff-bad';
      resEl.innerHTML = `
        <div class="pd-progress-bar">
          <div class="pd-progress-fill ${colorClass}" style="width:${Math.min(pct, 100)}%"></div>
        </div>
        <div class="pd-kpi-row"><span class="pd-kpi-label">Efficience</span><span class="pd-kpi-val">${pct}%</span></div>
        <div class="pd-kpi-row"><span class="pd-kpi-label">Perte infiltration</span><span class="pd-kpi-val">${r.perte_infiltration_m3s?.toFixed(5)} m³/s</span></div>
        <div class="pd-kpi-row"><span class="pd-kpi-label">Perte évaporation</span><span class="pd-kpi-val">${r.perte_vaporisation_m3s?.toFixed(5)} m³/s</span></div>`;
    } catch (err) { resEl.innerHTML = `<p class="pd-error">${err.message}</p>`; }
  });

  // T-3 — IP
  document.getElementById(`t3-btn-${pk}`)?.addEventListener('click', () => {
    _openIPForm(`t3-result-${pk}`, 'troncons_seguias');
  });
}

// ── §R-IP — Indice de priorité d'intervention ─────────────────────────────────

async function _openIPForm(containerId, couche) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = `<p class="pd-loading"><i class="fas fa-spinner fa-spin"></i> Chargement des critères…</p>`;
  try {
    const data     = await _apiFetch(`/carte/api/couche/${couche}/criteres/`);
    const criteres = data.criteres || [];
    if (!criteres.length) {
      container.innerHTML = `<p class="pd-muted">Aucun critère disponible.</p>`; return;
    }
    const uid  = `ip-${couche}-${Date.now()}`;
    const rows = criteres.map(c => `
      <tr>
        <td class="pd-ip-crit" title="${c.label}">${c.label}</td>
        <td class="pd-ip-note" id="${uid}-note-${c.champ}">—</td>
        <td><input type="number" min="0" max="5" step="0.5" value="1"
                   class="pd-input-sm" id="${uid}-coeff-${c.champ}" data-champ="${c.champ}"></td>
      </tr>`).join('');
    container.innerHTML = `
      <p class="pd-muted-sm">Coefficients (0–5 pour chaque critère)</p>
      <table class="pd-ip-table">
        <thead><tr><th>Critère</th><th>Note</th><th>Coeff.</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <button class="pd-btn pd-btn-full" id="${uid}-calc">
        <i class="fas fa-play"></i> Calculer l'indice
      </button>
      <div id="${uid}-result" class="pd-result"></div>`;

    // Pré-remplir les notes depuis les features MapLibre si disponibles
    _prefillIPNotes(uid, couche, criteres);

    document.getElementById(`${uid}-calc`)?.addEventListener('click', () => {
      _runIP(uid, couche, criteres);
    });
  } catch (err) {
    container.innerHTML = `<p class="pd-error">${err.message}</p>`;
  }
}

function _prefillIPNotes(uid, couche, criteres) {
  const pk = (window.selection_active || [])[0];
  if (!pk || !window.MAP?.getLayer(`lyr-${couche}`)) return;
  const feats = MAP.querySourceFeatures(`src-${couche}`, { filter: ['==', ['get', 'id'], pk] });
  if (!feats.length) return;
  const props = feats[0].properties || {};
  criteres.forEach(c => {
    const noteEl = document.getElementById(`${uid}-note-${c.champ}`);
    if (noteEl) noteEl.textContent = props[c.champ] ?? '—';
  });
}

async function _runIP(uid, couche, criteres) {
  const resEl = document.getElementById(`${uid}-result`);
  if (!resEl) return;

  const coefficients = {};
  criteres.forEach(c => {
    const val = parseFloat(document.getElementById(`${uid}-coeff-${c.champ}`)?.value || '1');
    coefficients[c.champ] = isNaN(val) ? 1 : val;
  });

  resEl.innerHTML = `<p class="pd-loading"><i class="fas fa-spinner fa-spin"></i> Calcul en cours…</p>`;
  try {
    const resp = await fetch('/carte/api/outils/indice-priorite/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify({ couche, coefficients }),
    });
    const data = await resp.json();
    if (data.erreur) throw new Error(data.erreur);

    // Légende + badge entité courante
    const pk    = (window.selection_active || [])[0];
    const myScr = pk != null ? data.scores[String(pk)] : null;
    const myCls = pk != null ? data.classes[String(pk)] : null;
    const myInf = myCls ? _IP_CLASS_INFO[myCls] : null;

    const legendItems = Object.entries(_IP_CLASS_INFO).map(([cls, info]) => {
      const nb = Object.values(data.classes).filter(c => String(c) === cls).length;
      return `<li style="display:flex;align-items:center;gap:5px;margin:2px 0">
        <span style="width:10px;height:10px;border-radius:2px;background:${info.color};flex-shrink:0"></span>
        <span style="font-size:10px">${info.label} — ${nb} entité${nb > 1 ? 's' : ''}</span>
      </li>`;
    }).join('');

    // Colorisation MapLibre — via le gestionnaire central CarteRendu (slot
    // 'resultat') pour éviter tout désordre avec les autres rendus carte.
    if (window.MAP?.getLayer(`lyr-${couche}`) && data.paint_expression) {
      const paints = [{ layer: `lyr-${couche}`, prop: 'fill-color', value: data.paint_expression }];
      if (MAP.getLayer(`lyr-${couche}-outline`)) {
        paints.push({ layer: `lyr-${couche}-outline`, prop: 'line-color', value: data.paint_expression });
      }
      if (window.CarteRendu) {
        CarteRendu.set('resultat', {
          outil:   `Indice de priorité — ${couche}`,
          choro:   paints,
          legende: `<ul style="list-style:none;padding:0;margin:0">${legendItems}</ul>`,
        });
      } else {
        paints.forEach(p => MAP.setPaintProperty(p.layer, p.prop, p.value));
      }
    }

    resEl.innerHTML = `
      ${myInf ? `<div class="pd-ip-badge" style="background:${myInf.color}">
        <i class="fas fa-exclamation-triangle"></i>
        Score : ${myScr}% — ${myInf.label}
      </div>` : ''}
      <p class="pd-muted-sm">${data.nb_entites} entité${data.nb_entites > 1 ? 's' : ''} analysée${data.nb_entites > 1 ? 's' : ''}</p>
      <ul style="list-style:none;padding:0;margin:4px 0">${legendItems}</ul>
      <button class="pd-btn pd-btn-secondary" id="${uid}-reset" style="margin-top:6px">
        <i class="fas fa-undo"></i> Réinitialiser style
      </button>`;

    document.getElementById(`${uid}-reset`)?.addEventListener('click', () => {
      if (window.CarteRendu) CarteRendu.clear('resultat');
      else _resetLayerStyle(couche);
    });
  } catch (err) {
    resEl.innerHTML = `<p class="pd-error">${err.message}</p>`;
  }
}

function _resetLayerStyle(couche) {
  if (!window.MAP) return;
  const meta  = window.COUCHES_META?.[couche];
  const color = (window.LAYER_GROUP_COLORS?.[meta?.groupe]) ?? (window.LAYER_COLOR_FALLBACK ?? '#7f8c8d');
  if (MAP.getLayer(`lyr-${couche}`))         MAP.setPaintProperty(`lyr-${couche}`,         'fill-color', color);
  if (MAP.getLayer(`lyr-${couche}-outline`)) MAP.setPaintProperty(`lyr-${couche}-outline`, 'line-color', color);
}

// ── Section Export ────────────────────────────────────────────────────────────

function _initExportSection() {
  document.getElementById('pd-btn-export-csv')?.addEventListener('click', () => {
    const couche = window.couche_active;
    if (!couche) return;
    const pks = window.selection_active?.length ? window.selection_active : null;
    fetch('/carte/api/export/csv/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify({ couche, pks }),
    }).then(r => r.blob()).then(blob => {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${couche}.csv`;
      a.click();
    }).catch(err => console.warn('[panneau-droit] export CSV :', err));
  });

  document.getElementById('pd-btn-export-geojson')?.addEventListener('click', () => {
    const couche = window.couche_active;
    if (!couche) return;
    const pks = window.selection_active?.length ? `?pks=${window.selection_active.join(',')}` : '';
    window.open(`/carte/api/couche/${couche}/${pks}`, '_blank');
  });

  document.getElementById('pd-btn-export-excel')?.addEventListener('click', () => {
    const couche = window.couche_active;
    if (!couche) return;
    const pks = window.selection_active?.length ? window.selection_active : null;
    fetch('/carte/api/export/excel/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify({ couche, pks }),
    }).then(r => r.blob()).then(blob => {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${couche}.xlsx`;
      a.click();
    }).catch(err => console.warn('[panneau-droit] export Excel :', err));
  });

  // Mise en page → onglet compositeur PDF (Phase 5)
  document.getElementById('pd-btn-mise-en-page')?.addEventListener('click', () => {
    document.getElementById('tab-central-layout-btn')?.click();
  });
}

// ── Masquage rôle visiteur ────────────────────────────────────────────────────

function _applyRoleGating() {
  const isVisiteur = typeof window.minRole === 'function' && !window.minRole('operateur');
  if (isVisiteur) {
    document.getElementById('panneau-droit-export')?.style &&
      (document.getElementById('panneau-droit-export').style.display = 'none');
    document.querySelectorAll('.pd-tab[data-pd-tab="export"]').forEach(b => {
      b.style.display = 'none';
    });
  }
}

// ── Point d'entrée ───────────────────────────────────────────────────────────

function initPanneauDroit() {
  _initPdTabs();
  _initExportSection();
  _applyRoleGating();
}
