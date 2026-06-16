/**
 * access.js — Helpers contrôle d'accès côté client (Phase 2 §5 Droits).
 *
 * Lit window.USER_ROLE et window.USER_ROLE_LEVEL injectés par carte/views.py.
 * Doit être chargé avant tout autre script qui utilise hasRole / minRole.
 *
 * API :
 *   hasRole('operateur', 'editeur')  → true si le rôle est dans la liste
 *   minRole('operateur')             → true si niveau >= operateur (0=visiteur, 1=opérateur, 2=éditeur)
 */

'use strict';

const _ROLE_LEVEL = { visiteur: 0, operateur: 1, editeur: 2 };

window.hasRole = (...roles) => roles.includes(window.USER_ROLE ?? 'visiteur');

window.minRole = (min) =>
  (window.USER_ROLE_LEVEL ?? 0) >= (_ROLE_LEVEL[min] ?? 99);
