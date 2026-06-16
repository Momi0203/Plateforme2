from functools import wraps
from django.shortcuts import render

# Tous les agents ORMVA (lecture + A3 responsable)
ROLES_PLAN = ('operateur', 'editeur', 'administrateur')
# Création / modification A1 et A2 (brouillon)
ROLES_ECRITURE_A1_A2 = ('operateur', 'administrateur')


def require_role(*roles):
    """
    Restreint une vue aux utilisateurs dont le rôle est dans `roles`.
    Les superusers passent toujours.  Si `roles` est vide, seuls les
    superusers sont autorisés.  Toujours combiner avec @login_required
    (placé en décorateur externe) qui gère le cas non-authentifié.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            user_role = getattr(request.user, 'role', None)
            if roles and user_role in roles:
                return view_func(request, *args, **kwargs)
            return render(request, '403.html', status=403)
        return _wrapped
    return decorator
