from django.contrib import admin
from .models import Requete, CommentaireRequete, HistoriqueStatut, PieceJointeRequete


class CommentaireInline(admin.TabularInline):
    model = CommentaireRequete
    extra = 0
    readonly_fields = ('auteur', 'date_creation')


class HistoriqueInline(admin.TabularInline):
    model = HistoriqueStatut
    extra = 0
    readonly_fields = ('statut_precedent', 'statut_nouveau', 'auteur', 'date')
    can_delete = False


class PieceJointeInline(admin.TabularInline):
    model = PieceJointeRequete
    extra = 0
    readonly_fields = ('nom_original', 'taille_ko', 'date_upload')


@admin.register(Requete)
class RequeteAdmin(admin.ModelAdmin):
    list_display = ('reference', 'titre', 'type_requete', 'urgence', 'statut',
                    'perimetre', 'emetteur', 'date_soumission')
    list_filter  = ('type_requete', 'urgence', 'statut')
    search_fields = ('reference', 'titre', 'nom_emetteur')
    readonly_fields = ('reference', 'date_soumission', 'date_modification',
                       'date_traitement', 'date_cloture')
    inlines = [CommentaireInline, HistoriqueInline, PieceJointeInline]


@admin.register(CommentaireRequete)
class CommentaireRequeteAdmin(admin.ModelAdmin):
    list_display = ('requete', 'auteur', 'interne', 'date_creation')
    list_filter  = ('interne',)


@admin.register(HistoriqueStatut)
class HistoriqueStatutAdmin(admin.ModelAdmin):
    list_display = ('requete', 'statut_precedent', 'statut_nouveau', 'auteur', 'date')
    readonly_fields = ('date',)


@admin.register(PieceJointeRequete)
class PieceJointeRequeteAdmin(admin.ModelAdmin):
    list_display = ('requete', 'nom_original', 'taille_ko', 'date_upload')
