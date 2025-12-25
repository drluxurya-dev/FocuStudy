# courses/ai_service.py
import google.generativeai as genai
from django.conf import settings

# Configuration de Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


def traiter_cours_avec_ia(cours):
    """Traite un cours avec Gemini pour générer du contenu pédagogique"""

    # Informations contextuelles sur l'élève
    eleve_info = f"""
    Niveau: {cours.eleve.get_niveau_display()}
    Classe: {cours.eleve.get_classe_display()}
    Série: {cours.eleve.get_serie_display() if cours.eleve.serie else 'Non spécifiée'}
    Pays: {cours.eleve.get_pays_display()}
    Matière: {cours.matiere.nom if cours.matiere else 'Non spécifiée'}
    """

    # Prompt pour l'IA
    prompt = f"""Tu es un assistant pédagogique expert pour les élèves d'Afrique de l'Ouest. 

CONTEXTE DE L'ÉLÈVE:
{eleve_info}

COURS À TRAITER:
Titre: {cours.titre}
Chapitre: {cours.chapitre or 'Non spécifié'}

CONTENU ORIGINAL DU COURS:
{cours.contenu_original}

INSTRUCTIONS:
Adapte ton langage et tes exemples au niveau de l'élève et au programme scolaire de son pays.

Génère 4 sections distinctes (sépare-les avec "### SECTION X ###"):

### SECTION 1: COURS RÉORGANISÉ ###
- Restructure le cours de manière claire et pédagogique
- Utilise des titres, sous-titres et paragraphes bien organisés
- Explique les concepts difficiles simplement
- Ajoute des exemples concrets adaptés au contexte africain

### SECTION 2: RÉSUMÉ ###
- Crée un résumé concis (200-300 mots max)
- Mets en avant les points essentiels à retenir
- Utilise des puces pour les concepts clés

### SECTION 3: FICHE DE RÉVISION ###
- Format type fiche bristol
- Définitions claires des termes importants
- Formules ou règles à mémoriser
- Astuces mnémotechniques si pertinent
- Schémas ou tableaux si utile (en texte ASCII simple)

### SECTION 4: EXEMPLES ET EXERCICES ###
- 3-5 exemples d'application pratiques
- 2-3 exercices avec leurs corrections détaillées
- Exercices adaptés au niveau et type d'examen du pays

Sois clair, pédagogique et adapté au niveau de l'élève !"""

    try:
        # Utilisation du modèle Gemini Pro
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Génération du contenu
        response = model.generate_content(prompt)
        response_text = response.text

        # Découpage en sections
        sections = response_text.split("### SECTION")

        cours_traite = ""
        resume = ""
        fiche_revision = ""
        exemples = ""

        for section in sections:
            if "1: COURS RÉORGANISÉ" in section or "1:" in section:
                cours_traite = section.split("###")[1].strip() if "###" in section else section.strip()
            elif "2: RÉSUMÉ" in section or "2:" in section:
                resume = section.split("###")[1].strip() if "###" in section else section.strip()
            elif "3: FICHE DE RÉVISION" in section or "3:" in section:
                fiche_revision = section.split("###")[1].strip() if "###" in section else section.strip()
            elif "4: EXEMPLES ET EXERCICES" in section or "4:" in section:
                exemples = section.split("###")[1].strip() if "###" in section else section.strip()

        # Si les sections ne sont pas bien séparées, utiliser tout le contenu
        if not cours_traite:
            cours_traite = response_text[:2000]
        if not resume:
            resume = response_text[:1000]
        if not fiche_revision:
            fiche_revision = "Fiche de révision en cours de génération..."
        if not exemples:
            exemples = "Exemples et exercices en cours de génération..."

        # Mise à jour du cours
        cours.contenu_traite = cours_traite
        cours.resume = resume
        cours.fiche_revision = fiche_revision
        cours.exemples = exemples
        cours.statut = 'traite'
        cours.save()

        return True, "Cours traité avec succès par l'IA !"

    except Exception as e:
        cours.statut = 'erreur'
        cours.save()
        return False, f"Erreur lors du traitement: {str(e)}"


def generer_questions_quiz(cours, nombre_questions=5):
    """Génère des questions de quiz à partir d'un cours avec Gemini"""

    prompt = f"""Tu es un créateur de quiz pédagogique.

CONTEXTE:
Niveau: {cours.eleve.get_classe_display()}
Matière: {cours.matiere.nom if cours.matiere else 'Non spécifiée'}

COURS:
{cours.contenu_traite or cours.contenu_original}

INSTRUCTION:
Génère {nombre_questions} questions de type QCM avec 4 options (A, B, C, D).

Format STRICT pour chaque question:
QUESTION X
Type: QCM
Difficulté: [facile/moyen/difficile]
Énoncé: [la question]
A) [option A]
B) [option B]
C) [option C]
D) [option D]
Réponse correcte: [A/B/C/D]
Explication: [pourquoi cette réponse]
---

Génère des questions variées (définitions, applications, compréhension)."""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        response_text = response.text

        questions_texte = response_text.split("QUESTION ")

        from .models import Question
        questions_creees = []

        for q_text in questions_texte[1:]:  # Skip le premier split vide
            try:
                lines = [l.strip() for l in q_text.split('\n') if l.strip()]

                difficulte = 'moyen'
                enonce = ""
                options = {'A': '', 'B': '', 'C': '', 'D': ''}
                reponse = ''
                explication = ''

                for line in lines:
                    if line.startswith('Difficulté:'):
                        diff = line.split(':')[1].strip().lower()
                        if diff in ['facile', 'moyen', 'difficile']:
                            difficulte = diff
                    elif line.startswith('Énoncé:'):
                        enonce = line.split(':', 1)[1].strip()
                    elif line.startswith('A)'):
                        options['A'] = line[2:].strip()
                    elif line.startswith('B)'):
                        options['B'] = line[2:].strip()
                    elif line.startswith('C)'):
                        options['C'] = line[2:].strip()
                    elif line.startswith('D)'):
                        options['D'] = line[2:].strip()
                    elif line.startswith('Réponse correcte:'):
                        reponse = line.split(':')[1].strip()[0]
                    elif line.startswith('Explication:'):
                        explication = line.split(':', 1)[1].strip()

                if enonce and reponse in options:
                    question = Question.objects.create(
                        cours=cours,
                        type_question='qcm',
                        difficulte=difficulte,
                        enonce=enonce,
                        option_a=options['A'],
                        option_b=options['B'],
                        option_c=options['C'],
                        option_d=options['D'],
                        reponse_correcte=reponse,
                        explication=explication
                    )
                    questions_creees.append(question)

            except Exception as e:
                print(f"Erreur parsing question: {e}")
                continue

        return True, f"{len(questions_creees)} questions créées avec succès !"

    except Exception as e:
        return False, f"Erreur lors de la génération: {str(e)}"


def expliquer_concept(concept, niveau, matiere):
    """Explique un concept spécifique de manière adaptée au niveau de l'élève"""

    prompt = f"""Tu es un professeur pédagogue pour un élève de {niveau} en {matiere}.

Explique simplement et clairement le concept suivant : "{concept}"

Instructions:
- Utilise un langage adapté au niveau {niveau}
- Donne des exemples concrets et contextualisés (Afrique de l'Ouest)
- Reste concis (150-200 mots maximum)
- Utilise des analogies si nécessaire

Commence directement par l'explication sans introduction."""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Erreur: {str(e)}"


def corriger_exercice(exercice, reponse_eleve, niveau):
    """Corrige un exercice et donne un feedback personnalisé"""

    prompt = f"""Tu es un professeur bienveillant qui corrige l'exercice d'un élève de {niveau}.

EXERCICE:
{exercice}

RÉPONSE DE L'ÉLÈVE:
{reponse_eleve}

Instructions:
- Indique si la réponse est correcte ou non
- Explique où sont les erreurs si nécessaire
- Donne la solution correcte avec les étapes détaillées
- Encourage l'élève de manière positive
- Reste concis et pédagogique

Format de réponse:
✓ ou ✗ [Correct / Incorrect]

[Ton feedback et explication]"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Erreur: {str(e)}"