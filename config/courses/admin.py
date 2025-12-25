# courses/admin.py
from django.contrib import admin
from .models import Matiere, Cours, Question, ReponseEleve, ConversationIA, ProgrammeScolaire, CoursGenere, Exercice


@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ['nom', 'icone', 'description']
    search_fields = ['nom']


@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display = ['titre', 'matiere', 'eleve', 'type_saisie', 'statut', 'date_ajout', 'favori']
    list_filter = ['statut', 'type_saisie', 'matiere', 'favori', 'date_ajout']
    search_fields = ['titre', 'chapitre', 'eleve__username', 'eleve__first_name', 'eleve__last_name']
    readonly_fields = ['date_ajout', 'date_modification', 'nombre_revisions', 'derniere_revision']

    fieldsets = (
        ('Informations générales', {
            'fields': ('eleve', 'matiere', 'titre', 'chapitre', 'type_saisie')
        }),
        ('Contenu original', {
            'fields': ('contenu_original', 'photo_cours')
        }),
        ('Contenu traité par IA', {
            'fields': ('contenu_traite', 'resume', 'fiche_revision', 'exemples'),
            'classes': ('collapse',)
        }),
        ('Statut et révisions', {
            'fields': ('statut', 'nombre_revisions', 'derniere_revision', 'favori', 'archive')
        }),
        ('Métadonnées', {
            'fields': ('date_ajout', 'date_modification'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['enonce_court', 'cours', 'type_question', 'difficulte', 'fois_posee', 'taux_reussite']
    list_filter = ['type_question', 'difficulte', 'date_creation']
    search_fields = ['enonce', 'cours__titre']

    def enonce_court(self, obj):
        return obj.enonce[:50] + "..." if len(obj.enonce) > 50 else obj.enonce

    enonce_court.short_description = 'Énoncé'


@admin.register(ReponseEleve)
class ReponseEleveAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'question_courte', 'est_correcte', 'date_reponse']
    list_filter = ['est_correcte', 'date_reponse']
    search_fields = ['eleve__username', 'question__enonce']

    def question_courte(self, obj):
        return obj.question.enonce[:40] + "..." if len(obj.question.enonce) > 40 else obj.question.enonce

    question_courte.short_description = 'Question'


@admin.register(ProgrammeScolaire)
class ProgrammeScolaireAdmin(admin.ModelAdmin):
    list_display = ['pays', 'classe', 'serie', 'matiere', 'titre', 'ordre', 'actif']
    list_filter = ['pays', 'niveau', 'classe', 'serie', 'matiere', 'actif']
    search_fields = ['titre', 'description']
    ordering = ['pays', 'classe', 'matiere', 'ordre']


@admin.register(CoursGenere)
class CoursGenereAdmin(admin.ModelAdmin):
    list_display = ['cours', 'programme', 'genere_automatiquement', 'date_generation']
    list_filter = ['genere_automatiquement', 'date_generation']
    search_fields = ['cours__titre', 'programme__titre']


@admin.register(Exercice)
class ExerciceAdmin(admin.ModelAdmin):
    list_display = ['titre', 'eleve', 'type_exercice', 'statut', 'utile', 'date_ajout']
    list_filter = ['statut', 'type_exercice', 'utile', 'date_ajout']
    search_fields = ['titre', 'enonce', 'eleve__username']
    readonly_fields = ['date_ajout', 'date_resolution']


@admin.register(ConversationIA)
class ConversationIAAdmin(admin.ModelAdmin):
    list_display = ['eleve', 'exercice', 'date_message']
    list_filter = ['date_message']
    search_fields = ['eleve__username', 'message_eleve']