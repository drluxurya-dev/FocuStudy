# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Configuration de l'interface admin pour les utilisateurs"""

    list_display = ['username', 'email', 'get_nom_complet', 'niveau', 'classe', 'pays', 'profil_complete']
    list_filter = ['niveau', 'classe', 'pays', 'profil_complete', 'date_inscription']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    fieldsets = UserAdmin.fieldsets + (
        ('Informations scolaires', {
            'fields': ('niveau', 'classe', 'pays')
        }),
        ('Informations personnelles supplémentaires', {
            'fields': ('telephone', 'date_naissance', 'photo_profil', 'profil_complete')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations scolaires', {
            'fields': ('niveau', 'classe', 'pays')
        }),
    )
