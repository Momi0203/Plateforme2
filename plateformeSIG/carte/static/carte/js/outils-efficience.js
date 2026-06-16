/**
 * outils-efficience.js — Box « Efficience réseau » du panneau droit Outils.
 *
 * Outils :
 *   - Efficience ouvrage de tête → fenêtre (cascade P/S/T → globale)
 *   - Profil de pertes (séguia)  → fenêtre (débit amont→aval + Pi/Pv par tronçon)
 *   - Rendement tronçons (carte) → couche de lignes colorées (slot 'resultat')
 *
 * Sélection par menu déroulant. Tout rendu carte passe par window.CarteRendu.
 * Dépend de : map.js (MAP), Chart.js, carte-rendu.js.
 */
'use strict';

(function () {

  const PANELS = ['ef-panel-ouvrage', 'ef-panel-profil', 'ef-panel-rendement'];
  const fmt2 = v => Number(v || 0).toLocaleString('fr-FR', { maximumFractionDigits: 2 });
  const fmt4 = v => Number(v || 0).toLocaleString('fr-FR', { maximumFractionDigits: 4 });

  // ── Navigation ─────────────────────────────────────────────────────────────

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

  // ── Fenêtres flottantes (multi-instances via window.FloatingChart, Lot C) ──

  const _AXIS_FONT = { family: 'Inter', size: 10 };
  const _LEGEND = { position: 'top', labels: { usePointStyle: true, boxWidth: 8, font: { family: 'Inter', size: 11 } } };

  // ── Outil : Efficience ouvrage de tête — D1 ───────────────────────────────

  const _effCache = {};   // pk -> option complète

  async function _fillOuvrages() {
    const sel = document.getElementById('ef-ouvrage-sel');
    if (!sel || sel.dataset.filled === '1') return;
    try {
      const d = await fetch('/carte/api/efficiences/liste/').then(r => r.json());
      (d.options || []).forEach(o => { _effCache[o.pk] = o; });
      sel.innerHTML = (d.options || []).map(o => `<option value="${o.pk}">${o.label}</option>`).join('')
        || '<option value="">Aucun résultat d\'efficience</option>';
      sel.dataset.filled = '1';
    } catch (e) { console.error('[efficience] _fillOuvrages', e); }
  }

  function _ouvrageGenerer() {
    const pk = document.getElementById('ef-ouvrage-sel').value;
    const o = _effCache[pk];
    if (!o) return;
    const win = FloatingChart.open({ titre: 'Efficience ouvrage de tête', icone: 'fa-sitemap' });
    const labels = [], data = [], colors = [];
    if (o.principale != null) { labels.push('Principale'); data.push(o.principale); colors.push('#27ae60'); }
    if (o.secondaire != null) { labels.push('Secondaire'); data.push(o.secondaire); colors.push('#2980b9'); }
    if (o.tertiaire != null) { labels.push('Tertiaire'); data.push(o.tertiaire); colors.push('#e67e22'); }
    labels.push('Globale'); data.push(o.globale); colors.push('#8e44ad');

    win.drawChart({
      type: 'bar',
      data: { labels, datasets: [{ label: 'Efficience (%)', data, backgroundColor: colors }] },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: c => `${fmt2(c.parsed.y)} %` } },
        },
        scales: {
          x: { grid: { display: false }, ticks: { font: _AXIS_FONT } },
          y: { beginAtZero: true, max: 100, ticks: { font: _AXIS_FONT }, title: { display: true, text: 'Efficience (%)', font: { family: 'Inter', weight: '600' } } },
        },
      },
    });
    win.setStatus(`<span class="cb-ok"><i class="fas fa-check-circle"></i> ${o.ouvrage} — ${o.perimetre}</span>
      <span class="cb-muted"> — globale ${fmt2(o.globale)} % · tronçons P ${o.nb_p} / S ${o.nb_s} / T ${o.nb_t}</span>`);
  }

  // ── Outil : Profil de pertes (séguia) — D2 ────────────────────────────────

  async function _fillSeguias() {
    const sel = document.getElementById('ef-profil-sel');
    if (!sel || sel.dataset.filled === '1') return;
    try {
      const d = await fetch('/carte/api/seguias/liste/').then(r => r.json());
      sel.innerHTML = (d.options || []).map(o => `<option value="${o.pk}">${o.label}</option>`).join('');
      sel.dataset.filled = '1';
    } catch (e) { console.error('[efficience] _fillSeguias', e); }
  }

  async function _profilGenerer() {
    const pk = document.getElementById('ef-profil-sel').value;
    if (!pk) return;
    const win = FloatingChart.open({ titre: 'Profil de pertes (séguia)', icone: 'fa-chart-area' });
    try {
      const d = await fetch(`/carte/api/seguia/${pk}/profil/`).then(r => r.json());
      const rows = d.troncons || [];
      if (!rows.length) {
        win.setStatus(`<span class="cb-err"><i class="fas fa-exclamation-triangle"></i> ${d.message || 'Aucun tronçon.'}</span>`);
        return;
      }
      win.drawChart({
        type: 'bar',
        data: {
          labels: rows.map(t => t.troncon),
          datasets: [
            { label: 'Débit aval', data: rows.map(t => t.debit_aval), backgroundColor: '#27ae60', stack: 's' },
            { label: 'Perte infiltration', data: rows.map(t => t.perte_infiltration), backgroundColor: '#e67e22', stack: 's' },
            { label: 'Perte vaporisation', data: rows.map(t => t.perte_vaporisation), backgroundColor: '#e74c3c', stack: 's' },
          ],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: _LEGEND,
            tooltip: { callbacks: { label: c => `${c.dataset.label} : ${fmt4(c.parsed.y)} m³/s` } },
          },
          scales: {
            x: { stacked: true, grid: { display: false }, ticks: { font: _AXIS_FONT } },
            y: { stacked: true, beginAtZero: true, ticks: { font: _AXIS_FONT }, title: { display: true, text: 'Débit (m³/s) — empilé = amont', font: { family: 'Inter', weight: '600' } } },
          },
        },
      }, Math.max(0, rows.length * 90));
      win.setStatus(`<span class="cb-ok"><i class="fas fa-check-circle"></i> ${d.seguia} (${d.type})</span>
        <span class="cb-muted"> — efficience séguia ${fmt2(d.efficience_seguia)} %</span>`);
    } catch (err) {
      win.setStatus(`<span class="cb-err">Erreur : ${err.message}</span>`);
    }
  }

  // ── Outil : Rendement tronçons (thématique carte) — D3 ────────────────────

  const REND_IDS = { src: 'ef-troncons-src', line: 'ef-troncons-line' };

  function _removeRend() {
    if (!window.MAP) return;
    if (MAP.getLayer(REND_IDS.line)) MAP.removeLayer(REND_IDS.line);
    if (MAP.getSource(REND_IDS.src)) MAP.removeSource(REND_IDS.src);
  }

  // Rampe rendement : faible efficience (rouge) → forte (vert).
  const REND_RAMP = ['#e74c3c', '#e67e22', '#f1c40f', '#a3d160', '#27ae60'];

  function _rendRows(stops) {
    return '<div>' + stops.map(([c, t]) =>
      `<div style="display:flex;align-items:center;gap:6px;margin:2px 0">
        <span style="width:16px;height:3px;background:${c};flex-shrink:0"></span>
        <span style="font-size:10.5px;color:#444">${t}</span></div>`).join('') + '</div>';
  }

  function _rendLegende() {
    return _rendRows([['#e74c3c', '< 50 %'], ['#e67e22', '50 – 75 %'], ['#f1c40f', '75 – 90 %'], ['#27ae60', '≥ 90 %'], ['#999999', 'non calculé']]);
  }

  // Mode « seuils fixes » : interpolation continue par % d'efficience.
  function _rendColorSeuils() {
    return ['interpolate', ['linear'], ['coalesce', ['get', 'efficience_calculee'], -1],
      -1, '#999999', 0, '#e74c3c', 50, '#e67e22', 75, '#f1c40f', 90, '#27ae60'];
  }

  // Mode « quantiles » : classes calculées sur les valeurs présentes.
  function _rendQuantiles(feats) {
    const vals = feats.map(f => f.properties && f.properties.efficience_calculee).filter(v => v != null);
    if (!vals.length) return null;
    const breaks = RenduCarte.quantileBreaks(vals, 5);
    const n = breaks.length;
    const colorsArr = [];
    for (let i = 0; i < n; i++) {
      const j = n === 1 ? 2 : Math.round((i / (n - 1)) * (REND_RAMP.length - 1));
      colorsArr.push(REND_RAMP[j]);
    }
    const stepArgs = [];
    for (let i = 0; i < n - 1; i++) stepArgs.push(breaks[i], colorsArr[i + 1]);
    const step = ['step', ['coalesce', ['get', 'efficience_calculee'], -1], colorsArr[0], ...stepArgs];
    const color = ['case', ['!=', ['get', 'efficience_calculee'], null], step, '#999999'];

    const stops = breaks.map((b, i) => {
      const lo = i === 0 ? 0 : breaks[i - 1];
      return [colorsArr[i], `${lo.toFixed(0)} – ${b.toFixed(0)} %`];
    });
    stops.push(['#999999', 'non calculé']);
    return { color, legende: _rendRows(stops) };
  }

  async function _rendementAfficher() {
    const resEl = document.getElementById('ef-rendement-result');
    if (!window.MAP) return;
    resEl.innerHTML = '<span class="po-muted"><i class="fas fa-spinner fa-spin"></i> Chargement…</span>';
    try {
      const geo = await fetch('/carte/api/couche/troncons_seguias/?limit=2000').then(r => r.json());
      const feats = geo.features || [];
      if (!feats.length) {
        if (window.CarteRendu) CarteRendu.clear('resultat');
        resEl.innerHTML = '<span class="po-err"><i class="fas fa-exclamation-triangle"></i> Aucun tronçon de séguia.</span>';
        document.getElementById('ef-rendement-clear').style.display = 'none';
        return;
      }
      const mode = document.getElementById('ef-rendement-mode')?.value || 'seuils';
      let color, legende;
      if (mode === 'quantiles') {
        const q = _rendQuantiles(feats);
        if (!q) {
          if (window.CarteRendu) CarteRendu.clear('resultat');
          resEl.innerHTML = '<span class="po-err"><i class="fas fa-exclamation-triangle"></i> Aucune efficience calculée pour le mode quantiles.</span>';
          document.getElementById('ef-rendement-clear').style.display = 'none';
          return;
        }
        color = q.color; legende = q.legende;
      } else {
        color = _rendColorSeuils(); legende = _rendLegende();
      }

      _removeRend();
      MAP.addSource(REND_IDS.src, { type: 'geojson', data: geo });
      MAP.addLayer({ id: REND_IDS.line, type: 'line', source: REND_IDS.src, paint: { 'line-color': color, 'line-width': 3 } });

      CarteRendu.set('resultat', {
        outil: `Rendement des tronçons (${mode === 'quantiles' ? 'quantiles' : 'seuils fixes'})`,
        legende,
        cleanup: _removeRend,
      });
      // Cadrage
      try {
        const ext = await fetch('/carte/api/couche/troncons_seguias/extent/').then(r => r.json());
        if (ext.bbox) MAP.fitBounds([[ext.bbox[0], ext.bbox[1]], [ext.bbox[2], ext.bbox[3]]], { padding: 70, duration: 600 });
      } catch (e) { /* non bloquant */ }

      const nbCalc = feats.filter(f => f.properties && f.properties.efficience_calculee != null).length;
      resEl.innerHTML = `<span class="po-ok"><i class="fas fa-check-circle"></i> ${feats.length} tronçon(s) · ${nbCalc} avec efficience.</span>`;
      document.getElementById('ef-rendement-clear').style.display = '';
    } catch (err) {
      resEl.innerHTML = `<span class="po-err">Erreur : ${err.message}</span>`;
    }
  }

  function _rendementClear() {
    if (window.CarteRendu) CarteRendu.clear('resultat'); else _removeRend();
    document.getElementById('ef-rendement-clear').style.display = 'none';
    document.getElementById('ef-rendement-result').innerHTML = '';
  }

  // ── Init ───────────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('ef-ouvrage')?.addEventListener('click', () => { _showPanel('ef-panel-ouvrage'); _fillOuvrages(); });
    document.getElementById('ef-profil')?.addEventListener('click', () => { _showPanel('ef-panel-profil'); _fillSeguias(); });
    document.getElementById('ef-rendement')?.addEventListener('click', () => _showPanel('ef-panel-rendement'));

    document.querySelectorAll('.ef-back').forEach(b => b.addEventListener('click', _hideAll));

    document.getElementById('ef-ouvrage-exec')?.addEventListener('click', _ouvrageGenerer);
    document.getElementById('ef-profil-exec')?.addEventListener('click', _profilGenerer);
    document.getElementById('ef-rendement-exec')?.addEventListener('click', _rendementAfficher);
    document.getElementById('ef-rendement-clear')?.addEventListener('click', _rendementClear);
  });

})();
