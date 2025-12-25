# courses/models.py
from django.db import models
from django.conf import settings


class Matiere(models.Model):
    """Matières scolaires disponibles"""

    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icone = models.CharField(max_length=50, blank=True, help_text="Nom de l'icône (ex: 📚, 🧮, 🔬)")

    class Meta:
        verbose_name = 'Matière'
        verbose_name_plural = 'Matières'
        ordering = ['nom']

    def __str__(self):
        return f"{self.icone} {self.nom}" if self.icone else self.nom


class Cours(models.Model):
    """Cours ajouté par l'élève"""

    TYPE_SAISIE_CHOICES = [
        ('manuel', 'Saisie manuelle'),
        ('photo', 'Photo du cahier'),
        ('copie', 'Copier-coller'),
    ]

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('en_traitement', 'En traitement'),
        ('traite', 'Traité'),
        ('erreur', 'Erreur'),
    ]

    # Relations
    eleve = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cours'
    )
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cours'
    )

    # Informations du cours
    titre = models.CharField(max_length=200)
    chapitre = models.CharField(max_length=200, blank=True)
    contenu_original = models.TextField(help_text="Contenu brut saisi par l'élève")

    # Type de saisie
    type_saisie = models.CharField(max_length=20, choices=TYPE_SAISIE_CHOICES)
    photo_cours = models.ImageField(upload_to='cours_photos/', blank=True, null=True)

    # Contenu traité par l'IA
    contenu_traite = models.TextField(blank=True, help_text="Cours réorganisé par l'IA")
    resume = models.TextField(blank=True, help_text="Résumé généré par l'IA")
    fiche_revision = models.TextField(blank=True, help_text="Fiche de révision")
    exemples = models.TextField(blank=True, help_text="Exemples et exercices")

    # Statut et métadonnées
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    date_ajout = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    nombre_revisions = models.IntegerField(default=0)
    derniere_revision = models.DateTimeField(null=True, blank=True)

    # Paramètres d'affichage
    favori = models.BooleanField(default=False)
    archive = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Cours'
        verbose_name_plural = 'Cours'
        ordering = ['-date_ajout']

    def __str__(self):
        return f"{self.titre} - {self.matiere} ({self.eleve.get_nom_complet()})"

    def marquer_comme_revise(self):
        """Marque le cours comme révisé"""
        from django.utils import timezone
        self.nombre_revisions += 1
        self.derniere_revision = timezone.now()
        self.save()


class Question(models.Model):
    """Questions de révision générées par l'IA"""

    TYPE_CHOICES = [
        ('qcm', 'QCM'),
        ('vrai_faux', 'Vrai/Faux'),
        ('ouverte', 'Question ouverte'),
        ('exercice', 'Exercice'),
    ]

    DIFFICULTE_CHOICES = [
        ('facile', 'Facile'),
        ('moyen', 'Moyen'),
        ('difficile', 'Difficile'),
    ]

    # Relations
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='questions')

    # Contenu de la question
    type_question = models.CharField(max_length=20, choices=TYPE_CHOICES)
    difficulte = models.CharField(max_length=20, choices=DIFFICULTE_CHOICES, default='moyen')
    enonce = models.TextField()

    # Options pour QCM
    option_a = models.CharField(max_length=500, blank=True)
    option_b = models.CharField(max_length=500, blank=True)
    option_c = models.CharField(max_length=500, blank=True)
    option_d = models.CharField(max_length=500, blank=True)

    # Réponses
    reponse_correcte = models.TextField()
    explication = models.TextField(blank=True, help_text="Explication de la réponse")

    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    fois_posee = models.IntegerField(default=0)
    fois_reussie = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['difficulte', '-date_creation']

    def __str__(self):
        return f"{self.get_type_question_display()} - {self.enonce[:50]}..."

    def taux_reussite(self):
        """Calcule le taux de réussite de la question"""
        if self.fois_posee == 0:
            return 0
        return round((self.fois_reussie / self.fois_posee) * 100, 1)


class ReponseEleve(models.Model):
    """Réponses données par l'élève aux questions"""

    # Relations
    eleve = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reponses'
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='reponses_eleves')

    # Réponse
    reponse_donnee = models.TextField()
    est_correcte = models.BooleanField()
    temps_reponse = models.IntegerField(help_text="Temps en secondes", null=True, blank=True)

    # Métadonnées
    date_reponse = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Réponse élève'
        verbose_name_plural = 'Réponses élèves'
        ordering = ['-date_reponse']

    def __str__(self):
        statut = "✅" if self.est_correcte else "❌"
        return f"{statut} {self.eleve.username} - {self.question.enonce[:30]}..."


class ProgrammeScolaire(models.Model):
    """Programme scolaire par pays, niveau, classe et matière"""

    pays = models.CharField(max_length=2)
    niveau = models.CharField(max_length=10)  # college, lycee
    classe = models.CharField(max_length=20)  # 6eme, 5eme, etc.
    serie = models.CharField(max_length=10, blank=True)  # A, C, D, etc.
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='programmes')

    # Contenu du programme
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    ordre = models.IntegerField(default=0, help_text="Ordre dans l'année scolaire")

    # Métadonnées
    date_ajout = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Programme scolaire'
        verbose_name_plural = 'Programmes scolaires'
        ordering = ['pays', 'classe', 'matiere', 'ordre']
        unique_together = ['pays', 'classe', 'serie', 'matiere', 'titre']

    def __str__(self):
        serie_str = f" - {self.serie}" if self.serie else ""
        return f"{self.pays} | {self.classe}{serie_str} | {self.matiere.nom} | {self.titre}"


class CoursGenere(models.Model):
    """Cours générés automatiquement par l'IA"""

    programme = models.ForeignKey(ProgrammeScolaire, on_delete=models.CASCADE, related_name='cours_generes')
    cours = models.OneToOneField(Cours, on_delete=models.CASCADE, related_name='cours_genere')

    genere_automatiquement = models.BooleanField(default=True)
    date_generation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cours généré'
        verbose_name_plural = 'Cours générés'

    def __str__(self):
        return f"Cours auto: {self.cours.titre}"


class Exercice(models.Model):
    """Exercices ajoutés par l'élève pour obtenir de l'aide"""

    TYPE_CHOICES = [
        ('maths', 'Mathématiques'),
        ('physique', 'Physique-Chimie'),
        ('francais', 'Français'),
        ('autres', 'Autres'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours de traitement'),
        ('resolu', 'Résolu'),
    ]

    # Relations
    eleve = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exercices'
    )
    matiere = models.ForeignKey(Matiere, on_delete=models.SET_NULL, null=True, blank=True, related_name='exercices')

    # Contenu
    titre = models.CharField(max_length=200)
    type_exercice = models.CharField(max_length=20, choices=TYPE_CHOICES, default='autres')
    enonce = models.TextField(help_text="L'énoncé de l'exercice")
    photo_exercice = models.ImageField(upload_to='exercices/', blank=True, null=True, help_text="Photo de l'exercice")

    # Tentative de l'élève
    tentative_eleve = models.TextField(blank=True, help_text="Ta tentative de résolution")

    # Réponse de l'IA
    explication_ia = models.TextField(blank=True, help_text="Explication détaillée par l'IA")
    solution_complete = models.TextField(blank=True, help_text="Solution complète")
    conseils = models.TextField(blank=True, help_text="Conseils pour progresser")

    # Métadonnées
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_ajout = models.DateTimeField(auto_now_add=True)
    date_resolution = models.DateTimeField(null=True, blank=True)
    utile = models.BooleanField(default=False, help_text="L'élève a trouvé l'aide utile")

    class Meta:
        verbose_name = 'Exercice'
        verbose_name_plural = 'Exercices'
        ordering = ['-date_ajout']

    def __str__(self):
        return f"{self.titre} - {self.eleve.username}"


class ConversationIA(models.Model):
    """Conversations avec l'assistant IA"""

    eleve = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    exercice = models.ForeignKey(Exercice, on_delete=models.CASCADE, related_name='conversations', null=True,
                                 blank=True)

    # Messages
    message_eleve = models.TextField()
    reponse_ia = models.TextField()

    # Métadonnées
    date_message = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Conversation IA'
        verbose_name_plural = 'Conversations IA'
        ordering = ['date_message']

    def __str__(self):
        return f"{self.eleve.username} - {self.date_message.strftime('%d/%m/%Y %H:%M')}"