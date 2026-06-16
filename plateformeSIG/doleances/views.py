import csv
import datetime
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.decorators.http import require_POST

from .models import (
    Requete, PieceJointeRequete, CommentaireRequete, HistoriqueStatut,
    EXTENSIONS_AUTORISEES, TAILLE_MAX_KO, STATUT_CHOICES,
)
from .forms import RequeteForm, CommentaireForm, ChangerStatutForm

# ── Workflow ──────────────────────────────────────────────────────────────────
# (statut_courant → [(statut_nouveau, roles_autorises, commentaire_requis)])
_TRANSITIONS = {
    'soumise': [
        ('en_cours',  ('operateur', 'administrateur'), False),
        ('rejetee',   ('administrateur',),             True),
    ],
    'en_cours': [
        ('en_attente', ('operateur', 'administrateur'), True),
        ('traitee',    ('operateur', 'administrateur'), True),
        ('rejetee',    ('administrateur',),             True),
    ],
    'en_attente': [
        ('en_cours', ('operateur', 'administrateur'), False),
    ],
    'traitee': [
        ('cloturee', ('administrateur',), False),
        ('en_cours', ('administrateur',), True),
    ],
}

_STATUT_LABELS = dict(STATUT_CHOICES)


def _est_staff(user):
    return user.role in ('operateur', 'administrateur') or user.is_superuser


def _est_admin(user):
    return user.role == 'administrateur' or user.is_superuser


def _peut_voir_requete(user, requete):
    return (
        requete.emetteur == user
        or requete.assignee == user
        or _est_staff(user)
    )


def _transitions_pour_user(statut_courant, user):
    """Retourne [(statut_nouveau, commentaire_requis)] selon le rôle."""
    role = getattr(user, 'role', '')
    return [
        (s_new, cr)
        for s_new, roles, cr in _TRANSITIONS.get(statut_courant, [])
        if role in roles or user.is_superuser
    ]


# ── Liste (mes requêtes) ──────────────────────────────────────────────────────

@login_required
def liste(request):
    # SC-05 : émetteur OU assigné (pas les requêtes des autres utilisateurs)
    qs = Requete.objects.filter(
        Q(emetteur=request.user) | Q(assignee=request.user)
    ).select_related('perimetre').distinct()

    filtre_type   = request.GET.get('type', '')
    filtre_statut = request.GET.get('statut', '')
    if filtre_type:
        qs = qs.filter(type_requete=filtre_type)
    if filtre_statut:
        qs = qs.filter(statut=filtre_statut)

    paginator  = Paginator(qs, 25)
    page_obj   = paginator.get_page(request.GET.get('page'))
    maintenant = timezone.now()

    return render(request, 'doleances/liste.html', {
        'page_obj':      page_obj,
        'filtre_type':   filtre_type,
        'filtre_statut': filtre_statut,
        'maintenant':    maintenant,
    })


# ── Nouvelle requête ──────────────────────────────────────────────────────────

@login_required
def nouvelle(request):
    if request.method == 'POST':
        form = RequeteForm(request.POST)

        if form.is_valid():
            # Matrice des droits : TYPE_PERIMETRE interdit aux visiteurs
            if (form.cleaned_data.get('type_requete') == 'perimetre'
                    and getattr(request.user, 'role', '') == 'visiteur'):
                form.add_error('type_requete',
                               "Les visiteurs ne peuvent pas soumettre une requête de type terrain.")
                return render(request, 'doleances/nouvelle.html', {'form': form})

            requete = form.save(commit=False)
            requete.emetteur = request.user
            requete.save()

            fichiers   = request.FILES.getlist('fichiers')
            erreurs_pj = []

            if len(fichiers) > 5:
                erreurs_pj.append("Maximum 5 pièces jointes par requête.")
                fichiers = fichiers[:5]

            for f in fichiers:
                ext = f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
                taille_ko = f.size // 1024
                if ext not in EXTENSIONS_AUTORISEES:
                    erreurs_pj.append(f"'{f.name}' : format non autorisé.")
                    continue
                if taille_ko > TAILLE_MAX_KO:
                    erreurs_pj.append(f"'{f.name}' dépasse 10 Mo.")
                    continue
                PieceJointeRequete.objects.create(
                    requete=requete, fichier=f,
                    nom_original=f.name, taille_ko=taille_ko,
                )

            for e in erreurs_pj:
                messages.warning(request, e)

            messages.success(request, f"Requête {requete.reference} soumise avec succès.")
            return redirect('doleances:detail', pk=requete.pk)
    else:
        form = RequeteForm()

    return render(request, 'doleances/nouvelle.html', {'form': form})


# ── Détail ────────────────────────────────────────────────────────────────────

@login_required
def detail(request, pk):
    requete = get_object_or_404(
        Requete.objects.select_related('perimetre', 'emetteur', 'assignee'),
        pk=pk,
    )
    if not _peut_voir_requete(request.user, requete):
        raise PermissionDenied

    est_staff = _est_staff(request.user)

    commentaires = (
        requete.commentaires.select_related('auteur').all()
        if est_staff
        else requete.commentaires.filter(interne=False).select_related('auteur')
    )
    historique = requete.historique_statuts.select_related('auteur').all()

    statuts_fermes = ('cloturee', 'rejetee')
    peut_commenter = (
        requete.statut not in statuts_fermes
        and (requete.emetteur == request.user or est_staff)
    )

    nb_pj = requete.pieces_jointes.count()
    transitions = _transitions_pour_user(requete.statut, request.user) if est_staff else []

    return render(request, 'doleances/detail.html', {
        'requete':          requete,
        'commentaires':     commentaires,
        'historique':       historique,
        'commentaire_form': CommentaireForm() if peut_commenter else None,
        'peut_commenter':   peut_commenter,
        'peut_ajouter_pj':  peut_commenter and nb_pj < 5,
        'nb_pj':            nb_pj,
        'est_staff':        est_staff,
        'est_admin':        _est_admin(request.user),
        'transitions':      transitions,
    })


# ── Ajouter un commentaire ────────────────────────────────────────────────────

@login_required
@require_POST
def commenter(request, pk):
    requete = get_object_or_404(Requete, pk=pk)

    if not _peut_voir_requete(request.user, requete):
        raise PermissionDenied

    if requete.statut in ('cloturee', 'rejetee'):
        messages.error(request, "Impossible d'ajouter un commentaire : la requête est clôturée ou rejetée.")
        return redirect('doleances:detail', pk=pk)

    est_staff = _est_staff(request.user)
    form = CommentaireForm(request.POST)

    if form.is_valid():
        commentaire = form.save(commit=False)
        commentaire.requete = requete
        commentaire.auteur  = request.user
        if not est_staff:
            commentaire.interne = False
        commentaire.save()

        f = request.FILES.get('pj_complementaire')
        if f:
            nb_pj = requete.pieces_jointes.count()
            if nb_pj >= 5:
                messages.warning(request, "Limite de 5 pièces jointes atteinte.")
            else:
                ext = f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
                taille_ko = f.size // 1024
                if ext not in EXTENSIONS_AUTORISEES:
                    messages.warning(request, f"'{f.name}' : format non autorisé.")
                elif taille_ko > TAILLE_MAX_KO:
                    messages.warning(request, f"'{f.name}' dépasse 10 Mo.")
                else:
                    PieceJointeRequete.objects.create(
                        requete=requete, fichier=f,
                        nom_original=f.name, taille_ko=taille_ko,
                    )
        messages.success(request, "Commentaire ajouté.")
    else:
        messages.error(request, "Le commentaire ne peut pas être vide.")

    return redirect('doleances:detail', pk=pk)


# ── Changer le statut ─────────────────────────────────────────────────────────

@login_required
def changer_statut(request, pk):
    requete = get_object_or_404(
        Requete.objects.select_related('perimetre', 'emetteur', 'assignee'),
        pk=pk,
    )
    if not _est_staff(request.user):
        raise PermissionDenied

    est_admin = _est_admin(request.user)
    transitions = _transitions_pour_user(requete.statut, request.user)

    if not transitions:
        messages.info(request, "Aucune transition possible depuis ce statut avec votre rôle.")
        return redirect('doleances:detail', pk=pk)

    transitions_choices = [
        (s, _STATUT_LABELS.get(s, s)) for s, _ in transitions
    ]
    # Dict pour le template : {statut_nouveau: commentaire_requis}
    commentaire_requis_map = {s: cr for s, cr in transitions}

    from django.contrib.auth import get_user_model
    User = get_user_model()
    assignee_qs = (
        User.objects.filter(
            role__in=('operateur', 'administrateur')
        ).order_by('last_name', 'first_name')
        if est_admin else None
    )

    if request.method == 'POST':
        form = ChangerStatutForm(transitions_choices, assignee_qs, request.POST)
        if form.is_valid():
            nouveau_statut = form.cleaned_data['nouveau_statut']
            commentaire    = (form.cleaned_data.get('commentaire') or '').strip()

            # Vérification transition valide
            if nouveau_statut not in commentaire_requis_map:
                form.add_error('nouveau_statut', 'Transition non autorisée.')
            elif commentaire_requis_map[nouveau_statut] and not commentaire:
                form.add_error('commentaire', 'Un commentaire est obligatoire pour cette transition.')
            else:
                # Historique
                HistoriqueStatut.objects.create(
                    requete=requete,
                    statut_precedent=requete.statut,
                    statut_nouveau=nouveau_statut,
                    auteur=request.user,
                    commentaire=commentaire,
                )

                requete.statut = nouveau_statut

                if nouveau_statut == 'traitee':
                    reponse = (form.cleaned_data.get('reponse_officielle') or '').strip()
                    if reponse:
                        requete.reponse = reponse
                    requete.date_traitement = timezone.now()

                if nouveau_statut == 'cloturee':
                    requete.date_cloture = timezone.now()

                if est_admin and 'assignee' in form.cleaned_data:
                    requete.assignee = form.cleaned_data['assignee']

                requete.save()

                label = _STATUT_LABELS.get(nouveau_statut, nouveau_statut)
                messages.success(request, f"Statut mis à jour : {label}.")
                return redirect('doleances:detail', pk=pk)
    else:
        form = ChangerStatutForm(
            transitions_choices, assignee_qs,
            initial={'assignee': requete.assignee_id},
        )

    return render(request, 'doleances/changer_statut.html', {
        'requete':               requete,
        'form':                  form,
        'commentaire_requis_map': commentaire_requis_map,
        'est_admin':             est_admin,
    })


# ── Tableau de bord ───────────────────────────────────────────────────────────

@login_required
def tableau_de_bord(request):
    if not _est_staff(request.user):
        raise PermissionDenied

    from diagnostic.models import Perimetre

    qs_all = Requete.objects.select_related('perimetre', 'emetteur', 'assignee')

    # Compteurs F-DD-18
    compteurs = {
        'soumises':  qs_all.filter(statut='soumise').count(),
        'en_cours':  qs_all.filter(statut='en_cours').count(),
        'traitees':  qs_all.filter(statut='traitee').count(),
        'critiques': qs_all.filter(urgence='critique').exclude(
            statut__in=('traitee', 'cloturee', 'rejetee')
        ).count(),
    }

    # Filtres
    filtre_type    = request.GET.get('type', '')
    filtre_urgence = request.GET.get('urgence', '')
    filtre_statut  = request.GET.get('statut', '')
    filtre_perim   = request.GET.get('perimetre', '')
    q              = request.GET.get('q', '')

    qs = qs_all
    if filtre_type:    qs = qs.filter(type_requete=filtre_type)
    if filtre_urgence: qs = qs.filter(urgence=filtre_urgence)
    if filtre_statut:  qs = qs.filter(statut=filtre_statut)
    if filtre_perim:   qs = qs.filter(perimetre_id=filtre_perim)
    if q:
        qs = qs.filter(
            Q(reference__icontains=q) | Q(titre__icontains=q) |
            Q(nom_emetteur__icontains=q) |
            Q(emetteur__first_name__icontains=q) | Q(emetteur__last_name__icontains=q)
        )

    paginator = Paginator(qs, 25)
    page_obj  = paginator.get_page(request.GET.get('page'))
    perimetres = Perimetre.objects.order_by('ksar_village')

    return render(request, 'doleances/tableau_de_bord.html', {
        'page_obj':       page_obj,
        'compteurs':      compteurs,
        'perimetres':     perimetres,
        'filtre_type':    filtre_type,
        'filtre_urgence': filtre_urgence,
        'filtre_statut':  filtre_statut,
        'filtre_perim':   filtre_perim,
        'q':              q,
        'est_admin':      _est_admin(request.user),
    })


# ── Export CSV (F-DD-20) ──────────────────────────────────────────────────────

@login_required
def export_csv(request):
    if not _est_admin(request.user):
        raise PermissionDenied

    qs = Requete.objects.select_related('perimetre', 'emetteur').order_by('-date_soumission')

    filtre_type    = request.GET.get('type', '')
    filtre_urgence = request.GET.get('urgence', '')
    filtre_statut  = request.GET.get('statut', '')
    filtre_perim   = request.GET.get('perimetre', '')
    q              = request.GET.get('q', '')

    if filtre_type:    qs = qs.filter(type_requete=filtre_type)
    if filtre_urgence: qs = qs.filter(urgence=filtre_urgence)
    if filtre_statut:  qs = qs.filter(statut=filtre_statut)
    if filtre_perim:   qs = qs.filter(perimetre_id=filtre_perim)
    if q:
        qs = qs.filter(
            Q(reference__icontains=q) | Q(titre__icontains=q) |
            Q(nom_emetteur__icontains=q) |
            Q(emetteur__first_name__icontains=q) | Q(emetteur__last_name__icontains=q)
        )

    today = datetime.date.today().strftime('%Y%m%d')
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="doleances_{today}.csv"'
    response.write('﻿')  # BOM UTF-8 pour Excel

    writer = csv.writer(response)
    writer.writerow([
        'Référence', 'Type', 'Urgence', 'Statut',
        'Périmètre', 'Date soumission', 'Émetteur',
    ])

    for req in qs:
        perimetre_str = str(req.perimetre) if req.perimetre else ''
        if req.emetteur:
            emetteur_str = req.emetteur.get_full_name() or req.emetteur.username
        else:
            emetteur_str = req.nom_emetteur or ''
        writer.writerow([
            req.reference,
            req.get_type_requete_display(),
            req.get_urgence_display(),
            req.get_statut_display(),
            perimetre_str,
            localtime(req.date_soumission).strftime('%d/%m/%Y %H:%M'),
            emetteur_str,
        ])

    return response


# ── Carte des requêtes (F-DD-19) ──────────────────────────────────────────────

_URGENCE_PRIO = {'critique': 4, 'haute': 3, 'normale': 2, 'faible': 1}


@login_required
def carte_requetes(request):
    if not _est_admin(request.user):
        raise PermissionDenied

    from diagnostic.models import Perimetre

    # Requêtes ouvertes liées à un périmètre
    requetes_vals = (
        Requete.objects
        .filter(
            perimetre__isnull=False,
            statut__in=('soumise', 'en_cours', 'en_attente', 'traitee'),
        )
        .values('perimetre_id', 'urgence')
    )

    # Agrégation par périmètre
    stats = {}
    for r in requetes_vals:
        pid = r['perimetre_id']
        if pid not in stats:
            stats[pid] = {'count': 0, 'prio': 0, 'urgence_max': 'faible'}
        stats[pid]['count'] += 1
        prio = _URGENCE_PRIO.get(r['urgence'], 0)
        if prio > stats[pid]['prio']:
            stats[pid]['prio'] = prio
            stats[pid]['urgence_max'] = r['urgence']

    perimetres = (
        Perimetre.objects
        .filter(pk__in=list(stats.keys()))
        .only('pk', 'ksar_village', 'commune_territoriale', 'geometrie')
    )

    features = []
    nb_sans_geometrie = 0
    tdb_url = reverse('doleances:tableau_de_bord')

    for p in perimetres:
        if not p.geometrie:
            nb_sans_geometrie += 1
            continue
        geom = p.geometrie
        center = geom if geom.geom_type == 'Point' else geom.centroid
        s = stats[p.pk]
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [center.x, center.y]},
            'properties': {
                'id':          p.pk,
                'nom':         str(p),
                'nb_requetes': s['count'],
                'urgence_max': s['urgence_max'],
                'url_tdb':     f'{tdb_url}?perimetre={p.pk}',
            },
        })

    geojson = json.dumps({'type': 'FeatureCollection', 'features': features})

    return render(request, 'doleances/carte.html', {
        'geojson':           geojson,
        'nb_features':       len(features),
        'nb_sans_geometrie': nb_sans_geometrie,
        'nb_perimetres':     len(stats),
    })
