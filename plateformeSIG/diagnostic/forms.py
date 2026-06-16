from django import forms
from .models import (
    Perimetre, Seuil, MurProtection, Seguias, TronconSeguia, BarrageRetenue,
    Khettara, ForagePuits, PriseLocale,
    EtatSeuil, EtatTronconSeguia, EtatMurProtection, EtatKhettara, EtatForagePuits,
    EtatBarrageRetenue, EtatPriseLocale,
    Assolement, TourEau, OrganisationAgriculteur,
    CULTURES_TAFILALET,
)


def _w(widget_class=forms.TextInput, **extra):
    return widget_class(attrs={'class': 'form-control', **extra})


def _apply_widgets(form_class):
    for name, field in form_class.base_fields.items():
        if isinstance(field.widget, forms.TextInput):
            field.widget.attrs.setdefault('class', 'form-control')
        elif isinstance(field.widget, forms.NumberInput):
            field.widget.attrs.setdefault('class', 'form-control')
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs.setdefault('class', 'form-control')
        elif isinstance(field.widget, forms.Textarea):
            field.widget.attrs.setdefault('class', 'form-control')
            field.widget.attrs.setdefault('rows', '3')
    return form_class


class PerimetreForm(forms.ModelForm):
    class Meta:
        model = Perimetre
        exclude = ['created_at', 'updated_at', 'statut']
        widgets = {
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'coordination': forms.TextInput(attrs={'class': 'form-control'}),
            'commune_territoriale': forms.TextInput(attrs={'class': 'form-control'}),
            'ksar_village': forms.TextInput(attrs={'class': 'form-control'}),
            'vent': forms.TextInput(attrs={'class': 'form-control'}),
            'humidite': forms.TextInput(attrs={'class': 'form-control'}),
            'temperature_moyenne_annuelle': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'precipitations_moyennes_annuelles': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'et0_mm_jour': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'nombre_beneficiaires': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombre_menages': forms.NumberInput(attrs={'class': 'form-control'}),
            'superficie_totale': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'superficie_agricole_utile': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'superficie_irriguee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'superficie_en_bour': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'type_de_sol': forms.Select(attrs={'class': 'form-control'}),
            'niveau_de_fertilite': forms.Select(attrs={'class': 'form-control'}),
            'parcelles_moins_1ha': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '100'}),
            'parcelles_1_a_3ha': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '100'}),
            'parcelles_plus_3ha': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '100'}),
            'moyenne_bovins': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'moyenne_ovins': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'moyenne_caprins': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'geometrie': forms.Textarea(attrs={'class': 'form-control', 'rows': '3', 'placeholder': 'WKT ou GeoJSON (optionnel)'}),
        }

    statut_juridique = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2',
                                     'placeholder': 'Ex: 30, 40, 30 (séparés par des virgules)'}),
        help_text="Valeurs numériques séparées par des virgules"
    )
    # `cultures` est posté en CSV par la textarea cachée du template (pilotée
    # par les <select> dynamiques). On valide en CharField + parsing manuel
    # dans clean_cultures pour éviter le crash de MultipleChoiceField sur une
    # chaîne unique.
    cultures = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2'}),
        help_text="Cultures séparées par des virgules"
    )
    pourcentage_cultures = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2',
                                     'placeholder': 'Ex: 40, 35, 25'}),
        help_text="Pourcentages séparés par des virgules"
    )
    rendement_cultures = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2',
                                     'placeholder': 'Ex: 25, 20, 30'}),
        help_text="Rendements séparés par des virgules"
    )
    unite_rendement_cultures = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2'}),
        help_text="Unité du rendement par culture (qx_ha ou kg_arbre)"
    )
    ayants_droit_eau = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2',
                                     'placeholder': 'Ex: Famille A, Famille B'}),
        help_text="Noms séparés par des virgules"
    )
    cycle_tour_eau_jours = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2',
                                     'placeholder': 'Ex: 7, 14, 21'}),
        help_text="Valeurs numériques séparées par des virgules"
    )
    duree_tour_eau_heures = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2',
                                     'placeholder': 'Ex: 4, 6, 8'}),
        help_text="Valeurs numériques séparées par des virgules"
    )
    organisations_agriculteurs = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2',
                                     'placeholder': 'Ex: AUEA Midelt, GIE Sud'}),
        help_text="Noms séparés par des virgules"
    )
    ouvrages_en_tete_associes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '2',
                                     'placeholder': 'Ex: Seuil A, Barrage B'}),
        help_text="Noms séparés par des virgules"
    )

    # Ces champs ne sont plus stockés sous forme de listes JSON séparées par des
    # virgules sur Perimetre : ils alimentent désormais soit 5 colonnes fixes
    # (statut_juridique_*) soit des tables enfants (Assolement, TourEau,
    # OrganisationAgriculteur, OuvrageTeteAssocie). Les champs de formulaire
    # CSV restent pour préserver l'UI dynamique du template (table-rows JS).

    SJ_KEYS = ['melk', 'collectif', 'location', 'guiche', 'habousse']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Province / Commune → Select avec cascade dynamique
        from carte.models import Province, Commune as CarteCommune
        provinces = list(Province.objects.values_list('nom_fr', flat=True).order_by('nom_fr'))
        self.fields['province'].widget = forms.Select(attrs={'class': 'form-control'})
        self.fields['province'].widget.choices = (
            [('', '— Sélectionner —')] + [(p, p) for p in provinces]
        )
        current_prov = (
            self.data.get('province') or
            (self.instance.province if self.instance.pk else None)
        )
        commune_choices = [('', '— Sélectionner —')]
        if current_prov:
            commune_choices += [
                (c, c) for c in CarteCommune.objects.filter(
                    province__nom_fr=current_prov
                ).values_list('nom_fr', flat=True).order_by('nom_fr')
            ]
        self.fields['commune_territoriale'].widget = forms.Select(attrs={'class': 'form-control'})
        self.fields['commune_territoriale'].widget.choices = commune_choices

        # Expose le référentiel au template (les <select> dynamiques itèrent
        # `form.cultures.field.choices` pour peupler leurs options).
        self.fields['cultures'].choices = CULTURES_TAFILALET
        instance = kwargs.get('instance')
        if instance and instance.pk:
            # Statut juridique : 5 colonnes → CSV ordonné
            sj_values = []
            for k in self.SJ_KEYS:
                v = getattr(instance, f'statut_juridique_{k}', None)
                sj_values.append('' if v is None else str(v))
            self.fields['statut_juridique'].initial = ', '.join(sj_values)

            # Assolement (table enfant) → 3 listes parallèles dans le form
            assols = list(instance.assolement.all())
            # cultures est désormais CharField (CSV) — initial doit être une str
            self.fields['cultures'].initial = ', '.join(a.culture for a in assols)
            self.fields['pourcentage_cultures'].initial = ', '.join(
                ('' if a.pourcentage is None else str(a.pourcentage)) for a in assols
            )
            self.fields['rendement_cultures'].initial = ', '.join(
                ('' if a.rendement is None else str(a.rendement)) for a in assols
            )
            self.fields['unite_rendement_cultures'].initial = ', '.join(
                (a.unite_rendement or 'qx_ha') for a in assols
            )

            # Tours d'eau (table enfant) → 3 listes parallèles
            tours = list(instance.tours_eau.all())
            self.fields['ayants_droit_eau'].initial = ', '.join(t.ayant_droit for t in tours)
            self.fields['cycle_tour_eau_jours'].initial = ', '.join(
                ('' if t.cycle_jours is None else str(t.cycle_jours)) for t in tours
            )
            self.fields['duree_tour_eau_heures'].initial = ', '.join(
                ('' if t.duree_heures is None else str(t.duree_heures)) for t in tours
            )

            # Organisations / Ouvrages associés
            self.fields['organisations_agriculteurs'].initial = ', '.join(
                o.nom for o in instance.organisations.all()
            )
            # OuvrageTeteAssocie supprimé : champ form CSV conservé pour la
            # compat template (textarea masquée), mais plus de stockage côté DB.
            self.fields['ouvrages_en_tete_associes'].initial = ''

    def _parse_list(self, value, cast=str):
        if not value:
            return []
        out = []
        for v in value.split(','):
            v = v.strip()
            if not v:
                continue
            try:
                out.append(cast(v))
            except (TypeError, ValueError):
                # En float : on garde None pour préserver l'alignement positionnel
                if cast is float:
                    out.append(None)
        return out

    def clean_cultures(self):
        """Parse la CSV postée par la textarea cachée et filtre sur le
        référentiel CULTURES_TAFILALET (les valeurs hors liste sont ignorées).
        """
        raw = self.cleaned_data.get('cultures') or ''
        if isinstance(raw, list):
            items = [str(x).strip() for x in raw if str(x).strip()]
        else:
            items = [v.strip() for v in raw.split(',') if v.strip()]
        valid = {v for v, _ in CULTURES_TAFILALET}
        return [v for v in items if v in valid]

    def save(self, commit=True):
        # 1) Statut juridique : CSV → 5 colonnes
        sj_csv = self.cleaned_data.get('statut_juridique', '')
        sj_values = self._parse_list(sj_csv, float)
        for i, k in enumerate(self.SJ_KEYS):
            v = sj_values[i] if i < len(sj_values) else None
            setattr(self.instance, f'statut_juridique_{k}', v)

        # 2) Synchroniser le FK commune depuis commune_territoriale
        from carte.models import Commune as CarteCommune
        commune_nom = self.cleaned_data.get('commune_territoriale', '').strip()
        self.instance.commune = (
            CarteCommune.objects.filter(nom_fr=commune_nom).first()
            if commune_nom else None
        )

        # 3) Sauvegarde du Perimetre (champs scalaires)
        instance = super().save(commit=commit)

        if commit:
            self._sync_child_tables(instance)
        else:
            # Différer la synchro après la persistance manuelle de l'instance
            old = self.save_m2m if hasattr(self, 'save_m2m') else None
            def _save_m2m():
                if old:
                    old()
                self._sync_child_tables(instance)
            self.save_m2m = _save_m2m

        return instance

    def _sync_child_tables(self, instance):
        """Recrée Assolement, TourEau, OrganisationAgriculteur, OuvrageTeteAssocie
        depuis les champs CSV du formulaire (stratégie delete-then-create).
        """
        # ── Assolement (4 listes parallèles)
        cultures = self.cleaned_data.get('cultures') or []
        pcts = self._parse_list(self.cleaned_data.get('pourcentage_cultures', ''), float)
        rdts = self._parse_list(self.cleaned_data.get('rendement_cultures', ''), float)
        unites = self._parse_list(self.cleaned_data.get('unite_rendement_cultures', ''))
        valid_unites = {k for k, _ in Assolement.UNITE_RENDEMENT_CHOICES}
        instance.assolement.all().delete()
        for i, culture in enumerate(cultures):
            culture = (culture or '').strip()
            if not culture:
                continue
            unite = unites[i] if i < len(unites) else 'qx_ha'
            if unite not in valid_unites:
                unite = 'qx_ha'
            Assolement.objects.create(
                perimetre=instance,
                culture=culture,
                pourcentage=pcts[i] if i < len(pcts) else None,
                rendement=rdts[i] if i < len(rdts) else None,
                unite_rendement=unite,
                ordre=i,
            )

        # ── Tour d'eau (3 listes parallèles)
        ayants = self._parse_list(self.cleaned_data.get('ayants_droit_eau', ''))
        cycs = self._parse_list(self.cleaned_data.get('cycle_tour_eau_jours', ''), float)
        durs = self._parse_list(self.cleaned_data.get('duree_tour_eau_heures', ''), float)
        instance.tours_eau.all().delete()
        for i, ayant in enumerate(ayants):
            if not ayant:
                continue
            TourEau.objects.create(
                perimetre=instance,
                ayant_droit=ayant,
                cycle_jours=cycs[i] if i < len(cycs) else None,
                duree_heures=durs[i] if i < len(durs) else None,
                ordre=i,
            )

        # ── Organisations
        instance.organisations.all().delete()
        for i, nom in enumerate(self._parse_list(self.cleaned_data.get('organisations_agriculteurs', ''))):
            OrganisationAgriculteur.objects.create(perimetre=instance, nom=nom, ordre=i)

        # ── Ouvrages en tête associés : modèle supprimé. Le champ form CSV est
        # conservé pour la compat du template mais n'est plus persisté.


class SeuilForm(forms.ModelForm):
    class Meta:
        model = Seuil
        # On exclut les champs d'état/réhabilitation : ils relèvent désormais du diagnostic
        # structuré (modèle EtatSeuil) édité depuis la vue diagnostic dédiée.
        exclude = [
            'created_at', 'updated_at', 'statut', 'perimetre',
            'saisi_par', 'valide_par',
            'etat_construction_fonctionnement', 'etat_materiel_hydromecanique',
            'annee_derniere_rehabilitation', 'date_diagnostic', 'defaut_ouvrage',
        ]
        widgets = {
            'nom_du_seuil': forms.TextInput(attrs={'class': 'form-control'}),
            'localisation_du_seuil': forms.TextInput(attrs={'class': 'form-control'}),
            'coordonnes_x': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'coordonnes_y': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'nature_du_seuil': forms.TextInput(attrs={'class': 'form-control'}),
            'type_du_seuil': forms.TextInput(attrs={'class': 'form-control'}),
            'materiaux_de_construction': forms.TextInput(attrs={'class': 'form-control'}),
            'debit_mobilise': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'longueur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'largeur_de_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hauteur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'largeur_tapis_amortissement': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'longueur_prise_droit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'largeur_prise_droit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nbr_pertuis_prise_droit': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'longueur_prise_gauche': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'largeur_prise_gauche': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nbr_pertuis_prise_gauche': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'longueur_degrevement_droit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'largeur_degrevement_droit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nbr_pertuis_degrevement_droit': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'longueur_degrevement_gauche': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'largeur_degrevement_gauche': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nbr_pertuis_degrevement_gauche': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'geometrie': forms.Textarea(attrs={'class': 'form-control', 'rows': '3',
                                               'placeholder': 'POINT(X Y) - Nord Maroc (m)'}),
        }


class EtatSeuilForm(forms.ModelForm):
    """Formulaire de saisie du diagnostic structuré d'un seuil."""

    class Meta:
        model = EtatSeuil
        exclude = ['seuil', 'editeur', 'created_at', 'updated_at']
        widgets = {
            'date_diagnostic': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'etat_construction_fonctionnement': forms.Select(attrs={'class': 'form-control'}),
            'etat_materiel_hydromecanique': forms.Select(attrs={'class': 'form-control'}),
            'etat_structurel_digue': forms.Select(attrs={'class': 'form-control'}),
            'affouillement_aval': forms.Select(attrs={'class': 'form-control'}),
            'envasement_retenue': forms.Select(attrs={'class': 'form-control'}),
            'murs_guideaux': forms.Select(attrs={'class': 'form-control'}),
            'radier_aval': forms.Select(attrs={'class': 'form-control'}),
            'etat_vannes': forms.Select(attrs={'class': 'form-control'}),
            'dessableur': forms.Select(attrs={'class': 'form-control'}),
            'degradation_beton': forms.Select(attrs={'class': 'form-control'}),
            'infiltration_fuite': forms.Select(attrs={'class': 'form-control'}),
            'limiteur_debit': forms.Select(attrs={'class': 'form-control'}),
        }


class MurProtectionForm(forms.ModelForm):
    class Meta:
        model = MurProtection
        # État (etat_construction, date_diagnostic, defaut_ouvrage) déplacé dans EtatMurProtection.
        exclude = [
            'created_at', 'updated_at', 'statut', 'perimetre',
            'saisi_par', 'valide_par',
            'etat_construction', 'date_diagnostic', 'defaut_ouvrage',
        ]
        widgets = {
            'nom_mur_protection': forms.TextInput(attrs={'class': 'form-control'}),
            'rive': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.Select(attrs={'class': 'form-control'}),
            'nature_materiaux': forms.TextInput(attrs={'class': 'form-control'}),
            'longueur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hauteur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'epaisseur_superieure': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'epaisseur_inferieure': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ouvrage_associe': forms.Select(attrs={'class': 'form-control'}),
            'geometrie': forms.Textarea(attrs={'class': 'form-control', 'rows': '3',
                                               'placeholder': 'WKT (POINT ou LINESTRING)'}),
        }


class EtatMurProtectionForm(forms.ModelForm):
    """Formulaire de saisie du diagnostic structuré d'un mur de protection."""

    class Meta:
        model = EtatMurProtection
        exclude = ['mur', 'editeur_operateur', 'created_at', 'updated_at']
        widgets = {
            'date_diagnostic': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'etat_general': forms.Select(attrs={'class': 'form-control'}),
            'valide': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fissures_revetement': forms.Select(attrs={'class': 'form-control'}),
            'degradation_beton': forms.Select(attrs={'class': 'form-control'}),
            'risque_contournement': forms.Select(attrs={'class': 'form-control'}),
        }


class SeguiasForm(forms.ModelForm):
    """Formulaire identité d'une séguia (nom + type). Les tronçons sont gérés séparément."""

    class Meta:
        model = Seguias
        exclude = [
            'created_at', 'updated_at', 'statut', 'perimetre',
            'saisi_par', 'valide_par', 'date_diagnostic', 'defaut_ouvrage',
        ]
        widgets = {
            'nom_de_la_seguia': forms.TextInput(attrs={'class': 'form-control'}),
            'type_deguia': forms.Select(attrs={'class': 'form-control'}),
        }


class TronconSeguiaForm(forms.ModelForm):
    """Formulaire de saisie d'un tronçon de séguia (dimensions + efficiences + géométrie)."""

    class Meta:
        model = TronconSeguia
        exclude = ['seguia', 'statut', 'efficience_calculee', 'perte_infiltration_m3s',
                   'perte_vaporisation_m3s', 'date_dernier_calcul', 'created_at', 'updated_at']
        widgets = {
            'troncon': forms.Select(attrs={'class': 'form-control'}),
            'forme': forms.Select(attrs={'class': 'form-control', 'id': 'id_forme'}),
            'longueur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'largeur_meroire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hauteur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hauteur_eau': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fruit_de_berge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'epaisseur_parois': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'diametre': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nature': forms.Select(attrs={'class': 'form-control'}),
            'debit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'type_decoulement': forms.Select(attrs={'class': 'form-control'}),
            'efficience_trancons': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '1'}),
            'geometrie': forms.Textarea(attrs={'class': 'form-control', 'rows': '3',
                                               'placeholder': 'WKT (LINESTRING ou POINT)'}),
        }

    def clean(self):
        cleaned = super().clean()
        forme = cleaned.get('forme')
        if forme == 'rectangulaire':
            cleaned['fruit_de_berge'] = 0
            if not cleaned.get('largeur_meroire'):
                self.add_error('largeur_meroire', "Largeur requise.")
            if not cleaned.get('hauteur'):
                self.add_error('hauteur', "Hauteur requise.")
        elif forme == 'trapezoidale':
            for f in ('largeur_meroire', 'hauteur', 'fruit_de_berge'):
                if cleaned.get(f) in (None, ''):
                    self.add_error(f, "Champ requis pour la forme trapézoïdale.")
        elif forme == 'circulaire':
            if not cleaned.get('diametre'):
                self.add_error('diametre', "Diamètre requis pour la forme circulaire.")
            cleaned['largeur_meroire'] = None
            cleaned['hauteur'] = None
            cleaned['fruit_de_berge'] = None
        return cleaned


class EtatTronconSeguiaForm(forms.ModelForm):
    """Formulaire de saisie du diagnostic structuré d'un tronçon de séguia."""

    class Meta:
        model = EtatTronconSeguia
        exclude = ['troncon', 'editeur_operateur', 'created_at', 'updated_at']
        widgets = {
            'date_diagnostic': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'etat_general': forms.Select(attrs={'class': 'form-control'}),
            'valide': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fissures_revetement': forms.Select(attrs={'class': 'form-control'}),
            'infiltration_fuite': forms.Select(attrs={'class': 'form-control'}),
            'obstructions_debris': forms.Select(attrs={'class': 'form-control'}),
            'erosion_berges': forms.Select(attrs={'class': 'form-control'}),
            'sedimentation_fond': forms.Select(attrs={'class': 'form-control'}),
            'ouvrages_regulation': forms.Select(attrs={'class': 'form-control'}),
            'spalling_beton': forms.Select(attrs={'class': 'form-control'}),
        }


class BarrageRetenueForm(forms.ModelForm):
    class Meta:
        model = BarrageRetenue
        # État (etat_construction_fonctionnement, date_diagnostic, defaut_ouvrage)
        # déplacé dans EtatBarrageRetenue.
        exclude = [
            'created_at', 'updated_at', 'statut', 'perimetre',
            'saisi_par', 'valide_par',
            'etat_construction_fonctionnement', 'date_diagnostic', 'defaut_ouvrage',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'coordonnees_lambert_x': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'coordonnees_lambert_y': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'debit_derive': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'volume_attribue_irrigation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'capacite_retenue': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'longueur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'largeur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hauteur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'materiaux_de_construction': forms.TextInput(attrs={'class': 'form-control'}),
            'geometrie': forms.Textarea(attrs={'class': 'form-control', 'rows': '3',
                                               'placeholder': 'POINT(X Y) - Nord Maroc (m)'}),
        }


class EtatBarrageRetenueForm(forms.ModelForm):
    """Formulaire de saisie du diagnostic structuré d'un barrage de retenue."""

    class Meta:
        model = EtatBarrageRetenue
        exclude = ['barrage', 'editeur_operateur', 'created_at', 'updated_at']
        widgets = {
            'date_diagnostic': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'etat_general': forms.Select(attrs={'class': 'form-control'}),
            'valide': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'affouillement_pied_digue_aval': forms.Select(attrs={'class': 'form-control'}),
            'taux_envasement_retenue': forms.Select(attrs={'class': 'form-control'}),
            'regulation_debits_aval': forms.Select(attrs={'class': 'form-control'}),
            'fonctionnement_ouvrages_prise_eau': forms.Select(attrs={'class': 'form-control'}),
        }


class KhettaraForm(forms.ModelForm):
    class Meta:
        model = Khettara
        # État (etat_construction_fonctionnement, date_diagnostic, defaut_ouvrage)
        # déplacé dans EtatKhettara.
        exclude = [
            'created_at', 'updated_at', 'statut', 'perimetre',
            'saisi_par', 'valide_par',
            'etat_construction_fonctionnement', 'date_diagnostic', 'defaut_ouvrage',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'coordonnees_lambert_x': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'coordonnees_lambert_y': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'debit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'longueur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'largeur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hauteur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'materiaux_de_construction': forms.TextInput(attrs={'class': 'form-control'}),
            'geometrie': forms.Textarea(attrs={'class': 'form-control', 'rows': '3',
                                               'placeholder': 'WKT (POINT ou LINESTRING)'}),
        }


class EtatKhettaraForm(forms.ModelForm):
    """Formulaire de saisie du diagnostic structuré d'une khettara."""

    class Meta:
        model = EtatKhettara
        exclude = ['khettara', 'editeur_operateur', 'created_at', 'updated_at']
        widgets = {
            'date_diagnostic': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'etat_general': forms.Select(attrs={'class': 'form-control'}),
            'valide': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'envasement_ensablement_fond': forms.Select(attrs={'class': 'form-control'}),
            'degradation_beton': forms.Select(attrs={'class': 'form-control'}),
            'accessibilite_entretien': forms.Select(attrs={'class': 'form-control'}),
            'stabilite_galerie_principale': forms.Select(attrs={'class': 'form-control'}),
        }


class ForagePuitsForm(forms.ModelForm):
    class Meta:
        model = ForagePuits
        # État (etat_construction_fonctionnement, date_diagnostic, defaut_ouvrage)
        # déplacé dans EtatForagePuits.
        exclude = [
            'created_at', 'updated_at', 'statut', 'perimetre',
            'saisi_par', 'valide_par',
            'etat_construction_fonctionnement', 'date_diagnostic', 'defaut_ouvrage',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'coordonnees_lambert_x': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'coordonnees_lambert_y': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'debit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'profondeur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'diametre': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'equipements_associes': forms.TextInput(attrs={'class': 'form-control'}),
            'source_energie_pompage': forms.Select(attrs={'class': 'form-control'}),
            'geometrie': forms.Textarea(attrs={'class': 'form-control', 'rows': '3',
                                               'placeholder': 'POINT(X Y) - Nord Maroc (m)'}),
        }


class EtatForagePuitsForm(forms.ModelForm):
    """Formulaire de saisie du diagnostic structuré d'un forage/puits."""

    class Meta:
        model = EtatForagePuits
        exclude = ['forage', 'editeur_operateur', 'created_at', 'updated_at']
        widgets = {
            'date_diagnostic': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'etat_general': forms.Select(attrs={'class': 'form-control'}),
            'valide': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'qualite_physico_chimique_eau': forms.Select(attrs={'class': 'form-control'}),
            'degradation_structurelle_forage': forms.Select(attrs={'class': 'form-control'}),
            'colmatage_forage': forms.Select(attrs={'class': 'form-control'}),
            'etat_equipements': forms.Select(attrs={'class': 'form-control'}),
        }


class PriseLocaleForm(forms.ModelForm):
    class Meta:
        model = PriseLocale
        # État (etat_fonctionnement, date_diagnostic, defaut_ouvrage) déplacé dans EtatPriseLocale.
        exclude = [
            'created_at', 'updated_at', 'statut', 'perimetre',
            'saisi_par', 'valide_par',
            'etat_fonctionnement', 'date_diagnostic', 'defaut_ouvrage',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'coordonnee_x': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'coordonnee_y': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'materiaux_construction': forms.TextInput(attrs={'class': 'form-control'}),
            'forme_pertuis': forms.Select(attrs={'class': 'form-control', 'onchange': 'updateFormeFields(this.value)'}),
            'largeur_au_miroir': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hauteur_pertuis': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fruit_pente': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'diametre': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'debit_derive': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'geometrie': forms.Textarea(attrs={'class': 'form-control', 'rows': '3',
                                               'placeholder': 'WKT (POINT, LINESTRING…)'}),
        }


class EtatPriseLocaleForm(forms.ModelForm):
    """Formulaire de saisie du diagnostic structuré d'une prise locale."""

    class Meta:
        model = EtatPriseLocale
        exclude = ['prise', 'editeur_operateur', 'created_at', 'updated_at']
        widgets = {
            'date_diagnostic': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'etat_general': forms.Select(attrs={'class': 'form-control'}),
            'valide': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'envasement_sedimentation_entree': forms.Select(attrs={'class': 'form-control'}),
            'degradation_revetement': forms.Select(attrs={'class': 'form-control'}),
            'accumulation_debris_vegetation': forms.Select(attrs={'class': 'form-control'}),
            'etat_dispositifs_regulation': forms.Select(attrs={'class': 'form-control'}),
            'protection_crues_debordements': forms.Select(attrs={'class': 'form-control'}),
        }


class ShpImportForm(forms.Form):
    fichier_zip = forms.FileField(
        label="Fichier Shapefile (.zip)",
        help_text="Compresser les fichiers .shp, .dbf, .shx (et .prj) dans un seul fichier .zip",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.zip'}),
    )
    perimetre = forms.ModelChoiceField(
        queryset=Perimetre.objects.all(),
        label="Périmètre associé",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )


class ShpImportUnifiedForm(forms.Form):
    """Formulaire unifié : sélectionner le type d'objet importé puis le fichier .zip."""

    TYPE_CHOICES = [
        ('perimetre', 'Périmètre'),
        ('seuil',     'Seuil (ouvrage de tête)'),
        ('barrage',   'Barrage de retenue (ouvrage de tête)'),
        ('khettara',  'Khettara (ouvrage de tête)'),
        ('forage',    'Forage / Puits (ouvrage de tête)'),
        ('mur',       'Mur de protection (ouvrage de tête)'),
        ('prise',     'Prise locale (ouvrage de tête)'),
        ('seguia',    'Séguia (réseau d\'irrigation)'),
    ]

    type_donnee = forms.ChoiceField(
        choices=TYPE_CHOICES,
        label="Type de données à importer",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_type_donnee'}),
    )
    perimetre = forms.ModelChoiceField(
        queryset=Perimetre.objects.all(),
        required=False,
        label="Périmètre associé",
        help_text="Obligatoire pour les ouvrages et réseaux ; ignoré pour l'import d'un périmètre.",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    fichier_zip = forms.FileField(
        label="Fichier Shapefile (.zip)",
        help_text="Compresser les fichiers .shp, .dbf, .shx (et .prj) dans un seul fichier .zip",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.zip'}),
    )

    def clean(self):
        cleaned = super().clean()
        type_donnee = cleaned.get('type_donnee')
        perimetre = cleaned.get('perimetre')
        if type_donnee and type_donnee != 'perimetre' and not perimetre:
            self.add_error('perimetre', "Le périmètre est obligatoire pour ce type de données.")
        return cleaned
