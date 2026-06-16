from django.conf import settings
from django.db import models

from diagnostic.models import Perimetre


class Efficience(models.Model):
    """Résultats agrégés du calcul d'efficience pour un ouvrage de tête.

    Une ligne représente le rendement consolidé d'un réseau alimenté par
    un ouvrage de tête donné, dans le contexte d'un périmètre. La cascade
    est : tronçon (Seguias) → catégorie (P/S/T) → global (Efficience).
    """

    OUVRAGE_TYPE_CHOICES = [
        ('seuil',           'Seuil'),
        ('prise_locale',    'Prise locale'),
        ('khettara',        'Khettara'),
        ('forage_puits',    'Forage / Puits'),
        ('barrage_retenue', 'Barrage de retenue'),
    ]

    perimetre = models.ForeignKey(
        Perimetre,
        on_delete=models.CASCADE,
        related_name='efficiences',
    )

    ouvrage_tete_type = models.CharField(max_length=30, choices=OUVRAGE_TYPE_CHOICES)
    ouvrage_tete_id = models.PositiveIntegerField(help_text="Identifiant de l'ouvrage de tête (selon le type)")

    efficience_principale = models.FloatField(null=True, blank=True, help_text="Efficience moyenne pondérée des tronçons principaux (%)")
    efficience_secondaire = models.FloatField(null=True, blank=True, help_text="Efficience moyenne pondérée des tronçons secondaires (%)")
    efficience_tertiaire  = models.FloatField(null=True, blank=True, help_text="Efficience moyenne pondérée des tronçons tertiaires (%)")
    efficience_globale    = models.FloatField(help_text="Efficience globale du réseau amont (%) — produit en cascade")

    nb_troncons_principaux  = models.PositiveSmallIntegerField(default=0)
    nb_troncons_secondaires = models.PositiveSmallIntegerField(default=0)
    nb_troncons_tertiaires  = models.PositiveSmallIntegerField(default=0)

    date_calcul = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(
        max_length=20,
        choices=[('brouillon', 'Brouillon'), ('valide', 'Validé')],
        default='brouillon',
        verbose_name="Statut",
    )
    operateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='efficiences_calculees',
    )

    class Meta:
        verbose_name = "Efficience de réseau"
        verbose_name_plural = "Efficiences de réseaux"
        ordering = ['-date_calcul']
        indexes = [
            models.Index(fields=['perimetre', 'ouvrage_tete_type', 'ouvrage_tete_id']),
        ]

    def __str__(self):
        return f"Efficience {self.get_ouvrage_tete_type_display()} #{self.ouvrage_tete_id} — {self.efficience_globale:.2f}%"
