# courses/homework_helper.py
import google.generativeai as genai
from django.conf import settings
from django.utils import timezone

genai.configure(api_key=settings.GEMINI_API_KEY)


def analyser_et_aider_exercice(exercice):
    """Analyse un exercice et fournit une aide pédagogique complète"""

    # Contexte de l'élève
    contexte = f"""
    Élève: {exercice.eleve.get_nom_complet()}
    Niveau: {exercice.eleve.get_niveau_display()} - {exercice.eleve.get_classe_display()}
    Série: {exercice.eleve.get_serie_display() if exercice.eleve.serie else 'Non spécifiée'}
    Matière: {exercice.matiere.nom if exercice.matiere else exercice.type_exercice}
    """

    # Construction du prompt
    prompt = f"""Tu es un professeur particulier bienveillant et pédagogue pour un élève d'Afrique de l'Ouest.

CONTEXTE DE L'ÉLÈVE:
{contexte}

EXERCICE À RÉSOUDRE:
Titre: {exercice.titre}
Énoncé:
{exercice.enonce}

TENTATIVE DE L'ÉLÈVE:
{exercice.tentative_eleve if exercice.tentative_eleve else "Aucune tentative pour le moment"}

MISSION:
Aide cet élève de manière pédagogique. Ne donne PAS directement la solution complète, mais guide-le étape par étape.

Structure ta réponse en 3 sections distinctes (sépare avec ###):

### SECTION 1: ANALYSE ET CONSEILS ###
- Analyse l'énoncé et identifie les concepts clés
- Si l'élève a fait une tentative, identifie ce qui est correct et ce qui peut être amélioré
- Donne des conseils sur la méthode à utiliser
- Rappelle les notions théoriques nécessaires

### SECTION 2: GUIDE ÉTAPE PAR ÉTAPE ###
- Décompose le problème en étapes simples
- Pour chaque étape, donne un indice sans révéler la réponse
- Pose des questions qui aident l'élève à réfléchir
- Utilise des exemples similaires plus simples si nécessaire

### SECTION 3: SOLUTION COMPLÈTE ###
- Donne la solution complète avec toutes les étapes détaillées
- Explique le raisonnement derrière chaque étape
- Ajoute des astuces pour des exercices similaires
- Propose un exercice similaire pour s'entraîner

Sois encourageant, pédagogique et adapté au niveau de l'élève !"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        response_text = response.text

        # Découpage en sections
        sections = response_text.split("### SECTION")

        explication = ""
        solution = ""
        conseils = ""

        for section in sections:
            if "1: ANALYSE ET CONSEILS" in section or "1:" in section:
                conseils = section.split("###")[1].strip() if "###" in section else section.strip()
            elif "2: GUIDE ÉTAPE PAR ÉTAPE" in section or "2:" in section:
                explication = section.split("###")[1].strip() if "###" in section else section.strip()
            elif "3: SOLUTION COMPLÈTE" in section or "3:" in section:
                solution = section.split("###")[1].strip() if "###" in section else section.strip()

        # Si pas de découpage, utiliser tout le texte
        if not explication:
            explication = response_text[:1500]
        if not solution:
            solution = response_text[1500:3000]
        if not conseils:
            conseils = "Continue à t'entraîner régulièrement !"

        # Mise à jour de l'exercice
        exercice.explication_ia = explication
        exercice.solution_complete = solution
        exercice.conseils = conseils
        exercice.statut = 'resolu'
        exercice.date_resolution = timezone.now()
        exercice.save()

        return True, "Aide générée avec succès !"

    except Exception as e:
        exercice.statut = 'en_attente'
        exercice.save()
        return False, f"Erreur: {str(e)}"


def continuer_conversation(exercice, message_eleve):
    """Continue la conversation avec l'IA pour approfondir l'aide"""

    from .models import ConversationIA

    # Récupérer l'historique des conversations
    conversations_precedentes = ConversationIA.objects.filter(exercice=exercice).order_by('date_message')

    historique = ""
    for conv in conversations_precedentes:
        historique += f"\nÉlève: {conv.message_eleve}\nIA: {conv.reponse_ia}\n"

    prompt = f"""Tu es un tuteur pédagogique qui aide un élève.

CONTEXTE:
Niveau: {exercice.eleve.get_classe_display()}
Matière: {exercice.matiere.nom if exercice.matiere else exercice.type_exercice}

EXERCICE INITIAL:
{exercice.enonce}

HISTORIQUE DE LA CONVERSATION:
{historique}

NOUVELLE QUESTION DE L'ÉLÈVE:
{message_eleve}

INSTRUCTIONS:
- Réponds de manière claire et pédagogique
- Adapte ton niveau de détail selon la question
- Encourage l'élève à réfléchir par lui-même
- Si l'élève est bloqué, donne plus d'indices
- Reste patient et bienveillant

Réponds directement à la question (maximum 300 mots):"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        reponse_ia = response.text

        # Sauvegarder la conversation
        ConversationIA.objects.create(
            eleve=exercice.eleve,
            exercice=exercice,
            message_eleve=message_eleve,
            reponse_ia=reponse_ia
        )

        return True, reponse_ia

    except Exception as e:
        return False, f"Erreur: {str(e)}"


def expliquer_concept_simple(concept, niveau, matiere):
    """Explique un concept de manière simple et claire"""

    prompt = f"""Tu es un professeur qui explique un concept à un élève de {niveau}.

CONCEPT À EXPLIQUER: {concept}
MATIÈRE: {matiere}

INSTRUCTIONS:
- Utilise un langage simple adapté au niveau {niveau}
- Donne 1-2 exemples concrets du quotidien (contexte africain)
- Évite le jargon technique
- Sois concis (150-200 mots maximum)

Commence directement par l'explication:"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Erreur: {str(e)}"


def verifier_reponse_eleve(question, reponse_eleve, reponse_correcte):
    """Vérifie la réponse d'un élève et donne un feedback"""

    prompt = f"""Tu es un correcteur bienveillant.

QUESTION:
{question}

RÉPONSE ATTENDUE:
{reponse_correcte}

RÉPONSE DE L'ÉLÈVE:
{reponse_eleve}

INSTRUCTIONS:
Analyse la réponse de l'élève et donne un feedback constructif.

Format de réponse:
✓ CORRECT / ✗ INCORRECT / ~ PARTIELLEMENT CORRECT

[Ton feedback en 2-3 phrases]
[Si incorrect, donne un indice sans révéler la réponse]"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Erreur: {str(e)}"


def generer_exercices_similaires(exercice_original, nombre=3):
    """Génère des exercices similaires pour s'entraîner"""

    prompt = f"""Tu es un créateur d'exercices pédagogiques.

EXERCICE ORIGINAL:
{exercice_original.enonce}

NIVEAU: {exercice_original.eleve.get_classe_display()}
MATIÈRE: {exercice_original.matiere.nom if exercice_original.matiere else exercice_original.type_exercice}

MISSION:
Crée {nombre} exercices SIMILAIRES mais avec des valeurs/contextes différents.

Format pour chaque exercice:
EXERCICE X
Énoncé: [l'énoncé complet]
Difficulté: [facile/moyen/difficile]
Solution brève: [la réponse en 1 ligne]
---

Les exercices doivent:
- Utiliser la même méthode de résolution
- Avoir des contextes variés et concrets
- Être progressifs en difficulté"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Erreur: {str(e)}"


def suggerer_ressources(sujet, niveau):
    """Suggère des ressources pour approfondir un sujet"""

    prompt = f"""Tu es un conseiller pédagogique.

SUJET: {sujet}
NIVEAU: {niveau}

Suggère 5 façons d'approfondir ce sujet:
1. [Conseil pratique #1]
2. [Conseil pratique #2]
3. [Conseil pratique #3]
4. [Conseil pratique #4]
5. [Conseil pratique #5]

Les conseils doivent être:
- Adaptés au contexte africain
- Accessibles (pas besoin de matériel coûteux)
- Pratiques et concrets
- Variés (lecture, pratique, vidéos, etc.)

Sois bref (10-15 mots par conseil):"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Erreur: {str(e)}"