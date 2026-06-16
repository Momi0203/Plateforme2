/**
 * outils-hydrologie.js — Box « Hydrologie / Crues » du panneau droit Outils.
 *
 * Outils :
 *   - Bassins versants & réseau  → contexte carte (BV ouvrage de tête + réseau),
 *                                  2 symbologies (slot 'contexte' de CarteRendu)
 *   - Débits de crue (T)         → fenêtre flottante (lecture dernière analyse)
 *   - Temps de concentration     → fenêtre flottante (calculer_tc_bv)
 *   - Apports de crue mensuels   → fenêtre flottante (calculer_apports_crue…)
 *   - Crue de projet (carte)     → thématique cercles (slot 'resultat')
 *
 * La couche bv_ouvrage_tete est masquée du panneau gauche : sélection par menu
 * déroulant. Tout rendu carte passe par window.CarteRendu (anti-désordre).
 *
 * Dépend de : map.js (MAP, maplibregl), Chart.js, carte-rendu.js.
 */
'use strict';

(function () {

  const PANELS = ['hy-panel-crue', 'hy-panel-tc',
                  'hy-panel-apports', 'hy-panel-cruecarte',
                  'hy-panel-ap-seuil', 'hy-panel-ap-prise', 'hy-panel-ap-barrage'];

  const fmt = v => Number(v || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
  const fmt2 = v => Number(v || 0).toLocaleString('fr-FR', { maximumFractionDigits: 2 });

  // ── Navigation liste ⇄ sous-panneaux ──────────────────────────────────────

  function _showPanel(panelId) {
    document.getElementById('po-outils-liste').style.display = 'none';
    PANELS.forEach(p => { const el = document.getElementById(p); if (el) el.style.display = 'none'; });
    const panel = document.getElementById(panelId);
    if (panel) panel.style.display = 'flex';
  }

  function _hideAll() {
    PANELS.forEach(p => { const el = document.getElementById(p); if (el) el.style.display = 'none'; });
    document.getElementById('po-outils-liste').style.display = '';
  }

  // ── Menus déroulants (pk + libellé depuis l'API liste) ────────────────────

  async function _fillSelect(selectEl, couche, keepTous) {
    if (!selectEl || selectEl.dataset.filled === '1') return;
    try {
      const data = await fetch(`/carte/api/couche/${couche}/liste/`).then(r => r.json());
      const tous = keepTous ? '<option value="">Tous</option>' : '';
      const opts = (data.options || [])
        .map(o => `<option value="${o.pk}">${o.label}</option>`).join('');
      selectEl.innerHTML = tous + opts;
      selectEl.dataset.filled = '1';
    } catch (e) {
      console.error('[hydrologie] _fillSelect', couche, e);
    }
  }

  // ── Fenêtres flottantes (multi-instances via window.FloatingChart, Lot C) ──

  const _AXIS_FONT = { family: 'Inter', size: 10 };
  const _LEGEND = { position: 'top', labels: { usePointStyle: true, boxWidth: 8, font: { family: 'Inter', size: 11 } } };

  // ── Outil : Débits de crue (T) — B1 ───────────────────────────────────────

  async function _crueGenerer() {
    const pk = document.getElementById('hy-crue-bv').value;
    if (!pk) return;
    const win = FloatingChart.open({ titre: 'Débits de crue', icone: 'fa-chart-bar' });
    try {
      const d = await fetch(`/carte/api/bv/${pk}/crue-periodes/`).then(r => r.json());
      if (!d.periodes || !d.periodes.length || d.periodes.every(p => p.q == null)) {
        win.setStatus(`<span class="cb-err"><i class="fas fa-exclamation-triangle"></i> ${d.message || 'Aucun débit de crue disponible.'}</span>`);
        return;
      }
      win.drawChart({
        type: 'bar',
        data: {
          labels: d.periodes.map(p => `T=${p.T} ans`),
          datasets: [{ label: 'Q de pointe (m³/s)', data: d.periodes.map(p => p.q), backgroundColor: '#c0392b' }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: _LEGEND,
            tooltip: { callbacks: { label: c => `${fmt2(c.parsed.y)} m³/s` } },
          },
          scales: {
            x: { grid: { display: false }, ticks: { font: _AXIS_FONT } },
            y: { beginAtZero: true, ticks: { font: _AXIS_FONT }, title: { display: true, text: 'Q (m³/s)', font: { family: 'Inter', weight: '600' } } },
          },
        },
      });
      const tc = d.tc_min != null ? ` · Tc ${fmt2(d.tc_min)} min` : '';
      win.setStatus(`<span class="cb-ok"><i class="fas fa-check-circle"></i> ${d.bv}</span>
        <span class="cb-muted"> — ${d.methode || '—'}${d.date_analyse ? ' · ' + d.date_analyse : ''}${tc}</span>`);
    } catch (err) {
      win.setStatus(`<span class="cb-err">Erreur : ${err.message}</span>`);
    }
  }

  // ── Outil : Temps de concentration — B2 ───────────────────────────────────

  async function _tcGenerer() {
    const pk = document.getElementById('hy-tc-bv').value;
    if (!pk) return;
    const win = FloatingChart.open({ titre: 'Temps de concentration', icone: 'fa-stopwatch' });
    try {
      const d = await fetch(`/carte/api/bv/${pk}/tc/`).then(r => r.json());
      if (d.erreur || !d.formules || !d.formules.length) {
        win.setStatus(`<span class="cb-err"><i class="fas fa-exclamation-triangle"></i> ${d.erreur || 'Tc non calculable.'}</span>`);
        return;
      }
      win.drawChart({
        type: 'bar',
        data: {
          labels: d.formules.map(f => f.nom),
          datasets: [{ label: 'Tc (min)', data: d.formules.map(f => f.tc_min), backgroundColor: '#2980b9' }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: _LEGEND,
            tooltip: { callbacks: { label: c => `${fmt2(c.parsed.y)} min` } },
          },
          scales: {
            x: { grid: { display: false }, ticks: { font: _AXIS_FONT, maxRotation: 55, autoSkip: false } },
            y: { beginAtZero: true, ticks: { font: _AXIS_FONT }, title: { display: true, text: 'Tc (min)', font: { family: 'Inter', weight: '600' } } },
          },
        },
      }, Math.max(0, d.formules.length * 70));
      win.setStatus(`<span class="cb-ok"><i class="fas fa-check-circle"></i> ${d.bv}</span>
        <span class="cb-muted"> — moyenne ${fmt2(d.moyenne_min)} min (${fmt2(d.moyenne_h)} h)</span>`);
    } catch (err) {
      win.setStatus(`<span class="cb-err">Erreur : ${err.message}</span>`);
    }
  }

  // ── Outil : Apports de crue mensuels — B3 ─────────────────────────────────

  const _APPORT_COL = { normale: '#27ae60', humide: '#2980b9', seche: '#e67e22' };

  async function _apportsGenerer() {
    const bvPk = document.getElementById('hy-apports-bv').value;
    const stPk = document.getElementById('hy-apports-station').value;
    if (!bvPk || !stPk) return;
    const tc = document.getElementById('hy-apports-tc').value;
    const win = FloatingChart.open({ titre: 'Apports de crue mensuels', icone: 'fa-chart-area' });
    try {
      let url = `/carte/api/bv/${bvPk}/apports-crue/?station=${encodeURIComponent(stPk)}`;
      if (tc) url += `&tc=${encodeURIComponent(tc)}`;
      const d = await fetch(url).then(r => r.json());
      if (d.erreur) {
        win.setStatus(`<span class="cb-err"><i class="fas fa-exclamation-triangle"></i> ${d.erreur}</span>`);
        return;
      }
      const mois = d.mois || [];
      const datasets = ['normale', 'humide', 'seche'].map(a => ({
        label: 'Année ' + (a === 'seche' ? 'sèche' : a),
        data: (d[a] && d[a].volumes_m3) || [],
        backgroundColor: _APPORT_COL[a],
      }));
      win.drawChart({
        type: 'bar',
        data: { labels: mois, datasets },
        options: {
          responsive: true, maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: _LEGEND,
            tooltip: { callbacks: { label: c => `${c.dataset.label} : ${fmt(c.parsed.y)} m³` } },
          },
          scales: {
            x: { grid: { display: false }, ticks: { font: _AXIS_FONT } },
            y: { beginAtZero: true, ticks: { font: _AXIS_FONT, callback: v => fmt(v) }, title: { display: true, text: 'Volume (m³)', font: { family: 'Inter', weight: '600' } } },
          },
        },
      }, 560);
      const tn = d.normale ? fmt(d.normale.total_m3) : '—';
      const trsp = d.transposition ? ' · transposé F-R' : '';
      win.setStatus(`<span class="cb-ok"><i class="fas fa-check-circle"></i> ${d.bv || ''}</span>
        <span class="cb-muted"> — station ${d.station} · Tc ${fmt2(d.tc_h)} h${trsp} · total normale ${tn} m³</span>`);
    } catch (err) {
      win.setStatus(`<span class="cb-err">Erreur : ${err.message}</span>`);
    }
  }

  // (Outil « Bassins versants & réseau » retiré au Lot E — remplacé par la box
  //  « Couches » / Hydrologie 2 + « Réseau du BV », voir outils-couches.js.)

  // ── Outil : Crue de projet (thématique carte) — B4 ────────────────────────

  function _propSize(v, vmin, vmax, minPx = 28, maxPx = 60) {
    if (vmax <= vmin) return (minPx + maxPx) / 2;
    const t = Math.sqrt((v - vmin) / (vmax - vmin));
    return Math.round(minPx + t * (maxPx - minPx));
  }

  function _circleEl(size, color, label, title) {
    const el = document.createElement('div');
    el.title = title || '';
    Object.assign(el.style, {
      width: size + 'px', height: size + 'px', borderRadius: '50%', background: color,
      border: '2px solid #fff', boxShadow: '0 1px 4px rgba(0,0,0,.4)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      color: '#fff', fontWeight: '700', fontFamily: "'Inter', sans-serif",
      fontSize: Math.max(9, Math.round(size * 0.3)) + 'px',
      textShadow: '0 1px 2px rgba(0,0,0,.5)', cursor: 'pointer', lineHeight: '1',
    });
    el.textContent = label;
    return el;
  }

  async function _crueCarteAfficher() {
    const resEl = document.getElementById('hy-cruecarte-result');
    const T = document.getElementById('hy-cruecarte-t').value;
    if (!window.MAP) return;
    resEl.innerHTML = '<span class="po-muted"><i class="fas fa-spinner fa-spin"></i> Chargement…</span>';
    try {
      const d = await fetch(`/carte/api/bv/crue-points/?t=${T}`).then(r => r.json());
      const feats = d.features || [];
      if (!feats.length) {
        if (window.CarteRendu) CarteRendu.clear('resultat');
        resEl.innerHTML = `<span class="po-err"><i class="fas fa-exclamation-triangle"></i> Aucun bassin avec un débit Q(T=${T}) calculé.</span>`;
        document.getElementById('hy-cruecarte-clear').style.display = 'none';
        return;
      }
      const mode = document.getElementById('hy-cruecarte-mode')?.value || 'cercle_prop';
      const points = feats.map(f => ({
        coord: f.geometry.coordinates, value: f.properties.value, nom: f.properties.nom,
      }));
      const r = RenduCarte.renderThematique(MAP, points, { mode, unite: 'm³/s', color: '#c0392b' });
      CarteRendu.set('resultat', {
        outil: `Crue de projet — T=${T} ans`,
        markers: r.markers, overlay: r.overlay, choro: r.paints, legende: r.legende,
      });
      resEl.innerHTML = `<span class="po-ok"><i class="fas fa-check-circle"></i> ${feats.length} bassin(s) — Q(T=${T} ans).</span>`;
      document.getElementById('hy-cruecarte-clear').style.display = '';
    } catch (err) {
      resEl.innerHTML = `<span class="po-err">Erreur : ${err.message}</span>`;
    }
  }

  function _crueCarteClear() {
    if (window.CarteRendu) CarteRendu.clear('resultat');
    document.getElementById('hy-cruecarte-clear').style.display = 'none';
    document.getElementById('hy-cruecarte-result').innerHTML = '';
  }

  // ── Outils : Apport de crue par ouvrage (seuil / prise / barrage) — Lot F ──
  // Sélection carte (1ʳᵉ entité) + fenêtre flottante : apport de crue du BV
  // (transposé) + volume capté au droit de l'ouvrage.

  const _AP_CFG = {
    seuil:   { couche: 'seuils',         url: pk => `/carte/api/seuil/${pk}/apport-crue/`,   titre: 'Apport de crue — seuil',   vide: 'Aucun — sélectionnez sur la carte' },
    prise:   { couche: 'prises_locales', url: pk => `/carte/api/prise/${pk}/apport-crue/`,    titre: 'Apport de crue — prise',   vide: 'Aucune — sélectionnez sur la carte' },
    barrage: { couche: 'barrages',       url: pk => `/carte/api/barrage/${pk}/apport-crue/`,  titre: 'Apport de crue — barrage', vide: 'Aucun — sélectionnez sur la carte' },
  };

  function _apPks(couche) { return (window.OutilsSel ? OutilsSel.pks(couche) : []); }

  async function _apportOuvrage(type) {
    const cfg = _AP_CFG[type];
    const resEl = document.getElementById(`hy-ap-${type}-result`);
    const pks = _apPks(cfg.couche);
    if (!pks.length) {
      if (resEl) resEl.innerHTML = `<span class="po-err"><i class="fas fa-exclamation-triangle"></i> Sélectionnez un ouvrage sur la carte.</span>`;
      return;
    }
    const pk = pks[0];
    const win = FloatingChart.open({ titre: cfg.titre, icone: 'fa-droplet' });
    try {
      const d = await fetch(cfg.url(pk)).then(r => r.json());
      if (!d.mois || !d.mois.length) {
        // Pas d'apport BV (ouvrage sans bassin versant lié) → afficher la part captée.
        const vc = d.volume_capte_m3_an != null
          ? ` · volume capté ${fmt(d.volume_capte_m3_an)} m³/an (débit ${fmt2(d.debit_l_s)} l/s)` : '';
        win.setStatus(`<span class="cb-warn"><i class="fas fa-exclamation-triangle"></i> ${d.message || d.erreur || 'Apport de crue indisponible'} — ${d.ouvrage || ''}${vc}</span>`);
        return;
      }
      const datasets = ['normale', 'humide', 'seche'].map(a => ({
        label: 'Année ' + (a === 'seche' ? 'sèche' : a),
        data: (d[a] && d[a].volumes_m3) || [],
        backgroundColor: _APPORT_COL[a],
      }));
      win.drawChart({
        type: 'bar',
        data: { labels: d.mois, datasets },
        options: {
          responsive: true, maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: _LEGEND,
            tooltip: { callbacks: { label: c => `${c.dataset.label} : ${fmt(c.parsed.y)} m³` } },
          },
          scales: {
            x: { grid: { display: false }, ticks: { font: _AXIS_FONT } },
            y: { beginAtZero: true, ticks: { font: _AXIS_FONT, callback: v => fmt(v) }, title: { display: true, text: 'Volume (m³)', font: { family: 'Inter', weight: '600' } } },
          },
        },
      }, 560);
      const tn = d.normale ? fmt(d.normale.total_m3) : '—';
      const vc = d.volume_capte_m3_an != null
        ? ` · volume capté ${fmt(d.volume_capte_m3_an)} m³/an (débit ${fmt2(d.debit_l_s)} l/s)` : '';
      const auto = d.auto_station ? ' · station auto' : '';
      win.setStatus(`<span class="cb-ok"><i class="fas fa-check-circle"></i> ${d.ouvrage}</span>
        <span class="cb-muted"> — BV ${d.bv} · station ${d.station}${auto} · total normale ${tn} m³${vc}</span>`);
    } catch (err) {
      win.setStatus(`<span class="cb-err">Erreur : ${err.message}</span>`);
    }
  }

  function _bindApCount(type) {
    const cfg = _AP_CFG[type];
    const maj = () => {
      const el = document.getElementById(`hy-ap-${type}-count`);
      if (!el) return;
      const n = _apPks(cfg.couche).length;
      el.value = n
        ? `${n} sélectionné${n > 1 ? 's' : ''}${n > 1 ? ' (1ᵉʳ utilisé)' : ''}`
        : cfg.vide;
    };
    document.addEventListener('carte:selectionChange', maj);
    maj();
  }

  // ── Init ───────────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', () => {
    // Ouverture des sous-panneaux (+ remplissage des menus déroulants)
    document.getElementById('hy-crue')?.addEventListener('click', () => {
      _showPanel('hy-panel-crue'); _fillSelect(document.getElementById('hy-crue-bv'), 'bv_ouvrage_tete', false);
    });
    document.getElementById('hy-tc')?.addEventListener('click', () => {
      _showPanel('hy-panel-tc'); _fillSelect(document.getElementById('hy-tc-bv'), 'bv_ouvrage_tete', false);
    });
    document.getElementById('hy-apports')?.addEventListener('click', () => {
      _showPanel('hy-panel-apports');
      _fillSelect(document.getElementById('hy-apports-bv'), 'bv_ouvrage_tete', false);
      _fillSelect(document.getElementById('hy-apports-station'), 'stations_hydro', false);
    });
    document.getElementById('hy-cruecarte')?.addEventListener('click', () => _showPanel('hy-panel-cruecarte'));
    document.getElementById('hy-ap-seuil')?.addEventListener('click', () => _showPanel('hy-panel-ap-seuil'));
    document.getElementById('hy-ap-prise')?.addEventListener('click', () => _showPanel('hy-panel-ap-prise'));
    document.getElementById('hy-ap-barrage')?.addEventListener('click', () => _showPanel('hy-panel-ap-barrage'));

    // Boutons retour
    document.querySelectorAll('.hy-back').forEach(b => b.addEventListener('click', _hideAll));

    // Compteurs de sélection carte (apport ouvrage)
    _bindApCount('seuil'); _bindApCount('prise'); _bindApCount('barrage');

    // Exécutions
    document.getElementById('hy-crue-exec')?.addEventListener('click', _crueGenerer);
    document.getElementById('hy-tc-exec')?.addEventListener('click', _tcGenerer);
    document.getElementById('hy-apports-exec')?.addEventListener('click', _apportsGenerer);
    document.getElementById('hy-cruecarte-exec')?.addEventListener('click', _crueCarteAfficher);
    document.getElementById('hy-cruecarte-clear')?.addEventListener('click', _crueCarteClear);
    document.getElementById('hy-ap-seuil-exec')?.addEventListener('click', () => _apportOuvrage('seuil'));
    document.getElementById('hy-ap-prise-exec')?.addEventListener('click', () => _apportOuvrage('prise'));
    document.getElementById('hy-ap-barrage-exec')?.addEventListener('click', () => _apportOuvrage('barrage'));
  });

})();
