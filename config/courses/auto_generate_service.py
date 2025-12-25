# courses/auto_generate_service.py
import google.generativeai as genai
from django.conf import settings
from .models import ProgrammeScolaire, Cours, CoursGenere, Matiere
from .ai_service import traiter_cours_avec_ia, generer_questions_quiz

genai.configure(api_key=settings.GEMINI_API_KEY)


def recuperer_programme_scolaire(pays, niveau, classe, serie=None):
    """Récupère le programme scolaire via l'IA Gemini"""

    serie_info = f" en série {serie}" if serie else ""

    prompt = f"""Tu es un expert des programmes scolaires d'Afrique de l'Ouest.

CONTEXTE:
- Pays: {pays}
- Niveau: {niveau}
- Classe: {classe}{serie_info}

MISSION:
Liste TOUS les chapitres/thèmes du programme scolaire officiel pour CHAQUE MATIÈRE étudiée dans cette classe.

Format STRICT (un thème par ligne):
MATIERE: [Nom de la matière]
1. [Titre du chapitre/thème 1]
2. [Titre du chapitre/thème 2]
3. [Titre du chapitre/thème 3]
...

MATIERE: [Nom de la matière suivante]
1. [Titre du chapitre/thème 1]
...

Inclus toutes les matières principales (Mathématiques, Français, Sciences, Histoire-Géo, etc.)
Sois précis et complet. Base-toi sur les programmes officiels du pays."""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        return f"Erreur: {str(e)}"


def parser_et_sauvegarder_programme(texte_programme, pays, niveau, classe, serie=None):
    """Parse le texte du programme et le sauvegarde en base de données"""

    lignes = texte_programme.split('\n')
    matiere_actuelle = None
    ordre = 0
    programmes_crees = []

    for ligne in lignes:
        ligne = ligne.strip()

        if ligne.startswith('MATIERE:') or ligne.startswith('MATIÈRE:'):
            # Nouvelle matière
            nom_matiere = ligne.split(':', 1)[1].strip()

            # Chercher ou créer la matière
            matiere_actuelle, created = Matiere.objects.get_or_create(
                nom=nom_matiere,
                defaults={'description': f'Matière: {nom_matiere}'}
            )
            ordre = 0

        elif ligne and matiere_actuelle and (ligne[0].isdigit() or ligne.startswith('-')):
            # C'est un chapitre/thème
            # Nettoyer le titre (enlever le numéro)
            titre = ligne.split('.', 1)[1].strip() if '.' in ligne else ligne.lstrip('- ')

            if titre:
                # Créer ou mettre à jour le programme
                programme, created = ProgrammeScolaire.objects.get_or_create(
                    pays=pays,
                    niveau=niveau,
                    classe=classe,
                    serie=serie or '',
                    matiere=matiere_actuelle,
                    titre=titre,
                    defaults={
                        'ordre': ordre,
                        'actif': True
                    }
                )

                programmes_crees.append(programme)
                ordre += 1

    return programmes_crees


def generer_cours_automatiquement(eleve, programme, force=False):
    """Génère automatiquement un cours basé sur un programme scolaire"""

    # Vérifier si le cours existe déjà
    cours_existant = Cours.objects.filter(
        eleve=eleve,
        titre__icontains=programme.titre,
        matiere=programme.matiere
    ).first()

    if cours_existant and not force:
        return cours_existant, False  # Déjà existant

    # Prompt pour générer le cours complet
    serie_info = f" en série {eleve.get_serie_display()}" if eleve.serie else ""

    prompt = f"""Tu es un professeur expert qui crée des cours complets pour les élèves.

CONTEXTE:
- Pays: {eleve.get_pays_display()}
- Niveau: {eleve.get_niveau_display()}
- Classe: {eleve.get_classe_display()}{serie_info}
- Matière: {programme.matiere.nom}
- Chapitre: {programme.titre}

MISSION:
Crée un cours COMPLET et DÉTAILLÉ sur ce chapitre, adapté au niveau de l'élève.

Le cours doit contenir:
1. Introduction (pourquoi ce chapitre est important)
2. Objectifs d'apprentissage (3-5 points)
3. Développement du cours (bien structuré avec titres et sous-titres)
   - Définitions claires
   - Explications détaillées
   - Exemples concrets adaptés au contexte africain
   - Schémas explicatifs en texte si nécessaire
4. Applications pratiques
5. Points clés à retenir

Le cours doit être:
- Complet (1500-2000 mots)
- Pédagogique et progressif
- Adapté au programme officiel du {eleve.get_pays_display()}
- Avec des exemples du quotidien en Afrique de l'Ouest

Commence directement par le cours sans introduction méta."""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        contenu = response.text

        # Créer le cours
        cours = Cours.objects.create(
            eleve=eleve,
            matiere=programme.matiere,
            titre=programme.titre,
            chapitre=f"Chapitre {programme.ordre + 1}",
            contenu_original=contenu,
            type_saisie='manuel',
            statut='en_traitement'
        )

        # Créer le lien avec le programme
        CoursGenere.objects.create(
            programme=programme,
            cours=cours,
            genere_automatiquement=True
        )

        # Traiter le cours avec l'IA
        traiter_cours_avec_ia(cours)

        # Générer des questions
        generer_questions_quiz(cours, nombre_questions=5)

        return cours, True  # Nouveau cours créé

    except Exception as e:
        print(f"Erreur génération cours: {e}")
        return None, False


def generer_tous_les_cours_pour_eleve(eleve):
    """Génère tous les cours du programme pour un élève"""

    if not eleve.niveau or not eleve.classe or not eleve.pays:
        return 0, "Profil incomplet. Complète ton niveau, classe et pays."

    # Récupérer les programmes correspondants
    programmes = ProgrammeScolaire.objects.filter(
        pays=eleve.pays,
        niveau=eleve.niveau,
        classe=eleve.classe,
        actif=True
    )

    # Si lycée avec série, filtrer par série
    if eleve.niveau == 'lycee' and eleve.serie:
        programmes = programmes.filter(
            models.Q(serie=eleve.serie) | models.Q(serie='')
        )

    if not programmes.exists():
        # Aucun programme trouvé, générer depuis l'IA
        texte_programme = recuperer_programme_scolaire(
            eleve.get_pays_display(),
            eleve.get_niveau_display(),
            eleve.get_classe_display(),
            eleve.get_serie_display() if eleve.serie else None
        )

        programmes = parser_et_sauvegarder_programme(
            texte_programme,
            eleve.pays,
            eleve.niveau,
            eleve.classe,
            eleve.serie
        )

    # Générer les cours
    cours_generes = 0

    for programme in programmes:
        cours, created = generer_cours_automatiquement(eleve, programme)
        if created:
            cours_generes += 1

    return cours_generes, f"{cours_generes} cours générés avec succès !"


def initialiser_programme_pour_eleve(eleve):
    """Initialise le programme scolaire pour un élève après inscription"""

    if not eleve.profil_complete:
        return False, "Profil incomplet"

    # Récupérer ou générer le programme
    texte_programme = recuperer_programme_scolaire(
        eleve.get_pays_display(),
        eleve.get_niveau_display(),
        eleve.get_classe_display(),
        eleve.get_serie_display() if eleve.serie else None
    )

    # Parser et sauvegarder
    programmes = parser_et_sauvegarder_programme(
        texte_programme,
        eleve.pays,
        eleve.niveau,
        eleve.classe,
        eleve.serie
    )

    return True, f"{len(programmes)} chapitres détectés dans le programme"


def generer_cours_matiere(eleve, matiere_id):
    """Génère tous les cours d'une matière spécifique"""

    programmes = ProgrammeScolaire.objects.filter(
        pays=eleve.pays,
        niveau=eleve.niveau,
        classe=eleve.classe,
        matiere_id=matiere_id,
        actif=True
    )

    if eleve.niveau == 'lycee' and eleve.serie:
        from django.db.models import Q
        programmes = programmes.filter(Q(serie=eleve.serie) | Q(serie=''))

    cours_generes = 0

    for programme in programmes:
        cours, created = generer_cours_automatiquement(eleve, programme)
        if created:
            cours_generes += 1

    return cours_generes