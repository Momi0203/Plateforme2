/**
 * export.js — Bouton « Export carte » : capture MapLibre + PDF via ReportLab côté serveur.
 *
 * Flux :
 *   1. Capture MAP.getCanvas().toDataURL('image/png')
 *   2. Récupère MAP.getBounds() pour la barre d'échelle
 *   3. Construit legende_items depuis les couches visibles (COUCHES_META + LAYER_GROUP_COLORS)
 *   4. POST /carte/api/export/carte/  → PDF blob
 *   5. Déclenche téléchargement navigateur
 *
 * Dépend de :
 *   map.js    → window.MAP
 *   layers.js → window.LOADED_LAYERS, window.COUCHES_META,
 *               window.LAYER_GROUP_COLORS, window.LAYER_COLOR_FALLBACK
 *   query.js  → getCsrf()
 */

'use strict';

// ── Légende depuis couches visibles ───────────────────────────────────────────

function _exportLegendItems() {
  const gc  = window.LAYER_GROUP_COLORS  ?? {};
  const fb  = window.LAYER_COLOR_FALLBACK ?? '#7f8c8d';
  const out = [];
  for (const nom of (window.LOADED_LAYERS ?? [])) {
    try {
      if (MAP.getLayoutProperty(`lyr-${nom}`, 'visibility') === 'none') continue;
    } catch (_) { continue; }
    const meta = window.COUCHES_META[nom] ?? {};
    out.push({
      label:     meta.label     ?? nom,
      color:     gc[meta.groupe] ?? fb,
      geom_type: meta.geom_type  ?? 'Geometry',
    });
  }
  return out;
}

// ── Panel toggle ──────────────────────────────────────────────────────────────

function _showExportPanel()  { document.getElementById('export-carte-panel').style.display = 'block'; }
function _hideExportPanel()  { document.getElementById('export-carte-panel').style.display = 'none';  }
function _clearExportError() {
  const el = document.getElementById('export-erreur');
  if (el) el.style.display = 'none';
}

// ── Téléchargement ────────────────────────────────────────────────────────────

async function exportCartePDF() {
  const btnDl   = document.getElementById('btn-export-telecharger');
  const spinner = document.getElementById('export-spinner');

  btnDl.disabled     = true;
  btnDl.textContent  = 'Génération…';
  if (spinner) spinner.style.display = 'inline-block';
  _clearExportError();

  try {
    // ── Capture carte ────────────────────────────────────────────────────────
    const mapCanvas = MAP.getCanvas();
    const mapImage  = mapCanvas.toDataURL('image/png');

    const bounds = MAP.getBounds();
    const bbox   = [
      bounds.getWest(), bounds.getSouth(),
      bounds.getEast(), bounds.getNorth(),
    ];

    // ── Lire le formulaire ───────────────────────────────────────────────────
    const fmt     = document.getElementById('export-format')?.value      ?? 'A4';
    const ori     = document.getElementById('export-orientation')?.value ?? 'landscape';
    const dpi     = parseInt(document.getElementById('export-dpi')?.value ?? '150', 10);
    const titreCb = document.getElementById('export-titre-cb')?.checked ?? true;
    const titre   = titreCb ? (document.getElementById('export-titre')?.value?.trim() ?? '') : '';

    const chkLegende  = document.getElementById('export-legende')?.checked  ?? true;
    const chkNord     = document.getElementById('export-nord')?.checked      ?? true;
    const chkEchelle  = document.getElementById('export-echelle')?.checked   ?? true;
    const chkDate     = document.getElementById('export-date')?.checked      ?? true;

    const body = {
      format:        fmt,
      orientation:   ori,
      dpi,
      map_image:     mapImage,
      bbox,
      legende_items: chkLegende ? _exportLegendItems() : [],
      elements: {
        titre,
        legende: chkLegende,
        nord:    chkNord,
        echelle: chkEchelle,
        date:    chkDate,
      },
    };

    // ── POST vers Django ─────────────────────────────────────────────────────
    const resp = await fetch('/carte/api/export/carte/', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body:    JSON.stringify(body),
    });

    if (!resp.ok) {
      let msg = resp.statusText;
      try { const j = await resp.json(); msg = j.erreur ?? msg; } catch (_) {}
      throw new Error(msg);
    }

    // ── Déclenche téléchargement ─────────────────────────────────────────────
    const blob = await resp.blob();
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), {
      href:     url,
      download: `carte_${fmt.toLowerCase()}_${ori}.pdf`,
    });
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    _hideExportPanel();

  } catch (err) {
    const errEl = document.getElementById('export-erreur');
    if (errEl) {
      errEl.textContent   = `Erreur : ${err.message}`;
      errEl.style.display = 'block';
    }
  } finally {
    btnDl.disabled    = false;
    btnDl.innerHTML   = '<i class="fas fa-download"></i> Télécharger';
    if (spinner) spinner.style.display = 'none';
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────

function initExportCarte() {
  const btnToggle = document.getElementById('btn-export-carte');
  const panel     = document.getElementById('export-carte-panel');
  if (!btnToggle || !panel) return;

  // Ouvre / ferme le panel
  btnToggle.addEventListener('click', e => {
    e.stopPropagation();
    const open = panel.style.display !== 'none';
    if (open) _hideExportPanel();
    else       _showExportPanel();
  });

  // Ferme en cliquant hors du panel
  document.addEventListener('click', e => {
    if (panel.style.display === 'none') return;
    if (!panel.contains(e.target) && e.target !== btnToggle) _hideExportPanel();
  });

  document.getElementById('btn-export-fermer')
    ?.addEventListener('click', _hideExportPanel);

  document.getElementById('btn-export-telecharger')
    ?.addEventListener('click', exportCartePDF);

  // Active/désactive le champ titre selon la case
  const titreCb    = document.getElementById('export-titre-cb');
  const titreInput = document.getElementById('export-titre');
  titreCb?.addEventListener('change', () => {
    if (titreInput) titreInput.disabled = !titreCb.checked;
  });

  // Efface l'erreur quand l'utilisateur modifie le formulaire
  panel.querySelectorAll('select, input').forEach(el =>
    el.addEventListener('change', _clearExportError)
  );

  // Masquer le bouton PDF pour les visiteurs (Phase 2 §5)
  if (typeof window.minRole === 'function' && !window.minRole('operateur')) {
    btnToggle.style.display = 'none';
    panel.style.display     = 'none';
  }
}
