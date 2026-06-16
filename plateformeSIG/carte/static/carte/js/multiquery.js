/**
 * multiquery.js — Constructeur visuel de requete multicritere (§5.1.4)
 *
 * RM-01  Blocs conditions dynamiques (champ, operateur, valeur)
 * RM-02  Combinaison ET / OU globale entre conditions
 * RM-07  Critere "etat_general" pour les couches avec join_etat
 *
 * Depend de :
 *   map.js       → window.MAP
 *   layers.js    → window.COUCHES_META, window.onCouchesRendered
 *   selection.js → window.applySelectionFromPks
 *   (getCsrf() declare dans query.js)
 */

'use strict';

// ── Operateurs (meme jeu que query.js) ───────────────────────────────────────

const RM_OPS = [
  { val: '=',            label: '= egal a' },
  { val: '!=',           label: '≠ different de' },
  { val: '>',            label: '> superieur a' },
  { val: '>=',           label: '≥ sup. ou egal' },
  { val: '<',            label: '< inferieur a' },
  { val: '<=',           label: '≤ inf. ou egal' },
  { val: 'CONTIENT',     label: 'contient' },
  { val: 'COMMENCE_PAR', label: 'commence par' },
  { val: 'EST_NULL',     label: 'est vide (NULL)' },
  { val: 'ENTRE',        label: 'entre … et …' },
];

const RM_OPS_HTML = RM_OPS
  .map(op => `<option value="${op.val}">${op.label}</option>`)
  .join('');

// ── Etat du module ────────────────────────────────────────────────────────────

let _logique   = 'ET';
let _condSeq   = 0;        // compteur unique pour les IDs de blocs
let _allCouches = [];      // liste complete depuis onCouchesRendered

// ── Init ──────────────────────────────────────────────────────────────────────

function initMultiQueryPanel(couches) {
  _allCouches = couches;

  const selCouche = document.getElementById('rm-couche');
  if (!selCouche) return;

  // Peupler la liste des couches
  couches.forEach(c => {
    const opt = document.createElement('option');
    opt.value       = c.nom;
    opt.textContent = c.label;
    selCouche.appendChild(opt);
  });

  // Changement de couche → reset des conditions
  selCouche.addEventListener('change', () => {
    document.getElementById('rm-conditions').innerHTML = '';
    _condSeq = 0;
    document.getElementById('rm-result').style.display = 'none';
    // Reset actif seulement si un filtre est deja pose sur cette couche
    const btnReset = document.getElementById('btn-rm-reset');
    if (btnReset) btnReset.disabled = !window.FILTERED_LAYERS?.has(selCouche.value);
    _syncBtns();
    if (selCouche.value) _addCondition();
  });

  // Boutons ET / OU
  document.querySelectorAll('.rm-logique-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.rm-logique-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      _logique = btn.dataset.logique;
      // Mettre a jour les etiquettes des separateurs existants
      document.querySelectorAll('.rm-sep-label').forEach(el => {
        el.textContent = _logique;
      });
    });
  });

  // Bouton "+ Ajouter condition"
  document.getElementById('btn-rm-add')?.addEventListener('click', _addCondition);

  // Bouton "Filtrer"
  document.getElementById('btn-rm-exec')?.addEventListener('click', _executer);

  // Bouton "Reinitialiser le filtre"
  document.getElementById('btn-rm-reset')?.addEventListener('click', () => {
    const nom = selCouche.value;
    if (!nom) return;
    window.clearLayerFilter?.(nom);
    document.getElementById('btn-rm-reset').disabled = true;
    _setResult('<i class="fas fa-undo"></i> Filtre effacé — toutes les entités sont réaffichées', 'ok');
  });

  _syncBtns();
}

// ── Gestion des blocs condition ───────────────────────────────────────────────

function _getCoucheInfo() {
  const nom = document.getElementById('rm-couche')?.value ?? '';
  return _allCouches.find(c => c.nom === nom) ?? null;
}

function _buildChampOptions(coucheInfo) {
  const meta   = (window.COUCHES_META ?? {})[coucheInfo.nom] ?? {};
  const fields = meta.fields ?? [];
  let opts = fields
    .map(f => `<option value="${f}">${f}</option>`)
    .join('');
  if (coucheInfo.has_etat) {
    opts += '<option value="etat_general">--- Etat general ---</option>';
  }
  return opts;
}

function _addCondition() {
  const coucheInfo = _getCoucheInfo();
  if (!coucheInfo) return;

  const idx       = ++_condSeq;
  const container = document.getElementById('rm-conditions');

  // Separateur logique entre deux conditions existantes
  if (container.querySelectorAll('.rm-cond-block').length > 0) {
    const sep = document.createElement('div');
    sep.className = 'rm-sep';
    sep.dataset.sepIdx = idx;
    sep.innerHTML = `<span class="rm-sep-label">${_logique}</span>`;
    container.appendChild(sep);
  }

  const champOpts = _buildChampOptions(coucheInfo);

  const block = document.createElement('div');
  block.className   = 'rm-cond-block';
  block.dataset.idx = idx;
  block.innerHTML   = `
    <div class="rm-cond-head">
      <span class="rm-cond-num">#${idx}</span>
      <button class="rm-del-btn" title="Supprimer cette condition">
        <i class="fas fa-times"></i>
      </button>
    </div>
    <select class="rm-champ qr-select rm-sel-sm">${champOpts}</select>
    <select class="rm-op    qr-select rm-sel-sm">${RM_OPS_HTML}</select>
    <div class="rm-val-wrap">
      <input  type="text" class="rm-val  qr-input"  placeholder="Valeur…">
      <select             class="rm-vsel qr-select" style="display:none"></select>
      <input  type="text" class="rm-val2 qr-input"  placeholder="Max…" style="display:none">
    </div>
  `;

  container.appendChild(block);

  // Refs internes
  const selChamp  = block.querySelector('.rm-champ');
  const selOp     = block.querySelector('.rm-op');
  const inputVal  = block.querySelector('.rm-val');
  const selValEl  = block.querySelector('.rm-vsel');
  const inputVal2 = block.querySelector('.rm-val2');

  // Charger les valeurs du premier champ si disponibles
  _loadValeurs(coucheInfo.nom, selChamp.value, selValEl, () => {
    _syncValeurUI(selOp.value, inputVal, selValEl, inputVal2);
  });

  selChamp.addEventListener('change', () => {
    selValEl.innerHTML = '';
    _loadValeurs(coucheInfo.nom, selChamp.value, selValEl, () => {
      _syncValeurUI(selOp.value, inputVal, selValEl, inputVal2);
    });
  });

  selOp.addEventListener('change', () => {
    _syncValeurUI(selOp.value, inputVal, selValEl, inputVal2);
  });

  block.querySelector('.rm-del-btn').addEventListener('click', () => {
    _removeCondition(idx);
  });

  _syncBtns();
}

function _removeCondition(idx) {
  const container = document.getElementById('rm-conditions');

  // Supprimer le separateur associe (celui qui precede ou suit ce bloc)
  const sep = container.querySelector(`.rm-sep[data-sep-idx="${idx}"]`);
  if (sep) sep.remove();

  const block = container.querySelector(`.rm-cond-block[data-idx="${idx}"]`);
  if (block) block.remove();

  // S'il reste des separateurs en trop (ex. si c'etait le premier bloc),
  // supprimer le premier separateur orphelin
  const firstChild = container.firstElementChild;
  if (firstChild?.classList.contains('rm-sep')) firstChild.remove();

  _syncBtns();
}

// ── Autocomplete (meme logique que query.js) ──────────────────────────────────

function _loadValeurs(couche, champ, selEl, onDone) {
  if (!champ) { if (onDone) onDone(); return; }
  fetch(`/carte/api/couche/${couche}/champs/${champ}/valeurs/`)
    .then(r => r.ok ? r.json() : null)
    .then(data => {
      const valeurs = data?.valeurs ?? [];
      if (valeurs.length) {
        selEl.innerHTML =
          '<option value="">— choisir —</option>' +
          valeurs.map(v => `<option value="${v.valeur}">${v.label}</option>`).join('');
      } else {
        selEl.innerHTML = '';
      }
    })
    .catch(() => { selEl.innerHTML = ''; })
    .finally(() => { if (onDone) onDone(); });
}

function _syncValeurUI(op, inputVal, selEl, inputVal2) {
  const hasChoices = selEl.options.length > 1;

  // Defaut : input texte visible
  inputVal.style.display  = '';
  selEl.style.display     = 'none';
  inputVal2.style.display = 'none';

  if (op === 'EST_NULL') {
    inputVal.style.display = 'none';
  } else if (op === 'ENTRE') {
    inputVal2.style.display = '';
  } else if (hasChoices) {
    inputVal.style.display = 'none';
    selEl.style.display    = '';
  }
}

// ── Execution ─────────────────────────────────────────────────────────────────

async function _executer() {
  const coucheInfo = _getCoucheInfo();
  if (!coucheInfo) return;

  const blocks = document.querySelectorAll('#rm-conditions .rm-cond-block');
  if (!blocks.length) return;

  // Collecter les conditions
  const conditions = [];
  for (let i = 0; i < blocks.length; i++) {
    const block     = blocks[i];
    const champ     = block.querySelector('.rm-champ').value;
    const operateur = block.querySelector('.rm-op').value;
    const inputVal  = block.querySelector('.rm-val');
    const selEl     = block.querySelector('.rm-vsel');
    const inputVal2 = block.querySelector('.rm-val2');

    let valeur;
    if (operateur === 'EST_NULL') {
      valeur = null;
    } else if (operateur === 'ENTRE') {
      const v1 = inputVal.value.trim();
      const v2 = inputVal2.value.trim();
      if (!v1 || !v2) {
        _setResult(`Condition ${i + 1} : entrez les deux valeurs limites.`, 'error');
        return;
      }
      valeur = [v1, v2];
    } else if (selEl.style.display !== 'none' && selEl.value) {
      valeur = selEl.value;
    } else {
      valeur = inputVal.value.trim();
      if (!valeur) {
        _setResult(`Condition ${i + 1} : valeur manquante.`, 'error');
        return;
      }
    }

    conditions.push({ champ, operateur, valeur });
  }

  // Appel API
  _setResult('<i class="fas fa-spinner fa-spin"></i> Execution…', 'loading');
  const btnExec = document.getElementById('btn-rm-exec');
  if (btnExec) btnExec.disabled = true;

  try {
    const resp = await fetch('/carte/api/requete/multicritere/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken':  typeof getCsrf === 'function' ? getCsrf() : '',
      },
      body: JSON.stringify({
        couche:     coucheInfo.nom,
        conditions,
        logique:    _logique,
      }),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.erreur ?? resp.statusText);
    }

    const data = await resp.json();
    const n    = data.count;

    // BUG-L4-A — charger la couche si elle n'est pas encore dans MapLibre
    if (!window.LOADED_LAYERS?.has(coucheInfo.nom)) {
      _setResult('<i class="fas fa-spinner fa-spin"></i> Chargement de la couche…', 'loading');
      await loadLayer(coucheInfo.nom, 'visible');
    }

    // La requete filtre les entites affichees sur la carte
    window.applyLayerFilter?.(coucheInfo.nom, data.pks);
    const btnReset = document.getElementById('btn-rm-reset');
    if (btnReset) btnReset.disabled = false;

    _setResult(
      `<i class="fas fa-${n > 0 ? 'filter' : 'info-circle'}"></i> `
      + `Filtre appliqué — ${n} entité${n > 1 ? 's' : ''} affichée${n > 1 ? 's' : ''}`,
      n > 0 ? 'ok' : 'empty'
    );
  } catch (err) {
    _setResult(
      `<i class="fas fa-exclamation-circle"></i> ${err.message}`,
      'error'
    );
  } finally {
    if (btnExec) btnExec.disabled = false;
  }
}

// ── Helpers DOM ───────────────────────────────────────────────────────────────

function _setResult(html, type = '') {
  const el = document.getElementById('rm-result');
  if (!el) return;
  el.innerHTML     = html;
  el.style.display = html ? '' : 'none';
  el.className     = 'qr-preview' + (type ? ` qr-preview--${type}` : '');
}

function _syncBtns() {
  const hasCouche = !!document.getElementById('rm-couche')?.value;
  const nbConds   = document.querySelectorAll('#rm-conditions .rm-cond-block').length;

  const btnAdd  = document.getElementById('btn-rm-add');
  const btnExec = document.getElementById('btn-rm-exec');
  if (btnAdd)  btnAdd.disabled  = !hasCouche;
  if (btnExec) btnExec.disabled = (nbConds === 0);
}

// ── Bouton « Multicritère » par couche (curseurs dans la liste) ───────────────
// Ouvre le sous-panneau Multicritere pre-rempli avec la couche cliquee et rend
// la couche visible ; le resultat filtre les entites affichees sur la carte.

document.getElementById('couches-liste').addEventListener('click', e => {
  const btn = e.target.closest('.couche-multi-btn');
  if (!btn) return;
  e.preventDefault();
  e.stopPropagation();

  const nom = btn.dataset.couche;

  // 1. Rendre la couche visible
  const cb = document.querySelector(`input[data-couche="${nom}"]`);
  if (cb && !cb.checked) {
    cb.checked = true;
    cb.dispatchEvent(new Event('change', { bubbles: true }));
  }

  // 2. Afficher le nom de la couche dans l'en-tete + ouvrir le sous-panneau
  const lbl = document.getElementById('pg-multi-couche-label');
  if (lbl) lbl.textContent = window.COUCHES_META?.[nom]?.label ?? nom;
  if (typeof window.showPgPanel === 'function') window.showPgPanel('multi');

  // 3. Pre-selectionner la couche → cree la premiere condition
  const selCouche = document.getElementById('rm-couche');
  if (selCouche && selCouche.value !== nom) {
    selCouche.value = nom;
    selCouche.dispatchEvent(new Event('change'));
  }
});

// ── Hook onCouchesRendered (chaine apres query.js) ────────────────────────────

const _prevOnCouchesRenderedMulti = window.onCouchesRendered;
window.onCouchesRendered = function(couches) {
  if (typeof _prevOnCouchesRenderedMulti === 'function') _prevOnCouchesRenderedMulti(couches);
  initMultiQueryPanel(couches);
};
