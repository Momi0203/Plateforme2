from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .layers import LAYER_REGISTRY
from compte.decorators import ROLE_HIERARCHY


@login_required
def index(request):
    groupes = {}
    for cle, meta in LAYER_REGISTRY.items():
        groupes.setdefault(meta["groupe"], []).append({"cle": cle, "label": meta["label"]})
    role = getattr(request.user, 'role', 'visiteur')
    return render(request, "carte/index.html", {
        "groupes": groupes,
        "user_role": role,
        "user_role_level": ROLE_HIERARCHY.get(role, 0),
    })
