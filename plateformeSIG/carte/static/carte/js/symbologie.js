/**
 * symbologie.js — Panneau de symbologie (SY-01 à SY-04)
 *
 * Ouverture : clic sur .couche-style-btn[data-couche] dans #couches-liste
 * Fermeture : bouton ← retour
 *
 * Modes :
 *   Simple      (SY-01) — couleur, contour, opacité, taille
 *   Catégorisé  (SY-02) — champ → valeurs uniques → couleur par valeur
 *
 * SY-04 — live preview : met à jour .couche-dot dans la liste ET dans le panneau
 *          à chaque frappe sur les inputs couleur.
 *
 * Dépend de :
 *   map.js    → window.MAP
 *   layers.js → window.COUCHES_META
 */

'use strict';

// ── Propriétés MapLibre selon le type de layer ────────────────────────────────

const PAINT_PROPS = {
  circle: {
    color:   'circle-color',
    outline: 'circle-stroke-color',
    opacity: 'circle-opacity',
    size:    'circle-radius',
    sizeLabel: 'Rayon (px)',
    sizeMax:   20,
  },
  line: {
    color:   'line-color',
    outline: null,
    opacity: 'line-opacity',
    size:    'line-width',
    sizeLabel: 'Épaisseur (px)',
    sizeMax:   12,
  },
  fill: {
    color:       'fill-color',
    outline:     'fill-outline-color',
    opacity:     'fill-opacity',
    size:        null,
    strokeWidth: 'line-width',    // géré sur le layer fantôme lyr-${nom}-outline
    sizeLabel:   'Épaisseur contour (px)',
    sizeMax:     10,
  },
};

// ── État courant ──────────────────────────────────────────────────────────────

let _nom   = null;   // couche en cours d'édition
let _ltype = null;   // 'circle' | 'line' | 'fill'
let _grad  = null;   // état du mode gradué { champ, stats, n, methode } — null si champ qualitatif

// ── Entrée / sortie ───────────────────────────────────────────────────────────

function openSymbologie(nom) {
  // Si la couche n'est pas encore dans MapLibre, attendre qu'elle le soit
  if (!MAP.getLayer(`lyr-${nom}`)) {
    const _waitAndOpen = setInterval(() => {
      if (MAP.getLayer(`lyr-${nom}`)) {
        clearInterval(_waitAndOpen);
        openSymbologie(nom);
      }
    }, 100);
    return;
  }

  _nom   = nom;
  _ltype = _getLayerType(nom);
  _grad  = null;

  _renderPanel();

  // Synchroniser le dot de la liste avec la couleur actuelle du layer
  _livePreviewFromLayer(nom);

  document.getElementById('couches-liste').style.display    = 'none';
  document.getElementById('panneau-symbologie').style.display = 'flex';
}

function closeSymbologie() {
  _nom = null;
  document.getElementById('panneau-symbologie').style.display = 'none';
  document.getElementById('couches-liste').style.display      = '';
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _getLayerType(nom) {
  const lyr = MAP.getLayer(`lyr-${nom}`);
  return lyr ? lyr.type : 'circle';
}

function _getPaint(nom, prop) {
  if (!prop || !MAP.getLayer(`lyr-${nom}`)) return null;
  try { return MAP.getPaintProperty(`lyr-${nom}`, prop); } catch { return null; }
}

// Retourne les pks du filtre de requête actif sur la couche, ou null.
// La requête (query.js / multiquery.js) pose le filtre via window.applyLayerFilter
// sous la forme ['in', ['id'], ['literal', [pk, ...]]]. La symbologie catégorisée
// s'y appuie pour ne s'appliquer QUE sur les entités issues de la requête ;
// en l'absence de filtre, elle porte sur toute la couche (comportement par défaut).
function _getActiveFilterPks(nom) {
  if (!(window.FILTERED_LAYERS instanceof Set) || !window.FILTERED_LAYERS.has(nom)) return null;
  if (!MAP.getLayer(`lyr-${nom}`)) return null;
  let f;
  try { f = MAP.getFilter(`lyr-${nom}`); } catch { return null; }
  if (Array.isArray(f) && f[0] === 'in' && Array.isArray(f[2]) && f[2][0] === 'literal') {
    const pks = f[2][1];
    return Array.isArray(pks) && pks.length ? pks.map(Number) : null;
  }
  return null;
}

// Enveloppe une expression de peinture pour la restreindre aux entités de la
// requête (les autres reçoivent `fallback`). Sans filtre actif → expression nue.
function _scopeToFilter(nom, expr, fallback) {
  const pks = _getActiveFilterPks(nom);
  if (!pks) return expr;
  return ['case', ['in', ['id'], ['literal', pks]], expr, fallback];
}

// Convertit une valeur CSS couleur → #rrggbb (ignore les expressions MapLibre)
function _toHex(val) {
  if (!val || Array.isArray(val)) return '#cccccc';
  const cvs = document.createElement('canvas');
  cvs.width = cvs.height = 1;
  const ctx = cvs.getContext('2d');
  ctx.fillStyle = String(val);
  ctx.fillRect(0, 0, 1, 1);
  const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
  return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
}

// ── Rendu du panneau ──────────────────────────────────────────────────────────

function _renderPanel() {
  const panel = document.getElementById('panneau-symbologie');
  const meta  = (window.COUCHES_META || {})[_nom] ?? {};
  const props = PAINT_PROPS[_ltype] ?? PAINT_PROPS.circle;

  // Valeurs paint actuelles
  const colorVal    = _toHex(_getPaint(_nom, props.color)   ?? '#cccccc');
  const outlineVal  = _toHex(_getPaint(_nom, props.outline) ?? '#ffffff');
  const opacityVal  = _getPaint(_nom, props.opacity) ?? 1;
  const sizeVal     = _getPaint(_nom, props.size) ?? (_ltype === 'line' ? 1 : 5);
  // BUG-L5 — lire l'épaisseur depuis le layer fantôme outline
  const strokeVal   = _ltype === 'fill'
    ? (MAP.getLayer(`lyr-${_nom}-outline`)
        ? (MAP.getPaintProperty(`lyr-${_nom}-outline`, 'line-width') ?? 1)
        : 1)
    : 1;

  const dotClass = { circle: 'geom-point', line: 'geom-linestring', fill: 'geom-polygon' }[_ltype] ?? 'geom-geometry';
  const champs   = (meta.fields ?? []).map(f => `<option value="${f}">${f}</option>`).join('');

  panel.innerHTML = `
    <div class="sym-header">
      <button id="sym-retour" title="Retour aux couches">
        <i class="fas fa-arrow-left"></i>
      </button>
      <span class="sym-title">${meta.label ?? _nom}</span>
    </div>

    <!-- SY-04 — prévisualisation légende en temps réel -->
    <div class="sym-preview">
      <span id="sym-preview-dot" class="couche-dot ${dotClass}" style="background:${colorVal}"></span>
      <span class="sym-preview-label">${meta.label ?? _nom}</span>
    </div>

    <!-- Sélecteur de mode -->
    <div class="sym-mode-bar">
      <button class="sym-mode active" data-mode="simple">Simple</button>
      <button class="sym-mode"        data-mode="categorise">Catégorisé</button>
    </div>

    <!-- Mode Simple (SY-01) -->
    <div id="sym-simple" class="sym-content">

      <div class="sym-field">
        <label>Couleur de remplissage</label>
        <input type="color" id="sym-color" value="${colorVal}">
      </div>

      ${props.outline ? `
      <div class="sym-field">
        <label>Couleur de contour</label>
        <input type="color" id="sym-outline" value="${outlineVal}">
      </div>` : ''}

      <div class="sym-field">
        <label>
          Opacité &mdash;
          <span id="sym-opacity-val">${Math.round(opacityVal * 100)}%</span>
        </label>
        <input type="range" id="sym-opacity" min="0" max="1" step="0.05"
               value="${opacityVal}">
      </div>

      ${props.size !== null ? `
      <div class="sym-field">
        <label>
          ${props.sizeLabel} &mdash;
          <span id="sym-size-val">${sizeVal}</span>
        </label>
        <input type="range" id="sym-size" min="1" max="${props.sizeMax}" step="0.5"
               value="${sizeVal}">
      </div>` : ''}

      ${_ltype === 'fill' ? `
      <div class="sym-field">
        <label>
          Épaisseur contour (px) &mdash;
          <span id="sym-stroke-val">${strokeVal}</span>
        </label>
        <input type="range" id="sym-stroke" min="0" max="${props.sizeMax}" step="0.5"
               value="${strokeVal}">
      </div>` : ''}

      <button id="sym-appliquer" class="sym-btn-apply">
        <i class="fas fa-check"></i>&nbsp; Appliquer
      </button>
    </div>

    <!-- Mode Catégorisé (SY-02) -->
    <div id="sym-categorise" class="sym-content" style="display:none">

      <div class="sym-field">
        <label>Champ de classification</label>
        <select id="sym-cat-field">
          <option value="">— choisir un champ —</option>
          ${champs}
        </select>
      </div>

      <div id="sym-cat-values" class="sym-cat-values">
        <p class="sym-hint">Sélectionnez un champ pour charger les valeurs.</p>
      </div>

      <div style="display:flex;gap:6px;margin-top:4px">
        <button id="sym-cat-appliquer" class="sym-btn-apply" disabled style="flex:1">
          <i class="fas fa-check"></i>&nbsp; Appliquer
        </button>
        <button id="sym-cat-reset" class="sym-btn-apply" style="flex:0;background:#95a5a6" title="Réinitialiser au style par défaut">
          <i class="fas fa-undo"></i>
        </button>
      </div>
    </div>
  `;

  _bindEvents();
}

// ── Liaison des événements ────────────────────────────────────────────────────

function _bindEvents() {
  const props = PAINT_PROPS[_ltype] ?? PAINT_PROPS.circle;

  document.getElementById('sym-retour').addEventListener('click', closeSymbologie);

  // Basculement Simple / Catégorisé
  document.querySelectorAll('#panneau-symbologie .sym-mode').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#panneau-symbologie .sym-mode')
        .forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const simple = btn.dataset.mode === 'simple';
      document.getElementById('sym-simple').style.display     = simple ? '' : 'none';
      document.getElementById('sym-categorise').style.display = simple ? 'none' : '';
    });
  });

  // ── Mode Simple — live preview (SY-04) ──────────────────────────────────
  const colorIn   = document.getElementById('sym-color');
  const opacityIn = document.getElementById('sym-opacity');
  const sizeIn    = document.getElementById('sym-size');

  colorIn?.addEventListener('input', () => _livePreview(_nom, colorIn.value));

  opacityIn?.addEventListener('input', () => {
    document.getElementById('sym-opacity-val').textContent =
      Math.round(parseFloat(opacityIn.value) * 100) + '%';
  });

  sizeIn?.addEventListener('input', () => {
    document.getElementById('sym-size-val').textContent = sizeIn.value;
  });

  // BUG-L5 — slider épaisseur contour (fill seulement)
  const strokeIn = document.getElementById('sym-stroke');
  strokeIn?.addEventListener('input', () => {
    document.getElementById('sym-stroke-val').textContent = strokeIn.value;
  });

  // Appliquer — mode Simple
  document.getElementById('sym-appliquer').addEventListener('click', () => {
    _applySimple(props);
  });

  // Catégorisé — chargement des valeurs sur changement de champ
  document.getElementById('sym-cat-field')?.addEventListener('change', e => {
    _symLoadValeurs(_nom, e.target.value);
  });

  // Appliquer — mode Catégorisé (qualitatif → match) ou Gradué (quantitatif → step)
  document.getElementById('sym-cat-appliquer').addEventListener('click', () => {
    if (_grad) _applyGradue(props);
    else       _applyCategorise(props);
  });

  // Réinitialiser — mode Catégorisé (BUG-L6)
  document.getElementById('sym-cat-reset')?.addEventListener('click', () => {
    _resetToDefault();
  });
}

// ── Mode Simple — application ─────────────────────────────────────────────────

function _applySimple(props) {
  if (!MAP.getLayer(`lyr-${_nom}`)) return;

  const colorIn   = document.getElementById('sym-color');
  const outlineIn = document.getElementById('sym-outline');
  const opacityIn = document.getElementById('sym-opacity');
  const sizeIn    = document.getElementById('sym-size');

  if (colorIn)                  MAP.setPaintProperty(`lyr-${_nom}`, props.color,   colorIn.value);
  if (outlineIn && props.outline) MAP.setPaintProperty(`lyr-${_nom}`, props.outline, outlineIn.value);
  if (opacityIn)                MAP.setPaintProperty(`lyr-${_nom}`, props.opacity, parseFloat(opacityIn.value));
  if (sizeIn && props.size)     MAP.setPaintProperty(`lyr-${_nom}`, props.size,    parseFloat(sizeIn.value));

  // BUG-L5 — appliquer l'épaisseur de contour sur le layer fantôme outline
  const strokeIn = document.getElementById('sym-stroke');
  if (strokeIn && _ltype === 'fill' && MAP.getLayer(`lyr-${_nom}-outline`)) {
    MAP.setPaintProperty(`lyr-${_nom}-outline`, 'line-width', parseFloat(strokeIn.value));
    if (outlineIn) {
      MAP.setPaintProperty(`lyr-${_nom}-outline`, 'line-color', outlineIn.value);
    }
  }

  // SY-04 — rafraîchissement final de la légende (dot liste + panneau)
  if (colorIn) _livePreview(_nom, colorIn.value);
  _livePreviewFromLayer(_nom);

  console.info(`[symbologie] "${_nom}" Simple appliqué`);
}

// ── Live preview (SY-04) — met à jour les deux points colorés ────────────────

function _livePreview(nom, color) {
  // Pastille dans le panneau symbologie
  const dot = document.getElementById('sym-preview-dot');
  if (dot) dot.style.background = color;

  // Pastille dans la liste des couches (légende)
  const cb      = document.querySelector(`input[data-couche="${nom}"]`);
  const listDot = cb?.closest('.couche-row')?.querySelector('.couche-dot');
  if (listDot) listDot.style.background = color;
}

// Lit la couleur courante du layer MapLibre et l'applique au dot de liste
function _livePreviewFromLayer(nom) {
  const ltype = _getLayerType(nom);
  const props  = PAINT_PROPS[ltype] ?? PAINT_PROPS.circle;
  const raw    = _getPaint(nom, props.color);
  if (!raw || Array.isArray(raw)) return;   // expression catégorisée → skip
  const color = _toHex(raw);
  const cb      = document.querySelector(`input[data-couche="${nom}"]`);
  const listDot = cb?.closest('.couche-row')?.querySelector('.couche-dot');
  if (listDot) listDot.style.background = color;
}

// ── Mode Catégorisé — chargement des valeurs depuis l'API ────────────────────
// Dispatcher : interroge /stats/ pour connaître le type du champ.
//   qualitatif  → une couleur par valeur distincte (comportement historique)
//   quantitatif → classification graduée par intervalles (SY-02 quantitatif)

// NB : préfixe _sym pour éviter la collision globale avec _loadValeurs de
// multiquery.js — les scripts classiques partagent le scope window, le fichier
// chargé en dernier écrase silencieusement la fonction homonyme.
async function _symLoadValeurs(nom, champ) {
  const container = document.getElementById('sym-cat-values');
  const btnApply  = document.getElementById('sym-cat-appliquer');

  _grad = null;

  if (!champ) {
    container.innerHTML = '<p class="sym-hint">Sélectionnez un champ pour charger les valeurs.</p>';
    btnApply.disabled = true;
    return;
  }

  container.innerHTML = '<p class="sym-hint"><i class="fas fa-spinner fa-spin"></i>&nbsp; Chargement…</p>';

  // Si une requête filtre la couche, restreindre valeurs/stats à son résultat.
  const pks   = _getActiveFilterPks(nom);
  const pksQS = pks ? `?pks=${pks.join(',')}` : '';

  try {
    const stResp = await fetch(`/carte/api/couche/${nom}/champs/${encodeURIComponent(champ)}/stats/${pksQS}`);
    if (stResp.ok) {
      const stats = await stResp.json();
      if (stats.type === 'quantitatif') {
        _initGradue(champ, stats);
        return;
      }
    }
  } catch { /* stats indisponibles → traitement qualitatif */ }

  _loadValeursQualitatif(nom, champ, pks);
}

async function _loadValeursQualitatif(nom, champ, pks) {
  const container = document.getElementById('sym-cat-values');
  const btnApply  = document.getElementById('sym-cat-appliquer');
  const pksQS     = pks ? `?pks=${pks.join(',')}` : '';

  try {
    const resp = await fetch(`/carte/api/couche/${nom}/champs/${encodeURIComponent(champ)}/valeurs/${pksQS}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    // L'API retourne { valeurs: [{ valeur, label }, ...] }
    const json    = await resp.json();
    const valeurs = json.valeurs ?? [];

    if (!valeurs.length) {
      container.innerHTML = pks
        ? '<p class="sym-hint">Aucune valeur dans le résultat de la requête pour ce champ.</p>'
        : '<p class="sym-hint">Aucune valeur trouvée.</p>';
      return;
    }

    // Bandeau : la catégorisation est restreinte aux entités issues de la requête
    const scopeHtml = pks
      ? `<p class="sym-hint" style="color:#2980b9;margin:0 0 4px">
           <i class="fas fa-filter"></i>&nbsp;
           Catégorisation restreinte au résultat de la requête (${pks.length} entité${pks.length > 1 ? 's' : ''}).
         </p>`
      : '';

    // BUG-L6 — avertissement et limitation à 50 catégories
    const MAX_CATEGORIES = 50;
    const totalCount = valeurs.length;
    const limited    = totalCount > MAX_CATEGORIES ? valeurs.slice(0, MAX_CATEGORIES) : valeurs;
    const warnHtml   = totalCount > MAX_CATEGORIES
      ? `<p class="sym-hint sym-hint--warn" style="color:#e67e22;margin-top:4px">
           <i class="fas fa-exclamation-triangle"></i>&nbsp;
           Trop de catégories (${totalCount}) — affichage limité aux ${MAX_CATEGORIES} premières.
         </p>`
      : '';

    const palette = _autoPalette(limited.length);
    container.innerHTML = scopeHtml + limited.map(({ valeur, label }, i) => `
      <div class="sym-cat-row">
        <input type="color" data-val="${_symEsc(valeur)}" value="${palette[i]}">
        <span class="sym-cat-val">${label ?? valeur ?? '(vide)'}</span>
      </div>`).join('') + warnHtml;

    btnApply.disabled = false;

  } catch (err) {
    container.innerHTML = `
      <p class="sym-hint sym-hint--error">
        <i class="fas fa-exclamation-triangle"></i>&nbsp;${err.message}
      </p>`;
    btnApply.disabled = true;
  }
}

// ── Mode Catégorisé — application ────────────────────────────────────────────

function _applyCategorise(props) {
  const champ = document.getElementById('sym-cat-field')?.value;
  const rows  = document.querySelectorAll('#sym-cat-values input[type=color]');
  if (!champ || !rows.length || !MAP.getLayer(`lyr-${_nom}`)) return;

  // BUG-L6 — construction correcte de l'expression MapLibre 'match'
  // Les valeurs null/vides sont exclues des branches (couvertes par le fallback).
  // Les valeurs numériques sont converties en Number pour correspondre au type du champ.
  const expr = ['match', ['get', champ]];
  rows.forEach(inp => {
    const rawVal = inp.dataset.val;
    if (rawVal === '' || rawVal === null || rawVal === 'null' || rawVal === undefined) return;
    const parsed = rawVal !== '' && !isNaN(rawVal) ? Number(rawVal) : rawVal;
    expr.push(parsed);
    expr.push(inp.value);
  });

  // Il faut au moins une branche pour que l'expression soit valide
  if (expr.length < 4) return;

  expr.push('#cccccc');   // fallback (valeurs non listées + null/vides)

  // Si une requête filtre la couche, n'appliquer les couleurs qu'aux entités
  // issues de la requête ; les autres restent en gris par défaut.
  const colorExpr = _scopeToFilter(_nom, expr, '#cccccc');

  MAP.setPaintProperty(`lyr-${_nom}`, props.color, colorExpr);

  // BUG-L5 + BUG-L6 — synchroniser la couleur du layer fantôme outline pour les polygones
  if (_ltype === 'fill' && MAP.getLayer(`lyr-${_nom}-outline`)) {
    MAP.setPaintProperty(`lyr-${_nom}-outline`, 'line-color', colorExpr);
  }

  _livePreviewFromLayer(_nom);
  const _scoped = _getActiveFilterPks(_nom);
  console.info(
    `[symbologie] "${_nom}" Catégorisé appliqué — champ "${champ}"` +
    (_scoped ? ` (restreint à ${_scoped.length} entité(s) de la requête)` : '')
  );
}

// ── Mode Gradué (SY-02 quantitatif) ──────────────────────────────────────────
// Champ numérique → classification par intervalles (quantiles / égaux) avec
// bornes éditables. Rendu selon la géométrie :
//   line   → épaisseur graduée (et/ou rampe de couleur)
//   circle → rayon gradué (et/ou rampe de couleur)
//   fill   → rampe de couleur (choroplèthe)

const GRAD_SIZE_DEFAULTS = {
  line:   { min: 1, max: 8,  label: 'Épaisseur (px)' },
  circle: { min: 3, max: 14, label: 'Rayon (px)' },
};

function _initGradue(champ, stats) {
  _grad = { champ, stats, n: 5, methode: 'quantiles' };
  _renderGradueUI();
}

function _renderGradueUI() {
  const container = document.getElementById('sym-cat-values');
  const btnApply  = document.getElementById('sym-cat-appliquer');
  const { stats } = _grad;

  if (!stats.count) {
    container.innerHTML = '<p class="sym-hint">Aucune valeur numérique renseignée pour ce champ.</p>';
    btnApply.disabled = true;
    return;
  }

  const meta      = (window.COUCHES_META ?? {})[_nom] ?? {};
  const baseColor = (window.LAYER_GROUP_COLORS ?? {})[meta.groupe] ?? '#7f8c8d';
  const sizeDef   = GRAD_SIZE_DEFAULTS[_ltype];

  // Options de rendu selon la géométrie (fill → couleur seule, toujours active)
  const optsHtml = `
    ${sizeDef ? `
    <div class="sym-grad-opt">
      <label class="sym-grad-check">
        <input type="checkbox" id="sym-grad-use-size" checked>
        Graduer ${_ltype === 'line' ? "l'épaisseur" : 'le rayon'}
      </label>
      <div class="sym-grad-minmax">
        <input type="number" id="sym-grad-size-min" value="${sizeDef.min}" min="0.5" step="0.5">
        <span>→</span>
        <input type="number" id="sym-grad-size-max" value="${sizeDef.max}" min="0.5" step="0.5">
        <span>px</span>
      </div>
    </div>` : ''}
    <div class="sym-grad-opt">
      ${sizeDef ? `
      <label class="sym-grad-check">
        <input type="checkbox" id="sym-grad-use-color">
        Graduer la couleur
      </label>` : `
      <span class="sym-grad-check" style="cursor:default">Rampe de couleur</span>`}
      <div class="sym-grad-minmax" id="sym-grad-color-row">
        <input type="color" id="sym-grad-color-from" value="#fdeedd">
        <span>→</span>
        <input type="color" id="sym-grad-color-to" value="${baseColor}">
      </div>
    </div>`;

  container.innerHTML = `
    <div class="sym-grad-params">
      <div class="sym-grad-param">
        <label>Classes</label>
        <select id="sym-grad-n">
          ${[3, 4, 5, 6, 7].map(k =>
            `<option value="${k}" ${k === _grad.n ? 'selected' : ''}>${k}</option>`).join('')}
        </select>
      </div>
      <div class="sym-grad-param">
        <label>Méthode</label>
        <select id="sym-grad-methode">
          <option value="quantiles" ${_grad.methode === 'quantiles' ? 'selected' : ''}>Quantiles</option>
          <option value="egaux"     ${_grad.methode === 'egaux'     ? 'selected' : ''}>Intervalles égaux</option>
        </select>
      </div>
    </div>
    <p class="sym-hint" style="margin:0">
      ${stats.count} valeur${stats.count > 1 ? 's' : ''} —
      min ${_fmtNum(stats.min)} / max ${_fmtNum(stats.max)}
    </p>
    ${optsHtml}
    <table class="sym-grad-table">
      <thead><tr><th>Symbole</th><th>≤ Borne sup</th><th>Étiquette</th></tr></thead>
      <tbody id="sym-grad-tbody"></tbody>
    </table>
    <p id="sym-grad-err" class="sym-hint sym-hint--error" style="display:none"></p>
  `;

  _gradFillTbody(stats.breaks[_grad.methode] ?? []);
  _bindGradueEvents();
  btnApply.disabled = false;
}

function _gradFillTbody(breaks) {
  const tbody = document.getElementById('sym-grad-tbody');
  tbody.innerHTML = breaks.map((b, i) => `
    <tr>
      <td><div class="sym-grad-swatch" data-idx="${i}"></div></td>
      <td><input type="number" step="any" class="sym-grad-borne" value="${_fmtNum(b)}"></td>
      <td class="sym-grad-label"></td>
    </tr>`).join('');
  _gradRefreshRows();
}

function _bindGradueEvents() {
  // Nombre de classes / méthode → recharger les bornes depuis l'API
  document.getElementById('sym-grad-n')?.addEventListener('change', _gradReload);
  document.getElementById('sym-grad-methode')?.addEventListener('change', e => {
    _grad.methode = e.target.value;
    _gradFillTbody(_grad.stats.breaks[_grad.methode] ?? []);
  });

  // Cases taille / couleur → griser les contrôles + rafraîchir les aperçus
  document.getElementById('sym-grad-use-size')?.addEventListener('change', _gradRefreshRows);
  document.getElementById('sym-grad-use-color')?.addEventListener('change', e => {
    const row = document.getElementById('sym-grad-color-row');
    if (row) row.style.opacity = e.target.checked ? '' : '0.4';
    _gradRefreshRows();
  });
  if (document.getElementById('sym-grad-use-color') &&
      !document.getElementById('sym-grad-use-color').checked) {
    const row = document.getElementById('sym-grad-color-row');
    if (row) row.style.opacity = '0.4';
  }

  // Min/max de taille et rampe de couleur → aperçus
  ['sym-grad-size-min', 'sym-grad-size-max', 'sym-grad-color-from', 'sym-grad-color-to']
    .forEach(id => document.getElementById(id)?.addEventListener('input', _gradRefreshRows));

  // Bornes éditées à la main → étiquettes recalculées (change : préserve le focus)
  document.getElementById('sym-grad-tbody')?.addEventListener('change', e => {
    if (e.target.classList.contains('sym-grad-borne')) _gradRefreshRows();
  });
}

async function _gradReload() {
  _grad.n = parseInt(document.getElementById('sym-grad-n')?.value ?? '5', 10);
  const _pks   = _getActiveFilterPks(_nom);
  const _pksQS = _pks ? `&pks=${_pks.join(',')}` : '';
  try {
    const resp = await fetch(
      `/carte/api/couche/${_nom}/champs/${encodeURIComponent(_grad.champ)}/stats/?classes=${_grad.n}${_pksQS}`
    );
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    _grad.stats = await resp.json();
    _gradFillTbody(_grad.stats.breaks[_grad.methode] ?? []);
  } catch (err) {
    _gradError(`Rechargement impossible : ${err.message}`);
  }
}

// Lit les contrôles courants et met à jour aperçus + étiquettes (sans toucher aux inputs)
function _gradRefreshRows() {
  const bornes  = _gradBornes();
  const n       = bornes.length;
  const useSize  = _gradUseSize();
  const useColor = _gradUseColor();

  const sizeMin = parseFloat(document.getElementById('sym-grad-size-min')?.value)  || 1;
  const sizeMax = parseFloat(document.getElementById('sym-grad-size-max')?.value)  || 8;
  const cFrom   = document.getElementById('sym-grad-color-from')?.value ?? '#fdeedd';
  const cTo     = document.getElementById('sym-grad-color-to')?.value   ?? '#7f8c8d';

  // Couleur fixe actuelle du layer (utilisée quand la couleur n'est pas graduée)
  const props     = PAINT_PROPS[_ltype] ?? PAINT_PROPS.circle;
  const fixedCol  = _toHex(_getPaint(_nom, props.color));

  const rows = document.querySelectorAll('#sym-grad-tbody tr');
  rows.forEach((tr, i) => {
    const t     = n <= 1 ? 1 : i / (n - 1);
    const color = useColor ? _lerpColor(cFrom, cTo, t) : fixedCol;
    const size  = sizeMin + t * (sizeMax - sizeMin);

    const sw = tr.querySelector('.sym-grad-swatch');
    if (sw) {
      if (_ltype === 'line') {
        sw.style.cssText =
          `width:34px;height:${Math.max(1.5, Math.min(size, 14))}px;` +
          `background:${color};border-radius:2px`;
      } else if (_ltype === 'circle') {
        const d = useSize ? Math.max(5, Math.min(size * 2, 20)) : 12;
        sw.style.cssText =
          `width:${d}px;height:${d}px;background:${color};border-radius:50%;` +
          `border:1px solid rgba(0,0,0,.25)`;
      } else {
        sw.style.cssText =
          `width:22px;height:13px;background:${color};border:1px solid rgba(0,0,0,.25);border-radius:2px`;
      }
    }

    const lbl = tr.querySelector('.sym-grad-label');
    if (lbl) {
      lbl.textContent = i === 0
        ? `≤ ${_fmtNum(bornes[0])}`
        : `${_fmtNum(bornes[i - 1])} – ${_fmtNum(bornes[i])}`;
    }
  });
}

// ── Application — expression MapLibre 'step' ──────────────────────────────────

function _applyGradue(props) {
  if (!_grad || !MAP.getLayer(`lyr-${_nom}`)) return;

  const bornes = _gradBornes();
  const n      = bornes.length;
  if (!n) return;

  // Validation : bornes toutes numériques et strictement croissantes
  if (bornes.some(b => !isFinite(b))) {
    _gradError('Bornes invalides : entrez des valeurs numériques.');
    return;
  }
  for (let i = 1; i < n; i++) {
    if (bornes[i] <= bornes[i - 1]) {
      _gradError(`Bornes non croissantes : classe ${i + 1} (${_fmtNum(bornes[i])}) ≤ classe ${i} (${_fmtNum(bornes[i - 1])}).`);
      return;
    }
  }

  const useSize  = _gradUseSize();
  const useColor = _gradUseColor();
  if (!useSize && !useColor) {
    _gradError('Cochez au moins un rendu (taille ou couleur).');
    return;
  }
  _gradError(null);

  const sizeMin = parseFloat(document.getElementById('sym-grad-size-min')?.value)  || 1;
  const sizeMax = parseFloat(document.getElementById('sym-grad-size-max')?.value)  || 8;
  const cFrom   = document.getElementById('sym-grad-color-from')?.value ?? '#fdeedd';
  const cTo     = document.getElementById('sym-grad-color-to')?.value   ?? '#7f8c8d';

  // Outputs par classe (interpolation linéaire)
  const colors = [], sizes = [];
  for (let i = 0; i < n; i++) {
    const t = n <= 1 ? 1 : i / (n - 1);
    colors.push(_lerpColor(cFrom, cTo, t));
    sizes.push(sizeMin + t * (sizeMax - sizeMin));
  }

  // step : entrée numérique ; stops = bornes sup des classes 1..n-1
  const inputExpr = ['to-number', ['get', _grad.champ], _grad.stats.min ?? 0];
  const stepExpr  = outputs => {
    if (n === 1) return outputs[0];
    const e = ['step', inputExpr, outputs[0]];
    for (let i = 1; i < n; i++) { e.push(bornes[i - 1]); e.push(outputs[i]); }
    return e;
  };

  // Restreindre aux entités issues de la requête si un filtre est actif.
  const _sizeFallback = _ltype === 'line' ? 1 : 5;
  if (useColor) {
    const expr = _scopeToFilter(_nom, stepExpr(colors), '#cccccc');
    MAP.setPaintProperty(`lyr-${_nom}`, props.color, expr);
    if (_ltype === 'fill' && MAP.getLayer(`lyr-${_nom}-outline`)) {
      MAP.setPaintProperty(`lyr-${_nom}-outline`, 'line-color', expr);
    }
  }
  if (useSize && props.size) {
    MAP.setPaintProperty(`lyr-${_nom}`, props.size, _scopeToFilter(_nom, stepExpr(sizes), _sizeFallback));
  }

  _livePreviewFromLayer(_nom);
  console.info(
    `[symbologie] "${_nom}" Gradué appliqué — champ "${_grad.champ}", ` +
    `${n} classes (${_grad.methode}), taille:${useSize}, couleur:${useColor}`
  );
}

// ── Helpers du mode gradué ────────────────────────────────────────────────────

function _gradBornes() {
  return [...document.querySelectorAll('#sym-grad-tbody .sym-grad-borne')]
    .map(inp => parseFloat(inp.value));
}

function _gradUseSize() {
  const cb = document.getElementById('sym-grad-use-size');
  return cb ? cb.checked : false;            // fill → pas de taille
}

function _gradUseColor() {
  const cb = document.getElementById('sym-grad-use-color');
  return cb ? cb.checked : true;             // fill → couleur toujours graduée
}

function _gradError(msg) {
  const el = document.getElementById('sym-grad-err');
  if (!el) return;
  el.textContent    = msg ?? '';
  el.style.display  = msg ? '' : 'none';
}

// Interpolation linéaire entre deux couleurs #rrggbb
function _lerpColor(hex1, hex2, t) {
  const p = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
  const [r1, g1, b1] = p(hex1);
  const [r2, g2, b2] = p(hex2);
  const mix = (a, b) => Math.round(a + (b - a) * t);
  return '#' + [mix(r1, r2), mix(g1, g2), mix(b1, b2)]
    .map(x => x.toString(16).padStart(2, '0')).join('');
}

// Format compact : 6 décimales max, sans zéros traînants
function _fmtNum(v) {
  if (v === null || v === undefined || !isFinite(v)) return '';
  return String(Math.round(v * 1e6) / 1e6);
}

// ── Réinitialiser au style par défaut du groupe (BUG-L6) ─────────────────────

function _resetToDefault() {
  if (!MAP.getLayer(`lyr-${_nom}`)) return;
  const meta  = (window.COUCHES_META ?? {})[_nom] ?? {};
  const color = (window.LAYER_GROUP_COLORS ?? {})[meta.groupe] ?? (window.LAYER_COLOR_FALLBACK ?? '#7f8c8d');
  const props = PAINT_PROPS[_ltype] ?? PAINT_PROPS.circle;

  MAP.setPaintProperty(`lyr-${_nom}`, props.color, color);
  if (_ltype === 'fill' && MAP.getLayer(`lyr-${_nom}-outline`)) {
    MAP.setPaintProperty(`lyr-${_nom}-outline`, 'line-color', color);
  }
  // Annule aussi une éventuelle taille graduée (mode Gradué)
  if (props.size) {
    MAP.setPaintProperty(`lyr-${_nom}`, props.size, _ltype === 'line' ? 1 : 5);
  }
  _livePreview(_nom, color);
  _livePreviewFromLayer(_nom);
  console.info(`[symbologie] "${_nom}" réinitialisé au style par défaut`);
}

// ── Palette automatique HSL ───────────────────────────────────────────────────

function _autoPalette(n) {
  const cvs = document.createElement('canvas');
  cvs.width = cvs.height = 1;
  const ctx = cvs.getContext('2d');
  return Array.from({ length: n }, (_, i) => {
    ctx.fillStyle = `hsl(${Math.round((i / n) * 360)}, 65%, 50%)`;
    ctx.fillRect(0, 0, 1, 1);
    const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
    return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
  });
}

// Préfixe _sym : dashboard.js déclare aussi _esc (même raison que _symLoadValeurs)
function _symEsc(v) { return String(v ?? '').replace(/"/g, '&quot;'); }

// ── Délégation du clic sur le bouton palette ──────────────────────────────────

document.getElementById('couches-liste').addEventListener('click', e => {
  const btn = e.target.closest('.couche-style-btn');
  if (!btn) return;
  e.preventDefault();
  e.stopPropagation();
  openSymbologie(btn.dataset.couche);
});
