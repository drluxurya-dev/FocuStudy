# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('inscription/', views.signup, name='signup'),
    path('connexion/', views.user_login, name='login'),
    path('deconnexion/', views.user_logout, name='logout'),
    path('profil/', views.profil, name='profil'),
    path('profil/completer/', views.complete_profil, name='complete_profil'),
    path('profil/modifier/', views.modifier_profil, name='modifier_profil'),
]