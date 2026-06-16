/**
 * outils-rendu.js — Primitives de rendu « carte » (Module A), mutualisées (Lot A).
 *
 * Extraites de outils-perimetre.js (outil Besoin) pour être réutilisées par tous
 * les outils carte qui proposent un choix de mode de présentation (point 4) :
 * Crue de projet, Taux de couverture, Débit mobilisé, Rendement tronçons…
 *
 * Expose window.RenduCarte :
 *   - classification : quantileBreaks, classIndex, classStyle, propSize
 *   - marqueurs DOM  : circleEl, pieEl, barsEl, labelEl
 *   - aides carte    : addMarkers(map, items) -> {markers, overlay}, fitTo(map, points)
 *   - légendes       : legendBox, dot, legendClasses, legendProp
 *   - format         : fmtCompact
 *
 * Les marqueurs sont des éléments DOM (maplibregl.Marker) — toujours au-dessus du
 * canvas WebGL, et recomposables par layout.js (capture PDF via CarteRendu).
 *
 * Dépend de : maplibregl (map.js).
 */
'use strict';

(function () {

  // Rampe de couleurs faible → fort + tailles associées (cercles classés).
  const RAMP  = ['#27ae60', '#f1c40f', '#e67e22', '#e74c3c', '#8e44ad'];
  const SIZES = [34, 40, 46, 54, 62];

  // ── Format compact ─────────────────────────────────────────────────────────

  function fmtCompact(v) {
    const abs = Math.abs(v);
    if (abs >= 1e6) return (v / 1e6).toFixed(2) + 'M';
    if (abs >= 1e3) return (v / 1e3).toFixed(1) + 'k';
    return String(Math.round(v));
  }

  // ── Classification par quantiles ────────────────────────────────────────────

  function quantileBreaks(vals, nClasses = 5) {
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

  function classIndex(v, breaks) {
    for (let i = 0; i < breaks.length; i++) if (v <= breaks[i]) return i;
    return breaks.length - 1;
  }

  function classStyle(nClasses) {
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
  function propSize(v, vmin, vmax, minPx = 30, maxPx = 66) {
    if (vmax <= vmin) return (minPx + maxPx) / 2;
    const t = Math.sqrt((v - vmin) / (vmax - vmin));
    return Math.round(minPx + t * (maxPx - minPx));
  }

  // ── Marqueurs DOM ────────────────────────────────────────────────────────────

  function circleEl(item) {
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
      if (s.active) {
        activeOutline = `<path d="${d}" fill="none" stroke="#fff" `
                      + `stroke-width="3" stroke-linejoin="round"/>`;
      }
      a0 = a1;
    }
    return { fills: paths, activeOutline };
  }

  function pieEl(item) {
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

  function barsEl(item) {
    const el = document.createElement('div');
    el.className = 'besoin-marker';
    el.title = item.title || '';
    el.style.cursor = 'pointer';
    const w = item.size;
    const H = item.size * 1.05;
    const headerH = H * 0.34;
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

  function labelEl(item) {
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

  /**
   * Ajoute les marqueurs DOM des items sur la carte.
   *   item.type ∈ { 'circle' (défaut), 'pie', 'bars', 'label' }
   * Retourne { markers, overlay } à transmettre à CarteRendu.set('resultat', …).
   */
  function addMarkers(map, items) {
    const markers = [];
    for (const it of items) {
      const el = it.type === 'pie'   ? pieEl(it)
               : it.type === 'bars'  ? barsEl(it)
               : it.type === 'label' ? labelEl(it)
               : circleEl(it);
      const marker = new maplibregl.Marker({ element: el, anchor: 'center' })
        .setLngLat(it.coord)
        .addTo(map);
      markers.push(marker);
    }
    return { markers, overlay: items };
  }

  function fitTo(map, points) {
    if (!points.length) return;
    if (points.length === 1) {
      map.flyTo({ center: points[0].coord, zoom: Math.max(map.getZoom(), 11), duration: 600 });
    } else {
      const lons = points.map(p => p.coord[0]);
      const lats = points.map(p => p.coord[1]);
      map.fitBounds(
        [[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]],
        { padding: 90, maxZoom: 12, duration: 600 }
      );
    }
  }

  // ── Légendes (HTML, pour CarteRendu / panneau) ───────────────────────────────

  function legendBox(titre, rowsHtml) {
    return `
      <div style="margin-top:8px;padding-top:6px;border-top:1px solid #eddfc8">
        <p style="font-size:10px;font-weight:700;text-transform:uppercase;
                  letter-spacing:.05em;color:var(--c-muted);margin:0 0 4px">${titre}</p>
        ${rowsHtml}
      </div>`;
  }

  function dot(color, sw = 13, ring = false) {
    const shadow = ring ? '0 0 0 1px #fff, 0 0 0 3px #1A1A2E' : '0 0 0 1px #ccc';
    return `<span style="width:${sw}px;height:${sw}px;border-radius:50%;
      background:${color};border:1.5px solid #fff;box-shadow:${shadow};
      flex-shrink:0"></span>`;
  }

  function legendClasses(breaks, colors, sizes, counts, vmin, unite = '') {
    const u = unite ? ' ' + unite : '';
    const rows = breaks.map((b, i) => {
      const lo = i === 0 ? vmin : breaks[i - 1];
      const sw = Math.max(10, Math.min(Math.round((sizes?.[i] ?? 26) * 0.4), 18));
      return `<div style="display:flex;align-items:center;gap:7px;margin:3px 0">
        ${dot(colors[i], sw)}
        <span style="font-size:10.5px;color:#444">${fmtCompact(lo)} – ${fmtCompact(b)}${u}</span>
        <span style="font-size:10px;color:var(--c-muted);margin-left:auto">${counts[i]}</span>
      </div>`;
    }).join('');
    return legendBox('Classes (quantiles)', rows);
  }

  function legendProp(vmin, vmax, unite = '') {
    const rows = `
      <div style="display:flex;align-items:flex-end;gap:14px;padding:4px 2px">
        <div style="text-align:center">
          ${dot('#2980b9', 14)}
          <div style="font-size:10px;color:#444;margin-top:3px">${fmtCompact(vmin)}</div>
        </div>
        <div style="text-align:center">
          ${dot('#2980b9', 26)}
          <div style="font-size:10px;color:#444;margin-top:3px">${fmtCompact(vmax)}</div>
        </div>
        <span style="font-size:10px;color:var(--c-muted);align-self:center">${unite}</span>
      </div>`;
    return legendBox('Cercle proportionnel', rows);
  }

  // ── Renderer thématique générique (Lot D, point 4) ──────────────────────────
  // Rend une couche de points selon le mode choisi et renvoie de quoi alimenter
  // CarteRendu.set('resultat', …).
  //
  //   points : [{ coord:[lng,lat], value:Number, nom:String, pk?:Number }]
  //   opts   : {
  //     mode             : 'cercle_prop' | 'point_valeur' | 'choroplethe',
  //     unite            : '' (libellé d'unité pour les légendes),
  //     color            : couleur des cercles proportionnels (#2980b9),
  //     choroLayer       : id de couche WebGL polygone (mode choroplethe),
  //     choroProp        : 'fill-color' (défaut),
  //     choroOpacityProp : 'fill-opacity' (défaut),
  //     choroErreur      : message si la couche polygone n'est pas chargée
  //   }
  // Retourne { markers, overlay, paints, legende } ou { erreur } (mode choroplethe
  // sans couche polygone disponible).
  function renderThematique(map, points, opts = {}) {
    const mode  = opts.mode || 'cercle_prop';
    const unite = opts.unite || '';
    const color = opts.color || '#2980b9';
    const vals  = points.map(p => p.value);
    const vmin  = Math.min(...vals), vmax = Math.max(...vals);
    let items = [], paints = [], legende = '';

    if (mode === 'point_valeur') {
      const breaks = quantileBreaks(vals, 5);
      const { colors, sizes } = classStyle(breaks.length);
      const counts = new Array(breaks.length).fill(0);
      items = points.map(p => {
        const ci = classIndex(p.value, breaks); counts[ci]++;
        return {
          type: 'circle', coord: p.coord, label: fmtCompact(p.value),
          color: colors[ci], size: sizes[ci],
          title: `${p.nom} — ${Number(p.value).toLocaleString('fr')} ${unite}`,
        };
      });
      legende = legendClasses(breaks, colors, sizes, counts, vmin, unite);

    } else if (mode === 'choroplethe') {
      if (!opts.choroLayer || !map.getLayer || !map.getLayer(opts.choroLayer)) {
        return { erreur: opts.choroErreur || 'Activez la couche polygone correspondante (panneau gauche) pour le mode aplat de couleur.' };
      }
      const breaks = quantileBreaks(vals, 5);
      const { colors } = classStyle(breaks.length);
      const counts = new Array(breaks.length).fill(0);
      const pairs = [];
      for (const p of points) {
        const ci = classIndex(p.value, breaks); counts[ci]++;
        pairs.push(Number(p.pk), colors[ci]);
      }
      const expr = pairs.length ? ['match', ['id'], ...pairs, '#d8d2c4'] : '#d8d2c4';
      paints = [
        { layer: opts.choroLayer, prop: opts.choroProp || 'fill-color', value: expr },
        { layer: opts.choroLayer, prop: opts.choroOpacityProp || 'fill-opacity', value: 0.78 },
      ];
      items = points.map(p => ({
        type: 'label', coord: p.coord, label: fmtCompact(p.value),
        title: `${p.nom} — ${Number(p.value).toLocaleString('fr')} ${unite}`,
      }));
      legende = legendClasses(breaks, colors, null, counts, vmin, unite);

    } else { // cercle_prop
      items = points.map(p => ({
        type: 'circle', coord: p.coord, label: fmtCompact(p.value),
        color, size: propSize(p.value, vmin, vmax),
        title: `${p.nom} — ${Number(p.value).toLocaleString('fr')} ${unite}`,
      }));
      legende = legendProp(vmin, vmax, unite);
    }

    const { markers, overlay } = addMarkers(map, items);
    fitTo(map, points);
    return { markers, overlay, paints, legende };
  }

  // ── API publique ─────────────────────────────────────────────────────────────

  window.RenduCarte = {
    RAMP, SIZES,
    fmtCompact,
    quantileBreaks, classIndex, classStyle, propSize,
    circleEl, pieEl, barsEl, labelEl,
    addMarkers, fitTo,
    legendBox, dot, legendClasses, legendProp,
    renderThematique,
  };

})();
