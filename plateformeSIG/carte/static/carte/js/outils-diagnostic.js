/**
 * outils-diagnostic.js — Box « Diagnostic » du panneau droit Outils.
 *
 * Outils :
 *   - Indice de priorité / Scoring → recoloration de la couche (slot 'resultat')
 *                                    via /outils/indice-priorite/ ou /outils/scoring/
 *   - Comparaison d'état           → fenêtre (barres : ouvrages par état)
 *   - Débit mobilisé (carte)       → cercles proportionnels (slot 'resultat')
 *   - Assolement                   → fenêtre (camembert des surfaces par culture)
 *
 * Tout rendu carte passe par window.CarteRendu. Dépend de : map.js (MAP,
 * maplibregl), Chart.js, carte-rendu.js, query.js (getCsrf).
 */
'use strict';

(function () {

  const PANELS = ['dg-panel-prio', 'dg-panel-etat', 'dg-panel-debit', 'dg-panel-asso'];
  const OUVRAGE_LINE = new Set(['troncons_seguias']);
  const fmt = v => Number(v || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
  const fmt2 = v => Number(v || 0).toLocaleString('fr-FR', { maximumFractionDigits: 2 });

  const ETAT_COLORS = {
    t_mauvais: '#8e1f3d', mauvais: '#e74c3c', moyen_mauvais: '#e67e22',
    moyen: '#f1c40f', moyen_bon: '#a3d160', bon: '#27ae60', excellent: '#16a085',
  };
  const PALETTE = ['#2980b9', '#27ae60', '#e67e22', '#8e44ad', '#c0392b', '#16a085',
    '#f1c40f', '#34495e', '#d35400', '#7f8c8d', '#2ecc71', '#e84393', '#00897b', '#fdcb6e', '#6c5ce7'];
  const SCORE_RAMP = ['#27ae60', '#a3d160', '#f1c40f', '#e67e22', '#e74c3c'];

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

  // ── Sélection carte (Lot B, point 1) ─────────────────────────────────────
  // PKs sélectionnés sur une couche (via le socle window.OutilsSel).
  function _pks(couche) {
    return (window.OutilsSel ? OutilsSel.pks(couche) : []);
  }
  // Compteur d'un outil « sélecteur de couche » : suit la couche du <select>
  // et la sélection carte (vide = toute la couche).
  function _bindCouchePicker(countId, coucheSelectId) {
    const sel = document.getElementById(coucheSelectId);
    const maj = () => {
      const el = document.getElementById(countId);
      if (!el || !sel) return;
      el.value = window.OutilsSel
        ? OutilsSel.texte(sel.value)
        : '0 — toute la couche';
    };
    document.addEventListener('carte:selectionChange', maj);
    if (sel) sel.addEventListener('change', maj);
    maj();
  }

  async function _postJSON(url, body) {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': (typeof getCsrf === 'function' ? getCsrf() : '') },
      body: JSON.stringify(body),
    });
    return r.json();
  }

  // ── Fenêtres flottantes (multi-instances via window.FloatingChart, Lot C) ──

  const _AXIS_FONT = { family: 'Inter', size: 10 };

  // ── Cercles thématiques (réutilisés par Débit mobilisé) ───────────────────

  function _propSize(v, vmin, vmax, minPx = 26, maxPx = 56) {
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
      fontSize: Math.max(8, Math.round(size * 0.26)) + 'px',
      textShadow: '0 1px 2px rgba(0,0,0,.5)', cursor: 'pointer', lineHeight: '1',
    });
    el.textContent = label;
    return el;
  }
  function _fitPoints(coords) {
    if (!coords.length) return;
    if (coords.length === 1) { MAP.flyTo({ center: coords[0], zoom: Math.max(MAP.getZoom(), 11), duration: 600 }); return; }
    const lons = coords.map(c => c[0]), lats = coords.map(c => c[1]);
    MAP.fitBounds([[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]], { padding: 80, maxZoom: 13, duration: 600 });
  }

  // ── Outil : Indice de priorité / Scoring ──────────────────────────────────

  async function _loadCriteres() {
    const couche = document.getElementById('dg-prio-couche').value;
    const cont = document.getElementById('dg-prio-crit');
    cont.innerHTML = '<span class="po-muted">Chargement…</span>';
    try {
      const d = await fetch(`/carte/api/couche/${couche}/criteres/`).then(r => r.json());
      const crit = d.criteres || [];
      cont.innerHTML = crit.length
        ? crit.map(c => `<div style="display:flex;align-items:center;gap:6px;margin:3px 0">
            <input type="number" min="0" max="5" step="0.5" value="1" class="po-input" style="width:54px" data-champ="${c.champ}">
            <span style="font-size:10.5px;color:#444">${c.label}</span></div>`).join('')
        : '<span class="po-muted">Aucun critère pour cette couche.</span>';
    } catch (e) { cont.innerHTML = `<span class="po-err">${e.message}</span>`; }
  }

  function _geomProp(couche) { return OUVRAGE_LINE.has(couche) ? 'line-color' : 'circle-color'; }

  function _legendeIP(d) {
    const counts = {};
    Object.values(d.classes || {}).forEach(c => { if (c != null) counts[c] = (counts[c] || 0) + 1; });
    return '<div>' + Object.keys(d.class_labels || {}).map(cls =>
      `<div style="display:flex;align-items:center;gap:6px;margin:2px 0">
        <span style="width:11px;height:11px;border-radius:2px;background:${d.class_colors[cls]};flex-shrink:0"></span>
        <span style="font-size:10.5px;color:#444">${d.class_labels[cls]} — ${counts[cls] || 0}</span></div>`).join('') + '</div>';
  }
  function _legendeScoring(d) {
    return '<div>' + (d.breaks || []).map((b, i) =>
      `<div style="display:flex;align-items:center;gap:6px;margin:2px 0">
        <span style="width:11px;height:11px;border-radius:2px;background:${SCORE_RAMP[Math.min(i, SCORE_RAMP.length - 1)]};flex-shrink:0"></span>
        <span style="font-size:10.5px;color:#444">≤ ${Number(b).toFixed(1)}</span></div>`).join('') + '</div>';
  }

  async function _prioExec() {
    const couche = document.getElementById('dg-prio-couche').value;
    const methode = document.getElementById('dg-prio-methode').value;
    const resEl = document.getElementById('dg-prio-result');
    if (!window.MAP) return;
    if (!MAP.getLayer(`lyr-${couche}`)) {
      resEl.innerHTML = `<span class="po-err"><i class="fas fa-exclamation-triangle"></i> Activez d'abord la couche dans le panneau gauche.</span>`;
      return;
    }
    const coefficients = {};
    document.querySelectorAll('#dg-prio-crit input[data-champ]').forEach(i => {
      const v = parseFloat(i.value); coefficients[i.dataset.champ] = isNaN(v) ? 0 : v;
    });
    if (!Object.keys(coefficients).length) {
      resEl.innerHTML = `<span class="po-err">Aucun critère disponible.</span>`; return;
    }
    resEl.innerHTML = '<span class="po-muted"><i class="fas fa-spinner fa-spin"></i> Calcul…</span>';
    const prop = _geomProp(couche);
    // Cas extrême (point 1) : on garde le choix de couche ET on restreint à la
    // sélection carte si l'utilisateur a sélectionné des ouvrages de cette couche.
    const pks = _pks(couche);
    try {
      let expr, legende, outil;
      const suffixe = pks.length ? ` (${pks.length} sél.)` : '';
      if (methode === 'fixe') {
        const body = { couche, coefficients };
        if (pks.length) body.pks = pks;
        const d = await _postJSON('/carte/api/outils/indice-priorite/', body);
        if (d.erreur) throw new Error(d.erreur);
        const args = [];
        for (const [pk, cls] of Object.entries(d.classes || {})) if (cls != null) args.push(Number(pk), d.class_colors[cls]);
        expr = args.length ? ['match', ['id'], ...args, '#95a5a6'] : '#95a5a6';
        legende = _legendeIP(d);
        outil = `Indice de priorité — ${couche}${suffixe}`;
      } else {
        const body = { couche, coefficients, n_classes: 5, methode };
        if (pks.length) body.pks = pks;
        const d = await _postJSON('/carte/api/outils/scoring/', body);
        if (d.erreur) throw new Error(d.erreur);
        const args = [];
        for (const r of (d.resultats || [])) args.push(Number(r.pk), SCORE_RAMP[Math.min(r.classe, SCORE_RAMP.length - 1)] || '#95a5a6');
        expr = args.length ? ['match', ['id'], ...args, '#95a5a6'] : '#95a5a6';
        legende = _legendeScoring(d);
        outil = `Scoring (${methode}) — ${couche}${suffixe}`;
      }
      CarteRendu.set('resultat', { outil, choro: [{ layer: `lyr-${couche}`, prop, value: expr }], legende });
      resEl.innerHTML = `<span class="po-ok"><i class="fas fa-check-circle"></i> Couche colorée (${methode === 'fixe' ? 'seuils fixes' : methode}).</span>`;
      document.getElementById('dg-prio-clear').style.display = '';
    } catch (err) {
      resEl.innerHTML = `<span class="po-err">Erreur : ${err.message}</span>`;
    }
  }

  function _prioClear() {
    if (window.CarteRendu) CarteRendu.clear('resultat');
    document.getElementById('dg-prio-clear').style.display = 'none';
    document.getElementById('dg-prio-result').innerHTML = '';
  }

  // ── Outil : Comparaison d'état ─────────────────────────────────────────────

  async function _etatGenerer() {
    const couche = document.getElementById('dg-etat-couche').value;
    const pks = _pks(couche);
    const win = FloatingChart.open({
      titre: "Comparaison d'état", icone: 'fa-chart-simple',
      sousTitre: pks.length ? `${pks.length} sél.` : 'toute la couche',
    });
    try {
      let url = `/carte/api/ouvrages/etat-comparaison/?couche=${couche}`;
      if (pks.length) url += `&pks=${pks.join(',')}`;
      const d = await fetch(url).then(r => r.json());
      const etats = (d.etats || []).filter(e => e.count > 0);
      if (!etats.length) {
        win.setStatus(`<span class="cb-err"><i class="fas fa-exclamation-triangle"></i> Aucun état renseigné.</span>`);
        return;
      }
      win.drawChart({
        type: 'bar',
        data: {
          labels: etats.map(e => e.label),
          datasets: [{ label: "Nombre d'ouvrages", data: etats.map(e => e.count), backgroundColor: etats.map(e => ETAT_COLORS[e.valeur] || '#95a5a6') }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => `${c.parsed.y} ouvrage(s)` } } },
          scales: {
            x: { grid: { display: false }, ticks: { font: _AXIS_FONT, maxRotation: 50, autoSkip: false } },
            y: { beginAtZero: true, ticks: { font: _AXIS_FONT, precision: 0 } },
          },
        },
      }, Math.max(0, etats.length * 70));
      win.setStatus(`<span class="cb-ok"><i class="fas fa-check-circle"></i> ${d.label}</span> <span class="cb-muted"> — ${d.total} ouvrage(s)</span>`);
    } catch (err) {
      win.setStatus(`<span class="cb-err">Erreur : ${err.message}</span>`);
    }
  }

  // ── Outil : Débit mobilisé (thématique carte) ─────────────────────────────

  async function _debitAfficher() {
    const couche = document.getElementById('dg-debit-couche').value;
    const pks = _pks(couche);
    const resEl = document.getElementById('dg-debit-result');
    if (!window.MAP) return;
    resEl.innerHTML = '<span class="po-muted"><i class="fas fa-spinner fa-spin"></i> Chargement…</span>';
    try {
      let url = `/carte/api/ouvrages/debit-points/?couche=${couche}`;
      if (pks.length) url += `&pks=${pks.join(',')}`;
      const d = await fetch(url).then(r => r.json());
      const feats = (d.features || []).filter(f => f.properties.value != null);
      if (!feats.length) {
        if (window.CarteRendu) CarteRendu.clear('resultat');
        resEl.innerHTML = `<span class="po-err"><i class="fas fa-exclamation-triangle"></i> Aucun débit géolocalisé pour cette couche.</span>`;
        document.getElementById('dg-debit-clear').style.display = 'none';
        return;
      }
      const mode = document.getElementById('dg-debit-mode')?.value || 'cercle_prop';
      const points = feats.map(f => ({
        coord: f.geometry.coordinates, value: f.properties.value, nom: f.properties.nom,
      }));
      const r = RenduCarte.renderThematique(MAP, points, { mode, unite: d.unite, color: '#c0392b' });
      CarteRendu.set('resultat', {
        outil: `Débit mobilisé — ${couche}`,
        markers: r.markers, overlay: r.overlay, choro: r.paints, legende: r.legende,
      });
      resEl.innerHTML = `<span class="po-ok"><i class="fas fa-check-circle"></i> ${feats.length} ouvrage(s) — débit (${d.unite}).</span>`;
      document.getElementById('dg-debit-clear').style.display = '';
    } catch (err) {
      resEl.innerHTML = `<span class="po-err">Erreur : ${err.message}</span>`;
    }
  }

  function _debitClear() {
    if (window.CarteRendu) CarteRendu.clear('resultat');
    document.getElementById('dg-debit-clear').style.display = 'none';
    document.getElementById('dg-debit-result').innerHTML = '';
  }

  // ── Outil : Assolement (camembert) ─────────────────────────────────────────

  async function _assoGenerer() {
    const pks = _pks('perimetres');
    const resEl = document.getElementById('dg-asso-result');
    if (!pks.length) {
      if (resEl) resEl.innerHTML = `<span class="po-err"><i class="fas fa-exclamation-triangle"></i> Sélectionnez un périmètre sur la carte.</span>`;
      return;
    }
    const pk = pks[0];   // assolement d'un périmètre (1ʳᵉ sélection)
    const win = FloatingChart.open({ titre: 'Assolement', icone: 'fa-seedling' });
    try {
      const d = await fetch(`/carte/api/perimetre/${pk}/rendement/`).then(r => r.json());
      const asso = (d.assolement || []).filter(a => (a.surface_ha || 0) > 0);
      if (!asso.length) {
        win.setStatus(`<span class="cb-err"><i class="fas fa-exclamation-triangle"></i> Aucune surface d'assolement renseignée.</span>`);
        return;
      }
      win.drawChart({
        type: 'doughnut',
        data: {
          labels: asso.map(a => a.culture),
          datasets: [{ data: asso.map(a => a.surface_ha), backgroundColor: asso.map((a, i) => PALETTE[i % PALETTE.length]), borderColor: '#fff', borderWidth: 1.5 }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { position: 'right', labels: { font: { family: 'Inter', size: 10 }, boxWidth: 10, padding: 6 } },
            tooltip: { callbacks: { label: c => `${c.label} : ${fmt2(c.parsed)} ha` } },
          },
        },
      });
      win.setStatus(`<span class="cb-ok"><i class="fas fa-check-circle"></i> ${fmt2(d.total_surface_ha)} ha</span>
        <span class="cb-muted"> — dominante ${d.culture_dominante || '—'}${d.rendement_pondere != null ? ' · rdt pondéré ' + fmt2(d.rendement_pondere) : ''}</span>`);
    } catch (err) {
      win.setStatus(`<span class="cb-err">Erreur : ${err.message}</span>`);
    }
  }

  // ── Init ───────────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('dg-prio')?.addEventListener('click', () => { _showPanel('dg-panel-prio'); _loadCriteres(); });
    document.getElementById('dg-etat')?.addEventListener('click', () => _showPanel('dg-panel-etat'));
    document.getElementById('dg-debit')?.addEventListener('click', () => _showPanel('dg-panel-debit'));
    document.getElementById('dg-asso')?.addEventListener('click', () => _showPanel('dg-panel-asso'));

    document.querySelectorAll('.dg-back').forEach(b => b.addEventListener('click', _hideAll));

    // Compteurs de sélection carte (point 1) — couche-pickers + assolement
    _bindCouchePicker('dg-prio-count', 'dg-prio-couche');
    _bindCouchePicker('dg-etat-count', 'dg-etat-couche');
    _bindCouchePicker('dg-debit-count', 'dg-debit-couche');
    const _majAsso = () => {
      const el = document.getElementById('dg-asso-count');
      if (!el) return;
      const n = _pks('perimetres').length;
      el.value = n
        ? `${n} périmètre${n > 1 ? 's' : ''} sélectionné${n > 1 ? 's' : ''}${n > 1 ? ' (1ᵉʳ utilisé)' : ''}`
        : 'Aucun — sélectionnez sur la carte';
    };
    document.addEventListener('carte:selectionChange', _majAsso);
    _majAsso();

    document.getElementById('dg-prio-couche')?.addEventListener('change', _loadCriteres);
    document.getElementById('dg-prio-exec')?.addEventListener('click', _prioExec);
    document.getElementById('dg-prio-clear')?.addEventListener('click', _prioClear);
    document.getElementById('dg-etat-exec')?.addEventListener('click', _etatGenerer);
    document.getElementById('dg-debit-exec')?.addEventListener('click', _debitAfficher);
    document.getElementById('dg-debit-clear')?.addEventListener('click', _debitClear);
    document.getElementById('dg-asso-exec')?.addEventListener('click', _assoGenerer);
  });

})();
