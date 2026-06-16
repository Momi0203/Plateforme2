/**
 * outils-bilan.js — Box « Bilan eau » du panneau droit Outils.
 *
 * Outils :
 *   - Bilan mensuel        → fenêtre flottante (besoins vs ressources, 12 mois)
 *   - Taux de couverture   → thématique carte (cercles classés, slot 'resultat')
 *   - ET0 climatique       → fenêtre flottante (calculer_eto)
 *
 * Sélection par menu déroulant. Tout rendu carte passe par window.CarteRendu.
 * Dépend de : map.js (MAP, maplibregl), Chart.js, carte-rendu.js.
 */
'use strict';

(function () {

  const PANELS = ['bl-panel-bilan', 'bl-panel-couverture', 'bl-panel-eto'];
  const ANNEE_LABEL = { normale: 'normale', humide: 'humide', seche: 'sèche' };

  const fmt = v => Number(v || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
  const fmt2 = v => Number(v || 0).toLocaleString('fr-FR', { maximumFractionDigits: 2 });

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

  // Sélection carte (Lot B, point 1) : 1ʳᵉ entité sélectionnée sur la couche.
  function _pks(couche) { return (window.OutilsSel ? OutilsSel.pks(couche) : []); }

  // Compteur d'un outil mono-entité (périmètre / station).
  function _bindMono(countId, couche, vide) {
    const maj = () => {
      const el = document.getElementById(countId);
      if (!el) return;
      const n = _pks(couche).length;
      el.value = n
        ? `${n} sélectionné${n > 1 ? 's' : ''}${n > 1 ? ' (1ᵉʳ utilisé)' : ''}`
        : vide;
    };
    document.addEventListener('carte:selectionChange', maj);
    maj();
  }

  // ── Fenêtres flottantes (multi-instances via window.FloatingChart, Lot C) ──

  const _AXIS_FONT = { family: 'Inter', size: 10 };
  const _LEGEND = { position: 'top', labels: { usePointStyle: true, boxWidth: 8, font: { family: 'Inter', size: 11 } } };

  // ── Outil : Bilan mensuel — C1 ─────────────────────────────────────────────

  async function _bilanGenerer() {
    const annee = document.getElementById('bl-bilan-annee').value;
    const pks = _pks('perimetres');
    const resEl = document.getElementById('bl-bilan-result');
    if (!pks.length) {
      if (resEl) resEl.innerHTML = `<span class="po-err"><i class="fas fa-exclamation-triangle"></i> Sélectionnez un périmètre sur la carte.</span>`;
      return;
    }
    const pk = pks[0];   // bilan d'un périmètre (1ʳᵉ sélection)
    const win = FloatingChart.open({ titre: 'Bilan mensuel', icone: 'fa-chart-line', sousTitre: `année ${ANNEE_LABEL[annee]}` });
    try {
      const d = await fetch(`/carte/api/perimetre/${pk}/bilan-mensuel/?annee=${annee}`).then(r => r.json());
      if (!d.mois || !d.mois.length) {
        win.setStatus(`<span class="cb-err"><i class="fas fa-exclamation-triangle"></i> ${d.message || 'Aucun bilan disponible.'}</span>`);
        return;
      }
      win.drawChart({
        type: 'bar',
        data: {
          labels: d.mois,
          datasets: [
            { label: 'Besoins', data: d.besoins_m3, backgroundColor: '#c0392b' },
            { label: 'Ressources', data: d.ressources_m3, backgroundColor: '#2980b9' },
          ],
        },
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
      const solde = (d.total_excedent || 0) - (d.total_deficit || 0);
      const soldeTxt = solde >= 0
        ? `<span style="color:#27ae60">excédent ${fmt(d.total_excedent)} m³</span>`
        : `<span style="color:#e74c3c">déficit ${fmt(d.total_deficit)} m³</span>`;
      win.setStatus(`<span class="cb-ok"><i class="fas fa-check-circle"></i> ${d.perimetre}</span>
        <span class="cb-muted"> — année ${ANNEE_LABEL[annee]} · besoins ${fmt(d.total_besoins)} / ressources ${fmt(d.total_ressources)} m³ · ${soldeTxt}</span>`);
    } catch (err) {
      win.setStatus(`<span class="cb-err">Erreur : ${err.message}</span>`);
    }
  }

  // ── Outil : ET0 climatique — C3 ────────────────────────────────────────────

  const _ETO_MAX = 12;   // courbes 12 mois → plafond bas (lisibilité)

  async function _etoGenerer() {
    const pks = _pks('stations_clim');
    const resEl = document.getElementById('bl-eto-result');
    if (!pks.length) {
      if (resEl) resEl.innerHTML = `<span class="po-err"><i class="fas fa-exclamation-triangle"></i> Sélectionnez une ou plusieurs stations climatiques sur la carte.</span>`;
      return;
    }
    const used = pks.slice(0, _ETO_MAX);
    const win = FloatingChart.open({ titre: 'ET0 climatique', icone: 'fa-sun' });
    try {
      // Multi-entités (point 2) : une requête par station, fusionnées dans un seul graphe.
      const results = await Promise.all(used.map(pk =>
        fetch(`/carte/api/station-clim/${pk}/eto/`).then(r => r.json()).catch(() => null)));
      const valid = results.filter(d => d && d.mois && d.mois.length);
      if (!valid.length) {
        win.setStatus(`<span class="cb-err"><i class="fas fa-exclamation-triangle"></i> Aucune station avec ET0 calculable.</span>`);
        return;
      }
      const labels = valid[0].mois;
      const mono = valid.length === 1;
      const datasets = valid.map((d, i) => ({
        label: d.station,
        data: d.eto_mm_mois,
        borderColor: window.OutilsChart ? OutilsChart.couleur(i) : '#e67e22',
        backgroundColor: mono ? 'rgba(230,126,34,.15)' : 'transparent',
        fill: mono, tension: 0.3, pointRadius: 2,
      }));
      win.drawChart({
        type: 'line',
        data: { labels, datasets },
        options: {
          responsive: true, maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: _LEGEND,
            tooltip: { callbacks: { label: c => `${c.dataset.label} : ${fmt2(c.parsed.y)} mm` } },
          },
          scales: {
            x: { grid: { display: false }, ticks: { font: _AXIS_FONT } },
            y: { beginAtZero: true, ticks: { font: _AXIS_FONT }, title: { display: true, text: 'ET0 (mm/mois)', font: { family: 'Inter', weight: '600' } } },
          },
        },
      }, 560);
      const tronque = pks.length > _ETO_MAX ? `<span class="cb-warn"> (${pks.length} sélectionnées — ${_ETO_MAX} affichées)</span>` : '';
      win.setStatus(`<span class="cb-ok"><i class="fas fa-check-circle"></i> ${valid.length} station(s)</span>${tronque}`);
    } catch (err) {
      win.setStatus(`<span class="cb-err">Erreur : ${err.message}</span>`);
    }
  }

  // ── Outil : Taux de couverture (thématique carte) — C2 ────────────────────

  function _couvColor(v) {
    if (v >= 100) return '#27ae60';   // couvert
    if (v >= 80)  return '#f1c40f';
    if (v >= 50)  return '#e67e22';
    return '#e74c3c';                 // fort déficit
  }

  function _circleEl(size, color, label, title) {
    const el = document.createElement('div');
    el.title = title || '';
    Object.assign(el.style, {
      width: size + 'px', height: size + 'px', borderRadius: '50%', background: color,
      border: '2px solid #fff', boxShadow: '0 1px 4px rgba(0,0,0,.4)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      color: '#fff', fontWeight: '700', fontFamily: "'Inter', sans-serif",
      fontSize: Math.max(9, Math.round(size * 0.28)) + 'px',
      textShadow: '0 1px 2px rgba(0,0,0,.5)', cursor: 'pointer', lineHeight: '1',
    });
    el.textContent = label;
    return el;
  }

  function _couvLegende() {
    const rows = [
      ['#27ae60', '≥ 100 % (couvert)'],
      ['#f1c40f', '80 – 100 %'],
      ['#e67e22', '50 – 80 %'],
      ['#e74c3c', '< 50 % (déficit)'],
    ].map(([c, t]) => `<div style="display:flex;align-items:center;gap:6px;margin:2px 0">
      <span style="width:11px;height:11px;border-radius:50%;background:${c};border:1.5px solid #fff;box-shadow:0 0 0 1px #ccc;flex-shrink:0"></span>
      <span style="font-size:10.5px;color:#444">${t}</span></div>`).join('');
    return `<div>${rows}</div>`;
  }

  async function _couvAfficher() {
    const resEl = document.getElementById('bl-couverture-result');
    const annee = document.getElementById('bl-couverture-annee').value;
    if (!window.MAP) return;
    resEl.innerHTML = '<span class="po-muted"><i class="fas fa-spinner fa-spin"></i> Chargement…</span>';
    try {
      const d = await fetch(`/carte/api/perimetres/couverture/?annee=${annee}`).then(r => r.json());
      const feats = d.features || [];
      if (!feats.length) {
        if (window.CarteRendu) CarteRendu.clear('resultat');
        resEl.innerHTML = `<span class="po-err"><i class="fas fa-exclamation-triangle"></i> Aucun bilan calculé (année ${ANNEE_LABEL[annee]}).</span>`;
        document.getElementById('bl-couverture-clear').style.display = 'none';
        return;
      }
      const mode = document.getElementById('bl-couverture-mode')?.value || 'seuils';
      const outil = `Taux de couverture — année ${ANNEE_LABEL[annee]}`;

      if (mode === 'seuils') {
        // Mode historique : classes fixes couvert/déficit (cercles colorés).
        const markers = [], overlay = [];
        for (const f of feats) {
          const v = f.properties.value;
          const color = _couvColor(v);
          const el = _circleEl(36, color, Math.round(v) + '%',
            `${f.properties.nom} — ${v}% (ress. ${fmt(f.properties.ressources)} / bes. ${fmt(f.properties.besoins)} m³)`);
          const m = new maplibregl.Marker({ element: el, anchor: 'center' }).setLngLat(f.geometry.coordinates).addTo(MAP);
          markers.push(m);
          overlay.push({ type: 'circle', coord: f.geometry.coordinates, size: 36, color, label: Math.round(v) + '%' });
        }
        CarteRendu.set('resultat', { outil, markers, overlay, legende: _couvLegende() });
        const lons = feats.map(f => f.geometry.coordinates[0]), lats = feats.map(f => f.geometry.coordinates[1]);
        if (feats.length === 1) MAP.flyTo({ center: feats[0].geometry.coordinates, zoom: Math.max(MAP.getZoom(), 10), duration: 600 });
        else MAP.fitBounds([[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]], { padding: 80, maxZoom: 12, duration: 600 });
      } else {
        // Modes génériques (quantiles / proportionnel / aplat) via RenduCarte.
        const points = feats.map(f => ({
          coord: f.geometry.coordinates, value: f.properties.value,
          nom: f.properties.nom, pk: f.properties.pk,
        }));
        const r = RenduCarte.renderThematique(MAP, points, {
          mode, unite: '%', color: '#16a085',
          choroLayer: 'lyr-perimetres',
          choroErreur: "Activez la couche « Périmètres agricoles » (panneau gauche) pour l'aplat de couleur.",
        });
        if (r.erreur) {
          resEl.innerHTML = `<span class="po-err"><i class="fas fa-exclamation-triangle"></i> ${r.erreur}</span>`;
          return;
        }
        CarteRendu.set('resultat', {
          outil, markers: r.markers, overlay: r.overlay, choro: r.paints, legende: r.legende,
        });
      }
      resEl.innerHTML = `<span class="po-ok"><i class="fas fa-check-circle"></i> ${feats.length} périmètre(s) — année ${ANNEE_LABEL[annee]}.</span>`;
      document.getElementById('bl-couverture-clear').style.display = '';
    } catch (err) {
      resEl.innerHTML = `<span class="po-err">Erreur : ${err.message}</span>`;
    }
  }

  function _couvClear() {
    if (window.CarteRendu) CarteRendu.clear('resultat');
    document.getElementById('bl-couverture-clear').style.display = 'none';
    document.getElementById('bl-couverture-result').innerHTML = '';
  }

  // ── Init ───────────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('bl-bilan')?.addEventListener('click', () => _showPanel('bl-panel-bilan'));
    document.getElementById('bl-couverture')?.addEventListener('click', () => _showPanel('bl-panel-couverture'));
    document.getElementById('bl-eto')?.addEventListener('click', () => _showPanel('bl-panel-eto'));

    document.querySelectorAll('.bl-back').forEach(b => b.addEventListener('click', _hideAll));

    // Compteurs de sélection carte (point 1)
    _bindMono('bl-bilan-count', 'perimetres', 'Aucun — sélectionnez sur la carte');
    _bindMono('bl-eto-count', 'stations_clim', 'Aucune — sélectionnez sur la carte');

    document.getElementById('bl-bilan-exec')?.addEventListener('click', _bilanGenerer);
    document.getElementById('bl-eto-exec')?.addEventListener('click', _etoGenerer);
    document.getElementById('bl-couverture-exec')?.addEventListener('click', _couvAfficher);
    document.getElementById('bl-couverture-clear')?.addEventListener('click', _couvClear);
  });

})();
