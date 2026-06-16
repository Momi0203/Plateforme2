import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from .models import Requete, HistoriqueStatut, STATUT_CHOICES

logger = logging.getLogger(__name__)

_STATUT_LABELS = dict(STATUT_CHOICES)


def _destinataires_admins():
    """Retourne la liste des emails des administrateurs et superusers."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    emails = set(
        User.objects.filter(role='administrateur', email__gt='')
        .values_list('email', flat=True)
    ) | set(
        User.objects.filter(is_superuser=True, email__gt='')
        .values_list('email', flat=True)
    )
    return list(emails)


def _envoyer(sujet, corps, destinataires):
    """Envoie un email en ignorant les erreurs pour ne pas bloquer la transaction."""
    if not destinataires:
        return
    try:
        send_mail(
            subject=sujet,
            message=corps,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=destinataires,
            fail_silently=False,
        )
    except Exception as exc:
        logger.error("Échec envoi email '%s' → %s : %s", sujet, destinataires, exc)


# ── Signal 1 : nouvelle requête urgente → admins (F-DD-06) ───────────────────

@receiver(post_save, sender=Requete)
def notifier_admin_urgence(sender, instance, created, **kwargs):
    """Notifie les admins à la création d'une requête haute ou critique."""
    if not created or instance.urgence not in ('haute', 'critique'):
        return

    destinataires = _destinataires_admins()
    if not destinataires:
        return

    if instance.emetteur:
        nom_emetteur = instance.emetteur.get_full_name() or instance.emetteur.username
    else:
        nom_emetteur = instance.nom_emetteur or 'Inconnu'

    perimetre_ligne = f"Périmètre  : {instance.perimetre}\n" if instance.perimetre else ''
    description_ext = instance.description[:500] + ('…' if len(instance.description) > 500 else '')

    sujet = f"[HydroPlan SIG] Requête {instance.get_urgence_display().upper()} — {instance.reference}"
    corps = (
        f"Une nouvelle requête de niveau {instance.get_urgence_display().upper()} a été soumise.\n\n"
        f"Référence  : {instance.reference}\n"
        f"Titre      : {instance.titre}\n"
        f"Type       : {instance.get_type_requete_display()}\n"
        f"Urgence    : {instance.get_urgence_display()}\n"
        f"Émetteur   : {nom_emetteur}\n"
        f"{perimetre_ligne}"
        f"\nDescription :\n{description_ext}\n\n"
        f"Connectez-vous à HydroPlan SIG pour traiter cette requête.\n\n"
        f"---\nHydroPlan SIG — ORMVA Tafilalet / Midelt"
    )

    _envoyer(sujet, corps, destinataires)


# ── Signal 2 : changement de statut → émetteur (F-DD-03/CDC §8.5) ────────────

@receiver(post_save, sender=HistoriqueStatut)
def notifier_emetteur_changement_statut(sender, instance, created, **kwargs):
    """Notifie l'émetteur à chaque changement de statut."""
    if not created:
        return

    requete = instance.requete

    # Destinataire : compte émetteur en priorité, sinon contact_emetteur si c'est un email
    email_dest = None
    if requete.emetteur and requete.emetteur.email:
        email_dest = requete.emetteur.email
    elif requete.contact_emetteur and '@' in requete.contact_emetteur:
        email_dest = requete.contact_emetteur

    if not email_dest:
        return

    statut_prec = _STATUT_LABELS.get(instance.statut_precedent, instance.statut_precedent)
    statut_nouv = _STATUT_LABELS.get(instance.statut_nouveau, instance.statut_nouveau)

    auteur_ligne = ''
    if instance.auteur:
        auteur_ligne = f"Modifié par : {instance.auteur.get_full_name() or instance.auteur.username}\n"

    commentaire_ligne = f"Commentaire : {instance.commentaire}\n" if instance.commentaire else ''

    reponse_bloc = ''
    if instance.statut_nouveau == 'traitee' and requete.reponse:
        reponse_bloc = f"\nRéponse officielle :\n{requete.reponse}\n"

    sujet = f"[HydroPlan SIG] Mise à jour de votre requête {requete.reference}"
    corps = (
        f"Bonjour,\n\n"
        f"Le statut de votre requête a été mis à jour.\n\n"
        f"Référence  : {requete.reference}\n"
        f"Titre      : {requete.titre}\n"
        f"Statut     : {statut_prec} → {statut_nouv}\n"
        f"Date       : {instance.date.strftime('%d/%m/%Y à %H:%M')}\n"
        f"{auteur_ligne}"
        f"{commentaire_ligne}"
        f"{reponse_bloc}\n"
        f"Connectez-vous à HydroPlan SIG pour consulter le détail de votre requête.\n\n"
        f"---\nHydroPlan SIG — ORMVA Tafilalet / Midelt"
    )

    _envoyer(sujet, corps, [email_dest])
