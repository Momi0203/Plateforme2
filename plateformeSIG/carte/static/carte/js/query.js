/**
 * query.js — Requetes attributaires (API bas niveau + UI onglet Requete simple §5.1.3)
 *
 * Fonctions API :  requeteSimple(), requeteMulticritere(), requeteSpatiale(), getCsrf()
 * UI :             initQueryPanel(couches) — declenche via window.onCouchesRendered
 *
 * Depend de :
 *   map.js      → window.MAP
 *   layers.js   → window.COUCHES_META, window.onCouchesRendered
 *   selection.js → window.applySelectionFromPks
 */

'use strict';

// ── Fonctions API bas niveau ──────────────────────────────────────────────────

async function requeteSimple(couche, champ, operateur, valeur) {
  const resp = await fetch('/carte/api/requete/simple/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
    body: JSON.stringify({ couche, champ, operateur, valeur }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.erreur ?? resp.statusText);
  }
  return resp.json();   // { pks: [...], count: N }
}

async function requeteMulticritere(couche, conditions, logique = 'ET') {
  const resp = await fetch('/carte/api/requete/multicritere/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
    body: JSON.stringify({ couche, conditions, logique }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.erreur ?? resp.statusText);
  }
  return resp.json();   // { pks: [...], count: N }
}

async function requeteSpatiale(couche, type_spatial, geometrie_ref, distance_m = null) {
  const body = { couche, type_spatial, geometrie_ref };
  if (distance_m !== null) body.distance_m = distance_m;
  const resp = await fetch('/carte/api/requete/spatiale/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
    body: JSON.stringify(body),
  });
  return resp.ok ? (await resp.json()).pks : [];
}

function getCsrf() {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';
}

// ── Filtre d'affichage par couche ─────────────────────────────────────────────
// La requete par couche est un FILTRE : seules les entites correspondantes
// restent visibles sur la carte (MAP.setFilter), les autres sont masquees.
// Partage avec multiquery.js.

window.FILTERED_LAYERS = new Set();

window.applyLayerFilter = function (couche, pks) {
  const numPks = (pks ?? []).map(Number);
  const base   = `lyr-${couche}`;
  if (!MAP.getLayer(base)) return;
  // ['id'] accede au top-level id du feature (= pk Django).
  // Applique aussi au contour (-outline) et au label (-label) s'ils existent.
  const expr = ['in', ['id'], ['literal', numPks]];
  for (const suffix of ['', '-outline', '-label']) {
    if (MAP.getLayer(`${base}${suffix}`)) MAP.setFilter(`${base}${suffix}`, expr);
  }
  window.FILTERED_LAYERS.add(couche);
};

window.clearLayerFilter = function (couche) {
  const base = `lyr-${couche}`;
  for (const suffix of ['', '-outline', '-label']) {
    if (MAP.getLayer(`${base}${suffix}`)) MAP.setFilter(`${base}${suffix}`, null);
  }
  window.FILTERED_LAYERS.delete(couche);
};

// ── Operateurs (RS-02) ────────────────────────────────────────────────────────

const OPERATEURS = [
  { val: '=',            label: '= egal a' },
  { val: '!=',           label: '≠ different de' },
  { val: '>',            label: '> superieur a' },
  { val: '>=',           label: '≥ superieur ou egal' },
  { val: '<',            label: '< inferieur a' },
  { val: '<=',           label: '≤ inferieur ou egal' },
  { val: 'CONTIENT',     label: 'contient' },
  { val: 'COMMENCE_PAR', label: 'commence par' },
  { val: 'EST_NULL',     label: 'est vide (NULL)' },
  { val: 'ENTRE',        label: 'entre ... et ...' },
];

// ── UI ────────────────────────────────────────────────────────────────────────

function initQueryPanel(couches) {
  const selCouche  = document.getElementById('qr-couche');
  const selChamp   = document.getElementById('qr-champ');
  const selOp      = document.getElementById('qr-op');
  const inputVal   = document.getElementById('qr-val');
  const selVal     = document.getElementById('qr-val-sel');
  const inputVal2  = document.getElementById('qr-val2');
  const divPreview = document.getElementById('qr-preview');
  const btnPreview = document.getElementById('btn-qr-preview');
  const btnApply   = document.getElementById('btn-qr-apply');
  const btnReset   = document.getElementById('btn-qr-reset');
  const btnAddCond = document.getElementById('btn-qr-add-cond');
  const extraConds = document.getElementById('qr-extra-conditions');
  const logiqueFld = document.getElementById('qr-logique-field');

  if (!selCouche) return;  // onglet pas encore dans le DOM

  // Peupler les couches
  couches.forEach(c => {
    const opt = document.createElement('option');
    opt.value       = c.nom;
    opt.textContent = c.label;
    selCouche.appendChild(opt);
  });

  // Peupler les operateurs
  selOp.innerHTML = OPERATEURS
    .map(op => `<option value="${op.val}">${op.label}</option>`)
    .join('');

  let _lastPks = null;   // resultat de la derniere previsualisation reussie
  let _logique = 'ET';   // combinaison des conditions (ET / OU)

  // Toute modification d'un critere invalide la previsualisation
  function _invalidate() {
    _lastPks = null;
    btnApply.disabled = true;
    _setPreview();
  }

  // La saisie d'une valeur invalide aussi le resultat previsualise
  [inputVal, inputVal2].forEach(el => el.addEventListener('input', _invalidate));
  selVal.addEventListener('change', _invalidate);

  // ── Cascade couche → champ ────────────────────────────────────────────
  selCouche.addEventListener('change', () => {
    _lastPks = null;
    _setPreview();
    const nom = selCouche.value;

    selChamp.innerHTML = '<option value="">— choisir —</option>';
    selChamp.disabled  = !nom;
    selOp.disabled     = true;
    _disableValeur();
    _disableBtns();

    // Conditions supplementaires : remises a zero pour la nouvelle couche
    if (extraConds) extraConds.innerHTML = '';
    if (logiqueFld) logiqueFld.style.display = 'none';
    if (btnAddCond) btnAddCond.disabled = !nom;

    // Reset actif seulement si un filtre est deja pose sur cette couche
    if (btnReset) btnReset.disabled = !window.FILTERED_LAYERS.has(nom);

    if (!nom) return;

    const meta = (window.COUCHES_META ?? {})[nom];
    (meta?.fields ?? []).forEach(f => {
      const opt = document.createElement('option');
      opt.value = opt.textContent = f;
      selChamp.appendChild(opt);
    });
  });

  // ── Champ → activer operateur + tentative autocomplete (RS-03) ────────
  selChamp.addEventListener('change', async () => {
    _lastPks = null;
    _setPreview();
    const champ = selChamp.value;
    if (!champ) { selOp.disabled = true; _disableValeur(); _disableBtns(); return; }

    selOp.disabled = false;
    selVal.innerHTML = '';   // reset autocomplete precedent

    // Reset valeur affichee selon operateur courant
    _syncValeurUI();

    // Tentative de chargement des valeurs closes (RS-03)
    const couche = selCouche.value;
    try {
      const resp = await fetch(`/carte/api/couche/${couche}/champs/${champ}/valeurs/`);
      if (resp.ok) {
        const data    = await resp.json();
        const valeurs = data.valeurs ?? [];
        if (valeurs.length) {
          selVal.innerHTML =
            '<option value="">— choisir —</option>' +
            valeurs.map(v => `<option value="${v.valeur}">${v.label}</option>`).join('');
          _syncValeurUI();  // re-syncroniser maintenant qu'on a des choices
        }
      }
    } catch { /* pas d'autocomplete : input texte reste */ }
  });

  // ── Operateur → adapter le(s) input(s) valeur ────────────────────────
  selOp.addEventListener('change', () => {
    _lastPks = null;
    _setPreview();
    _syncValeurUI();
  });

  // ── Logique ET / OU entre conditions ──────────────────────────────────
  document.querySelectorAll('.qr-logique-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.qr-logique-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      _logique = btn.dataset.logique;
      // Mettre a jour les etiquettes des separateurs existants
      extraConds.querySelectorAll('.rm-sep-label').forEach(el => { el.textContent = _logique; });
      _invalidate();
    });
  });

  // ── Conditions supplementaires (combinees par ET/OU) ──────────────────

  if (btnAddCond) btnAddCond.addEventListener('click', _addExtraCondition);

  function _addExtraCondition() {
    const nom  = selCouche.value;
    if (!nom) return;
    const meta   = (window.COUCHES_META ?? {})[nom];
    const fields = meta?.fields ?? [];
    if (!fields.length) return;

    // Separateur ET/OU (la condition principale existe toujours au-dessus)
    const sep = document.createElement('div');
    sep.className = 'rm-sep';
    sep.innerHTML = `<span class="rm-sep-label">${_logique}</span>`;
    extraConds.appendChild(sep);

    const block = document.createElement('div');
    block.className = 'rm-cond-block';
    block.innerHTML = `
      <div class="rm-cond-head">
        <span class="rm-cond-num"></span>
        <button type="button" class="rm-del-btn" title="Supprimer cette condition">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <select class="qrx-champ qr-select rm-sel-sm">
        ${fields.map(f => `<option value="${f}">${f}</option>`).join('')}
      </select>
      <select class="qrx-op qr-select rm-sel-sm">
        ${OPERATEURS.map(op => `<option value="${op.val}">${op.label}</option>`).join('')}
      </select>
      <div class="rm-val-wrap">
        <input  type="text" class="qrx-val  qr-input"  placeholder="Valeur…">
        <select             class="qrx-vsel qr-select" style="display:none"></select>
        <input  type="text" class="qrx-val2 qr-input"  placeholder="Valeur max…" style="display:none">
      </div>`;
    extraConds.appendChild(block);

    const selChampX = block.querySelector('.qrx-champ');
    const selOpX    = block.querySelector('.qrx-op');
    const inputX    = block.querySelector('.qrx-val');
    const selValX   = block.querySelector('.qrx-vsel');
    const inputX2   = block.querySelector('.qrx-val2');

    // Autocomplete du champ initial puis a chaque changement de champ
    _loadValeursBlock(nom, selChampX.value, selValX,
      () => _syncBlockValeurUI(selOpX.value, inputX, selValX, inputX2));

    selChampX.addEventListener('change', () => {
      selValX.innerHTML = '';
      _loadValeursBlock(nom, selChampX.value, selValX,
        () => _syncBlockValeurUI(selOpX.value, inputX, selValX, inputX2));
      _invalidate();
    });
    selOpX.addEventListener('change', () => {
      _syncBlockValeurUI(selOpX.value, inputX, selValX, inputX2);
      _invalidate();
    });
    [inputX, inputX2].forEach(el => el.addEventListener('input', _invalidate));
    selValX.addEventListener('change', _invalidate);

    block.querySelector('.rm-del-btn').addEventListener('click', () => {
      sep.remove();
      block.remove();
      _renumberBlocks();
      if (logiqueFld) logiqueFld.style.display =
        extraConds.querySelector('.rm-cond-block') ? '' : 'none';
      _invalidate();
    });

    _renumberBlocks();
    if (logiqueFld) logiqueFld.style.display = '';
    _invalidate();
  }

  function _renumberBlocks() {
    extraConds.querySelectorAll('.rm-cond-num').forEach((el, i) => {
      el.textContent = `Condition #${i + 2}`;   // la condition principale = #1
    });
  }

  // Autocomplete des valeurs closes pour un bloc supplementaire
  function _loadValeursBlock(couche, champ, selEl, onDone) {
    if (!champ) { onDone?.(); return; }
    fetch(`/carte/api/couche/${couche}/champs/${champ}/valeurs/`)
      .then(r => (r.ok ? r.json() : null))
      .then(data => {
        const valeurs = data?.valeurs ?? [];
        selEl.innerHTML = valeurs.length
          ? '<option value="">— choisir —</option>' +
            valeurs.map(v => `<option value="${v.valeur}">${v.label}</option>`).join('')
          : '';
      })
      .catch(() => { selEl.innerHTML = ''; })
      .finally(() => onDone?.());
  }

  function _syncBlockValeurUI(op, inputX, selValX, inputX2) {
    const hasChoice = selValX.options.length > 1;
    inputX.style.display  = '';
    selValX.style.display = 'none';
    inputX2.style.display = 'none';
    if (op === 'EST_NULL') {
      inputX.style.display = 'none';
    } else if (op === 'ENTRE') {
      inputX2.style.display = '';
    } else if (hasChoice) {
      inputX.style.display  = 'none';
      selValX.style.display = '';
    }
  }

  // Collecte la condition d'un bloc supplementaire (null si invalide)
  function _collectBlock(block, numero) {
    const champ     = block.querySelector('.qrx-champ').value;
    const operateur = block.querySelector('.qrx-op').value;
    const inputX    = block.querySelector('.qrx-val');
    const selValX   = block.querySelector('.qrx-vsel');
    const inputX2   = block.querySelector('.qrx-val2');

    let valeur;
    if (operateur === 'EST_NULL') {
      valeur = null;
    } else if (operateur === 'ENTRE') {
      const v1 = inputX.value.trim();
      const v2 = inputX2.value.trim();
      if (!v1 || !v2) {
        _setPreview(`Condition #${numero} : entrez les deux valeurs limites.`, 'error');
        return null;
      }
      valeur = [v1, v2];
    } else if (selValX.style.display !== 'none' && selValX.value !== '') {
      valeur = selValX.value;
    } else {
      valeur = inputX.value.trim();
      if (!valeur) {
        _setPreview(`Condition #${numero} : entrez une valeur.`, 'error');
        return null;
      }
    }
    return { champ, operateur, valeur };
  }

  // Condition principale + blocs supplementaires → { couche, conditions[] }
  function _collectAllConditions() {
    const main = _collectParams();
    if (!main) return null;

    const conditions = [{ champ: main.champ, operateur: main.operateur, valeur: main.valeur }];
    const blocks = extraConds.querySelectorAll('.rm-cond-block');
    for (let i = 0; i < blocks.length; i++) {
      const cond = _collectBlock(blocks[i], i + 2);
      if (!cond) return null;
      conditions.push(cond);
    }
    return { couche: main.couche, conditions };
  }

  // Masque/affiche les inputs valeur selon l'operateur et la presence de choices
  function _syncValeurUI() {
    const op        = selOp.value;
    const hasChoice = selVal.options.length > 1;

    // Reinitialiser
    inputVal.style.display  = '';
    selVal.style.display    = 'none';
    inputVal2.style.display = 'none';
    inputVal.disabled = false;
    selVal.disabled   = true;
    inputVal2.disabled = true;

    if (op === 'EST_NULL') {
      inputVal.style.display = 'none';
      inputVal.disabled = true;
    } else if (op === 'ENTRE') {
      inputVal2.style.display = '';
      inputVal2.disabled = false;
    } else if (hasChoice) {
      inputVal.style.display = 'none';
      inputVal.disabled = true;
      selVal.style.display = '';
      selVal.disabled = false;
    }

    // Activer le bouton Preview des que l'operateur est choisi
    btnPreview.disabled = (selOp.disabled || !selChamp.value);
    btnApply.disabled   = true;
  }

  // ── Previsualiser (RS-04) ─────────────────────────────────────────────
  // 1 condition → API requete simple ; ≥ 2 conditions → API multicritere ET/OU.
  btnPreview.addEventListener('click', async () => {
    const all = _collectAllConditions();
    if (!all) return;

    _setPreview('<i class="fas fa-spinner fa-spin"></i>', 'loading');
    btnApply.disabled = true;
    _lastPks = null;

    try {
      let result;
      if (all.conditions.length === 1) {
        const c = all.conditions[0];
        result = await requeteSimple(all.couche, c.champ, c.operateur, c.valeur);
      } else {
        result = await requeteMulticritere(all.couche, all.conditions, _logique);
      }
      _lastPks = result.pks;
      const n   = result.count;
      const det = all.conditions.length > 1
        ? ` (${all.conditions.length} conditions, ${_logique})`
        : '';
      _setPreview(
        `<i class="fas fa-${n > 0 ? 'check-circle' : 'info-circle'}"></i> ${n} resultat${n !== 1 ? 's' : ''}${det}`,
        n > 0 ? 'ok' : 'empty'
      );
      btnApply.disabled = (n === 0);
    } catch (err) {
      _setPreview(`<i class="fas fa-exclamation-circle"></i> ${err.message}`, 'error');
    }
  });

  // ── Filtrer (RS-05) — la requete filtre les entites affichees sur la carte ──
  btnApply.addEventListener('click', async () => {
    if (!_lastPks) return;
    const couche = selCouche.value;
    if (!couche) return;

    // BUG-L4-A — charger la couche si elle n'est pas encore dans MapLibre
    if (!window.LOADED_LAYERS?.has(couche)) {
      _setPreview('<i class="fas fa-spinner fa-spin"></i> Chargement de la couche…', 'loading');
      await loadLayer(couche, 'visible');
    }

    window.applyLayerFilter(couche, _lastPks);
    if (btnReset) btnReset.disabled = false;

    const n = _lastPks.length;
    _setPreview(
      `<i class="fas fa-filter"></i> Filtre appliqué — ${n} entité${n > 1 ? 's' : ''} affichée${n > 1 ? 's' : ''}`,
      'applied'
    );
  });

  // ── Reinitialiser : efface le filtre, reaffiche toutes les entites ──────
  if (btnReset) btnReset.addEventListener('click', () => {
    const nom = selCouche.value;
    if (!nom) return;
    window.clearLayerFilter(nom);
    btnReset.disabled = true;
    _setPreview('<i class="fas fa-undo"></i> Filtre effacé — toutes les entités sont réaffichées', 'ok');
  });

  // ── Helpers ───────────────────────────────────────────────────────────

  function _collectParams() {
    const couche    = selCouche.value;
    const champ     = selChamp.value;
    const operateur = selOp.value;
    if (!couche || !champ || !operateur) return null;

    let valeur;
    if (operateur === 'EST_NULL') {
      valeur = null;
    } else if (operateur === 'ENTRE') {
      const v1 = inputVal.value.trim();
      const v2 = inputVal2.value.trim();
      if (!v1 || !v2) { _setPreview('Entrez les deux valeurs limites.', 'error'); return null; }
      valeur = [v1, v2];
    } else if (selVal.style.display !== 'none' && selVal.value !== '') {
      valeur = selVal.value;
    } else {
      valeur = inputVal.value.trim();
      if (!valeur) { _setPreview('Entrez une valeur.', 'error'); return null; }
    }

    return { couche, champ, operateur, valeur };
  }

  // Mise a jour du bandeau de resultat
  function _setPreview(html = '', type = '') {
    divPreview.innerHTML     = html;
    divPreview.style.display = html ? '' : 'none';
    divPreview.className     = 'qr-preview' + (type ? ` qr-preview--${type}` : '');
  }

  function _disableValeur() {
    inputVal.disabled  = true;
    selVal.disabled    = true;
    inputVal2.disabled = true;
    inputVal.style.display  = '';
    selVal.style.display    = 'none';
    inputVal2.style.display = 'none';
  }

  function _disableBtns() {
    btnPreview.disabled = true;
    btnApply.disabled   = true;
  }
}

// ── Bouton « Requête » par couche (entonnoir dans la liste) ───────────────────
// Classe dediee .couche-filter-btn (≠ .couche-style-btn de la symbologie → aucune
// collision). Ouvre le sous-panneau Requete pre-rempli avec la couche cliquee,
// rend la couche visible ; le resultat filtre les entites affichees sur la carte.

document.getElementById('couches-liste').addEventListener('click', e => {
  const btn = e.target.closest('.couche-filter-btn');
  if (!btn) return;
  e.preventDefault();
  e.stopPropagation();

  const nom = btn.dataset.couche;

  // 1. Rendre la couche visible (coche la case → layers.js charge/affiche)
  const cb = document.querySelector(`input[data-couche="${nom}"]`);
  if (cb && !cb.checked) {
    cb.checked = true;
    cb.dispatchEvent(new Event('change', { bubbles: true }));
  }

  // 2. Afficher le nom de la couche dans l'en-tete + ouvrir le sous-panneau
  const lbl = document.getElementById('pg-requete-couche-label');
  if (lbl) lbl.textContent = window.COUCHES_META?.[nom]?.label ?? nom;
  if (typeof window.showPgPanel === 'function') window.showPgPanel('requete');

  // 3. Pre-selectionner la couche → declenche la cascade vers les champs
  const selCouche = document.getElementById('qr-couche');
  if (selCouche && selCouche.value !== nom) {
    selCouche.value = nom;
    selCouche.dispatchEvent(new Event('change'));
  }
});

// ── Hook sur window.onCouchesRendered ─────────────────────────────────────────
// Enchain apres le callback de layers.js (qui charge les couches sur la carte).

const _prevOnCouchesRendered = window.onCouchesRendered;
window.onCouchesRendered = function(couches) {
  if (typeof _prevOnCouchesRendered === 'function') _prevOnCouchesRendered(couches);
  initQueryPanel(couches);
};
