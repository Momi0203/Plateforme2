from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


TYPE_REQUETE_CHOICES = [
    ('plateforme', 'Signalement plateforme'),
    ('acces',      "Demande d'utilisation / accès"),
    ('perimetre',  'Requête périmètre agricole'),
]

SOUS_TYPE_CHOICES = [
    ('PROB-01', 'Rupture / brèche d\'ouvrage'),
    ('PROB-02', 'Fuite ou colmatage de canal'),
    ('PROB-03', 'Panne de pompe / forage'),
    ('PROB-04', 'Tarissement ou débit insuffisant'),
    ('PROB-05', 'Conflit de tour d\'eau'),
    ('PROB-06', 'Déficit hydrique critique (sécheresse)'),
    ('PROB-07', 'Détérioration suite à crue'),
    ('PROB-08', 'Obstruction par sédiments / dépôts'),
    ('PROB-09', 'Vandalisme ou intrusion'),
    ('PROB-10', 'Autre problème terrain'),
]

URGENCE_CHOICES = [
    ('faible',   'Faible — aucun risque immédiat'),
    ('normale',  'Normale — à traiter sous 5 jours'),
    ('haute',    'Haute — à traiter sous 48 h'),
    ('critique', 'Critique — intervention immédiate requise'),
]

STATUT_CHOICES = [
    ('soumise',     'Soumise'),
    ('en_cours',    'En cours de traitement'),
    ('en_attente',  "En attente d'informations complémentaires"),
    ('traitee',     'Traitée'),
    ('cloturee',    'Clôturée'),
    ('rejetee',     'Rejetée'),
]

EMETTEUR_CHOICES = [
    ('auea',                 'Responsable AUEA'),
    ('agriculteur',          'Agriculteur / Fellah'),
    ('agent_ormva',          'Agent ORMVA'),
    ('chef_secteur',         'Chef de secteur ORMVA'),
    ('garde_hydraulique',    'Garde hydraulique'),
    ('commune',              'Représentant de commune'),
    ('bureau_etudes',        "Bureau d'études / Consultant"),
    ('ayant_droit_khettara', 'Actionnaire de khettara'),
    ('autre',                'Autre'),
]

OUVRAGE_TYPE_CHOICES = [
    ('seuil',          'Seuil'),
    ('mur_protection', 'Mur de protection'),
    ('seguia',         'Séguia'),
    ('barrage',        'Barrage'),
    ('khettara',       'Khettara'),
    ('forage',         'Forage / Puits'),
    ('prise_locale',   'Prise locale'),
]


def _generate_reference():
    from django.db import transaction
    year = timezone.now().year
    prefix = f'DD-{year}-'
    with transaction.atomic():
        last = (
            Requete.objects
            .filter(reference__startswith=prefix)
            .select_for_update()
            .order_by('-reference')
            .values_list('reference', flat=True)
            .first()
        )
        if last:
            try:
                seq = int(last.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = Requete.objects.filter(reference__startswith=prefix).count() + 1
        else:
            seq = 1
        return f'{prefix}{seq:04d}'


class Requete(models.Model):
    reference       = models.CharField(max_length=20, unique=True, editable=False)
    titre           = models.CharField(max_length=200, verbose_name='Titre')
    type_requete    = models.CharField(max_length=20, choices=TYPE_REQUETE_CHOICES,
                                       verbose_name='Type de requête')
    sous_type       = models.CharField(max_length=10, choices=SOUS_TYPE_CHOICES,
                                       null=True, blank=True, verbose_name='Sous-type')
    description     = models.TextField(verbose_name='Description')
    urgence         = models.CharField(max_length=10, choices=URGENCE_CHOICES,
                                       default='normale', verbose_name='Urgence')
    statut          = models.CharField(max_length=15, choices=STATUT_CHOICES,
                                       default='soumise', verbose_name='Statut')

    # Émetteur
    emetteur        = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='requetes_emises',
        verbose_name='Émetteur (compte)'
    )
    type_emetteur   = models.CharField(max_length=25, choices=EMETTEUR_CHOICES,
                                       verbose_name='Profil émetteur')
    nom_emetteur    = models.CharField(max_length=150, blank=True,
                                       verbose_name='Nom (si non connecté)')
    contact_emetteur = models.CharField(max_length=150, blank=True,
                                        verbose_name='Contact (email ou tél.)')
    organisation    = models.CharField(max_length=200, blank=True,
                                       verbose_name='Organisation / communauté')

    # Localisation métier
    perimetre       = models.ForeignKey(
        'diagnostic.Perimetre', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='requetes',
        verbose_name='Périmètre concerné'
    )
    ouvrage_type    = models.CharField(max_length=20, choices=OUVRAGE_TYPE_CHOICES,
                                       null=True, blank=True, verbose_name='Type d\'ouvrage')
    ouvrage_id      = models.PositiveIntegerField(null=True, blank=True,
                                                  verbose_name='ID ouvrage')

    # Traitement
    assignee        = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='requetes_assignees',
        verbose_name='Assignée à'
    )
    reponse         = models.TextField(blank=True, verbose_name='Réponse officielle')
    date_soumission  = models.DateTimeField(auto_now_add=True, verbose_name='Date de soumission')
    date_traitement  = models.DateTimeField(null=True, blank=True, verbose_name='Date de traitement')
    date_cloture     = models.DateTimeField(null=True, blank=True, verbose_name='Date de clôture')
    date_modification = models.DateTimeField(auto_now=True, verbose_name='Dernière modification')

    class Meta:
        verbose_name = 'Requête'
        verbose_name_plural = 'Requêtes'
        ordering = ['-date_soumission']

    def __str__(self):
        return f'{self.reference} — {self.titre}'

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = _generate_reference()
        super().save(*args, **kwargs)

    def clean(self):
        if self.type_requete == 'perimetre' and not self.perimetre_id:
            raise ValidationError(
                {'perimetre': "Le périmètre est obligatoire pour une requête de type 'Requête périmètre agricole'."}
            )

    def get_ouvrage(self):
        """Retourne l'instance ORM de l'ouvrage référencé (polymorphe)."""
        if not self.ouvrage_type or not self.ouvrage_id:
            return None
        from diagnostic import models as diag
        mapping = {
            'seuil':          diag.Seuil,
            'mur_protection': diag.MurProtection,
            'seguia':         diag.Seguias,
            'barrage':        diag.BarrageRetenue,
            'khettara':       diag.Khettara,
            'forage':         diag.ForagePuits,
            'prise_locale':   diag.PriseLocale,
        }
        model = mapping.get(self.ouvrage_type)
        if model is None:
            return None
        return model.objects.filter(pk=self.ouvrage_id).first()


class CommentaireRequete(models.Model):
    requete         = models.ForeignKey(Requete, on_delete=models.CASCADE,
                                        related_name='commentaires')
    auteur          = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name='Auteur'
    )
    contenu         = models.TextField(verbose_name='Contenu')
    interne         = models.BooleanField(default=False,
                                          verbose_name='Commentaire interne (staff uniquement)')
    date_creation   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
        ordering = ['date_creation']

    def __str__(self):
        nature = 'interne' if self.interne else 'public'
        return f'Commentaire {nature} — {self.requete.reference}'


class HistoriqueStatut(models.Model):
    requete             = models.ForeignKey(Requete, on_delete=models.CASCADE,
                                            related_name='historique_statuts')
    statut_precedent    = models.CharField(max_length=15, verbose_name='Statut précédent')
    statut_nouveau      = models.CharField(max_length=15, verbose_name='Nouveau statut')
    auteur              = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name='Modifié par'
    )
    commentaire         = models.CharField(max_length=500, blank=True,
                                           verbose_name='Commentaire')
    date                = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historique statut'
        verbose_name_plural = 'Historiques statuts'
        ordering = ['date']

    def __str__(self):
        return f'{self.requete.reference} : {self.statut_precedent} → {self.statut_nouveau}'


EXTENSIONS_AUTORISEES = {'jpg', 'jpeg', 'png', 'pdf', 'docx'}
TAILLE_MAX_KO = 10 * 1024  # 10 Mo


class PieceJointeRequete(models.Model):
    requete         = models.ForeignKey(Requete, on_delete=models.CASCADE,
                                        related_name='pieces_jointes')
    fichier         = models.FileField(upload_to='doleances/pj/%Y/%m/')
    nom_original    = models.CharField(max_length=255)
    taille_ko       = models.PositiveIntegerField(verbose_name='Taille (Ko)')
    date_upload     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pièce jointe'
        verbose_name_plural = 'Pièces jointes'

    def __str__(self):
        return f'{self.nom_original} ({self.taille_ko} Ko)'

    def clean(self):
        ext = self.nom_original.rsplit('.', 1)[-1].lower() if '.' in self.nom_original else ''
        if ext not in EXTENSIONS_AUTORISEES:
            raise ValidationError(
                {'fichier': f"Format non autorisé. Extensions acceptées : {', '.join(sorted(EXTENSIONS_AUTORISEES))}."}
            )
        if self.taille_ko > TAILLE_MAX_KO:
            raise ValidationError({'fichier': "La pièce jointe dépasse la taille maximale de 10 Mo."})
        if self.requete_id:
            count = PieceJointeRequete.objects.filter(requete_id=self.requete_id).exclude(pk=self.pk).count()
            if count >= 5:
                raise ValidationError({'fichier': "La requête ne peut pas avoir plus de 5 pièces jointes."})
