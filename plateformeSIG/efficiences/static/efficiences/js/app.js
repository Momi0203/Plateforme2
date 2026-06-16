(function () {
    'use strict';

    const cfg = window.EFFICIENCES_CFG || {};
    const form = document.getElementById('formCalcul');
    if (!form) return;

    const selectOuvrage = document.getElementById('selectOuvrage');
    const cardLiaisons = document.getElementById('cardLiaisons');
    const seguiasBox = document.getElementById('seguiasBox');
    const feedbackLiaisons = document.getElementById('feedbackLiaisons');
    const zoneResultats = document.getElementById('zoneResultats');
    const btnEnregistrer = document.getElementById('btnEnregistrerLiaisons');
    const btnLancer = document.getElementById('btnLancerCalcul');

    let map = null;
    let perimetreLayer = null;
    let ouvragesLayer = null;
    let seguiasLayer = null;
    let donneesCarte = null;
    let ouvrageMarkers = {};
    let liaisonsSauvegardees = false;

    // ────────────────────────────────────────────── Utils ──
    function getCsrfToken() {
        const input = form.querySelector('input[name=csrfmiddlewaretoken]');
        return input ? input.value : '';
    }

    function parseOuvrage(value) {
        if (!value) return null;
        const [type, id] = value.split(':');
        return { type, id: parseInt(id, 10) };
    }

    function urlSeguiasDisponibles(type, id) {
        return cfg.urlSeguias.replace('TYPE', encodeURIComponent(type)).replace('/0/', '/' + id + '/');
    }

    function setFeedback(el, msg, kind) {
        const cls = kind === 'ok' ? 'ok' : (kind === 'error' ? 'error' : '');
        el.innerHTML = msg
            ? `<div class="info-box ${cls}"><i class="fas fa-${kind === 'ok' ? 'check-circle' : (kind === 'error' ? 'exclamation-triangle' : 'info-circle')}"></i><span>${msg}</span></div>`
            : '';
    }

    // ────────────────────────────────────────────── Carte Leaflet ──
    const SEGUIA_COLORS = { 'principale': '#1a6fa8', 'secondaire': '#5ba4cf', 'tertiaire': '#9ecae1' };

    async function initCarte() {
        map = L.map('perimetre-map');
        const basemaps = {
            'OpenStreetMap':      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap contributors', maxZoom: 18 }),
            'ESRI Topographique': L.esri.basemapLayer('Topographic'),
            'ESRI Satellite':     L.esri.basemapLayer('Imagery'),
            'ESRI Streets':       L.esri.basemapLayer('Streets'),
        };
        basemaps['OpenStreetMap'].addTo(map);
        map.setView([31.5, -5], 8);

        try {
            const resp = await fetch(cfg.urlCarte);
            donneesCarte = await resp.json();
        } catch (err) {
            console.warn('Carte indisponible :', err);
            return;
        }

        const bounds = [];

        if (donneesCarte.perimetre && donneesCarte.perimetre.geometrie) {
            perimetreLayer = L.geoJSON(JSON.parse(donneesCarte.perimetre.geometrie), {
                style: { color: '#f0a500', weight: 2.5, fillOpacity: 0.18, fillColor: '#f0a500' },
            }).addTo(map);
            perimetreLayer.bindTooltip(donneesCarte.perimetre.nom, { sticky: true });
            bounds.push(perimetreLayer.getBounds());
        }

        const colors = (donneesCarte.styles && donneesCarte.styles.colors) || {};
        const labels = (donneesCarte.styles && donneesCarte.styles.labels) || {};

        ouvragesLayer = L.layerGroup().addTo(map);
        (donneesCarte.ouvrages || []).forEach(o => {
            if (!o.geometrie) return;
            const geo = JSON.parse(o.geometrie);
            const color = colors[o.type] || '#1a1a2e';
            const isBarrage = o.type === 'barrage_retenue';

            let marker;
            if (geo.type === 'Point') {
                marker = L.circleMarker([geo.coordinates[1], geo.coordinates[0]], {
                    radius: 8,
                    color: '#fff', weight: 2,
                    fillColor: color, fillOpacity: 1,
                });
                if (isBarrage) {
                    marker.setStyle({ radius: 9 });
                }
            } else {
                marker = L.geoJSON(geo, {
                    style: { color, weight: 3, fillOpacity: .3, fillColor: color },
                });
            }
            marker.bindTooltip(`<strong>${labels[o.type] || o.type}</strong><br>${o.nom}`, { sticky: true });
            marker.on('click', () => {
                selectOuvrage.value = `${o.type}:${o.id}`;
                selectOuvrage.dispatchEvent(new Event('change'));
            });
            marker.addTo(ouvragesLayer);
            ouvrageMarkers[`${o.type}:${o.id}`] = marker;
            if (marker.getBounds) {
                bounds.push(marker.getBounds());
            } else if (marker.getLatLng) {
                bounds.push(L.latLngBounds([marker.getLatLng()]));
            }
        });

        seguiasLayer = L.layerGroup().addTo(map);
        (donneesCarte.seguias || []).forEach(s => {
            if (!s.geometrie) return;
            const color = SEGUIA_COLORS[s.type_deguia] || '#1a6fa8';
            const layer = L.geoJSON(JSON.parse(s.geometrie), {
                style: {
                    color,
                    weight: 2.5,
                    dashArray: s.type_decoulement === 'dalot' ? '6,4' : null,
                },
            });
            layer.bindTooltip(`<i>Séguia</i> ${s.nom}`, { sticky: true });
            layer.addTo(seguiasLayer);
        });

        if (bounds.length) {
            const merged = bounds.reduce((acc, b) => acc.extend(b), L.latLngBounds(bounds[0].getSouthWest(), bounds[0].getNorthEast()));
            map.fitBounds(merged, { padding: [20, 20] });
        }

        // Contrôle couches
        const overlays = {};
        if (perimetreLayer) overlays['Périmètre'] = perimetreLayer;
        if (ouvragesLayer)  overlays['Ouvrages de tête'] = ouvragesLayer;
        if (seguiasLayer)   overlays['Séguias'] = seguiasLayer;
        L.control.layers(basemaps, overlays, { collapsed: true }).addTo(map);

        // Légende
        const legend = L.control({ position: 'bottomright' });
        legend.onAdd = () => {
            const div = L.DomUtil.create('div');
            div.style.cssText = 'background:rgba(255,255,255,0.92);padding:8px 10px;border-radius:6px;font-size:11px;line-height:1.5;box-shadow:0 1px 4px rgba(0,0,0,.15);min-width:140px;';
            div.innerHTML =
                '<div style="font-weight:700;margin-bottom:5px;">Légende</div>' +
                '<div style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:16px;height:4px;background:#f0a500;border-radius:2px;"></span> Périmètre</div>' +
                '<div style="display:flex;align-items:center;gap:6px;margin-top:3px;"><span style="display:inline-block;width:12px;height:12px;background:#c0392b;border-radius:50%;"></span> Ouvrage de tête</div>' +
                '<div style="display:flex;align-items:center;gap:6px;margin-top:3px;"><span style="display:inline-block;width:16px;height:4px;background:#1a6fa8;border-radius:2px;"></span> Séguia principale</div>' +
                '<div style="display:flex;align-items:center;gap:6px;margin-top:3px;"><span style="display:inline-block;width:16px;height:4px;background:#5ba4cf;border-radius:2px;"></span> Séguia secondaire</div>' +
                '<div style="display:flex;align-items:center;gap:6px;margin-top:3px;"><span style="display:inline-block;width:16px;height:4px;background:#9ecae1;border-radius:2px;"></span> Séguia tertiaire</div>';
            return div;
        };
        legend.addTo(map);
    }

    // ────────────────────────────────────────────── Sélection ouvrage ──
    async function onOuvrageChange() {
        const parsed = parseOuvrage(selectOuvrage.value);
        liaisonsSauvegardees = false;
        btnLancer.disabled = true;
        zoneResultats.innerHTML = '';
        feedbackLiaisons.innerHTML = '';

        // Reset all markers to default style
        Object.entries(ouvrageMarkers).forEach(([key, marker]) => {
            if (marker.setStyle) {
                const isActive = key === selectOuvrage.value;
                marker.setStyle({ weight: isActive ? 4 : 2, radius: isActive ? 11 : 8 });
            }
        });

        if (!parsed) {
            cardLiaisons.style.display = 'none';
            return;
        }

        cardLiaisons.style.display = '';
        seguiasBox.innerHTML = '<div style="text-align:center; padding:20px; color:#888;"><span class="spinner"></span> Chargement des séguias…</div>';

        try {
            const resp = await fetch(urlSeguiasDisponibles(parsed.type, parsed.id), {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });
            const data = await resp.json();
            if (!data.success) {
                seguiasBox.innerHTML = `<div class="info-box error"><i class="fas fa-exclamation-triangle"></i><span>${data.error || 'Erreur de chargement.'}</span></div>`;
                return;
            }
            renderSeguias(data.seguias, data.nb_lies, data.nb_total);
        } catch (err) {
            seguiasBox.innerHTML = `<div class="info-box error"><i class="fas fa-exclamation-triangle"></i><span>Erreur réseau : ${err.message}</span></div>`;
        }
    }

    // ────────────────────────────────────────────── Render séguias ──
    function renderSeguias(seguias, nbLies, nbTotal) {
        if (!seguias.length) {
            seguiasBox.innerHTML = `
                <div class="info-box error" style="margin-bottom:0;">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Aucune séguia n'est définie dans ce périmètre. Créez-en via le module Diagnostic.</span>
                </div>`;
            return;
        }

        const header = `
            <div style="font-size:12.5px; color:#666; margin-bottom:10px;">
                <strong>${nbLies}</strong> séguia${nbLies > 1 ? 's' : ''} actuellement liée${nbLies > 1 ? 's' : ''} sur <strong>${nbTotal}</strong> dans le périmètre.
            </div>
            <div style="border:1px solid #f0e8d8; border-radius:10px; overflow:hidden;">
                <div class="seguia-row" style="background:#1a1a2e; color:#fff; font-weight:700; font-size:11.5px; text-transform:uppercase; letter-spacing:.3px;">
                    <div></div>
                    <div>Séguia</div>
                    <div>Type</div>
                    <div>Tronçons</div>
                    <div>Nature (1er)</div>
                    <div style="text-align:right;">Long. tot. (m)</div>
                    <div style="text-align:right;">Débit 1er tronçon (m³/s)</div>
                    <div>Écoulement (1er)</div>
                </div>
        `;

        const rows = seguias.map(s => {
            const checked = s.is_linked ? 'checked' : '';
            const cls = s.is_linked ? 'is-linked' : '';
            const ecoul = s.type_decoulement === 'dalot'
                ? '<span class="badge badge-dalot">Dalot</span>'
                : (s.type_decoulement ? '<span class="badge badge-ciel">Ciel ouvert</span>' : '—');
            return `
                <label class="seguia-row ${cls}" for="seg-${s.id}" style="cursor:pointer;">
                    <input type="checkbox" id="seg-${s.id}" value="${s.id}" data-was-linked="${s.is_linked ? 1 : 0}" ${checked}>
                    <div class="sg-nom">${escapeHtml(s.nom)}</div>
                    <div class="sg-type">${escapeHtml(s.type || '—')}</div>
                    <div style="text-align:center;">${s.nb_troncons != null ? s.nb_troncons : '—'}</div>
                    <div class="sg-type">${escapeHtml(s.nature || '—')}</div>
                    <div class="sg-longueur">${s.longueur != null ? Number(s.longueur).toFixed(1) : '—'}</div>
                    <div class="sg-debit">${s.debit != null ? Number(s.debit).toFixed(3) : '—'}</div>
                    <div>${ecoul}</div>
                </label>
            `;
        }).join('');

        seguiasBox.innerHTML = header + rows + '</div>';

        // Update visual on check change
        seguiasBox.querySelectorAll('input[type=checkbox]').forEach(cb => {
            cb.addEventListener('change', () => {
                cb.closest('.seguia-row').classList.toggle('is-linked', cb.checked);
                liaisonsSauvegardees = false;
                btnLancer.disabled = true;
                setFeedback(feedbackLiaisons,
                    'Modifications non enregistrées. Cliquez sur « Enregistrer les liaisons ».', 'info');
            });
        });
    }

    function escapeHtml(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
        }[c]));
    }

    // ────────────────────────────────────────────── Enregistrer liaisons ──
    async function enregistrerLiaisons() {
        const parsed = parseOuvrage(selectOuvrage.value);
        if (!parsed) return;

        const checkboxes = seguiasBox.querySelectorAll('input[type=checkbox]:checked');
        const formData = new FormData();
        formData.append('ouvrage_type', parsed.type);
        formData.append('ouvrage_id', parsed.id);
        checkboxes.forEach(cb => formData.append('seguia_ids', cb.value));

        btnEnregistrer.disabled = true;
        const original = btnEnregistrer.innerHTML;
        btnEnregistrer.innerHTML = '<span class="spinner"></span> Enregistrement…';

        try {
            const resp = await fetch(cfg.urlEnregistrer, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
            });
            const data = await resp.json();
            if (data.success) {
                liaisonsSauvegardees = true;
                btnLancer.disabled = data.total_lies === 0;
                let msg = `Liaisons enregistrées : <strong>${data.total_lies}</strong> séguia${data.total_lies > 1 ? 's' : ''} liée${data.total_lies > 1 ? 's' : ''}.`;
                if (data.created || data.deleted) {
                    msg += ` (+${data.created} créée${data.created > 1 ? 's' : ''}, −${data.deleted} supprimée${data.deleted > 1 ? 's' : ''})`;
                }
                if (data.total_lies > 0) {
                    msg += ' Vous pouvez maintenant lancer le calcul.';
                }
                setFeedback(feedbackLiaisons, msg, 'ok');
                // Update data-was-linked attributes
                seguiasBox.querySelectorAll('input[type=checkbox]').forEach(cb => {
                    cb.dataset.wasLinked = cb.checked ? '1' : '0';
                });
            } else {
                setFeedback(feedbackLiaisons, data.error || 'Erreur inconnue.', 'error');
            }
        } catch (err) {
            setFeedback(feedbackLiaisons, 'Erreur réseau : ' + err.message, 'error');
        } finally {
            btnEnregistrer.innerHTML = original;
            btnEnregistrer.disabled = false;
        }
    }

    // ────────────────────────────────────────────── Lancer calcul ──
    async function lancerCalcul() {
        const parsed = parseOuvrage(selectOuvrage.value);
        if (!parsed) return;

        if (!liaisonsSauvegardees) {
            setFeedback(feedbackLiaisons, 'Enregistrez d\'abord les liaisons.', 'error');
            return;
        }

        btnLancer.disabled = true;
        const original = btnLancer.innerHTML;
        btnLancer.innerHTML = '<span class="spinner"></span> Calcul en cours…';
        zoneResultats.innerHTML = '';

        const formData = new FormData();
        formData.append('ouvrage_type', parsed.type);
        formData.append('ouvrage_id', parsed.id);

        try {
            const resp = await fetch(cfg.urlCalcul, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
            });
            const data = await resp.json();
            if (data.success) {
                zoneResultats.innerHTML = data.html;
                zoneResultats.scrollIntoView({ behavior: 'smooth', block: 'start' });
                // Câbler le bouton Valider + modale de confirmation
                const btnVal    = zoneResultats.querySelector('#btn-valider-eff');
                const modal     = zoneResultats.querySelector('#modal-confirm-validation');
                const btnAnnul  = zoneResultats.querySelector('#btn-annuler-validation');
                const btnConf   = zoneResultats.querySelector('#btn-confirmer-validation');

                if (btnVal && modal) {
                    // Ouvrir la modale
                    btnVal.addEventListener('click', function () {
                        modal.style.display = 'flex';
                    });

                    // Fermer sur "Annuler"
                    btnAnnul.addEventListener('click', function () {
                        modal.style.display = 'none';
                    });

                    // Fermer en cliquant l'arrière-plan
                    modal.addEventListener('click', function (e) {
                        if (e.target === modal) modal.style.display = 'none';
                    });

                    // Confirmer → appel API validation
                    btnConf.addEventListener('click', function () {
                        btnConf.disabled = true;
                        btnConf.innerHTML = '<span class="spinner"></span> Validation…';
                        fetch(btnVal.dataset.url, {
                            method: 'POST',
                            headers: { 'X-CSRFToken': btnVal.dataset.csrf },
                        })
                        .then(r => r.json())
                        .then(d => {
                            if (d.ok) {
                                modal.style.display = 'none';
                                btnVal.outerHTML =
                                    '<span style="display:inline-flex;align-items:center;gap:5px;' +
                                    'padding:6px 14px;border-radius:8px;font-size:12.5px;font-weight:700;' +
                                    'background:#1a7a4a;color:#fff;">' +
                                    '<i class="fas fa-check-circle"></i> Validé</span>';
                            } else {
                                modal.style.display = 'none';
                                btnConf.disabled = false;
                                btnConf.innerHTML = '<i class="fas fa-check-circle"></i> Confirmer';
                            }
                        })
                        .catch(() => {
                            modal.style.display = 'none';
                            btnConf.disabled = false;
                            btnConf.innerHTML = '<i class="fas fa-check-circle"></i> Confirmer';
                        });
                    });
                }
            } else {
                zoneResultats.innerHTML = `<div class="info-box error"><i class="fas fa-exclamation-triangle"></i><span>${data.error || 'Erreur inconnue.'}</span></div>`;
            }
        } catch (err) {
            zoneResultats.innerHTML = `<div class="info-box error"><i class="fas fa-exclamation-triangle"></i><span>Erreur réseau : ${err.message}</span></div>`;
        } finally {
            btnLancer.innerHTML = original;
            btnLancer.disabled = false;
        }
    }

    // ────────────────────────────────────────────── Bind ──
    selectOuvrage.addEventListener('change', onOuvrageChange);
    btnEnregistrer.addEventListener('click', enregistrerLiaisons);
    btnLancer.addEventListener('click', lancerCalcul);
    form.addEventListener('submit', e => e.preventDefault());

    initCarte();
})();

