from django.conf import settings
from django.db import models
from django.contrib.gis.db import models as gismodels


# ── Hydrologie : couches cartographiques (indépendantes de analyse_hydrologique) ──

class BassinVersant(models.Model):
    """Contour d'un bassin versant — couche cartographique (module Carte)."""

    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    superficie_km2 = models.FloatField(verbose_name="Superficie (km²)")
    perimetre_km = models.FloatField(default=0.0, verbose_name="Périmètre (km)")
    altitude_min = models.FloatField(verbose_name="Altitude minimale (m)")
    altitude_max = models.FloatField(verbose_name="Altitude maximale (m)")
    altitude_exutoire = models.FloatField(verbose_name="Altitude exutoire (m)")
    thalweg_km = models.FloatField(verbose_name="Longueur thalweg principal (km)")
    precipitations_annuelles_mm = models.FloatField(
        null=True, blank=True, verbose_name="Précipitations annuelles (mm/an)"
    )
    evapotranspiration_annuelle_mm = models.FloatField(
        null=True, blank=True, verbose_name="Évapotranspiration annuelle (mm/an)"
    )
    geometrie = gismodels.PolygonField(srid=4326, null=True, blank=True, verbose_name="Géométrie")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bassin versant (Carte)"
        verbose_name_plural = "Bassins versants (Carte)"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class ReseauHydrographique(models.Model):
    """Tronçon du réseau hydrographique — couche cartographique (module Carte)."""

    bassin_versant = models.ForeignKey(
        BassinVersant,
        on_delete=models.CASCADE,
        related_name="troncons",
        verbose_name="Bassin versant",
    )
    comid = models.IntegerField(verbose_name="COMID (identifiant tronçon)")
    sorder = models.IntegerField(verbose_name="Ordre de Strahler")
    geometrie = gismodels.LineStringField(srid=4326, verbose_name="Géométrie")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Réseau hydrographique (Carte)"
        verbose_name_plural = "Réseaux hydrographiques (Carte)"
        indexes = [
            models.Index(fields=["bassin_versant"]),
            models.Index(fields=["sorder"]),
        ]

    def __str__(self):
        return f"Tronçon #{self.pk} — {self.bassin_versant.nom} (ordre {self.sorder})"


# ── Réseaux hydrographiques « ouvrage de tête » par bassin ──────────────────────
# Couches indépendantes (une table par bassin), forme minimale : grid_code +
# geometrie, SANS aucune clé étrangère. Alimentées depuis les shapefiles de
# plateformeSIG/static/resaux hydrographique ouvrage en tete/ via les commandes
# import_reseau_<bassin>. Prévues pour un usage ultérieur.

class ReseauOuvrageTeteZiz(models.Model):
    """Réseau hydrographique en amont de l'ouvrage de tête — bassin Ziz."""

    grid_code = models.IntegerField(null=True, blank=True, verbose_name="Grid code")
    geometrie = gismodels.LineStringField(srid=4326, verbose_name="Géométrie (polyligne)")

    class Meta:
        verbose_name = "Réseau ouvrage de tête — Ziz"
        verbose_name_plural = "Réseau ouvrage de tête — Ziz"

    def __str__(self):
        return f"Tronçon Ziz #{self.pk} (grid_code={self.grid_code})"


class ReseauOuvrageTeteMoulouya(models.Model):
    """Réseau hydrographique en amont de l'ouvrage de tête — bassin Moulouya."""

    grid_code = models.IntegerField(null=True, blank=True, verbose_name="Grid code")
    geometrie = gismodels.LineStringField(srid=4326, verbose_name="Géométrie (polyligne)")

    class Meta:
        verbose_name = "Réseau ouvrage de tête — Moulouya"
        verbose_name_plural = "Réseau ouvrage de tête — Moulouya"

    def __str__(self):
        return f"Tronçon Moulouya #{self.pk} (grid_code={self.grid_code})"


class ReseauOuvrageTeteGuir(models.Model):
    """Réseau hydrographique en amont de l'ouvrage de tête — bassin Guir."""

    grid_code = models.IntegerField(null=True, blank=True, verbose_name="Grid code")
    geometrie = gismodels.LineStringField(srid=4326, verbose_name="Géométrie (polyligne)")

    class Meta:
        verbose_name = "Réseau ouvrage de tête — Guir"
        verbose_name_plural = "Réseau ouvrage de tête — Guir"

    def __str__(self):
        return f"Tronçon Guir #{self.pk} (grid_code={self.grid_code})"


class ReseauOuvrageTeteRheris(models.Model):
    """Réseau hydrographique en amont de l'ouvrage de tête — bassin Rhéris."""

    grid_code = models.IntegerField(null=True, blank=True, verbose_name="Grid code")
    geometrie = gismodels.LineStringField(srid=4326, verbose_name="Géométrie (polyligne)")

    class Meta:
        verbose_name = "Réseau ouvrage de tête — Rhéris"
        verbose_name_plural = "Réseau ouvrage de tête — Rhéris"

    def __str__(self):
        return f"Tronçon Rhéris #{self.pk} (grid_code={self.grid_code})"


class ReseauOuvrageTeteMaider(models.Model):
    """Réseau hydrographique en amont de l'ouvrage de tête — bassin Maïder."""

    grid_code = models.IntegerField(null=True, blank=True, verbose_name="Grid code")
    geometrie = gismodels.LineStringField(srid=4326, verbose_name="Géométrie (polyligne)")

    class Meta:
        verbose_name = "Réseau ouvrage de tête — Maïder"
        verbose_name_plural = "Réseau ouvrage de tête — Maïder"

    def __str__(self):
        return f"Tronçon Maïder #{self.pk} (grid_code={self.grid_code})"


# ── Géographies administratives de référence ───────────────────────────────────

class Province(models.Model):
    """Province"""

    nom_fr = models.CharField(max_length=100)
    nom_ar = models.CharField(max_length=100)
    annee_refe = models.IntegerField()
    population_totale = models.IntegerField()
    population_urbaine = models.IntegerField()
    population_rurale = models.IntegerField()
    nombre_menages = models.IntegerField()
    superficie_km2 = models.DecimalField(max_digits=12, decimal_places=2)
    densite_hab_km2 = models.DecimalField(max_digits=10, decimal_places=2)
    taux_urbanisation_pct = models.DecimalField(max_digits=5, decimal_places=2)
    taux_accroissement_pct = models.DecimalField(max_digits=5, decimal_places=2)
    communes_urbaines = models.IntegerField()
    communes_rurales = models.IntegerField()
    station_meteo = models.CharField(max_length=50)
    temp_moy_annuelle_c = models.DecimalField(max_digits=4, decimal_places=1)
    precip_annuelle_mm = models.DecimalField(max_digits=8, decimal_places=1)
    humidite_rel_moy_pct = models.DecimalField(max_digits=4, decimal_places=1)
    et0_moy_journaliere_mm_j = models.DecimalField(max_digits=5, decimal_places=2)
    et0_annuelle_mm = models.DecimalField(max_digits=8, decimal_places=1)

    geometrie = gismodels.PolygonField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Provinces"

    def __str__(self):
        return self.nom_fr


class Commune(models.Model):
    """Commune territoriale"""

    TYPE_COMMUNE_CHOICES = [
        ('Urbaine', 'Urbaine'),
        ('Rurale', 'Rurale'),
    ]

    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='communes')
    nom_fr = models.CharField(max_length=100, unique=True)
    nom_ar = models.CharField(max_length=100)
    annee_refe = models.IntegerField(null=True, blank=True)
    type_commune = models.CharField(max_length=10, choices=TYPE_COMMUNE_CHOICES)
    population_totale = models.IntegerField()
    nombre_menages = models.IntegerField()
    superficie_km2 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    station_meteo = models.CharField(max_length=50)
    temp_moy_annuelle_c = models.DecimalField(max_digits=4, decimal_places=1)
    precip_annuelle_mm = models.DecimalField(max_digits=8, decimal_places=1)
    humidite_rel_moy_pct = models.DecimalField(max_digits=4, decimal_places=1)
    et0_moy_journaliere_mm_j = models.DecimalField(max_digits=5, decimal_places=2)
    et0_annuelle_mm = models.DecimalField(max_digits=8, decimal_places=1)
    nbr_perimetres_agricoles = models.IntegerField(null=True, blank=True)

    geometrie = gismodels.PolygonField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Communes"

    def __str__(self):
        return self.nom_fr


class StyleCouche(models.Model):
    """Bibliothèque de styles personnels de l'utilisateur."""

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='styles_couche')
    nom_couche  = models.CharField(max_length=100)
    nom_style   = models.CharField(max_length=100)
    parametres  = models.JSONField()
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Style de couche"
        verbose_name_plural = "Styles de couches"
        unique_together = [('utilisateur', 'nom_couche', 'nom_style')]

    def __str__(self):
        return f"{self.nom_style} ({self.nom_couche})"


class RequeteNommee(models.Model):
    """Sauvegarde des requêtes multicritères de l'utilisateur."""

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requetes_nommees')
    nom        = models.CharField(max_length=100)
    couche     = models.CharField(max_length=100)
    expression = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Requête nommée"
        verbose_name_plural = "Requêtes nommées"
        unique_together = [('utilisateur', 'nom')]

    def __str__(self):
        return f"{self.nom} ({self.couche})"
