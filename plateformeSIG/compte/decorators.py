"""
Décorateurs de contrôle d'accès par rôle (SEC-02 — §8.2).

Usage :
    @login_required
    @role_required('operateur', 'editeur')
    def ma_vue(request): ...

Toujours combiner avec @login_required pour garantir que
request.user est authentifié avant la vérification du rôle.
"""

from functools import wraps

from django.http import JsonResponse
from django.shortcuts import redirect

ROLE_HIERARCHY = {'visiteur': 0, 'operateur': 1, 'editeur': 2}


def role_level(role: str) -> int:
    return ROLE_HIERARCHY.get(role, -1)


def has_role(user, *required_roles) -> bool:
    return user.is_authenticated and user.role in required_roles


def api_login_required(view_func):
    """
    Remplace @login_required pour les endpoints API.

    Retourne JSON 403 (au lieu d'un redirect) quand l'utilisateur n'est pas
    authentifié, ce qui est le comportement attendu pour un client JavaScript
    (SEC-01 / CA-13).
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'erreur': 'Non authentifié'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped


def role_required(*roles):
    """
    Vérifie que l'utilisateur authentifié possède l'un des rôles autorisés.

    Retourne :
      - redirect('connexion') si l'utilisateur n'est pas authentifié
        (garde-fou si @login_required est absent)
      - JsonResponse 403 si le rôle est insuffisant
      - délègue à la vue si le rôle est autorisé
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('connexion')
            if request.user.role not in roles:
                return JsonResponse(
                    {'erreur': 'Accès refusé : rôle insuffisant'},
                    status=403,
                )
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
