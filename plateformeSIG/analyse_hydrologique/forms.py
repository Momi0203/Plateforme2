from django import forms
from django.contrib.postgres.forms import SimpleArrayField

from .models import (
    BassinVersant, StationPluviometrique, StationHydrometrique,
    CoefficientMontana,
)
from .calculs import FORMULES_TC_DISPONIBLES, FORMULES_Q_DISPONIBLES

_NB_MOIS = 12
_JOURS_MOIS_HYDRO = [30, 31, 30, 31, 31, 28, 31, 30, 31, 30, 31, 31]
_COORD_MIN = -500_000
_COORD_MAX = 1_500_000


def _validate_coord_nord_maroc(value, field_label):
    if value is None:
        return
    if not (_COORD_MIN <= value <= _COORD_MAX):
        raise forms.ValidationError(
            f"{field_label} doit être saisi en coordonnées Nord Maroc (m)."
        )


# =============================================================================
# Champs personnalisÃ©s pour les sÃ©ries (ArrayField)
# =============================================================================

class ListeAnneesField(SimpleArrayField):
    """Accepte une suite d'annÃ©es sÃ©parÃ©es par des virgules â†’ list[int]"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('base_field', forms.FloatField())
        kwargs.setdefault('delimiter', ',')
        kwargs.setdefault('label', "Années (séparées par virgule)")
        kwargs.setdefault('help_text', "Ex : 1990, 1991, 1992, …")
        super().__init__(*args, **kwargs)


class ListeFlottantsField(SimpleArrayField):
    """Accepte une suite de flottants sÃ©parÃ©s par des virgules â†’ list[float]"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('base_field', forms.FloatField())
        kwargs.setdefault('delimiter', ',')
        kwargs.setdefault('help_text', "Ex : 25.3, 42.1, 18.7, …")
        super().__init__(*args, **kwargs)


# =============================================================================
# Bassin Versant
# =============================================================================

class BassinVersantForm(forms.ModelForm):
    class Meta:
        model  = BassinVersant
        exclude = ['geometrie']
        widgets = {
            'ouvrage_en_tete': forms.TextInput(),
        }

    def clean_x_exutoire(self):
        value = self.cleaned_data.get('x_exutoire')
        _validate_coord_nord_maroc(value, "X exutoire")
        return value

    def clean_y_exutoire(self):
        value = self.cleaned_data.get('y_exutoire')
        _validate_coord_nord_maroc(value, "Y exutoire")
        return value


# =============================================================================
# Station PluviomÃ©trique
# =============================================================================

class StationPluviometriqueForm(forms.ModelForm):
    annees = ListeAnneesField(required=False)
    pjmax  = ListeFlottantsField(
        required=False,
        label="Pjmax observées (mm, séparées par virgule)",
        help_text="Une valeur par année, dans le même ordre",
    )

    class Meta:
        model  = StationPluviometrique
        exclude = ['geometrie']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['x'].widget.attrs.setdefault('step', '0.01')
        self.fields['x'].widget.attrs.setdefault('placeholder', 'Ex : 500000')
        self.fields['y'].widget.attrs.setdefault('step', '0.01')
        self.fields['y'].widget.attrs.setdefault('placeholder', 'Ex : 300000')

    def clean(self):
        cleaned = super().clean()
        annees = cleaned.get('annees') or []
        pjmax  = cleaned.get('pjmax')  or []
        if annees and pjmax and len(annees) != len(pjmax):
            raise forms.ValidationError(
                "Le nombre d'années et le nombre de Pjmax doivent être égaux."
            )
        return cleaned

    def clean_x(self):
        value = self.cleaned_data.get('x')
        _validate_coord_nord_maroc(value, "X")
        return value

    def clean_y(self):
        value = self.cleaned_data.get('y')
        _validate_coord_nord_maroc(value, "Y")
        return value


# =============================================================================
# Station HydromÃ©trique
# =============================================================================

class StationHydrometriqueForm(forms.ModelForm):
    annees = ListeAnneesField(required=False)
    qjmax  = ListeFlottantsField(
        required=False,
        label="Qjmax observées (m3/s, séparées par virgule)",
        help_text="Une valeur par année, dans le même ordre",
    )
    debits_mensuels_annee_normale = SimpleArrayField(
        base_field=forms.FloatField(),
        delimiter=',',
        required=False,
        widget=forms.HiddenInput(),
        label="Débits mensuels année normale (Sep → Aou)",
    )
    frequences_mensuelles_annee_normale = SimpleArrayField(
        base_field=forms.FloatField(min_value=1),
        delimiter=',',
        required=False,
        widget=forms.HiddenInput(),
        label="Fréquences mensuelles année normale (jours, Sep → Aou)",
    )
    debits_mensuels_annee_humide = SimpleArrayField(
        base_field=forms.FloatField(),
        delimiter=',',
        required=False,
        widget=forms.HiddenInput(),
        label="Débits mensuels année humide (Sep → Aou)",
    )
    frequences_mensuelles_annee_humide = SimpleArrayField(
        base_field=forms.FloatField(min_value=1),
        delimiter=',',
        required=False,
        widget=forms.HiddenInput(),
        label="Fréquences mensuelles année humide (jours, Sep → Aou)",
    )
    debits_mensuels_annee_seche = SimpleArrayField(
        base_field=forms.FloatField(),
        delimiter=',',
        required=False,
        widget=forms.HiddenInput(),
        label="Débits mensuels année sèche (Sep → Aou)",
    )
    frequences_mensuelles_annee_seche = SimpleArrayField(
        base_field=forms.FloatField(min_value=1),
        delimiter=',',
        required=False,
        widget=forms.HiddenInput(),
        label="Fréquences mensuelles année sèche (jours, Sep → Aou)",
    )

    class Meta:
        model  = StationHydrometrique
        exclude = ['geometrie']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['x'].widget.attrs.setdefault('step', '0.01')
        self.fields['x'].widget.attrs.setdefault('placeholder', 'Ex : 500000')
        self.fields['y'].widget.attrs.setdefault('step', '0.01')
        self.fields['y'].widget.attrs.setdefault('placeholder', 'Ex : 300000')

        default_freq = ','.join(str(v) for v in _JOURS_MOIS_HYDRO)
        if not self.instance.pk:
            self.initial.setdefault('frequences_mensuelles_annee_normale', default_freq)
            self.initial.setdefault('frequences_mensuelles_annee_humide', default_freq)
            self.initial.setdefault('frequences_mensuelles_annee_seche', default_freq)
        else:
            if not self.instance.frequences_mensuelles_annee_normale:
                self.initial.setdefault('frequences_mensuelles_annee_normale', default_freq)
            if not self.instance.frequences_mensuelles_annee_humide:
                self.initial.setdefault('frequences_mensuelles_annee_humide', default_freq)
            if not self.instance.frequences_mensuelles_annee_seche:
                self.initial.setdefault('frequences_mensuelles_annee_seche', default_freq)

    def clean(self):
        cleaned = super().clean()
        annees = cleaned.get('annees') or []
        qjmax = cleaned.get('qjmax') or []
        if annees and qjmax and len(annees) != len(qjmax):
            raise forms.ValidationError(
                "Le nombre d'années et le nombre de Qjmax doivent être égaux."
            )

        matrice_6x12 = [
            ('debits_mensuels_annee_normale', "Les débits année normale"),
            ('frequences_mensuelles_annee_normale', "Les fréquences année normale"),
            ('debits_mensuels_annee_humide', "Les débits année humide"),
            ('frequences_mensuelles_annee_humide', "Les fréquences année humide"),
            ('debits_mensuels_annee_seche', "Les débits année sèche"),
            ('frequences_mensuelles_annee_seche', "Les fréquences année sèche"),
        ]
        for field_name, label in matrice_6x12:
            values = cleaned.get(field_name) or []
            if values and len(values) != _NB_MOIS:
                self.add_error(
                    field_name,
                    f"{label} doivent contenir exactement {_NB_MOIS} valeurs (Sep → Aou).",
                )

        freq_normale = cleaned.get('frequences_mensuelles_annee_normale') or []
        freq_humide = cleaned.get('frequences_mensuelles_annee_humide') or []
        freq_seche = cleaned.get('frequences_mensuelles_annee_seche') or []
        for freq_name, freqs in (
            ('frequences_mensuelles_annee_normale', freq_normale),
            ('frequences_mensuelles_annee_humide', freq_humide),
            ('frequences_mensuelles_annee_seche', freq_seche),
        ):
            if freqs and any(v <= 0 for v in freqs):
                self.add_error(freq_name, "Les fréquences mensuelles doivent être supérieures à 0.")

        return cleaned

    def clean_x(self):
        value = self.cleaned_data.get('x')
        _validate_coord_nord_maroc(value, "X")
        return value

    def clean_y(self):
        value = self.cleaned_data.get('y')
        _validate_coord_nord_maroc(value, "Y")
        return value


# =============================================================================
# Coefficients Montana
# =============================================================================

class CoefficientMontanaForm(forms.ModelForm):
    class Meta:
        model  = CoefficientMontana
        fields = '__all__'

    def clean(self):
        cleaned = super().clean()
        a_vals = [cleaned.get(f'a{t}') for t in [10, 20, 50, 100]]
        b_vals = [cleaned.get(f'b{t}') for t in [10, 20, 50, 100]]
        if any(v is None for v in a_vals) or any(v is None for v in b_vals):
            raise forms.ValidationError(
                "Tous les coefficients a et b (T=10, 20, 50, 100) sont obligatoires."
            )
        return cleaned


# =============================================================================
# Formulaire de lancement d'analyse
# =============================================================================

_TC_CHOICES = [(f, f) for f in FORMULES_TC_DISPONIBLES]
_Q_CHOICES  = [(f, f) for f in FORMULES_Q_DISPONIBLES]

# SÃ©lection par dÃ©faut : toutes les formules sauf Fuller II
_Q_DEFAULT = [f for f in FORMULES_Q_DISPONIBLES if f != 'Fuller II']


class AnalyseParametresForm(forms.Form):

    # â”€â”€ Stations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    station_pluvio = forms.ModelChoiceField(
        queryset=StationPluviometrique.objects.all(),
        label="Station pluviométrique de référence",
        help_text="Fournit les Pj24h et les coefficients Montana",
    )
    station_hydro = forms.ModelChoiceField(
        queryset=StationHydrometrique.objects.all(),
        required=False,
        label="Station hydrométrique (optionnel)",
        help_text="Nécessaire uniquement si Francou-Rodier est inclus",
    )

    # â”€â”€ SÃ©lection des formules Tc â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    formules_tc = forms.MultipleChoiceField(
        choices=_TC_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        initial=FORMULES_TC_DISPONIBLES,
        label="Formules de temps de concentration",
        help_text="La moyenne des Tc retenus est utilisée dans les calculs",
    )

    # â”€â”€ SÃ©lection des formules Q pour la moyenne finale â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    formules_q_incluses = forms.MultipleChoiceField(
        choices=_Q_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        initial=_Q_DEFAULT,
        label="Formules incluses dans la moyenne finale",
        help_text="Fuller II souvent exclu (valeurs hors-échelle sur certains BV)",
    )

    # â”€â”€ ParamÃ¨tres des formules â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    C_rationnel = forms.FloatField(
        initial=0.42, min_value=0.0, max_value=1.0,
        label="C — coefficient de ruissellement (Rationnelle)",
    )
    K_macmath = forms.FloatField(
        initial=0.48,
        label="K (Mac-Math)",
    )
    A_fuller = forms.FloatField(
        initial=3.2,
        label="A (Fuller II)",
    )
    N_fuller = forms.FloatField(
        initial=80,
        label="N (Fuller II)",
    )
    k_mallet = forms.FloatField(
        initial=5.5,
        label="k (Mallet-Gauthier)",
    )
    a_mallet = forms.FloatField(
        initial=20,
        label="a (Mallet-Gauthier)",
    )
    K1_hl = forms.FloatField(
        initial=13.47,
        label="K1 (Hazen-Lazervic)",
    )
    K2_hl = forms.FloatField(
        initial=0.587,
        label="K2 (Hazen-Lazervic)",
    )
    a_hl = forms.FloatField(
        initial=0.8,
        label="a exposant (Hazen-Lazervic)",
    )

    # â”€â”€ Texte libre â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    observations = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Observations",
    )
    conclusions = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Conclusions et recommandations",
    )

    def clean(self):
        cleaned = super().clean()
        formules_q = cleaned.get('formules_q_incluses', [])
        station_hydro = cleaned.get('station_hydro')
        if 'Francou-Rodier' in formules_q and not station_hydro:
            self.add_error(
                'station_hydro',
                "Une station hydrométrique est requise pour la méthode Francou-Rodier.",
            )
        return cleaned
