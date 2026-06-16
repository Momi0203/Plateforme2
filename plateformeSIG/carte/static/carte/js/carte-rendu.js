/**
 * carte-rendu.js — Gestionnaire central des rendus thématiques sur la carte.
 *
 * Objectif : afficher les résultats des outils « carte » SANS désordre entre eux
 * (marqueurs superposés, recolorations WebGL concurrentes, légendes empilées).
 *
 * Deux emplacements (slots) qui cohabitent proprement :
 *   - 'contexte' : fond contextuel (ex. Bassins versants + réseau)
 *   - 'resultat' : thématique d'un outil (Besoin, Indice de priorité, Crue…)
 *
 * Règle : un seul contenu par slot. Réécrire un slot efface automatiquement
 * l'ancien (retrait des marqueurs + restauration des peintures WebGL).
 *
 * API publique (window.CarteRendu) :
 *   set(slot, { outil, markers, choro, overlay, legende })
 *       markers : maplibregl.Marker[] déjà ajoutés à la carte (tracés pour retrait)
 *       choro   : [{ layer, prop, value }] — peintures à appliquer (sauvegardées
 *                 puis restaurées automatiquement)
 *       overlay : items {type, coord, …} exposés pour la capture Layout/PDF
 *       legende : HTML affiché dans la légende unifiée sur la carte
 *   clear(slot) · clearAll() · getOverlay()
 *
 * Dépend de : map.js (window.MAP, maplibregl).
 */
'use strict';

window.CarteRendu = (function () {

  const SLOTS = ['contexte', 'resultat'];
  const SLOT_LABEL = { contexte: 'Contexte', resultat: 'Résultat' };

  // slot -> { outil, markers:[], saved:[{layer, prop, value}], overlay:[], legende:'' }
  const _state = { contexte: null, resultat: null };

  // ── Peintures WebGL (sauvegarde / restauration) ──────────────────────────

  function _applyPaints(paints) {
    const saved = [];
    if (!window.MAP) return saved;
    for (const p of (paints || [])) {
      if (!p || !MAP.getLayer(p.layer)) continue;
      // Mémoriser la valeur courante AVANT modification (pour restauration).
      saved.push({ layer: p.layer, prop: p.prop, value: MAP.getPaintProperty(p.layer, p.prop) });
      MAP.setPaintProperty(p.layer, p.prop, p.value);
    }
    return saved;
  }

  function _restorePaints(saved) {
    if (!window.MAP || !saved) return;
    // Restaurer dans l'ordre inverse de l'application.
    for (let i = saved.length - 1; i >= 0; i--) {
      const s = saved[i];
      if (MAP.getLayer(s.layer)) MAP.setPaintProperty(s.layer, s.prop, s.value);
    }
  }

  // ── Légende unifiée (un seul bloc sur la carte) ──────────────────────────

  function _renderLegende() {
    const box = document.getElementById('carte-rendu-legende');
    if (!box) return;

    const actifs = SLOTS.filter(s => _state[s]);
    if (!actifs.length) {
      box.style.display = 'none';
      box.innerHTML = '';
      return;
    }

    box.style.display = 'block';
    box.innerHTML = actifs.map(slot => {
      const st = _state[slot];
      return `<div class="cr-bloc">
        <div class="cr-head">
          <span class="cr-tag cr-tag-${slot}">${SLOT_LABEL[slot]}</span>
          <span class="cr-titre" title="${(st.outil || '').replace(/"/g, '&quot;')}">${st.outil || '—'}</span>
          <button class="cr-x" data-clear="${slot}" title="Effacer">&times;</button>
        </div>
        ${st.legende ? `<div class="cr-corps">${st.legende}</div>` : ''}
      </div>`;
    }).join('') +
    (actifs.length > 1 ? `<button class="cr-all" data-clear-all="1">Tout effacer</button>` : '');

    box.querySelectorAll('[data-clear]').forEach(btn =>
      btn.addEventListener('click', () => clear(btn.getAttribute('data-clear'))));
    box.querySelector('[data-clear-all]')?.addEventListener('click', clearAll);
  }

  // ── API ───────────────────────────────────────────────────────────────────

  function set(slot, payload) {
    if (!SLOTS.includes(slot)) {
      console.warn('[CarteRendu] slot inconnu :', slot);
      return;
    }
    payload = payload || {};
    clear(slot);                                   // efface le contenu précédent du slot
    _state[slot] = {
      outil:   payload.outil   || '',
      markers: payload.markers || [],
      saved:   _applyPaints(payload.choro),
      overlay: payload.overlay || [],
      legende: payload.legende || '',
      cleanup: typeof payload.cleanup === 'function' ? payload.cleanup : null,
    };
    _renderLegende();
  }

  function clear(slot) {
    const st = _state[slot];
    if (!st) return;
    (st.markers || []).forEach(m => { try { m.remove(); } catch (e) {} });
    _restorePaints(st.saved);
    // Nettoyage des couches/sources MapLibre ajoutées par l'outil (ex. BV + réseau).
    if (st.cleanup) { try { st.cleanup(); } catch (e) { console.warn('[CarteRendu] cleanup :', e); } }
    _state[slot] = null;
    _renderLegende();
  }

  function clearAll() {
    SLOTS.forEach(clear);
  }

  // Concatène les overlays actifs (pour la capture Layout/PDF — layout.js).
  function getOverlay() {
    let out = [];
    for (const slot of SLOTS) if (_state[slot]) out = out.concat(_state[slot].overlay || []);
    return out;
  }

  function isActive(slot) {
    return slot ? !!_state[slot] : SLOTS.some(s => _state[s]);
  }

  return { set, clear, clearAll, getOverlay, isActive };

})();
