/**
 * tools.js — Appels aux endpoints /carte/api/outils/* et affichage des résultats.
 */

const TOOLS_BASE = "/carte/api/outils/";

async function _postTool(endpoint, body) {
  const resp = await fetch(TOOLS_BASE + endpoint + "/", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrf() },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(err.erreur ?? resp.statusText);
  }
  return resp.json();
}

function _afficherResultatGeoJSON(geojson, sourceId = "tool-result") {
  if (MAP.getLayer(sourceId)) MAP.removeLayer(sourceId);
  if (MAP.getSource(sourceId)) MAP.removeSource(sourceId);
  MAP.addSource(sourceId, { type: "geojson", data: geojson });
  MAP.addLayer({
    id: sourceId,
    type: "fill",
    source: sourceId,
    paint: { "fill-color": "#f39c12", "fill-opacity": 0.5, "fill-outline-color": "#e67e22" },
  });
}

async function outilBuffer(couche, distanceM, pks = null) {
  const result = await _postTool("buffer", { couche, distance_m: distanceM, pks });
  _afficherResultatGeoJSON(result, "tool-buffer");
}

async function outilIntersection(coucheA, coucheB, pksA = null) {
  const result = await _postTool("intersection", { couche_a: coucheA, couche_b: coucheB, pks_a: pksA });
  _afficherResultatGeoJSON(result, "tool-intersection");
}

async function outilUnion(couche, pks = null) {
  const result = await _postTool("union", { couche, pks });
  _afficherResultatGeoJSON(result, "tool-union");
}

async function outilDissolve(couche, champ) {
  const result = await _postTool("dissolve", { couche, champ });
  _afficherResultatGeoJSON(result, "tool-dissolve");
}

async function outilNear(coucheA, coucheB, pksA = null) {
  return _postTool("near", { couche_a: coucheA, couche_b: coucheB, pks_a: pksA });
}

async function outilStats(coucheZones, coucheValeurs, champValeur, agregats = ["count", "avg"]) {
  return _postTool("stats", { couche_zones: coucheZones, couche_valeurs: coucheValeurs, champ_valeur: champValeur, agregats });
}

async function outilScoring(couche, poids, pks = null) {
  return _postTool("scoring", { couche, poids, pks });
}

// ── Box Seuil — scoring ───────────────────────────────────────────────────────

const SCORE_COLORS = ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#27ae60'];

function _scoreColors(n) {
  if (n <= 1) return [SCORE_COLORS[4]];
  const step = (SCORE_COLORS.length - 1) / (n - 1);
  return Array.from({ length: n }, (_, i) => SCORE_COLORS[Math.round(i * step)]);
}

async function outilScoringFetch(couche, pks, coefficients, nClasses = 3, methode = 'jenks') {
  return _postTool('scoring', { couche, pks, coefficients, n_classes: nClasses, methode });
}

function _applyScoringChoropleth(couche, resultats, nClasses) {
  const sourceName = `src-${couche}`;
  const layerName  = `lyr-${couche}`;
  if (!MAP.getSource(sourceName)) return;

  // Store classe per pk via feature-state
  for (const r of resultats) {
    if (r.classe != null) {
      MAP.setFeatureState({ source: sourceName, id: r.pk }, { scoring_classe: r.classe });
    }
  }

  const colors = _scoreColors(nClasses);
  const paintProp = MAP.getLayer(layerName)?.type === 'circle' ? 'circle-color' : 'fill-color';
  const expr = ['case'];
  for (let c = 1; c <= nClasses; c++) {
    expr.push(['==', ['feature-state', 'scoring_classe'], c]);
    expr.push(colors[c - 1]);
  }
  expr.push('#bdc3c7'); // unclassified / no EtatX
  MAP.setPaintProperty(layerName, paintProp, expr);
}

function _clearScoringChoropleth(couche) {
  const sourceName = `src-${couche}`;
  const layerName  = `lyr-${couche}`;
  if (!MAP.getSource(sourceName)) return;
  // Reset paint to original accent color
  const paintProp = MAP.getLayer(layerName)?.type === 'circle' ? 'circle-color' : 'fill-color';
  try { MAP.setPaintProperty(layerName, paintProp, '#c0392b'); } catch (_) {}
}

function _buildScoringTable(resultats, breaks, nClasses) {
  if (!resultats.length) return '<p style="color:#999;font-size:12px">Aucun résultat.</p>';
  const colors = _scoreColors(nClasses);
  const rows = [...resultats]
    .filter(r => r.score != null)
    .sort((a, b) => b.score - a.score)
    .map(r => {
      const color = r.classe != null ? colors[r.classe - 1] : '#bdc3c7';
      return `<tr>
        <td style="text-align:left">${r.pk}</td>
        <td>${r.score != null ? r.score.toFixed(1) + ' %' : 'N/D'}</td>
        <td><span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:${color};vertical-align:middle"></span> ${r.classe ?? '—'}</td>
      </tr>`;
    }).join('');
  const brk = breaks.length ? `<p style="font-size:10px;color:#888;margin:4px 0">Seuils : ${breaks.map(v=>v.toFixed(1)).join(' | ')}</p>` : '';
  return `${brk}<table class="seg-result-table">
    <thead><tr><th style="text-align:left">PK</th><th>Score</th><th>Classe</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

async function initBoxSeuil() {
  const container = document.getElementById('seuil-criteres-form');
  const btnExec   = document.getElementById('btn-seuil-scoring');
  const resultDiv = document.getElementById('seuil-scoring-result');
  const couche    = 'seuils';

  if (!container || !btnExec || !resultDiv) return;

  // Fetch criteria once
  let criteres = [];
  try {
    const resp = await fetch(`/carte/api/couche/${couche}/criteres/`);
    if (!resp.ok) throw new Error(await resp.text());
    const data = await resp.json();
    criteres = data.criteres;
  } catch (e) {
    container.innerHTML = `<p style="color:#c0392b;font-size:11px">Impossible de charger les critères : ${e.message}</p>`;
    return;
  }

  // Render sliders
  container.innerHTML = criteres.map(c => `
    <div class="seuil-critere-row">
      <label class="seuil-critere-label" for="coeff-${c.champ}" title="${c.champ}">
        ${c.label}
      </label>
      <div class="seuil-slider-wrap">
        <input type="range" id="coeff-${c.champ}" data-champ="${c.champ}"
               class="seuil-slider" min="0" max="5" step="1" value="3">
        <span class="seuil-slider-val" id="val-${c.champ}">3</span>
      </div>
    </div>
  `).join('');

  // Live value display
  container.querySelectorAll('.seuil-slider').forEach(slider => {
    const valEl = document.getElementById(`val-${slider.dataset.champ}`);
    slider.addEventListener('input', () => { if (valEl) valEl.textContent = slider.value; });
  });

  btnExec.addEventListener('click', async () => {
    const coefficients = {};
    container.querySelectorAll('.seuil-slider').forEach(s => {
      coefficients[s.dataset.champ] = parseFloat(s.value);
    });

    const pks       = window.selection_active?.length ? window.selection_active : null;
    const nClasses  = parseInt(document.getElementById('seuil-n-classes')?.value ?? '3', 10);
    const methode   = document.getElementById('seuil-methode')?.value ?? 'jenks';

    btnExec.disabled = true;
    btnExec.textContent = 'Calcul…';
    resultDiv.innerHTML = '';

    try {
      const data = await outilScoringFetch(couche, pks, coefficients, nClasses, methode);
      _applyScoringChoropleth(couche, data.resultats, data.n_classes);
      resultDiv.innerHTML = _buildScoringTable(data.resultats, data.breaks, data.n_classes);
    } catch (e) {
      resultDiv.innerHTML = `<p style="color:#c0392b;font-size:11px">${e.message}</p>`;
    } finally {
      btnExec.disabled = false;
      btnExec.textContent = 'Exécuter';
    }
  });

  document.getElementById('btn-seuil-reset')?.addEventListener('click', () => {
    _clearScoringChoropleth(couche);
    resultDiv.innerHTML = '';
  });
}

// ── Box Séguia ────────────────────────────────────────────────────────────────

async function outilEfficience(pks) {
  return _postTool("efficience", { pks });
}

async function outilManning(pks, nManning = null, pente = 0.001) {
  const body = { pks, pente };
  if (nManning !== null) body.n_manning = nManning;
  return _postTool("manning", body);
}

// ── Box Séguia — UI ───────────────────────────────────────────────────────────

function _renderTableEfficience(resultats) {
  if (!resultats.length) return '<p style="color:#999;font-size:12px">Aucun résultat.</p>';
  const rows = resultats.map(r =>
    `<tr>
      <td>${r.troncon}</td>
      <td>${r.debit_amont.toFixed(4)}</td>
      <td>${r.perte_infiltration_m3s.toFixed(5)}</td>
      <td>${r.perte_vaporisation_m3s.toFixed(5)}</td>
      <td><b>${r.efficience_pourcent.toFixed(1)} %</b></td>
    </tr>`
  ).join('');
  return `<table class="seg-result-table">
    <thead><tr><th>Tronçon</th><th>Q amont</th><th>PI (m³/s)</th><th>PV (m³/s)</th><th>Efficience</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function _renderTableManning(resultats) {
  if (!resultats.length) return '<p style="color:#999;font-size:12px">Aucun résultat.</p>';
  const rows = resultats.map(r =>
    `<tr>
      <td>${r.troncon}</td>
      <td>${r.forme}</td>
      <td>${r.n_utilise}</td>
      <td><b>${r.debit_calcule.toFixed(4)} m³/s</b></td>
    </tr>`
  ).join('');
  return `<table class="seg-result-table">
    <thead><tr><th>Tronçon</th><th>Forme</th><th>n</th><th>Q Manning</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function _showSegMsg(elId, msg, isError = false) {
  const el = document.getElementById(elId);
  if (!el) return;
  el.innerHTML = `<p style="color:${isError ? '#c0392b' : '#27ae60'};font-size:12px;margin:6px 0">${msg}</p>`;
}

function initBoxSeguia() {
  const btnEff = document.getElementById('btn-seg-efficience');
  const btnMan = document.getElementById('btn-seg-manning');
  if (!btnEff || !btnMan) return;

  btnEff.addEventListener('click', async () => {
    const pks = window.selection_active ?? [];
    if (!pks.length) {
      _showSegMsg('seg-eff-result', 'Aucun tronçon sélectionné.', true);
      return;
    }
    if (window.couche_active !== 'troncons_seguias') {
      _showSegMsg('seg-eff-result', 'Activez la couche « Tronçons de séguias » et sélectionnez des tronçons.', true);
      return;
    }
    btnEff.disabled = true;
    btnEff.textContent = 'Calcul…';
    try {
      const data = await outilEfficience(pks);
      const errMsg = data.erreurs?.length
        ? `<p style="color:#c0392b;font-size:11px">${data.erreurs.length} erreur(s) : ${data.erreurs.map(e=>e.erreur).join(', ')}</p>`
        : '';
      document.getElementById('seg-eff-result').innerHTML =
        `<p style="font-size:11px;color:#666;margin:4px 0">${data.nb_calcules} tronçon(s) mis à jour.</p>`
        + errMsg
        + _renderTableEfficience(data.resultats);
    } catch (e) {
      _showSegMsg('seg-eff-result', e.message, true);
    } finally {
      btnEff.disabled = false;
      btnEff.textContent = 'Calculer';
    }
  });

  btnMan.addEventListener('click', async () => {
    const pks = window.selection_active ?? [];
    if (!pks.length) {
      _showSegMsg('seg-man-result', 'Aucun tronçon sélectionné.', true);
      return;
    }
    if (window.couche_active !== 'troncons_seguias') {
      _showSegMsg('seg-man-result', 'Activez la couche « Tronçons de séguias » et sélectionnez des tronçons.', true);
      return;
    }
    const nInput  = document.getElementById('seg-n-manning');
    const pInput  = document.getElementById('seg-pente');
    const nVal    = nInput?.value  ? parseFloat(nInput.value)  : null;
    const pente   = pInput?.value  ? parseFloat(pInput.value)  : 0.001;
    btnMan.disabled = true;
    btnMan.textContent = 'Calcul…';
    try {
      const data = await outilManning(pks, nVal, pente);
      document.getElementById('seg-man-result').innerHTML = _renderTableManning(data.resultats);
    } catch (e) {
      _showSegMsg('seg-man-result', e.message, true);
    } finally {
      btnMan.disabled = false;
      btnMan.textContent = 'Calculer';
    }
  });
}
