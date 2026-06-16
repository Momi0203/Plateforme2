/* ============================================================================
 * Réseau hydrographique « ouvrage de tête » — affichage personnalisable.
 *
 * Symbologie graduée à N classes (échelle log du grid_code), avec couleur,
 * épaisseurs min/max et nombre de classes réglables par l'utilisateur, plus un
 * filtre « détail réseau » (min_grid_code) qui recharge les données.
 * Préférences mémorisées en localStorage (clé « reseauStyle »).
 *
 * Utilisé par toutes les cartes de l'app analyse_hydrologique
 * (détail BV, lancer analyse, résultat d'analyse).
 *
 * Usage :
 *   ReseauPersonnalisable.init(map, {
 *       url:       "{% url 'bv_reseau_geojson' bv.pk %}",
 *       gridMax:   {{ reseau_grid_max|default:0 }},
 *       basemaps:  basemaps,        // dict des fonds de carte
 *       bvLayer:   bvLayer,         // couche polygone du BV (optionnel)
 *       statusEl:  document.getElementById('reseau-status'),  // optionnel
 *   });
 * ==========================================================================*/
window.ReseauPersonnalisable = (function () {
    "use strict";

    var O_MIN = 0.45, O_MAX = 0.95;                     // opacité (échelle fixe)
    var DEFAUT = { color: "#1a6fa8", wMin: 0.6, wMax: 5.0, nbClasses: 3 };

    function chargerStyle() {
        try {
            return Object.assign({}, DEFAUT, JSON.parse(localStorage.getItem("reseauStyle") || "null") || {});
        } catch (e) {
            return Object.assign({}, DEFAUT);
        }
    }
    function sauverStyle(s) {
        try { localStorage.setItem("reseauStyle", JSON.stringify(s)); } catch (e) { /* ignore */ }
    }

    function init(map, opts) {
        opts = opts || {};
        var url      = opts.url;
        var gridMax  = opts.gridMax || 0;
        var statusEl = opts.statusEl || null;
        var style    = chargerStyle();

        var reseauLayer = null, legend = null;
        var curLogMin = 0, curLogMax = 1, curGcMin = null, curGcMax = null;

        var layersControl = L.control.layers(opts.basemaps || {}, {}, { collapsed: true }).addTo(map);
        if (opts.bvLayer) layersControl.addOverlay(opts.bvLayer, "Bassin versant");

        // ── Classification log(grid_code) -> N classes ───────────────────────
        function classeDe(gc) {
            if (gc === null || gc === undefined || gc <= 0) return 0;
            if (curLogMax === curLogMin) return Math.floor((style.nbClasses - 1) / 2);
            var t = (Math.log(gc) - curLogMin) / (curLogMax - curLogMin);
            var idx = Math.floor(t * style.nbClasses);
            if (idx >= style.nbClasses) idx = style.nbClasses - 1;
            if (idx < 0) idx = 0;
            return idx;
        }
        function frac(i)    { return style.nbClasses <= 1 ? 0.5 : i / (style.nbClasses - 1); }
        function poids(i)   { return style.wMin + frac(i) * (style.wMax - style.wMin); }
        function opacite(i) { return O_MIN + frac(i) * (O_MAX - O_MIN); }
        function styleTroncon(f) {
            var i = classeDe(f.properties.grid_code);
            return { color: style.color, weight: poids(i), opacity: opacite(i), lineCap: "round" };
        }
        function bornesClasse(i) {
            if (curGcMin === null) return null;
            var lo = Math.round(Math.exp(curLogMin + (i / style.nbClasses) * (curLogMax - curLogMin)));
            var hi = Math.round(Math.exp(curLogMin + ((i + 1) / style.nbClasses) * (curLogMax - curLogMin)));
            return [lo, hi];
        }

        function construireLegende() {
            if (legend) { map.removeControl(legend); legend = null; }
            legend = L.control({ position: "bottomright" });
            legend.onAdd = function () {
                var div = L.DomUtil.create("div");
                div.style.cssText = "background:rgba(255,255,255,0.92);padding:8px 10px;border-radius:6px;font-size:11px;line-height:1.5;box-shadow:0 1px 4px rgba(0,0,0,.15);";
                var html = '<div style="font-weight:700;margin-bottom:4px;">Hiérarchie du réseau (' + style.nbClasses + ' classes)</div>';
                for (var i = 0; i < style.nbClasses; i++) {
                    var b = bornesClasse(i);
                    var lbl = b ? (b[0] + "–" + b[1]) : "—";
                    html += '<div style="display:flex;align-items:center;gap:6px;">' +
                            '<span style="display:inline-block;width:22px;height:' + poids(i) + 'px;background:' + style.color + ';opacity:' + opacite(i) + ';"></span> ' +
                            'grid_code ' + lbl + '</div>';
                }
                div.innerHTML = html;
                return div;
            };
            legend.addTo(map);
        }

        function appliquer() {
            if (reseauLayer) { reseauLayer.setStyle(styleTroncon); construireLegende(); }
        }

        function setStatus(txt, color) {
            if (statusEl) { statusEl.textContent = txt; statusEl.style.color = color || "#888"; }
        }

        function charger(val) {
            if (reseauLayer) { map.removeLayer(reseauLayer); layersControl.removeLayer(reseauLayer); reseauLayer = null; }
            if (legend)      { map.removeControl(legend); legend = null; }
            setStatus("Chargement du réseau…");
            var u = url;
            if (val !== undefined && val !== "auto") {
                u += (u.indexOf("?") >= 0 ? "&" : "?") + "min_grid_code=" + val;
            }
            fetch(u)
                .then(function (r) { return r.json(); })
                .then(function (fc) {
                    if (!fc.features || !fc.features.length) { setStatus("Aucun tronçon (avec ce filtre)"); return; }
                    var gcv = fc.features
                        .map(function (f) { return f.properties.grid_code; })
                        .filter(function (v) { return v !== null && v !== undefined && v > 0; });
                    curLogMin = gcv.length ? Math.log(Math.min.apply(null, gcv)) : 0;
                    curLogMax = gcv.length ? Math.log(Math.max.apply(null, gcv)) : 1;
                    curGcMin  = gcv.length ? Math.min.apply(null, gcv) : null;
                    curGcMax  = gcv.length ? Math.max.apply(null, gcv) : null;

                    reseauLayer = L.geoJSON(fc, {
                        style: styleTroncon,
                        onEachFeature: function (f, layer) {
                            var gc = (f.properties.grid_code === null || f.properties.grid_code === undefined) ? "—" : f.properties.grid_code;
                            layer.bindTooltip("Tronçon #" + f.id + " · grid_code " + gc);
                        }
                    }).addTo(map);

                    setStatus(fc.features.length + " tronçons · grid_code " + (curGcMin === null ? "—" : curGcMin) + " → " + (curGcMax === null ? "—" : curGcMax));
                    layersControl.addOverlay(reseauLayer, "Réseau hydrographique");
                    construireLegende();
                })
                .catch(function (err) {
                    console.error(err);
                    setStatus("Erreur de chargement du réseau", "#c0392b");
                });
        }

        // ── Panneau de personnalisation (contrôle Leaflet, en haut à droite) ──
        var panneau = L.control({ position: "topright" });
        panneau.onAdd = function () {
            var div = L.DomUtil.create("div");
            div.style.cssText = "background:rgba(255,255,255,0.95);padding:8px 10px;border-radius:6px;font-size:11px;box-shadow:0 1px 4px rgba(0,0,0,.18);min-width:178px;";
            var optionsGrid = '<option value="auto">Automatique</option><option value="0">Réseau complet (grid faible)</option>';
            for (var k = 1; k <= gridMax; k++) {
                optionsGrid += '<option value="' + k + '">grid_code ≥ ' + k + (k === gridMax ? " (grid fort)" : "") + '</option>';
            }
            div.innerHTML =
                '<div style="font-weight:700;margin-bottom:5px;"><i class="fas fa-sliders-h"></i> Réseau</div>' +
                '<label style="display:block;margin-bottom:4px;">Détail : <select id="rp-grid" style="font-size:11px;">' + optionsGrid + '</select></label>' +
                '<label style="display:block;margin-bottom:4px;">Couleur : <input type="color" id="rp-color" value="' + style.color + '" style="width:30px;height:18px;padding:0;border:1px solid #ccc;vertical-align:middle;"></label>' +
                '<label style="display:block;margin-bottom:4px;">Classes : <input type="number" id="rp-nb" value="' + style.nbClasses + '" min="2" max="8" step="1" style="width:48px;font-size:11px;"></label>' +
                '<label style="display:block;">Épaisseur : <input type="number" id="rp-wmin" value="' + style.wMin + '" min="0.2" max="6" step="0.2" style="width:46px;font-size:11px;"> → <input type="number" id="rp-wmax" value="' + style.wMax + '" min="1" max="14" step="0.5" style="width:46px;font-size:11px;"></label>';
            L.DomEvent.disableClickPropagation(div);
            L.DomEvent.disableScrollPropagation(div);
            return div;
        };
        panneau.addTo(map);

        // Branchement des contrôles (le DOM existe après addTo)
        var elGrid  = document.getElementById("rp-grid");
        var elColor = document.getElementById("rp-color");
        var elNb    = document.getElementById("rp-nb");
        var elWmin  = document.getElementById("rp-wmin");
        var elWmax  = document.getElementById("rp-wmax");

        function majStyle() {
            if (elColor) style.color = elColor.value || DEFAUT.color;
            if (elNb)    style.nbClasses = Math.max(2, Math.min(8, parseInt(elNb.value, 10) || DEFAUT.nbClasses));
            if (elWmin)  style.wMin = parseFloat(elWmin.value) || DEFAUT.wMin;
            if (elWmax)  style.wMax = parseFloat(elWmax.value) || DEFAUT.wMax;
            if (style.wMax < style.wMin) style.wMax = style.wMin;
            sauverStyle(style);
            appliquer();
        }
        if (elColor) elColor.addEventListener("input",  majStyle);
        if (elNb)    elNb.addEventListener("change",    majStyle);
        if (elWmin)  elWmin.addEventListener("change",  majStyle);
        if (elWmax)  elWmax.addEventListener("change",  majStyle);
        if (elGrid)  elGrid.addEventListener("change",  function (e) { charger(e.target.value); });

        charger("auto");
        return { charger: charger, appliquer: appliquer };
    }

    return { init: init };
})();
