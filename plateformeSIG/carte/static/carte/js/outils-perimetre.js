/**
 * outils-perimetre.js — Panneau droit « Outils » : outils périmètre
 *
 * Outil « Besoin » — affiche le volume de besoin des périmètres sur la carte
 * selon plusieurs modes de présentation :
 *
 *   point_valeur : cercle classé (quantiles) + valeur au centre
 *   cercle_prop  : cercle proportionnel à la valeur (taille graduée continue)
 *   camembert    : diagramme circulaire des 3 années (humide/normale/sèche)
 *   choroplethe  : aplat de couleur sur le polygone du périmètre (par classe)
 *
 * Données : endpoint /carte/api/perimetres/besoin/ (point_on_surface + valeurs).
 * Rendu des points/camemberts via maplibregl.Marker (élément DOM → toujours
 * au-dessus du canvas) ; le choroplèthe colore la couche WebGL lyr-perimetres.
 * window.getBesoinOverlay() expose les marqueurs pour la capture du Layout.
 *
 * Dépend de :
 *   map.js       → window.MAP, maplibregl
 *   selection.js → window.selection_par_couche, window.selection_active
 *   layers.js    → couche « perimetres » chargée (pour le mode choroplèthe)
 */
'use strict';

(function () {

  const ANNEE_LABEL = { humide: 'humide', normale: 'normale', seche: 'sèche' };

  // Classification (point_valeur / choroplèthe) — rampe faible → fort
  const RAMP  = ['#27ae60', '#f1c40f', '#e67e22', '#e74c3c', '#8e44ad'];
  const SIZES = [34, 40, 46, 54, 62];

  // Camembert — couleur par type d'année
  const YEAR_COLORS = { humide: '#2980b9', normale: '#27ae60', seche: '#e67e22' };
  // Diagramme en barres — palette jaune / orange / bordeaux
  const BAR_COLORS  = { humide: '#f1c40f', normale: '#e67e22', seche: '#8e1f3d' };

  const PERIM_LAYER = 'lyr-perimetres';

  // Tampons remplis par les renderers, transmis ensuite à CarteRendu (slot
  // 'resultat'). Le gestionnaire central gère l'ajout/retrait et la restauration
  // des peintures → aucun désordre entre outils carte.
  let _pendingMarkers = [];   // maplibregl.Marker ajoutés au rendu courant
  let _pendingOverlay = [];   // items {type, coord, ...} pour la capture PDF
  let _pendingPaints  = [];   // [{layer, prop, value}] (mode choroplèthe)

  // Rétro-compat : layout.js privilégie CarteRendu.getOverlay().
  window.getBesoinOverlay = () =>
    (window.CarteRendu ? CarteRendu.getOverlay() : _pendingOverlay);

  // ── Navigation liste ⇄ sous-panneau ─────────────────────────────────────

  function _showBesoinPanel() {
    document.getElementById('po-outils-liste').style.display = 'none';
    document.getElementById('po-panel-besoin').style.display = 'flex';
    _updateCount();
  }

  function _hideBesoinPanel() {
    document.getElementById('po-panel-besoin').style.display = 'none';
    document.getElementById('po-outils-liste').style.display = '';
  }

  // ── Navigation liste ⇄ sous-panneau « Comparaison besoin » ───────────────

  function _showCompPanel() {
    document.getElementById('po-outils-liste').style.display = 'none';
    document.getElementById('po-panel-comparaison').style.display = 'flex';
    _updateCount();
  }

  function _hideCompPanel() {
    document.getElementById('po-panel-comparaison').style.display = 'none';
    document.getElementById('po-outils-liste').style.display = '';
  }

  // ── Fenêtre flottante de comparaison (multi-instances via FloatingChart) ──

  const COMP_COL = { besoin: '#2980b9', excedent: '#27ae60', deficit: '#e74c3c' };
  const _fmtFr = v => Number(v || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });

  // Récupère les données et dessine le graphe dans une nouvelle fenêtre flottante.
  // (Lot C, point 3 : chaque exécution ouvre sa propre fenêtre — pas d'écrasement.)
  async function _execComparaison() {
    const annee = document.getElementById('po-comp-annee').value;
    const pks   = _selectedPerimetrePks();
    if (!window.FloatingChart) return;

    const win = FloatingChart.open({
      titre: 'Comparaison besoin', icone: 'fa-chart-column',
      sousTitre: `année ${ANNEE_LABEL[annee] || annee}`,
    });

    let url = `/carte/api/perimetres/comparaison-besoin/?annee=${encodeURIComponent(annee)}`;
    if (pks.length) url += `&pks=${pks.slice(0, COMP_MAX).join(',')}`;

    try {
      const resp = await fetch(url);
      if (!resp.ok) {
        const e = await resp.json().catch(() => ({}));
        throw new Error(e.erreur || `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      const rows = data.perimetres || [];

      if (!rows.length) {
        win.setStatus(`<span class="cb-err"><i class="fas fa-exclamation-triangle"></i>
          Aucune valeur de besoin (année ${ANNEE_LABEL[annee]}) pour
          ${pks.length ? 'la sélection' : 'cette couche'}.</span>`);
        return;
      }

      // Largeur du graphe ∝ nombre de périmètres (scroll horizontal au besoin)
      win.drawChart({
        type: 'bar',
        data: {
          labels: rows.map(r => r.nom),
          datasets: [
            { label: 'Besoin',   data: rows.map(r => r.besoin),   backgroundColor: COMP_COL.besoin },
            { label: 'Excédent', data: rows.map(r => r.excedent), backgroundColor: COMP_COL.excedent },
            { label: 'Déficit',  data: rows.map(r => r.deficit),  backgroundColor: COMP_COL.deficit },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { position: 'top', labels: { usePointStyle: true, boxWidth: 8, font: { family: 'Inter', size: 11 } } },
            tooltip: { callbacks: { label: ctx => `${ctx.dataset.label} : ${_fmtFr(ctx.parsed.y)} m³` } },
          },
          scales: {
            x: { grid: { display: false }, ticks: { font: { family: 'Inter', size: 10 }, maxRotation: 60, autoSkip: false } },
            y: { beginAtZero: true, ticks: { font: { family: 'Inter', size: 10 }, callback: v => _fmtFr(v) } },
          },
        },
      }, Math.max(0, rows.length * 96));

      const note = data.tronque
        ? ` <span class="cb-warn">(${data.total} trouvés — ${COMP_MAX} premiers affichés)</span>`
        : '';
      win.setStatus(`<span class="cb-ok"><i class="fas fa-check-circle"></i>
        ${rows.length} périmètre${rows.length > 1 ? 's' : ''} — année ${ANNEE_LABEL[annee]} (m³).</span>${note}`);
    } catch (err) {
      win.setStatus(`<span class="cb-err">Erreur : ${err.message}</span>`);
      console.error('[outils-perimetre] comparaison :', err);
    }
  }

  // ── Compteur de périmètres sélectionnés ─────────────────────────────────

  function _selectedPerimetrePks() {
    const parCouche = window.selection_par_couche || {};
    if (parCouche.perimetres?.length) return parCouche.perimetres.map(Number);
    if (window.couche_active === 'perimetres' && window.selection_active?.length) {
      return window.selection_active.map(Number);
    }
    return [];
  }

  const COMP_MAX = 25;   // plafond de l'outil « Comparaison besoin »

  function _updateCount() {
    const n = _selectedPerimetrePks().length;
    const txt = n
      ? `${n} périmètre${n > 1 ? 's' : ''} sélectionné${n > 1 ? 's' : ''}`
      : '0 — toute la couche';

    const besoinInput = document.getElementById('po-besoin-count');
    if (besoinInput) besoinInput.value = txt;

    const compInput = document.getElementById('po-comp-count');
    if (compInput) compInput.value = txt;

    const compWarn = document.getElementById('po-comp-warn');
    if (compWarn) compWarn.style.display = n > COMP_MAX ? '' : 'none';
  }

  document.addEventListener('carte:selectionChange', _updateCount);

  // ── Format ───────────────────────────────────────────────────────────────

  function _fmtCompact(v) {
    const abs = Math.abs(v);
    if (abs >= 1e6) return (v / 1e6).toFixed(2) + 'M';
    if (abs >= 1e3) return (v / 1e3).toFixed(1) + 'k';
    return String(Math.round(v));
  }

  // ── Classification par quantiles ─────────────────────────────────────────

  function _quantileBreaks(vals, nClasses = 5) {
    const sorted = [...vals].sort((a, b) => a - b);
    const nDistinct = new Set(sorted).size;
    const n = Math.max(1, Math.min(nClasses, nDistinct));
    const breaks = [];
    for (let i = 1; i <= n; i++) {
      const idx = Math.min(sorted.length - 1, Math.ceil((i * sorted.length) / n) - 1);
      breaks.push(sorted[idx]);
    }
    breaks[breaks.length - 1] = sorted[sorted.length - 1];
    const out = [];
    for (const b of breaks) if (!out.length || b > out[out.length - 1]) out.push(b);
    return out;
  }

  function _classIndex(v, breaks) {
    for (let i = 0; i < breaks.length; i++) if (v <= breaks[i]) return i;
    return breaks.length - 1;
  }

  function _classStyle(nClasses) {
    if (nClasses === 1) return { colors: [RAMP[2]], sizes: [SIZES[2]] };
    const colors = [], sizes = [];
    for (let i = 0; i < nClasses; i++) {
      const j = Math.round((i / (nClasses - 1)) * (RAMP.length - 1));
      colors.push(RAMP[j]);
      sizes.push(SIZES[j]);
    }
    return { colors, sizes };
  }

  // Taille proportionnelle (perception par l'aire → racine carrée)
  function _propSize(v, vmin, vmax, minPx = 30, maxPx = 66) {
    if (vmax <= vmin) return (minPx + maxPx) / 2;
    const t = Math.sqrt((v - vmin) / (vmax - vmin));
    return Math.round(minPx + t * (maxPx - minPx));
  }

  // ── Nettoyage ────────────────────────────────────────────────────────────

  // Réinitialise les tampons avant un nouveau rendu (n'efface PAS la carte —
  // c'est CarteRendu.set('resultat', …) qui remplace le rendu précédent).
  function _resetBuffers() {
    _pendingMarkers = [];
    _pendingOverlay = [];
    _pendingPaints  = [];
  }

  function _clearAll() {
    if (window.CarteRendu) CarteRendu.clear('resultat');
  }

  // ── Construction des marqueurs (cercle ou camembert) ─────────────────────

  function _circleEl(item) {
    const el = document.createElement('div');
    el.className = 'besoin-marker';
    el.title = item.title || item.label;
    Object.assign(el.style, {
      width: item.size + 'px', height: item.size + 'px', borderRadius: '50%',
      background: item.color, border: '2.5px solid #fff',
      boxShadow: '0 1px 4px rgba(0,0,0,.4)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      color: '#fff', fontWeight: '700', fontFamily: "'Inter', sans-serif",
      fontSize: Math.max(10, Math.round(item.size * 0.30)) + 'px',
      textShadow: '0 1px 2px rgba(0,0,0,.45)', cursor: 'pointer',
      userSelect: 'none', lineHeight: '1',
    });
    el.textContent = item.label;
    return el;
  }

  function _pieSvgPaths(size, slices) {
    const r = size / 2, cx = r, cy = r;
    const total = slices.reduce((s, x) => s + Math.max(0, x.value), 0) || 1;
    let a0 = -Math.PI / 2, paths = '', activeOutline = '';
    for (const s of slices) {
      const frac = Math.max(0, s.value) / total;
      if (frac <= 0) continue;
      if (frac >= 0.999) {
        paths += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${s.color}"/>`;
        if (s.active) {
          activeOutline = `<circle cx="${cx}" cy="${cy}" r="${r - 1.5}" `
                        + `fill="none" stroke="#fff" stroke-width="3"/>`;
        }
        continue;
      }
      const a1 = a0 + frac * 2 * Math.PI;
      const x0 = cx + r * Math.cos(a0), y0 = cy + r * Math.sin(a0);
      const x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1);
      const large = frac > 0.5 ? 1 : 0;
      const d = `M${cx},${cy} L${x0.toFixed(2)},${y0.toFixed(2)} `
              + `A${r},${r} 0 ${large} 1 ${x1.toFixed(2)},${y1.toFixed(2)} Z`;
      paths += `<path d="${d}" fill="${s.color}"/>`;
      // Contour blanc de la part de l'année affichée (dessiné au-dessus)
      if (s.active) {
        activeOutline = `<path d="${d}" fill="none" stroke="#fff" `
                      + `stroke-width="3" stroke-linejoin="round"/>`;
      }
      a0 = a1;
    }
    return { fills: paths, activeOutline };
  }

  function _pieEl(item) {
    const el = document.createElement('div');
    el.className = 'besoin-marker';
    el.title = item.title || '';
    el.style.cursor = 'pointer';
    const r = item.size / 2;
    const holeR = r * 0.54;
    const fs = Math.max(8, Math.round(item.size * 0.22));
    const { fills, activeOutline } = _pieSvgPaths(item.size, item.slices);
    el.innerHTML = `<svg width="${item.size}" height="${item.size}"
      viewBox="0 0 ${item.size} ${item.size}" style="display:block;
      filter:drop-shadow(0 1px 3px rgba(0,0,0,.4))">
      ${fills}
      <circle cx="${r}" cy="${r}" r="${r - 1}" fill="none" stroke="#fff" stroke-width="2"/>
      ${activeOutline}
      <circle cx="${r}" cy="${r}" r="${holeR}" fill="#fff"/>
      <text x="${r}" y="${r}" text-anchor="middle" dominant-baseline="central"
            font-family="Inter, sans-serif" font-weight="700" font-size="${fs}"
            fill="#1A1A2E">${item.label ?? ''}</text>
    </svg>`;
    return el;
  }

  function _barsEl(item) {
    const el = document.createElement('div');
    el.className = 'besoin-marker';
    el.title = item.title || '';
    el.style.cursor = 'pointer';
    const w = item.size;
    const H = item.size * 1.05;          // hauteur totale (en-tête + barres)
    const headerH = H * 0.34;            // bande supérieure pour la valeur
    const chartH  = H - headerH;
    const bars = item.bars;
    const maxV = Math.max(...bars.map(b => Math.max(0, b.value)), 1);
    const n = bars.length, gap = w * 0.12, bw = (w - gap * (n + 1)) / n;
    const fs = Math.max(8, Math.round(item.size * 0.26));

    let rects = '';
    bars.forEach((b, i) => {
      const bh = Math.max(2, (Math.max(0, b.value) / maxV) * (chartH - 4));
      const x  = gap + i * (bw + gap);
      const y  = H - bh - 1.5;
      // Contour foncé sur la barre de l'année affichée (lisible sur le carton blanc)
      const stroke = b.active ? ' stroke="#1A1A2E" stroke-width="2"' : '';
      rects += `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" `
             + `width="${bw.toFixed(1)}" height="${bh.toFixed(1)}" rx="1.5" `
             + `fill="${b.color}"${stroke}/>`;
    });

    el.innerHTML = `<svg width="${w}" height="${H}" viewBox="0 0 ${w} ${H}"
      style="display:block;filter:drop-shadow(0 1px 2px rgba(0,0,0,.35))">
      <rect x="0" y="0" width="${w}" height="${H}" rx="4"
            fill="rgba(255,255,255,.88)" stroke="#fff" stroke-width="1"/>
      <text x="${w / 2}" y="${headerH / 2}" text-anchor="middle" dominant-baseline="central"
            font-family="Inter, sans-serif" font-weight="700" font-size="${fs}"
            fill="#1A1A2E">${item.label ?? ''}</text>
      ${rects}
    </svg>`;
    return el;
  }

  function _labelEl(item) {
    const el = document.createElement('div');
    el.className = 'besoin-marker';
    el.title = item.title || item.label;
    Object.assign(el.style, {
      color: '#ffffff', fontWeight: '800', fontFamily: "'Inter', sans-serif",
      fontSize: '12px', whiteSpace: 'nowrap', cursor: 'pointer', userSelect: 'none',
      textShadow: '0 0 3px rgba(0,0,0,.9), 0 1px 2px rgba(0,0,0,.9)',
    });
    el.textContent = item.label;
    return el;
  }

  function _addMarkers(items) {
    for (const it of items) {
      const el = it.type === 'pie'   ? _pieEl(it)
               : it.type === 'bars'  ? _barsEl(it)
               : it.type === 'label' ? _labelEl(it)
               : _circleEl(it);
      const marker = new maplibregl.Marker({ element: el, anchor: 'center' })
        .setLngLat(it.coord)
        .addTo(MAP);
      _pendingMarkers.push(marker);
    }
    _pendingOverlay = _pendingOverlay.concat(items);
  }

  function _fitTo(points) {
    if (points.length === 1) {
      MAP.flyTo({ center: points[0].coord, zoom: Math.max(MAP.getZoom(), 11), duration: 600 });
    } else {
      const lons = points.map(p => p.coord[0]);
      const lats = points.map(p => p.coord[1]);
      MAP.fitBounds(
        [[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]],
        { padding: 90, maxZoom: 12, duration: 600 }
      );
    }
  }

  // ── Légendes (panneau) ───────────────────────────────────────────────────

  function _legendBox(titre, rowsHtml) {
    return `
      <div style="margin-top:8px;padding-top:6px;border-top:1px solid #eddfc8">
        <p style="font-size:10px;font-weight:700;text-transform:uppercase;
                  letter-spacing:.05em;color:var(--c-muted);margin:0 0 4px">${titre}</p>
        ${rowsHtml}
      </div>`;
  }

  function _dot(color, sw = 13, ring = false) {
    // ring = true → anneau d'accent foncé (année affichée)
    const shadow = ring ? '0 0 0 1px #fff, 0 0 0 3px #1A1A2E' : '0 0 0 1px #ccc';
    return `<span style="width:${sw}px;height:${sw}px;border-radius:50%;
      background:${color};border:1.5px solid #fff;box-shadow:${shadow};
      flex-shrink:0"></span>`;
  }

  function _legendClasses(breaks, colors, sizes, counts, vmin) {
    const rows = breaks.map((b, i) => {
      const lo = i === 0 ? vmin : breaks[i - 1];
      const sw = Math.max(10, Math.min(Math.round((sizes?.[i] ?? 26) * 0.4), 18));
      return `<div style="display:flex;align-items:center;gap:7px;margin:3px 0">
        ${_dot(colors[i], sw)}
        <span style="font-size:10.5px;color:#444">${_fmtCompact(lo)} – ${_fmtCompact(b)} m³</span>
        <span style="font-size:10px;color:var(--c-muted);margin-left:auto">${counts[i]} pér.</span>
      </div>`;
    }).join('');
    return _legendBox('Classes (quantiles)', rows);
  }

  function _legendYears(colors = YEAR_COLORS, titre = 'Parts du camembert', annee = null) {
    const rows = ['humide', 'normale', 'seche'].map(y => {
      const actif = y === annee;
      const badge = actif
        ? `<span style="margin-left:auto;font-size:9px;font-weight:700;
             text-transform:uppercase;letter-spacing:.04em;color:#1A1A2E;
             background:#f0a500;border-radius:3px;padding:1px 5px">affichée</span>`
        : '';
      return `<div style="display:flex;align-items:center;gap:7px;margin:3px 0">
        ${_dot(colors[y], 13, actif)}
        <span style="font-size:10.5px;color:#444;font-weight:${actif ? 700 : 400}">Année ${ANNEE_LABEL[y]}</span>
        ${badge}
      </div>`;
    }).join('');
    return _legendBox(titre, rows);
  }

  function _legendProp(vmin, vmax) {
    const rows = `
      <div style="display:flex;align-items:flex-end;gap:14px;padding:4px 2px">
        <div style="text-align:center">
          ${_dot('#2980b9', 14)}
          <div style="font-size:10px;color:#444;margin-top:3px">${_fmtCompact(vmin)}</div>
        </div>
        <div style="text-align:center">
          ${_dot('#2980b9', 26)}
          <div style="font-size:10px;color:#444;margin-top:3px">${_fmtCompact(vmax)}</div>
        </div>
        <span style="font-size:10px;color:var(--c-muted);align-self:center">m³</span>
      </div>`;
    return _legendBox('Cercle proportionnel', rows);
  }

  // ── Modes de rendu ───────────────────────────────────────────────────────

  function _renderPointValeur(points) {
    const vals = points.map(p => p.value);
    const vmin = Math.min(...vals);
    const breaks = _quantileBreaks(vals, 5);
    const { colors, sizes } = _classStyle(breaks.length);
    const counts = new Array(breaks.length).fill(0);

    const items = points.map(p => {
      const ci = _classIndex(p.value, breaks);
      counts[ci]++;
      return {
        type: 'circle', coord: p.coord, label: _fmtCompact(p.value),
        color: colors[ci], size: sizes[ci],
        title: `${p.nom} — ${Number(p.value).toLocaleString('fr')} m³`,
      };
    });

    _addMarkers(items);
    _fitTo(points);
    return _legendClasses(breaks, colors, sizes, counts, vmin);
  }

  function _renderCercleProp(points) {
    const vals = points.map(p => p.value);
    const vmin = Math.min(...vals), vmax = Math.max(...vals);

    const items = points.map(p => ({
      type: 'circle', coord: p.coord, label: _fmtCompact(p.value),
      color: '#2980b9', size: _propSize(p.value, vmin, vmax),
      title: `${p.nom} — ${Number(p.value).toLocaleString('fr')} m³`,
    }));

    _addMarkers(items);
    _fitTo(points);
    return _legendProp(vmin, vmax);
  }

  function _renderCamembert(points, annee) {
    // Taille du camembert ∝ total des 3 années ; la part de l'année
    // sélectionnée (= valeur affichée au centre) est mise en évidence.
    const totals = points.map(p =>
      (p.v_humide || 0) + (p.v_normale || 0) + (p.v_seche || 0));
    const tmin = Math.min(...totals), tmax = Math.max(...totals);

    const items = points.map((p, i) => ({
      type: 'pie', coord: p.coord, size: _propSize(totals[i], tmin, tmax, 38, 74),
      label: _fmtCompact(p.value),
      slices: [
        { value: p.v_humide  || 0, color: YEAR_COLORS.humide,  year: 'humide',  active: annee === 'humide' },
        { value: p.v_normale || 0, color: YEAR_COLORS.normale, year: 'normale', active: annee === 'normale' },
        { value: p.v_seche   || 0, color: YEAR_COLORS.seche,   year: 'seche',   active: annee === 'seche' },
      ],
      title: `${p.nom}\nHumide ${_fmtCompact(p.v_humide || 0)} · `
           + `Normale ${_fmtCompact(p.v_normale || 0)} · `
           + `Sèche ${_fmtCompact(p.v_seche || 0)} m³`,
    }));

    _addMarkers(items);
    _fitTo(points);
    return _legendYears(YEAR_COLORS, 'Parts du camembert', annee);
  }

  function _renderBarres(points, annee) {
    // Taille du graphe ∝ total des 3 années ; la barre de l'année
    // sélectionnée (= valeur affichée en en-tête) est mise en évidence.
    const totals = points.map(p =>
      (p.v_humide || 0) + (p.v_normale || 0) + (p.v_seche || 0));
    const tmin = Math.min(...totals), tmax = Math.max(...totals);

    const items = points.map((p, i) => ({
      type: 'bars', coord: p.coord, size: _propSize(totals[i], tmin, tmax, 36, 64),
      label: _fmtCompact(p.value),
      bars: [
        { value: p.v_humide  || 0, color: BAR_COLORS.humide,  year: 'humide',  active: annee === 'humide' },
        { value: p.v_normale || 0, color: BAR_COLORS.normale, year: 'normale', active: annee === 'normale' },
        { value: p.v_seche   || 0, color: BAR_COLORS.seche,   year: 'seche',   active: annee === 'seche' },
      ],
      title: `${p.nom}\nHumide ${_fmtCompact(p.v_humide || 0)} · `
           + `Normale ${_fmtCompact(p.v_normale || 0)} · `
           + `Sèche ${_fmtCompact(p.v_seche || 0)} m³`,
    }));

    _addMarkers(items);
    _fitTo(points);
    return _legendYears(BAR_COLORS, 'Barres (années)', annee);
  }

  function _renderChoroplethe(points) {
    if (!window.MAP?.getLayer(PERIM_LAYER)) {
      return `<div style="margin-top:8px"><span class="po-err">
        <i class="fas fa-exclamation-triangle"></i>
        Activez d'abord la couche « Périmètres agricoles » dans le panneau gauche
        pour le mode aplat de couleur.</span></div>`;
    }

    const vals = points.map(p => p.value);
    const vmin = Math.min(...vals);
    const breaks = _quantileBreaks(vals, 5);
    const { colors } = _classStyle(breaks.length);
    const counts = new Array(breaks.length).fill(0);

    // Expression MapLibre : match sur l'id de l'entité → couleur de classe
    const pairs = [];
    for (const p of points) {
      const ci = _classIndex(p.value, breaks);
      counts[ci]++;
      pairs.push(Number(p.pk), colors[ci]);
    }
    const expr = ['match', ['id'], ...pairs, '#d8d2c4'];

    // Peintures transmises à CarteRendu (sauvegarde/restauration centralisées)
    _pendingPaints.push(
      { layer: PERIM_LAYER, prop: 'fill-color',   value: expr },
      { layer: PERIM_LAYER, prop: 'fill-opacity', value: 0.78 },
    );

    // Étiquettes de valeur au centre de chaque polygone
    _addMarkers(points.map(p => ({
      type: 'label', coord: p.coord, label: _fmtCompact(p.value),
      title: `${p.nom} — ${Number(p.value).toLocaleString('fr')} m³`,
    })));

    _fitTo(points);
    return _legendClasses(breaks, colors, null, counts, vmin);
  }

  const _RENDERERS = {
    point_valeur: _renderPointValeur,
    cercle_prop:  _renderCercleProp,
    camembert:    _renderCamembert,
    barres:       _renderBarres,
    choroplethe:  _renderChoroplethe,
  };

  // ── Exécution ────────────────────────────────────────────────────────────

  async function _executer() {
    const resEl = document.getElementById('po-besoin-result');
    const annee = document.getElementById('po-besoin-annee').value;
    const mode  = document.getElementById('po-besoin-mode').value;
    if (!window.MAP) return;

    resEl.innerHTML = '<span class="po-muted"><i class="fas fa-spinner fa-spin"></i> Chargement…</span>';

    const pks = _selectedPerimetrePks();
    let url = `/carte/api/perimetres/besoin/?annee=${encodeURIComponent(annee)}`;
    if (pks.length) url += `&pks=${pks.join(',')}`;

    try {
      const resp = await fetch(url);
      if (!resp.ok) {
        const e = await resp.json().catch(() => ({}));
        throw new Error(e.erreur || `HTTP ${resp.status}`);
      }
      const data = await resp.json();

      const points = (data.features ?? []).map(f => ({
        coord:     f.geometry.coordinates,
        pk:        f.properties.pk,
        nom:       f.properties.nom,
        value:     f.properties.value,
        v_humide:  f.properties.v_humide,
        v_normale: f.properties.v_normale,
        v_seche:   f.properties.v_seche,
      }));

      _resetBuffers();

      if (!points.length) {
        _clearAll();
        resEl.innerHTML =
          `<span class="po-err"><i class="fas fa-exclamation-triangle"></i>
           Aucune valeur de besoin (année ${ANNEE_LABEL[annee]}) renseignée
           pour ${pks.length ? 'la sélection' : 'cette couche'}.</span>`;
        document.getElementById('po-besoin-clear').style.display = 'none';
        return;
      }

      const legend = (_RENDERERS[mode] || _renderPointValeur)(points, annee);

      if (window.CarteRendu) {
        CarteRendu.set('resultat', {
          outil:   `Besoin — année ${ANNEE_LABEL[annee]}`,
          markers: _pendingMarkers,
          choro:   _pendingPaints,
          overlay: _pendingOverlay,
          legende: legend,
        });
      }

      resEl.innerHTML =
        `<span class="po-ok"><i class="fas fa-check-circle"></i>
         ${points.length} périmètre${points.length > 1 ? 's' : ''} affiché${points.length > 1 ? 's' : ''}
         (année ${ANNEE_LABEL[annee]}, m³).</span>` + legend;
      document.getElementById('po-besoin-clear').style.display = '';
    } catch (err) {
      resEl.innerHTML = `<span class="po-err">Erreur : ${err.message}</span>`;
      console.error('[outils-perimetre] besoin :', err);
    }
  }

  // ── Init ─────────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('po-besoin')?.addEventListener('click', _showBesoinPanel);
    document.getElementById('po-besoin-back')?.addEventListener('click', _hideBesoinPanel);
    document.getElementById('po-besoin-exec')?.addEventListener('click', _executer);
    document.getElementById('po-besoin-clear')?.addEventListener('click', () => {
      _clearAll();
      document.getElementById('po-besoin-clear').style.display = 'none';
      document.getElementById('po-besoin-result').innerHTML = '';
    });

    // Outil « Comparaison besoin » (fenêtre flottante dans la carte)
    document.getElementById('po-comparaison')?.addEventListener('click', _showCompPanel);
    document.getElementById('po-comp-back')?.addEventListener('click', _hideCompPanel);
    document.getElementById('po-comp-exec')?.addEventListener('click', _execComparaison);
  });

})();
