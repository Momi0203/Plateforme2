/**
 * outils-couches.js — Box « Couches » du panneau droit (Lot E).
 *
 * Outil « Hydrologie 2 » : active/désactive, dans le PANNEAU GAUCHE, un groupe
 * de couches « ouvrage de tête » masquées par défaut :
 *   - bv_ouvrage_tete   : bassins versants (ligne couche standard — case,
 *                         symbologie, requête, sélection, centrer, isoler).
 *   - 5 réseaux (Ziz…)  : couches volumineuses « intersection-only » → pas de
 *                         case ; bouton « Réseau du BV » qui affiche le réseau
 *                         CLIPPÉ à un bassin versant (mode forcé, Q5-bis), via
 *                         l'endpoint /carte/api/reseau-ouvrage-tete/.
 *
 * Remplace l'ancien outil « Bassins versants & réseau » de la box Hydrologie.
 *
 * Dépend de : map.js (window.coucheRowHtml, MAP), layers.js (COUCHES_META,
 * LOADED_LAYERS, loadLayer/hideLayer), carte-rendu.js (slot 'contexte').
 */
'use strict';

(function () {

  let _activated   = false;
  let _activables  = [];
  let _currentReseau = null;            // couche réseau active dans le mini-panel
  const SRC = 'co-reseau-src', LYR = 'co-reseau-line';

  // ── Activation du groupe « Réseaux ouvrage de tête » (panneau gauche) ──────

  async function _toggleHydro2() {
    if (_activated) { _deactivate(); return; }
    try {
      if (!_activables.length) {
        _activables = await fetch('/carte/api/couches/activables/').then(r => r.json());
      }
      _injectGroup(_activables);
      _activated = true;
      document.getElementById('co-hydro2')?.classList.add('active');
    } catch (e) {
      console.error('[couches] activables', e);
    }
  }

  function _injectGroup(couches) {
    const container = document.getElementById('couches-liste');
    if (!container || document.getElementById('couche-groupe-tete')) return;

    // Enregistrer les métadonnées (pour loadLayer / _colorFor / symbologie).
    couches.forEach(c => { window.COUCHES_META[c.nom] = c; });

    const lignes = couches.map(c => window.coucheRowHtml(c)).join('');
    const details = document.createElement('details');
    details.className = 'couche-groupe';
    details.id = 'couche-groupe-tete';
    details.open = true;
    details.innerHTML =
      `<summary>Réseaux ouvrage de tête <small>(${couches.length})</small></summary>
       <ul class="couche-liste">${lignes}</ul>`;
    container.appendChild(details);
  }

  function _deactivate() {
    _clearReseau();
    // Décharger les couches « normales » du groupe (ex. bv_ouvrage_tete).
    if (typeof window.hideLayer === 'function') {
      _activables.forEach(c => {
        if (!c.reseau_tete && window.LOADED_LAYERS && window.LOADED_LAYERS.has(c.nom)) {
          hideLayer(c.nom);
        }
      });
    }
    document.getElementById('couche-groupe-tete')?.remove();
    _activated = false;
    document.getElementById('co-hydro2')?.classList.remove('active');
    _hidePanel();
  }

  // ── Mini-panel « Réseau du BV » (panneau droit) ───────────────────────────

  function _showPanel() {
    const l = document.getElementById('po-outils-liste'); if (l) l.style.display = 'none';
    const p = document.getElementById('co-panel-reseau'); if (p) p.style.display = 'flex';
  }
  function _hidePanel() {
    const p = document.getElementById('co-panel-reseau'); if (p) p.style.display = 'none';
    const l = document.getElementById('po-outils-liste'); if (l) l.style.display = '';
  }

  async function _fillBvSelect() {
    const sel = document.getElementById('co-reseau-bv');
    if (!sel || sel.dataset.filled === '1') return;
    try {
      const d = await fetch('/carte/api/couche/bv_ouvrage_tete/liste/').then(r => r.json());
      sel.innerHTML = (d.options || []).map(o => `<option value="${o.pk}">${o.label}</option>`).join('');
      sel.dataset.filled = '1';
    } catch (e) { console.error('[couches] bv liste', e); }
  }

  function _openReseauPanel(couche) {
    _currentReseau = couche;
    const meta = window.COUCHES_META[couche] || {};
    const lbl = document.getElementById('co-reseau-label');
    if (lbl) lbl.value = meta.label || couche;
    _showPanel();
    _fillBvSelect();
  }

  function _removeReseau() {
    if (!window.MAP) return;
    if (MAP.getLayer(LYR)) MAP.removeLayer(LYR);
    if (MAP.getSource(SRC)) MAP.removeSource(SRC);
  }

  // Bbox d'une FeatureCollection de lignes (cadrage carte).
  function _fcBounds(fc) {
    let mnx = Infinity, mny = Infinity, mxx = -Infinity, mxy = -Infinity;
    for (const f of (fc.features || [])) {
      const g = f.geometry; if (!g) continue;
      const cs = g.type === 'MultiLineString' ? g.coordinates.flat() : g.coordinates;
      for (const c of (cs || [])) {
        mnx = Math.min(mnx, c[0]); mny = Math.min(mny, c[1]);
        mxx = Math.max(mxx, c[0]); mxy = Math.max(mxy, c[1]);
      }
    }
    return (mnx < mxx) ? [[mnx, mny], [mxx, mxy]] : null;
  }

  async function _afficherReseau() {
    const resEl = document.getElementById('co-reseau-result');
    const bv    = document.getElementById('co-reseau-bv').value;
    const grid  = document.getElementById('co-reseau-grid').value;
    if (!_currentReseau || !bv || !window.MAP) return;
    resEl.innerHTML = '<span class="po-muted"><i class="fas fa-spinner fa-spin"></i> Chargement…</span>';
    try {
      let url = `/carte/api/reseau-ouvrage-tete/?reseau=${encodeURIComponent(_currentReseau)}&bv=${encodeURIComponent(bv)}`;
      if (grid !== '') url += `&min_grid_code=${encodeURIComponent(grid)}`;
      const d = await fetch(url).then(r => r.json());
      const feats = d.features || [];
      if (!feats.length) {
        if (window.CarteRendu) CarteRendu.clear('contexte'); else _removeReseau();
        resEl.innerHTML = `<span class="po-err"><i class="fas fa-exclamation-triangle"></i> Aucun tronçon de ce réseau dans le BV « ${d.bv || ''} ».</span>`;
        document.getElementById('co-reseau-clear').style.display = 'none';
        return;
      }
      _removeReseau();
      MAP.addSource(SRC, { type: 'geojson', data: d, tolerance: 0 });
      const gmax = Math.max(1, d.grid_max || 1);
      const width = ['interpolate', ['linear'], ['coalesce', ['get', 'grid_code'], 0], 0, 0.6, gmax, 3.4];
      const color = ['interpolate', ['linear'], ['coalesce', ['get', 'grid_code'], 0], 0, '#9cccd6', gmax, '#1d4ed8'];
      MAP.addLayer({ id: LYR, type: 'line', source: SRC, paint: { 'line-color': color, 'line-width': width } });

      CarteRendu.set('contexte', {
        outil: `Réseau du BV — ${d.bv}`,
        legende: `<div style="font-size:10.5px;color:#444">${feats.length} tronçon(s) · réseau gradué par grid_code (max ${d.grid_max ?? '—'})</div>`,
        cleanup: _removeReseau,
      });

      const b = _fcBounds(d);
      if (b) MAP.fitBounds(b, { padding: 60, duration: 600 });

      resEl.innerHTML = `<span class="po-ok"><i class="fas fa-check-circle"></i> ${feats.length} tronçon(s) — BV ${d.bv}.</span>`;
      document.getElementById('co-reseau-clear').style.display = '';
    } catch (err) {
      resEl.innerHTML = `<span class="po-err">Erreur : ${err.message}</span>`;
    }
  }

  function _clearReseau() {
    if (window.CarteRendu) CarteRendu.clear('contexte'); else _removeReseau();
    const c = document.getElementById('co-reseau-clear'); if (c) c.style.display = 'none';
    const r = document.getElementById('co-reseau-result'); if (r) r.innerHTML = '';
  }

  // ── Init ───────────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('co-hydro2')?.addEventListener('click', _toggleHydro2);
    document.querySelectorAll('.co-back').forEach(b => b.addEventListener('click', _hidePanel));
    document.getElementById('co-reseau-exec')?.addEventListener('click', _afficherReseau);
    document.getElementById('co-reseau-clear')?.addEventListener('click', _clearReseau);

    // Délégation : bouton « Réseau du BV » des lignes réseau injectées.
    document.getElementById('couches-liste')?.addEventListener('click', (e) => {
      const btn = e.target.closest('.couche-inter-btn');
      if (!btn) return;
      e.preventDefault();
      e.stopPropagation();
      _openReseauPanel(btn.dataset.couche);
    });
  });

})();
