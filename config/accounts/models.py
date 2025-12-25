# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Modèle utilisateur personnalisé pour FocusStudy"""

    NIVEAU_CHOICES = [
        ('college', 'Collège'),
        ('lycee', 'Lycée'),
    ]

    CLASSE_CHOICES = [
        # Collège
        ('6eme', '6ème'),
        ('5eme', '5ème'),
        ('4eme', '4ème'),
        ('3eme', '3ème'),
        # Lycée
        ('seconde', 'Seconde'),
        ('premiere', 'Première'),
        ('terminale', 'Terminale'),
    ]

    SERIE_CHOICES = [
        ('A', 'Série A (Littéraire)'),
        ('C', 'Série C (Scientifique)'),
        ('D', 'Série D (Sciences expérimentales)'),
        ('E', 'Série E (Mathématiques et Techniques)'),
        ('G', 'Série G (Techniques administratives)'),
        ('F', 'Série F (Techniques industrielles)'),
    ]

    PAYS_CHOICES = [
        ('TG', 'Togo'),
        ('BJ', 'Bénin'),
        ('SN', 'Sénégal'),
        ('CI', 'Côte d\'Ivoire'),
        ('BF', 'Burkina Faso'),
        ('ML', 'Mali'),
        ('NE', 'Niger'),
        ('GN', 'Guinée'),
    ]

    # Champs du profil élève
    niveau = models.CharField(max_length=10, choices=NIVEAU_CHOICES, blank=True)
    classe = models.CharField(max_length=20, choices=CLASSE_CHOICES, blank=True)
    serie = models.CharField(max_length=10, choices=SERIE_CHOICES, blank=True, help_text="Pour le lycée uniquement")
    pays = models.CharField(max_length=2, choices=PAYS_CHOICES, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    photo_profil = models.ImageField(upload_to='profils/', blank=True, null=True)

    # Métadonnées
    date_inscription = models.DateTimeField(auto_now_add=True)
    profil_complete = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.get_full_name() or self.username} - {self.get_classe_display()}"

    def get_nom_complet(self):
        """Retourne le nom complet de l'élève"""
        return f"{self.first_name} {self.last_name}".strip() or self.username