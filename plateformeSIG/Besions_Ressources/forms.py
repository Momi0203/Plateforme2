import json
from django import forms
from django.forms.models import inlineformset_factory
from .models import (
    StationClimatique, Kc_Kr_culture, BilanBesoinRessources,
    BilanOuvrageAssocie, AutreRessource,
)
from diagnostic.models import CULTURES_TAFILALET
from .calculs import taux_insolation_par_latitude

MOIS_LABELS = ["Sep", "Oct", "Nov", "Déc", "Jan", "Fév", "Mar", "Avr", "Mai", "Jui", "Jul", "Aoû"]
_COORD_MIN = -500_000
_COORD_MAX = 1_500_000


def _monthly_fields(prefix, label, min_val=None, max_val=None, step="0.01", placeholder=""):
    """Génère 12 champs FloatField nommés prefix_0 … prefix_11."""
    fields = {}
    for i, mois in enumerate(MOIS_LABELS):
        kwargs = dict(
            label=f"{label} — {mois}",
            required=True,
            widget=forms.NumberInput(attrs={
                'step': step,
                'class': 'form-control form-control-sm monthly-input',
                'data-prefix': prefix,
                'data-index': str(i),
                'placeholder': placeholder,
            }),
        )
        if min_val is not None:
            kwargs['min_value'] = min_val
        if max_val is not None:
            kwargs['max_value'] = max_val
        fields[f'{prefix}_{i}'] = forms.FloatField(**kwargs)
    return fields


class StationClimatique12Form(forms.ModelForm):
    """Formulaire StationClimatique avec 12 champs mensuels."""

    class Meta:
        model = StationClimatique
        fields = ['nom', 'latitude', 'x', 'y']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'x': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ex : 500000'}),
            'y': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ex : 300000'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['x'].required = True
        self.fields['y'].required = True
        self.insolation_auto = self._build_auto_insolation()

        for name, field in _monthly_fields('temp', 'T moy (°C)', step='0.1').items():
            self.fields[name] = field

        for name, field in _monthly_fields('insol', 'n/N (auto)', min_val=0.0, max_val=1.0).items():
            field.required = False
            field.disabled = True
            field.widget.attrs['readonly'] = True
            self.fields[name] = field

        for name, field in _monthly_fields('pnorm', 'P normale (mm/mois)', min_val=0.0, step='0.1').items():
            self.fields[name] = field

        for name, field in _monthly_fields('phumide', 'P humide (mm/mois)', min_val=0.0, step='0.1').items():
            field.required = False
            self.fields[name] = field

        if self.instance and self.instance.pk:
            self._prefill_monthly('temp', self.instance.temperatures_moyennes)
            self._prefill_monthly('pnorm', self.instance.precipitations_normales)
            if self.instance.precipitations_humides:
                self._prefill_monthly('phumide', self.instance.precipitations_humides)
        self._prefill_monthly('insol', self.insolation_auto)

    def _build_auto_insolation(self):
        latitude = None
        if self.is_bound:
            raw = self.data.get('latitude')
            if raw not in (None, ''):
                try:
                    latitude = float(str(raw).replace(',', '.'))
                except ValueError:
                    latitude = None
        elif self.instance and self.instance.pk:
            latitude = self.instance.latitude

        if latitude is None:
            if self.instance and self.instance.pk and self.instance.taux_insolation:
                vals = self.instance.taux_insolation
                if isinstance(vals, list) and len(vals) == 12:
                    return [round(float(v), 2) for v in vals]
            return [0.0] * 12
        return taux_insolation_par_latitude(latitude)

    def _prefill_monthly(self, prefix, values):
        if not values:
            return
        for i, v in enumerate(values):
            key = f'{prefix}_{i}'
            if key in self.fields:
                self.initial[key] = v

    def _collect_monthly(self, prefix):
        return [self.cleaned_data.get(f'{prefix}_{i}', 0.0) for i in range(12)]

    def clean_latitude(self):
        latitude = self.cleaned_data['latitude']
        if latitude < -90 or latitude > 90:
            raise forms.ValidationError("Latitude invalide (degrés).")
        return latitude

    def clean_x(self):
        value = self.cleaned_data['x']
        if value < _COORD_MIN or value > _COORD_MAX:
            raise forms.ValidationError("X doit être saisi en coordonnées Nord Maroc (m).")
        return value

    def clean_y(self):
        value = self.cleaned_data['y']
        if value < _COORD_MIN or value > _COORD_MAX:
            raise forms.ValidationError("Y doit être saisi en coordonnées Nord Maroc (m).")
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.temperatures_moyennes = self._collect_monthly('temp')
        instance.taux_insolation = taux_insolation_par_latitude(instance.latitude)
        instance.precipitations_normales = self._collect_monthly('pnorm')
        humide = self._collect_monthly('phumide')
        instance.precipitations_humides = humide if any(v for v in humide) else None
        if commit:
            instance.save()
        return instance


class KcKrCultureForm(forms.ModelForm):
    """Référentiel global : 1 enregistrement Kc/Kr par nom de culture.

    Aucune notion de périmètre. Le champ `nom` est un select parmi
    CULTURES_TAFILALET (unique en DB).
    """

    class Meta:
        model = Kc_Kr_culture
        fields = ['nom']
        widgets = {
            'nom': forms.Select(attrs={'class': 'form-control'}, choices=CULTURES_TAFILALET),
        }

    def __init__(self, *args, **kwargs):
        # Le kwarg `perimetre` est accepté mais ignoré (compat appels existants).
        kwargs.pop('perimetre', None)
        super().__init__(*args, **kwargs)
        self.fields['nom'].label = "Nom de culture"

        for name, field in _monthly_fields('kc', 'Kc', min_val=0.0, max_val=3.0).items():
            self.fields[name] = field
        for name, field in _monthly_fields('kr', 'Kr', min_val=0.0, max_val=1.0).items():
            self.fields[name] = field

        if self.instance and self.instance.pk:
            self._prefill('kc', self.instance.kc)
            self._prefill('kr', self.instance.kr)

    def _prefill(self, prefix, values):
        if not values:
            return
        for i, v in enumerate(values):
            self.initial[f'{prefix}_{i}'] = v

    def _collect(self, prefix):
        return [self.cleaned_data.get(f'{prefix}_{i}', 0.0) for i in range(12)]

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.kc = self._collect('kc')
        instance.kr = self._collect('kr')
        if commit:
            instance.save()
        return instance


# Alias rétrocompat
CulturePerimetreForm = KcKrCultureForm


class BilanBaseForm(forms.ModelForm):
    """Formulaire de création/configuration du bilan.

    Champs visibles : périmètre, stations climatique et hydrométrique,
    dimensions canal (optionnelles — défauts via Manning si vides).

    Les paramètres efficience réseau et coefficient humide ne sont plus
    exposés ici : ils sont définis ouvrage par ouvrage dans le div
    « Ouvrages associés ».

    Les paramètres dérivés (BV, Tc, débits) viennent des ouvrages associés
    et sont remplis dans la vue à partir du formset.
    """

    class Meta:
        model = BilanBesoinRessources
        fields = [
            'perimetre', 'station_climatique', 'station_hydrometrique',
            'canal_forme',
            'canal_b', 'canal_y', 'canal_z', 'canal_diametre',
            'canal_pente', 'canal_manning_n',
        ]
        widgets = {
            'perimetre': forms.Select(attrs={'class': 'form-control'}),
            'station_climatique': forms.Select(attrs={'class': 'form-control'}),
            'station_hydrometrique': forms.Select(attrs={'class': 'form-control'}),
            'canal_forme': forms.Select(attrs={'class': 'form-control'}),
            'canal_b': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'canal_y': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'canal_z': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'canal_diametre': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'canal_pente': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001', 'placeholder': '0.0001 si vide'}),
            'canal_manning_n': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': '0.015 si vide'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields:
            if f not in ('perimetre', 'station_climatique'):
                self.fields[f].required = False


class BilanOuvrageAssocieForm(forms.ModelForm):
    """Une ligne d'ouvrage associé au bilan.

    Le JS de la page injecte la FK appropriée (`seuil`/`prise_locale`/…) selon
    `type_ouvrage`. Le snapshot (BV, Tc, débit_tronçon) est calculé côté
    serveur dans la vue après validation. Les paramètres saisis (efficience,
    débit amont, capacité déversement, débit khettara/transfert, tour d'eau,
    durée, coefficients humide/sèche, apports mensuels) sont stockés sur la
    ligne formset.
    """

    class Meta:
        model = BilanOuvrageAssocie
        fields = [
            'type_ouvrage',
            'seuil', 'prise_locale', 'barrage', 'khettara', 'forage',
            'troncon_amenee', 'troncon_amenee_2', 'bassin_versant', 'ordre',
            # Paramètres saisis dans le bilan (hidden inputs alimentés par JS)
            'efficience_reseau',
            'debit_amont_m3s', 'capacite_deversement_pct',
            'debit_khettarat_m3s', 'transfert_amont', 'debit_transfert_m3s',
            'tour_eau_jours', 'duree_jours',
            'coeff_humide', 'coeff_seche',
            'apports_mensuels_normale', 'apports_mensuels_humide', 'apports_mensuels_seche',
        ]
        widgets = {
            'type_ouvrage': forms.HiddenInput(),
            'seuil': forms.HiddenInput(),
            'prise_locale': forms.HiddenInput(),
            'barrage': forms.HiddenInput(),
            'khettara': forms.HiddenInput(),
            'forage': forms.HiddenInput(),
            'troncon_amenee': forms.HiddenInput(),
            'troncon_amenee_2': forms.HiddenInput(),
            'bassin_versant': forms.HiddenInput(),
            'ordre': forms.HiddenInput(),
            'efficience_reseau': forms.HiddenInput(),
            'debit_amont_m3s': forms.HiddenInput(),
            'capacite_deversement_pct': forms.HiddenInput(),
            'debit_khettarat_m3s': forms.HiddenInput(),
            'transfert_amont': forms.HiddenInput(),
            'debit_transfert_m3s': forms.HiddenInput(),
            'tour_eau_jours': forms.HiddenInput(),
            'duree_jours': forms.HiddenInput(),
            'coeff_humide': forms.HiddenInput(),
            'coeff_seche': forms.HiddenInput(),
            'apports_mensuels_normale': forms.HiddenInput(),
            'apports_mensuels_humide': forms.HiddenInput(),
            'apports_mensuels_seche': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tous les paramètres saisis sont optionnels au niveau form ;
        # leur pertinence dépend du type d'ouvrage (validée côté UI/JS).
        for f in list(self.fields):
            if f not in ('type_ouvrage',):
                self.fields[f].required = False

    def clean_apports_mensuels_normale(self):
        return self._clean_apports('apports_mensuels_normale')

    def clean_apports_mensuels_humide(self):
        return self._clean_apports('apports_mensuels_humide')

    def clean_apports_mensuels_seche(self):
        return self._clean_apports('apports_mensuels_seche')

    def _clean_apports(self, field_name):
        raw = self.cleaned_data.get(field_name)
        if raw in (None, '', [], {}):
            return None
        # Accepter une CSV en provenance d'un HiddenInput
        if isinstance(raw, str):
            try:
                vals = [float(v.strip().replace(',', '.')) for v in raw.split(',') if v.strip() != '']
            except ValueError:
                raise forms.ValidationError(f"{field_name} : valeurs numériques attendues (CSV).")
        elif isinstance(raw, list):
            vals = raw
        else:
            return None
        if len(vals) and len(vals) != 12:
            raise forms.ValidationError(f"{field_name} : 12 valeurs Sep→Aoû attendues.")
        return vals or None

    def clean(self):
        cleaned = super().clean()
        typ = cleaned.get('type_ouvrage')
        if not typ:
            return cleaned
        ouvrage_fields = {
            'seuil':        cleaned.get('seuil'),
            'prise_locale': cleaned.get('prise_locale'),
            'barrage':      cleaned.get('barrage'),
            'khettara':     cleaned.get('khettara'),
            'forage':       cleaned.get('forage'),
        }
        # L'ouvrage du type déclaré doit être renseigné
        if not ouvrage_fields.get(typ):
            raise forms.ValidationError(
                f"Aucun ouvrage sélectionné pour le type « {typ} »."
            )
        # Nettoyer les autres FK pour rester cohérent
        for k, v in ouvrage_fields.items():
            if k != typ and v is not None:
                cleaned[k] = None
        return cleaned


BilanOuvrageFormSet = inlineformset_factory(
    BilanBesoinRessources,
    BilanOuvrageAssocie,
    form=BilanOuvrageAssocieForm,
    extra=0,
    can_delete=True,
)


class AutreRessourceForm(forms.ModelForm):
    """Ressource en eau indépendante du périmètre (parallèle aux ouvrages).

    Apports mensuels 3 années (normale/humide/sèche) + efficience (défaut 0.80).
    """

    class Meta:
        model = AutreRessource
        fields = [
            'nom', 'efficience',
            'apports_mensuels_normale', 'apports_mensuels_humide', 'apports_mensuels_seche',
            'ordre',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : Source X, Recyclage Y…'}),
            'efficience': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '1'}),
            'apports_mensuels_normale': forms.HiddenInput(),
            'apports_mensuels_humide': forms.HiddenInput(),
            'apports_mensuels_seche': forms.HiddenInput(),
            'ordre': forms.HiddenInput(),
        }

    def clean_apports_mensuels_normale(self):
        return self._clean_apports('apports_mensuels_normale')

    def clean_apports_mensuels_humide(self):
        return self._clean_apports('apports_mensuels_humide')

    def clean_apports_mensuels_seche(self):
        return self._clean_apports('apports_mensuels_seche')

    def _clean_apports(self, field_name):
        raw = self.cleaned_data.get(field_name)
        if raw in (None, '', [], {}):
            return None
        if isinstance(raw, str):
            try:
                vals = [float(v.strip().replace(',', '.')) for v in raw.split(',') if v.strip() != '']
            except ValueError:
                raise forms.ValidationError(f"{field_name} : valeurs numériques attendues (CSV).")
        elif isinstance(raw, list):
            vals = raw
        else:
            return None
        if len(vals) and len(vals) != 12:
            raise forms.ValidationError(f"{field_name} : 12 valeurs Sep→Aoû attendues.")
        return vals or None


AutreRessourceFormSet = inlineformset_factory(
    BilanBesoinRessources,
    AutreRessource,
    form=AutreRessourceForm,
    extra=0,
    can_delete=True,
)
