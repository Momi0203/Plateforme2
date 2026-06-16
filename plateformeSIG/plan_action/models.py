from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os


# ─── Référentiel des types d'action PMH ───────────────────────────────────────

TYPE_ACTION_CHOICES = [
    ('ACT-01', 'Réhabilitation de séguias'),
    ('ACT-02', 'Construction de séguias neuves'),
    ('ACT-03', 'Construction de seuils de dérivation'),
    ('ACT-04', 'Réhabilitation de khettaras'),
    ('ACT-05', 'Construction / réhabilitation de barrages collinaires'),
    ('ACT-06', 'Aménagement de prises d\'eau locales'),
    ('ACT-07', 'Renforcement de murs de protection'),
    ('ACT-08', 'Entretien et curage de canaux'),
    ('ACT-09', 'Réhabilitation de forages / puits'),
    ('ACT-10', 'Irrigation localisée (goutte à goutte)'),
    ('ACT-11', 'Planage et nivellement de parcelles'),
    ('ACT-12', 'Aménagement de pistes d\'accès'),
    ('ACT-13', 'Protection contre les crues (digues, épis)'),
    ('ACT-14', 'Étude technique préalable (APD / APS)'),
    ('ACT-16', 'Réhabilitation de seuils de dérivation'),
    ('ACT-15', 'Autre'),
]

SOURCE_FINANCEMENT_CHOICES = [
    ('budget_etat', 'Budget État'),
    ('feader', 'FEADER'),
    ('collectivite', 'Collectivité'),
    ('partenariat', 'Partenariat'),
    ('autre', 'Autre'),
]

STATUT_PLAN_CHOICES = [
    ('en_preparation', 'En préparation'),
    ('publie', 'Publié'),
    ('archive', 'Archivé'),
]

STATUT_ACTION_CHOICES = [
    ('programme', 'Programmé'),
    ('en_cours', 'En cours'),
    ('realise', 'Réalisé'),
    ('annule', 'Annulé'),
]

PRIORITE_CHOICES = [
    (1, 'Haute'),
    (2, 'Moyenne'),
    (3, 'Basse'),
]

MODE_REALISATION_CHOICES = [
    ('etude_interne_ormva', 'Étude interne ORMVA'),
    ('marche_public', 'Marché public'),
    ('appel_manifestation_interet', "Appel à manifestation d'intérêt"),
    ('regie', 'Régie'),
]

STATUT_CALENDRIER_CHOICES = [
    ('brouillon', 'Brouillon'),
    ('valide', 'Validé'),
    ('cloture', 'Clôturé'),
]

TYPE_SUIVI_CHOICES = [
    ('suivi_travaux', 'Suivi travaux'),
    ('suivi_etude', 'Suivi étude'),
    ('suivi_administratif', 'Suivi administratif'),
    ('realisation_etude_interne', 'Réalisation étude interne'),
]

STATUT_TACHE_CHOICES = [
    ('non_demarree', 'Non démarrée'),
    ('en_cours', 'En cours'),
    ('terminee', 'Terminée'),
    ('bloquee', 'Bloquée'),
]

ETAT_BLOC_CHOICES = [
    ('conforme', 'Conforme'),
    ('retard', 'En retard'),
    ('bloque', 'Bloqué'),
    ('termine', 'Terminé'),
]

TYPE_PIECE_CHOICES = [
    ('pv_attachement', "PV d'attachement"),
    ('pv_reception', 'PV de réception'),
    ('photo_chantier', 'Photo de chantier'),
    ('rapport_etude', "Rapport d'étude"),
    ('note_administrative', 'Note administrative'),
    ('autre', 'Autre'),
]


def piece_upload_path(instance, filename):
    annee = instance.suivi.tache.calendrier.action.plan.annee
    action_id = instance.suivi.tache.calendrier.action.id
    return os.path.join('plan_action', 'pieces', str(annee), str(action_id), filename)


# ─── Axe 1 — Plans d'aménagement ─────────────────────────────────────────────

class PlanAmenagement(models.Model):
    annee = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(2000), MaxValueValidator(2050)],
        verbose_name='Année',
    )
    titre = models.CharField(max_length=200, verbose_name='Titre')
    budget_total = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name='Budget total (MAD)',
    )
    source_financement = models.CharField(
        max_length=50, choices=SOURCE_FINANCEMENT_CHOICES,
        verbose_name='Source de financement',
    )
    statut = models.CharField(
        max_length=20, choices=STATUT_PLAN_CHOICES,
        default='en_preparation',
        verbose_name='Statut',
    )
    description = models.TextField(blank=True, verbose_name='Description')
    date_creation = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='plans_crees',
        verbose_name='Créé par',
    )

    class Meta:
        verbose_name = "Plan d'aménagement"
        verbose_name_plural = "Plans d'aménagement"
        ordering = ['-annee']

    def __str__(self):
        return f"Plan PMH {self.annee} — {self.titre}"

    def taux_realisation(self):
        total = self.actions.count()
        if total == 0:
            return 0
        realises = self.actions.filter(statut='realise').count()
        return round(realises * 100 / total)


class ActionPlan(models.Model):
    plan = models.ForeignKey(
        PlanAmenagement, on_delete=models.CASCADE,
        related_name='actions',
        verbose_name="Plan d'aménagement",
    )
    commune = models.ForeignKey(
        'carte.Commune', on_delete=models.PROTECT,
        verbose_name='Commune',
    )
    perimetre = models.ForeignKey(
        'diagnostic.Perimetre',
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Périmètre (optionnel)',
    )
    type_action = models.CharField(
        max_length=10, choices=TYPE_ACTION_CHOICES,
        verbose_name="Type d'action",
    )
    description = models.TextField(verbose_name='Description')
    budget_prevu = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name='Budget prévu (MAD)',
    )
    superficie_concernee = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        verbose_name='Superficie concernée (ha)',
    )
    longueur_prevue = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name='Longueur prévue (ml)',
    )
    statut = models.CharField(
        max_length=20, choices=STATUT_ACTION_CHOICES,
        default='programme',
        verbose_name='Statut',
    )
    priorite = models.IntegerField(
        choices=PRIORITE_CHOICES, default=2,
        verbose_name='Priorité',
    )
    observations = models.TextField(blank=True, verbose_name='Observations')

    class Meta:
        verbose_name = "Action du plan"
        verbose_name_plural = "Actions du plan"
        ordering = ['priorite', 'type_action']

    def __str__(self):
        return f"{self.get_type_action_display()} — {self.commune} ({self.plan.annee})"


# ─── Axe 2 — Calendrier d'intervention ───────────────────────────────────────

class CalendrierIntervention(models.Model):
    action = models.OneToOneField(
        ActionPlan, on_delete=models.CASCADE,
        related_name='calendrier',
        verbose_name="Action du plan",
    )
    date_debut_prevue = models.DateField(verbose_name='Date de début prévue')
    date_fin_prevue = models.DateField(verbose_name='Date de fin prévue')
    mode_realisation = models.CharField(
        max_length=50, choices=MODE_REALISATION_CHOICES,
        verbose_name='Mode de réalisation',
    )
    chef_projet = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='calendriers_chef',
        verbose_name='Chef de projet',
    )
    statut_calendrier = models.CharField(
        max_length=20, choices=STATUT_CALENDRIER_CHOICES,
        default='brouillon',
        verbose_name='Statut du calendrier',
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='calendriers_valides',
        verbose_name='Validé par',
    )
    date_validation = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Calendrier d'intervention"
        verbose_name_plural = "Calendriers d'intervention"

    def __str__(self):
        return f"Calendrier — {self.action}"


class TacheIntervention(models.Model):
    calendrier = models.ForeignKey(
        CalendrierIntervention, on_delete=models.CASCADE,
        related_name='taches',
        verbose_name="Calendrier",
    )
    code_tache = models.CharField(max_length=20, verbose_name='Code tâche')
    nom_tache = models.CharField(max_length=200, verbose_name='Nom de la tâche')
    description = models.TextField(blank=True, verbose_name='Description')
    date_debut_prevue = models.DateField(verbose_name='Date de début prévue')
    date_fin_prevue = models.DateField(verbose_name='Date de fin prévue')
    duree_prevue = models.PositiveIntegerField(
        verbose_name='Durée prévue (jours calendaires)',
    )
    taches_anterieures = models.ManyToManyField(
        'self', symmetrical=False, blank=True,
        verbose_name='Tâches antérieures (dépendances FS)',
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='taches_responsable',
        verbose_name='Responsable',
    )
    type_suivi = models.CharField(
        max_length=30, choices=TYPE_SUIVI_CHOICES,
        verbose_name='Type de suivi',
    )
    statut_tache = models.CharField(
        max_length=20, choices=STATUT_TACHE_CHOICES,
        default='non_demarree',
        verbose_name='Statut de la tâche',
    )

    class Meta:
        verbose_name = "Tâche d'intervention"
        verbose_name_plural = "Tâches d'intervention"
        unique_together = [('calendrier', 'code_tache')]
        ordering = ['code_tache']

    def __str__(self):
        return f"{self.code_tache} — {self.nom_tache}"


# ─── Axe 3 — Suivi d'avancement ──────────────────────────────────────────────

class SuiviAvancement(models.Model):
    tache = models.ForeignKey(
        TacheIntervention, on_delete=models.CASCADE,
        related_name='suivis',
        verbose_name='Tâche',
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='rapports_suivi',
        verbose_name='Auteur',
    )
    date_rapport = models.DateField(verbose_name='Date du rapport')
    avancement_pct = models.PositiveIntegerField(
        validators=[MaxValueValidator(100)],
        verbose_name='Avancement (%)',
    )
    etat_bloc = models.CharField(
        max_length=20, choices=ETAT_BLOC_CHOICES,
        verbose_name='État',
    )
    commentaire = models.TextField(blank=True, verbose_name='Commentaire')
    date_prochaine_echeance = models.DateField(
        null=True, blank=True,
        verbose_name='Prochaine échéance',
    )
    date_saisie = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rapport de suivi"
        verbose_name_plural = "Rapports de suivi"
        ordering = ['-date_rapport']

    def __str__(self):
        return f"Suivi {self.tache.code_tache} — {self.date_rapport} ({self.avancement_pct}%)"


class PieceJustificative(models.Model):
    suivi = models.ForeignKey(
        SuiviAvancement, on_delete=models.CASCADE,
        related_name='pieces',
        verbose_name='Rapport de suivi',
    )
    type_piece = models.CharField(
        max_length=30, choices=TYPE_PIECE_CHOICES,
        verbose_name='Type de pièce',
    )
    fichier = models.FileField(
        upload_to=piece_upload_path,
        verbose_name='Fichier',
    )
    libelle = models.CharField(max_length=200, verbose_name='Libellé')
    date_document = models.DateField(null=True, blank=True, verbose_name='Date du document')
    date_upload = models.DateTimeField(auto_now_add=True)
    uploade_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='pieces_uploadees',
        verbose_name='Uploadé par',
    )

    class Meta:
        verbose_name = "Pièce justificative"
        verbose_name_plural = "Pièces justificatives"

    def __str__(self):
        return f"{self.get_type_piece_display()} — {self.libelle}"


# Suppression physique du fichier après delete ORM
@receiver(post_delete, sender=PieceJustificative)
def _delete_piece_file(sender, instance, **kwargs):
    if instance.fichier:
        try:
            path = instance.fichier.path
            if os.path.isfile(path):
                os.remove(path)
        except (ValueError, OSError):
            pass
