# courses/urls.py
from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.liste_cours, name='liste'),
    path('ajouter/', views.ajouter_cours, name='ajouter'),
    path('<int:cours_id>/', views.detail_cours, name='detail'),
    path('<int:cours_id>/modifier/', views.modifier_cours, name='modifier'),
    path('<int:cours_id>/supprimer/', views.supprimer_cours, name='supprimer'),

    # Génération automatique
    path('bibliotheque/', views.bibliotheque_cours, name='bibliotheque'),
    path('generer/<int:programme_id>/', views.generer_cours_auto, name='generer_auto'),
    path('generer-tous/', views.generer_tous_cours, name='generer_tous'),
    path('generer-matiere/<int:matiere_id>/', views.generer_cours_par_matiere, name='generer_matiere'),

    # Aide aux devoirs
    path('aide/', views.aide_devoirs, name='aide_devoirs'),
    path('aide/ajouter/', views.ajouter_exercice, name='ajouter_exercice'),
    path('aide/<int:exercice_id>/', views.detail_exercice, name='detail_exercice'),
    path('aide/<int:exercice_id>/utile/', views.marquer_exercice_utile, name='marquer_utile'),
    path('aide/<int:exercice_id>/supprimer/', views.supprimer_exercice, name='supprimer_exercice'),
]