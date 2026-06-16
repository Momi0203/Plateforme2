/**
 * outils-commun.js — Socle transversal des outils du panneau droit (Lot A).
 *
 * Fournit deux briques partagées par tous les outils (boxes Hydrologie, Bilan,
 * Efficience, Diagnostic, Périmètre) :
 *
 *   window.OutilsSel     — sélection carte unifiée (remplace les menus déroulants)
 *                          patron : outil « Besoin ». Lit window.selection_par_couche.
 *
 *   window.FloatingChart — fabrique de fenêtres flottantes Chart.js. Chaque appel
 *                          .open() crée UNE NOUVELLE fenêtre (cascade, illimité) ;
 *                          relancer un outil n'écrase plus le graphe précédent.
 *
 * Dépend de :
 *   selection.js → window.selection_par_couche, évènement carte:selectionChange
 *   layers.js    → window.COUCHES_META (libellés)
 *   Chart.js     → fenêtres graphiques
 */
'use strict';

(function () {

  // ════════════════════════════════════════════════════════════════════════
  //  OutilsSel — sélection sur la carte (par couche)
  // ════════════════════════════════════════════════════════════════════════
  // « Sélection vide = toute la couche » (convention de l'outil Besoin).

  window.OutilsSel = {

    /** PKs sélectionnés sur la couche donnée (tableau d'entiers ; [] si aucun). */
    pks(couche) {
      const parCouche = window.selection_par_couche || {};
      return (parCouche[couche] || []).map(Number);
    },

    /** Nombre d'entités sélectionnées sur la couche. */
    count(couche) {
      return this.pks(couche).length;
    },

    /** Libellé lisible de la couche (depuis COUCHES_META), repli sur la clé. */
    label(couche) {
      return (window.COUCHES_META && window.COUCHES_META[couche] &&
              window.COUCHES_META[couche].label) || couche;
    },

    /** Couche chargée (visible / interrogeable) sur la carte ? */
    estChargee(couche) {
      return !!(window.LOADED_LAYERS && window.LOADED_LAYERS.has &&
                window.LOADED_LAYERS.has(couche));
    },

    /**
     * Texte du compteur lecture seule (style « Besoin »).
     *   - 0          → « 0 — toute la couche »
     *   - n          → « n entité(s) sélectionnée(s) »
     *   - n>plafond  → suffixe « (max N traités) »
     */
    texte(couche, opts) {
      opts = opts || {};
      const n = this.count(couche);
      if (!n) return '0 — toute la couche';
      let t = `${n} entité${n > 1 ? 's' : ''} sélectionnée${n > 1 ? 's' : ''}`;
      if (opts.plafond && n > opts.plafond) t += ` (max ${opts.plafond} traités)`;
      return t;
    },

    /**
     * Branche un <input readonly> sur la sélection d'une couche : il se met à
     * jour à chaque carte:selectionChange.
     *   inputId   : id de l'input
     *   couche    : nom de couche (string) OU fonction () => string (couche dynamique)
     *   opts      : { plafond }
     * Retourne la fonction de rafraîchissement (utile pour la rappeler à la main).
     */
    bindCount(inputId, couche, opts) {
      opts = opts || {};
      const resoudre = () => (typeof couche === 'function' ? couche() : couche);
      const maj = () => {
        const el = document.getElementById(inputId);
        if (!el) return;
        const c = resoudre();
        el.value = c ? this.texte(c, opts) : '0 — toute la couche';
      };
      document.addEventListener('carte:selectionChange', maj);
      maj();
      return maj;
    },
  };


  // ════════════════════════════════════════════════════════════════════════
  //  FloatingChart — fenêtres flottantes Chart.js (multi-instances, cascade)
  // ════════════════════════════════════════════════════════════════════════

  let _seq      = 0;        // identifiant unique de fenêtre
  let _zTop     = 1400;     // z-index courant (réutilise la base de .cb-window)
  const _wins   = new Set();  // fenêtres ouvertes (pour « Fermer toutes »)
  const _CASCADE = 26;      // décalage en pixels entre fenêtres successives

  function _majBoutonFermerTout() {
    const btn = document.getElementById('fc-close-all');
    if (btn) btn.style.display = _wins.size ? '' : 'none';
  }

  /** Rend l'en-tête d'une fenêtre déplaçable (souris). */
  function _rendreDeplacable(win, head) {
    let sx, sy, ox, oy, dragging = false;
    head.addEventListener('mousedown', (e) => {
      if (e.target.closest('.cb-window-btn')) return;   // pas sur la croix
      dragging = true;
      const r = win.getBoundingClientRect();
      win.style.left = r.left + 'px';
      win.style.top  = r.top + 'px';
      win.style.transform = 'none';
      sx = e.clientX; sy = e.clientY; ox = r.left; oy = r.top;
      _amenerAuPremierPlan(win);
      e.preventDefault();
    });
    document.addEventListener('mousemove', (e) => {
      if (!dragging) return;
      let nx = ox + e.clientX - sx;
      let ny = oy + e.clientY - sy;
      nx = Math.min(Math.max(nx, -(win.offsetWidth - 120)), window.innerWidth - 120);
      ny = Math.min(Math.max(ny, 56), window.innerHeight - 40);
      win.style.left = nx + 'px';
      win.style.top  = ny + 'px';
    });
    document.addEventListener('mouseup', () => { dragging = false; });
  }

  function _amenerAuPremierPlan(win) {
    win.style.zIndex = String(++_zTop);
  }

  /**
   * Ouvre une nouvelle fenêtre flottante.
   *   opts : { titre, sousTitre, icone }   (icone = classe Font Awesome, défaut fa-chart-bar)
   * Retourne un handle :
   *   { el, id, setStatus(html), setSousTitre(txt), drawChart(config, minWidth), close() }
   */
  function open(opts) {
    opts = opts || {};
    const id     = ++_seq;
    const icone  = opts.icone || 'fa-chart-bar';

    const win = document.createElement('div');
    win.className = 'cb-window fc-window';
    win.id = 'fc-window-' + id;
    win.style.zIndex = String(++_zTop);

    // Position en cascade (sans le centrage translateX de .cb-window)
    const offset = ((_wins.size) % 8) * _CASCADE;
    win.style.left = `calc(50% - 320px + ${offset}px)`;
    win.style.top  = (88 + offset) + 'px';
    win.style.transform = 'none';

    win.innerHTML = `
      <div class="cb-window-head" id="fc-head-${id}">
        <span class="cb-window-title">
          <i class="fas ${icone}"></i>
          <span class="fc-title">${opts.titre || 'Graphique'}</span>
          <span class="fc-soustitre" style="font-weight:400;color:#cbb;margin-left:4px"></span>
        </span>
        <button class="cb-window-btn fc-close" title="Fermer">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="cb-window-body">
        <div class="cb-window-status fc-status"></div>
        <div class="cb-window-chart-scroll">
          <div class="cb-window-chart fc-chart">
            <canvas></canvas>
          </div>
        </div>
      </div>`;

    document.body.appendChild(win);
    _wins.add(win);
    _majBoutonFermerTout();

    const head    = win.querySelector('.cb-window-head');
    const statusEl = win.querySelector('.fc-status');
    const chartEl  = win.querySelector('.fc-chart');
    const canvas   = win.querySelector('canvas');
    const soustEl  = win.querySelector('.fc-soustitre');

    _rendreDeplacable(win, head);
    win.addEventListener('mousedown', () => _amenerAuPremierPlan(win));

    let chart = null;

    function close() {
      if (chart) { chart.destroy(); chart = null; }
      win.remove();
      _wins.delete(win);
      _majBoutonFermerTout();
    }

    win.querySelector('.fc-close').addEventListener('click', close);

    if (opts.sousTitre) soustEl.textContent = opts.sousTitre;
    // État initial : « Chargement… »
    statusEl.innerHTML = '<span class="cb-muted"><i class="fas fa-spinner fa-spin"></i> Chargement…</span>';

    return {
      el: win,
      id,
      setStatus(html)     { statusEl.innerHTML = html; },
      setSousTitre(txt)   { soustEl.textContent = txt || ''; },
      drawChart(config, minWidth) {
        chartEl.style.minWidth = (minWidth || 0) + 'px';
        if (chart) chart.destroy();
        chart = new Chart(canvas, config);
        return chart;
      },
      close,
    };
  }

  function closeAll() {
    // copie : close() modifie _wins pendant l'itération
    [..._wins].forEach(win => {
      const btn = win.querySelector('.fc-close');
      if (btn) btn.click();
    });
  }

  window.FloatingChart = { open, closeAll, get count() { return _wins.size; } };

  // ── Bouton « Fermer toutes les fenêtres » (en-tête du panneau droit) ──────
  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('fc-close-all');
    if (btn) {
      btn.style.display = 'none';
      btn.addEventListener('click', closeAll);
    }
  });

  // ── Constantes utiles aux outils (axes Chart.js homogènes) ────────────────
  window.OutilsChart = {
    AXIS_FONT: { family: 'Inter', size: 10 },
    LEGEND: { position: 'top', labels: { usePointStyle: true, boxWidth: 8, font: { family: 'Inter', size: 11 } } },
    // Palette stable pour les séries multi-entités (point 2)
    SERIES_COLORS: [
      '#2980b9', '#27ae60', '#e67e22', '#8e44ad', '#c0392b', '#16a085',
      '#f1c40f', '#2c3e50', '#d35400', '#7f8c8d', '#e84393', '#00cec9',
      '#6c5ce7', '#fdcb6e', '#00b894', '#0984e3', '#b71540', '#079992',
      '#eb2f06', '#1e3799', '#38ada9', '#e58e26', '#b8860b', '#4a69bd', '#60a3bc',
    ],
    couleur(i) { return this.SERIES_COLORS[i % this.SERIES_COLORS.length]; },
  };

})();
