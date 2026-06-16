'use strict';

// ── FEATURE-C4 : Compositeur de mise en page / exportation PDF ─────────────
// Écoute carte:layoutOpen → capture la carte MapLibre → génère un aperçu
// canvas → envoie POST /carte/api/export/carte/ → déclenche téléchargement PDF.

(function () {

  let _captured = null; // {dataUrl, bbox, loadedLayers}

  // ──────────────────────────────────────────────────────────────────────────
  //  Helpers
  // ──────────────────────────────────────────────────────────────────────────

  function _el(id) { return document.getElementById(id); }

  function _getParams() {
    return {
      format:      _el('lc-format')?.value      || 'A4',
      orientation: _el('lc-orientation')?.value || 'paysage',
      dpi:         parseInt(_el('lc-dpi')?.value || '150', 10),
      titre:       (_el('lc-titre')?.value       || '').trim(),
      sous_titre:  (_el('lc-sous-titre')?.value  || '').trim(),
      source:      (_el('lc-source')?.value      || '').trim(),
      logos: {
        hydroplan_icone: !!_el('lc-logo-hydroplan_icone')?.checked,
        hydroplan_texte: !!_el('lc-logo-hydroplan_texte')?.checked,
        sgiat:           !!_el('lc-logo-sgiat')?.checked,
        iav:             !!_el('lc-logo-iav')?.checked,
      },
      show_legende: !!_el('lc-elem-legende')?.checked,
      show_nord:    !!_el('lc-elem-nord')?.checked,
      show_echelle: !!_el('lc-elem-echelle')?.checked,
      show_cadre:   !!_el('lc-elem-cadre')?.checked,
    };
  }

  // ──────────────────────────────────────────────────────────────────────────
  //  Légende — construite depuis LOADED_LAYERS + COUCHES_META + couleurs
  // ──────────────────────────────────────────────────────────────────────────

  function _buildLegend() {
    const meta   = window.COUCHES_META   || {};
    const colors = window.LAYER_GROUP_COLORS || {};
    const loaded = window.LOADED_LAYERS  || [];
    const items  = [];

    loaded.forEach(couche => {
      const m = meta[couche];
      if (!m) return;
      const grp   = m.groupe || couche;
      const label = m.label  || couche;
      const color = colors[grp] || window.LAYER_COLOR_FALLBACK || '#888888';
      items.push({ label, color, geom_type: m.geom_type || 'point' });
    });

    return items;
  }

  // ──────────────────────────────────────────────────────────────────────────
  //  Capture de la carte
  // ──────────────────────────────────────────────────────────────────────────

  function _capture() {
    const map = window.MAP;
    if (!map) {
      _setStatus('error', 'Carte non disponible — activez l\'onglet Carte d\'abord.');
      return;
    }
    try {
      // Forcer un rendu synchrone avant la lecture du buffer
      map.triggerRepaint?.();
      const canvas   = map.getCanvas();
      const baseUrl  = canvas.toDataURL('image/png');
      const bounds   = map.getBounds();
      const bbox     = [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()];
      const loaded   = window.LOADED_LAYERS ? [...window.LOADED_LAYERS] : [];

      // Marqueurs HTML (rendus thématiques) non inclus dans le canvas WebGL :
      // on les dessine par-dessus l'image capturée. Source : gestionnaire
      // central CarteRendu (repli sur l'ancien getBesoinOverlay).
      const overlay = (window.CarteRendu && typeof CarteRendu.getOverlay === 'function')
        ? CarteRendu.getOverlay()
        : (typeof window.getBesoinOverlay === 'function' ? window.getBesoinOverlay() : []);

      _compositeOverlay(baseUrl, canvas, overlay, dataUrl => {
        _captured = { dataUrl, bbox, loadedLayers: loaded };
        _drawPreview(dataUrl);
        _setStatus('ok', 'Carte capturée. Renseignez les options puis cliquez sur Générer PDF.');
      });
    } catch (e) {
      _setStatus('error', 'Impossible de capturer la carte : ' + e.message);
    }
  }

  // Dessine les marqueurs « Besoin » (cercle coloré + valeur) sur l'image
  // capturée, à leur position projetée. cb reçoit le dataURL composité.
  function _compositeOverlay(baseUrl, mapCanvas, overlay, cb) {
    const img = new Image();
    img.onload = () => {
      try {
        const c   = document.createElement('canvas');
        c.width   = img.width;
        c.height  = img.height;
        const ctx = c.getContext('2d');
        ctx.drawImage(img, 0, 0);

        if (overlay && overlay.length && window.MAP) {
          // Canvas en pixels physiques, project() en pixels CSS → facteur d'échelle
          const scaleX = mapCanvas.width  / mapCanvas.clientWidth;
          const scaleY = mapCanvas.height / mapCanvas.clientHeight;
          const scale  = (scaleX + scaleY) / 2;

          for (const p of overlay) {
            const pt = window.MAP.project(p.coord);
            const x  = pt.x * scaleX;
            const y  = pt.y * scaleY;
            const r  = (p.size / 2) * scale;

            if (p.type === 'pie') {
              // Camembert : une part par année
              const total = (p.slices || []).reduce((s, sl) => s + Math.max(0, sl.value), 0) || 1;
              let a0 = -Math.PI / 2;
              let activeArc = null;
              for (const sl of (p.slices || [])) {
                const frac = Math.max(0, sl.value) / total;
                if (frac <= 0) continue;
                const a1 = a0 + frac * 2 * Math.PI;
                ctx.beginPath();
                ctx.moveTo(x, y);
                ctx.arc(x, y, r, a0, a1);
                ctx.closePath();
                ctx.fillStyle = sl.color;
                ctx.fill();
                if (sl.active) activeArc = [a0, a1];
                a0 = a1;
              }
              ctx.beginPath();
              ctx.arc(x, y, r, 0, 2 * Math.PI);
              ctx.lineWidth   = 2 * scale;
              ctx.strokeStyle = '#ffffff';
              ctx.stroke();

              // Contour blanc de la part de l'année affichée (le trou la masque au centre)
              if (activeArc) {
                ctx.beginPath();
                ctx.moveTo(x, y);
                ctx.arc(x, y, r, activeArc[0], activeArc[1]);
                ctx.closePath();
                ctx.lineWidth   = 3 * scale;
                ctx.strokeStyle = '#ffffff';
                ctx.stroke();
              }

              // Donut : trou central + valeur
              if (p.label) {
                ctx.beginPath();
                ctx.arc(x, y, r * 0.54, 0, 2 * Math.PI);
                ctx.fillStyle = '#ffffff';
                ctx.fill();
                ctx.fillStyle    = '#1A1A2E';
                ctx.font         = `700 ${Math.max(8, Math.round(p.size * 0.22)) * scale}px Inter, Arial, sans-serif`;
                ctx.textAlign    = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(p.label, x, y);
              }
              continue;
            }

            if (p.type === 'bars') {
              // Diagramme en barres : en-tête (valeur) + une barre par année
              const w       = p.size * scale;
              const H       = p.size * 1.05 * scale;
              const headerH = H * 0.34;
              const chartH  = H - headerH;
              const x0  = x - w / 2;
              const y0  = y - H / 2;
              const bars = p.bars || [];
              const maxV = Math.max(...bars.map(b => Math.max(0, b.value)), 1);
              const n   = bars.length;
              const gap = w * 0.12;
              const bw  = (w - gap * (n + 1)) / n;

              ctx.fillStyle   = 'rgba(255,255,255,0.88)';
              ctx.strokeStyle = '#ffffff';
              ctx.lineWidth   = 1 * scale;
              ctx.beginPath();
              ctx.rect(x0, y0, w, H);
              ctx.fill();
              ctx.stroke();

              bars.forEach((b, i) => {
                const bh = Math.max(2 * scale, (Math.max(0, b.value) / maxV) * (chartH - 4 * scale));
                const bx = x0 + gap + i * (bw + gap);
                const by = y0 + H - bh - 1.5 * scale;
                ctx.fillStyle = b.color;
                ctx.fillRect(bx, by, bw, bh);
                // Contour foncé sur la barre de l'année affichée
                if (b.active) {
                  ctx.lineWidth   = 2 * scale;
                  ctx.strokeStyle = '#1A1A2E';
                  ctx.strokeRect(bx, by, bw, bh);
                }
              });

              if (p.label) {
                ctx.fillStyle    = '#1A1A2E';
                ctx.font         = `700 ${Math.max(8, Math.round(p.size * 0.26)) * scale}px Inter, Arial, sans-serif`;
                ctx.textAlign    = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(p.label, x0 + w / 2, y0 + headerH / 2);
              }
              continue;
            }

            if (p.type === 'label') {
              // Étiquette de valeur seule (choroplèthe)
              ctx.font         = `800 ${12 * scale}px Inter, Arial, sans-serif`;
              ctx.textAlign    = 'center';
              ctx.textBaseline = 'middle';
              ctx.lineWidth    = 3 * scale;
              ctx.strokeStyle  = 'rgba(0,0,0,0.9)';
              ctx.strokeText(p.label, x, y);
              ctx.fillStyle    = '#ffffff';
              ctx.fillText(p.label, x, y);
              continue;
            }

            // Cercle (point selon valeur / cercle proportionnel)
            ctx.beginPath();
            ctx.arc(x, y, r, 0, 2 * Math.PI);
            ctx.fillStyle   = p.color;
            ctx.fill();
            ctx.lineWidth   = 2.5 * scale;
            ctx.strokeStyle = '#ffffff';
            ctx.stroke();

            ctx.fillStyle    = '#ffffff';
            ctx.font         = `700 ${Math.max(10, Math.round(p.size * 0.30)) * scale}px Inter, Arial, sans-serif`;
            ctx.textAlign    = 'center';
            ctx.textBaseline = 'middle';
            ctx.shadowColor  = 'rgba(0,0,0,0.45)';
            ctx.shadowBlur   = 2 * scale;
            ctx.fillText(p.label, x, y);
            ctx.shadowColor  = 'transparent';
            ctx.shadowBlur   = 0;
          }
        }
        cb(c.toDataURL('image/png'));
      } catch (e) {
        cb(baseUrl);   // repli : image sans marqueurs
      }
    };
    img.onerror = () => cb(baseUrl);
    img.src = baseUrl;
  }

  function _drawPreview(dataUrl) {
    const previewCanvas = _el('lc-preview-canvas');
    const placeholder   = _el('lc-preview-placeholder');
    if (!previewCanvas) return;

    const img = new Image();
    img.onload = () => {
      const maxW = previewCanvas.parentElement?.clientWidth  || 600;
      const maxH = previewCanvas.parentElement?.clientHeight || 400;
      const ratio = Math.min(maxW / img.width, maxH / img.height, 1);
      previewCanvas.width  = img.width  * ratio;
      previewCanvas.height = img.height * ratio;
      const ctx = previewCanvas.getContext('2d');
      ctx.drawImage(img, 0, 0, previewCanvas.width, previewCanvas.height);
      previewCanvas.style.display = 'block';
      if (placeholder) placeholder.style.display = 'none';

      // Info dimensions
      const info = _el('lc-preview-info');
      if (info) info.textContent = `${img.width}×${img.height} px`;
    };
    img.src = dataUrl;
  }

  // ──────────────────────────────────────────────────────────────────────────
  //  Génération PDF
  // ──────────────────────────────────────────────────────────────────────────

  async function _generatePdf() {
    if (!_captured) {
      _setStatus('error', 'Capturez d\'abord la carte avant de générer le PDF.');
      return;
    }

    const btn = _el('lc-btn-pdf');
    const params = _getParams();

    _setStatus('loading', 'Génération en cours…');
    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> En cours…'; }

    const legend = params.show_legende ? _buildLegend() : [];

    const payload = {
      image_base64: _captured.dataUrl.replace(/^data:image\/\w+;base64,/, ''),
      bbox:         _captured.bbox,
      format:       params.format,
      orientation:  params.orientation,
      titre:        params.titre,
      sous_titre:   params.sous_titre,
      source:       params.source,
      logos:        params.logos,
      show_legende: params.show_legende,
      show_nord:    params.show_nord,
      show_echelle: params.show_echelle,
      show_cadre:   params.show_cadre,
      legend_items: legend,
      dpi:          params.dpi,
    };

    try {
      const resp = await fetch('/carte/api/export/carte/', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
        body:    JSON.stringify(payload),
      });

      if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(`HTTP ${resp.status} — ${txt.slice(0, 200)}`);
      }

      const blob     = await resp.blob();
      const url      = URL.createObjectURL(blob);
      const a        = document.createElement('a');
      const titre    = params.titre || 'carte';
      a.href         = url;
      a.download     = titre.replace(/[^a-zA-Z0-9_\-]/g, '_').toLowerCase() + '.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      _setStatus('ok', 'PDF généré et téléchargé.');
    } catch (e) {
      _setStatus('error', 'Erreur : ' + e.message);
    } finally {
      if (btn) {
        btn.disabled = !window.minRole || window.minRole('operateur') ? false : true;
        btn.innerHTML = '<i class="fas fa-file-pdf"></i> Générer PDF';
      }
    }
  }

  // ──────────────────────────────────────────────────────────────────────────
  //  Status helper
  // ──────────────────────────────────────────────────────────────────────────

  function _setStatus(type, msg) {
    const el = _el('lc-status');
    if (!el) return;
    el.style.display = '';
    el.className = 'lc-status lc-status-' + type;
    const icons = { ok: 'fa-check-circle', error: 'fa-exclamation-circle', loading: 'fa-spinner fa-spin' };
    el.innerHTML = `<i class="fas ${icons[type] || 'fa-info-circle'}"></i> ${msg}`;
  }

  // ──────────────────────────────────────────────────────────────────────────
  //  Gestion du rôle (visiteur ne peut pas générer PDF)
  // ──────────────────────────────────────────────────────────────────────────

  function _applyRoleGating() {
    const btn = _el('lc-btn-pdf');
    if (!btn) return;
    const isOp = window.minRole ? window.minRole('operateur') : true;
    if (!isOp) {
      btn.disabled = true;
      btn.title = 'Réservé aux opérateurs et éditeurs.';
      btn.innerHTML = '<i class="fas fa-lock"></i> PDF (accès restreint)';
    }
  }

  // ──────────────────────────────────────────────────────────────────────────
  //  Écoute de l'ouverture de l'onglet Layout
  // ──────────────────────────────────────────────────────────────────────────

  document.addEventListener('carte:layoutOpen', () => {
    // Si la carte a bougé depuis la dernière capture, proposer de recapturer
    const info = _el('lc-preview-info');
    if (!_captured && info) info.textContent = '';

    // Re-vérifier le rôle à chaque ouverture (session change)
    _applyRoleGating();
  });

  // ──────────────────────────────────────────────────────────────────────────
  //  Entrée publique
  // ──────────────────────────────────────────────────────────────────────────

  window.initLayout = function initLayout() {
    // Bouton Capturer
    const btnCapture = _el('lc-btn-capture');
    if (btnCapture) btnCapture.addEventListener('click', _capture);

    // Bouton Générer PDF
    const btnPdf = _el('lc-btn-pdf');
    if (btnPdf) btnPdf.addEventListener('click', _generatePdf);

    // Gating initial
    _applyRoleGating();
  };

}());
