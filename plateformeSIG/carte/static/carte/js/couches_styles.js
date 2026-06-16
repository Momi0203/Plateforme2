/**
 * couches_styles.js — Styles spéciaux déclenchés après chargement des couches.
 *
 * Enregistre des hooks dans window.LAYER_POST_LOAD (défini par layers.js).
 * Chaque hook est appelé une seule fois juste après MAP.addLayer().
 *
 * ── tronçons de séguias ──────────────────────────────────────────────────────
 *   SY-08  largeur de tracé proportionnelle au débit (m³/s)
 *   SY-09  couleur par nature de matériau — valeurs lues dynamiquement depuis
 *          GET /carte/api/couche/troncons_seguias/champs/nature/valeurs/
 *          (règle §11.3 : aucune valeur de CHOICES codée en dur dans le JS)
 */

'use strict';

// ── Palette catégorielle ──────────────────────────────────────────────────────
// 8 teintes fixes pour les cas usuels (≤ 8 natures), puis HSL cyclique.

const _PALETTE_CAT = [
  '#e74c3c',   // rouge
  '#3498db',   // bleu
  '#2ecc71',   // vert
  '#f39c12',   // orange
  '#9b59b6',   // violet
  '#1abc9c',   // turquoise
  '#e67e22',   // orange foncé
  '#34495e',   // gris anthracite
];

function _catPalette(n) {
  if (n <= _PALETTE_CAT.length) return _PALETTE_CAT.slice(0, n);
  // Au-delà de 8 valeurs : teintes HSL uniformément réparties
  const cvs = document.createElement('canvas');
  cvs.width = cvs.height = 1;
  const ctx = cvs.getContext('2d');
  return Array.from({ length: n }, (_, i) => {
    ctx.fillStyle = `hsl(${Math.round((i / n) * 360)}, 65%, 48%)`;
    ctx.fillRect(0, 0, 1, 1);
    const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
    return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
  });
}

// ── Hook troncons_seguias ─────────────────────────────────────────────────────

window.LAYER_POST_LOAD = window.LAYER_POST_LOAD || {};

window.LAYER_POST_LOAD['troncons_seguias'] = async function () {
  const layerId = 'lyr-troncons_seguias';

  // ── SY-08 — largeur proportionnelle au débit ──────────────────────────────
  // Utilise coalesce pour traiter les débits null (→ 0.05 m³/s par défaut).
  MAP.setPaintProperty(layerId, 'line-width', [
    'interpolate', ['linear'],
    ['coalesce', ['to-number', ['get', 'debit'], 0], 0.05],
    0.05, 1,   //  0.05 m³/s → 1 px
    0.5,  3,   //  0.5  m³/s → 3 px
    2.0,  8,   //  2.0  m³/s → 8 px
  ]);

  console.info('[styles] troncons_seguias SY-08 appliqué');

  // ── SY-09 — couleur par nature matériau (dynamique) ───────────────────────
  try {
    const resp = await fetch(
      '/carte/api/couche/troncons_seguias/champs/nature/valeurs/'
    );
    if (!resp.ok) throw new Error(`HTTP ${resp.status} — ${resp.statusText}`);

    const json    = await resp.json();
    const valeurs = json.valeurs ?? [];

    if (!valeurs.length) {
      console.warn('[styles] SY-09 : aucune valeur « nature » retournée par l\'API');
      return;
    }

    const palette = _catPalette(valeurs.length);

    // Expression MapLibre 'match' construite dynamiquement — §11.3
    const matchExpr = ['match', ['get', 'nature']];
    valeurs.forEach(({ valeur }, i) => {
      matchExpr.push(String(valeur));
      matchExpr.push(palette[i]);
    });
    matchExpr.push('#aaaaaa');   // couleur de repli pour valeurs non listées

    MAP.setPaintProperty(layerId, 'line-color', matchExpr);

    console.info(
      '[styles] troncons_seguias SY-09 appliqué — %d nature(s) : %s',
      valeurs.length,
      valeurs.map(v => v.valeur).join(', ')
    );

  } catch (err) {
    console.warn('[styles] SY-09 impossible :', err.message);
  }
};
