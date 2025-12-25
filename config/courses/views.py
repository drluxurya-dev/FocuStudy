# courses/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cours, Matiere


@login_required
def liste_cours(request):
    """Liste des cours de l'élève"""
    cours = Cours.objects.filter(eleve=request.user).order_by('-date_ajout')
    return render(request, 'courses/liste.html', {'cours': cours})


@login_required
def ajouter_cours(request):
    """Ajouter un nouveau cours"""
    matieres = Matiere.objects.all()

    if request.method == 'POST':
        # Récupération des données
        titre = request.POST.get('titre')
        matiere_id = request.POST.get('matiere')
        chapitre = request.POST.get('chapitre', '')
        contenu_original = request.POST.get('contenu_original')
        type_saisie = request.POST.get('type_saisie', 'manuel')

        # Validation
        if not titre or not contenu_original:
            messages.error(request, "Le titre et le contenu sont obligatoires.")
            return render(request, 'courses/ajouter.html', {'matieres': matieres})

        # Création du cours
        cours = Cours.objects.create(
            eleve=request.user,
            matiere_id=matiere_id if matiere_id else None,
            titre=titre,
            chapitre=chapitre,
            contenu_original=contenu_original,
            type_saisie=type_saisie
        )

        # Gestion de la photo
        if 'photo_cours' in request.FILES:
            cours.photo_cours = request.FILES['photo_cours']
            cours.type_saisie = 'photo'
            cours.save()

        messages.success(request, f"Cours '{titre}' ajouté avec succès ! 🎉")
        return redirect('courses:detail', cours_id=cours.id)

    return render(request, 'courses/ajouter.html', {'matieres': matieres})


@login_required
def detail_cours(request, cours_id):
    """Détail d'un cours"""
    cours = get_object_or_404(Cours, id=cours_id, eleve=request.user)
    return render(request, 'courses/detail.html', {'cours': cours})


@login_required
def modifier_cours(request, cours_id):
    """Modifier un cours"""
    cours = get_object_or_404(Cours, id=cours_id, eleve=request.user)
    matieres = Matiere.objects.all()

    if request.method == 'POST':
        cours.titre = request.POST.get('titre')
        cours.matiere_id = request.POST.get('matiere')
        cours.chapitre = request.POST.get('chapitre', '')
        cours.contenu_original = request.POST.get('contenu_original')

        if 'photo_cours' in request.FILES:
            cours.photo_cours = request.FILES['photo_cours']

        cours.save()
        messages.success(request, "Cours modifié avec succès ! ✅")
        return redirect('courses:detail', cours_id=cours.id)

    return render(request, 'courses/modifier.html', {
        'cours': cours,
        'matieres': matieres
    })


@login_required
def supprimer_cours(request, cours_id):
    """Supprimer un cours"""
    cours = get_object_or_404(Cours, id=cours_id, eleve=request.user)

    if request.method == 'POST':
        titre = cours.titre
        cours.delete()
        messages.success(request, f"Cours '{titre}' supprimé avec succès.")
        return redirect('courses:liste')

    return render(request, 'courses/supprimer.html', {'cours': cours})


@login_required
def bibliotheque_cours(request):
    """Bibliothèque de cours générés automatiquement"""
    from .models import ProgrammeScolaire, Matiere
    from .auto_generate_service import initialiser_programme_pour_eleve

    # Vérifier si le profil est complet
    if not request.user.profil_complete:
        messages.warning(request, "Complète ton profil pour accéder aux cours automatiques.")
        return redirect('accounts:complete_profil')

    # Initialiser le programme si nécessaire
    programmes = ProgrammeScolaire.objects.filter(
        pays=request.user.pays,
        niveau=request.user.niveau,
        classe=request.user.classe,
        actif=True
    )

    if not programmes.exists():
        success, message = initialiser_programme_pour_eleve(request.user)
        messages.info(request, message)
        programmes = ProgrammeScolaire.objects.filter(
            pays=request.user.pays,
            niveau=request.user.niveau,
            classe=request.user.classe,
            actif=True
        )

    # Filtrer par série si lycée
    if request.user.niveau == 'lycee' and request.user.serie:
        from django.db.models import Q
        programmes = programmes.filter(Q(serie=request.user.serie) | Q(serie=''))

    # Grouper par matière
    matieres = Matiere.objects.filter(programmes__in=programmes).distinct()

    # Compter les cours générés par matière
    matieres_data = []
    for matiere in matieres:
        progs = programmes.filter(matiere=matiere)
        cours_generes = Cours.objects.filter(
            eleve=request.user,
            matiere=matiere
        ).count()

        matieres_data.append({
            'matiere': matiere,
            'total_chapitres': progs.count(),
            'cours_generes': cours_generes,
            'programmes': progs
        })

    return render(request, 'courses/bibliotheque.html', {
        'matieres_data': matieres_data
    })


@login_required
def generer_cours_auto(request, programme_id):
    """Générer un cours automatiquement"""
    from .models import ProgrammeScolaire
    from .auto_generate_service import generer_cours_automatiquement

    programme = get_object_or_404(ProgrammeScolaire, id=programme_id)

    # Vérifier que le programme correspond au profil de l'élève
    if (programme.pays != request.user.pays or
            programme.classe != request.user.classe):
        messages.error(request, "Ce programme ne correspond pas à ton profil.")
        return redirect('courses:bibliotheque')

    cours, created = generer_cours_automatiquement(request.user, programme)

    if created:
        messages.success(request, f"✨ Cours '{cours.titre}' généré avec succès !")
    else:
        messages.info(request, "Ce cours existe déjà dans ta liste.")

    return redirect('courses:detail', cours_id=cours.id)


@login_required
def generer_tous_cours(request):
    """Générer tous les cours du programme"""
    from .auto_generate_service import generer_tous_les_cours_pour_eleve

    if request.method == 'POST':
        nombre, message = generer_tous_les_cours_pour_eleve(request.user)

        if nombre > 0:
            messages.success(request, message)
        else:
            messages.warning(request, message)

        return redirect('courses:liste')

    return render(request, 'courses/generer_tous.html')


@login_required
def generer_cours_par_matiere(request, matiere_id):
    """Générer tous les cours d'une matière"""
    from .models import Matiere
    from .auto_generate_service import generer_cours_matiere

    matiere = get_object_or_404(Matiere, id=matiere_id)

    if request.method == 'POST':
        nombre = generer_cours_matiere(request.user, matiere_id)

        if nombre > 0:
            messages.success(request, f"✨ {nombre} cours de {matiere.nom} générés !")
        else:
            messages.info(request, "Tous les cours de cette matière sont déjà générés.")

        return redirect('courses:bibliotheque')

    return redirect('courses:bibliotheque')


# ===== AIDE AUX DEVOIRS =====

@login_required
def aide_devoirs(request):
    """Liste des exercices de l'élève"""
    from .models import Exercice

    exercices = Exercice.objects.filter(eleve=request.user).order_by('-date_ajout')

    stats = {
        'total': exercices.count(),
        'resolus': exercices.filter(statut='resolu').count(),
        'en_attente': exercices.filter(statut='en_attente').count(),
    }

    return render(request, 'courses/aide_devoirs.html', {
        'exercices': exercices,
        'stats': stats
    })


@login_required
def ajouter_exercice(request):
    """Ajouter un exercice pour obtenir de l'aide"""
    from .models import Exercice, Matiere
    from .homework_helper import analyser_et_aider_exercice

    matieres = Matiere.objects.all()

    if request.method == 'POST':
        titre = request.POST.get('titre')
        type_exercice = request.POST.get('type_exercice', 'autres')
        matiere_id = request.POST.get('matiere')
        enonce = request.POST.get('enonce')
        tentative_eleve = request.POST.get('tentative_eleve', '')

        if not titre or not enonce:
            messages.error(request, "Le titre et l'énoncé sont obligatoires.")
            return render(request, 'courses/ajouter_exercice.html', {'matieres': matieres})

        # Créer l'exercice
        exercice = Exercice.objects.create(
            eleve=request.user,
            titre=titre,
            type_exercice=type_exercice,
            matiere_id=matiere_id if matiere_id else None,
            enonce=enonce,
            tentative_eleve=tentative_eleve,
            statut='en_cours'
        )

        # Gestion de la photo
        if 'photo_exercice' in request.FILES:
            exercice.photo_exercice = request.FILES['photo_exercice']
            exercice.save()

        # Analyser avec l'IA
        success, message = analyser_et_aider_exercice(exercice)

        if success:
            messages.success(request, f"✨ Aide générée pour '{titre}' !")
        else:
            messages.warning(request, f"Exercice ajouté mais erreur IA: {message}")

        return redirect('courses:detail_exercice', exercice_id=exercice.id)

    return render(request, 'courses/ajouter_exercice.html', {'matieres': matieres})


@login_required
def detail_exercice(request, exercice_id):
    """Détail d'un exercice avec l'aide de l'IA"""
    from .models import Exercice, ConversationIA
    from .homework_helper import continuer_conversation

    exercice = get_object_or_404(Exercice, id=exercice_id, eleve=request.user)
    conversations = ConversationIA.objects.filter(exercice=exercice).order_by('date_message')

    # Poser une question de suivi
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            success, reponse = continuer_conversation(exercice, message)
            if success:
                messages.success(request, "Réponse ajoutée !")
            else:
                messages.error(request, reponse)
            return redirect('courses:detail_exercice', exercice_id=exercice.id)

    return render(request, 'courses/detail_exercice.html', {
        'exercice': exercice,
        'conversations': conversations
    })


@login_required
def marquer_exercice_utile(request, exercice_id):
    """Marquer un exercice comme utile"""
    from .models import Exercice

    exercice = get_object_or_404(Exercice, id=exercice_id, eleve=request.user)
    exercice.utile = not exercice.utile
    exercice.save()

    return redirect('courses:detail_exercice', exercice_id=exercice.id)


@login_required
def supprimer_exercice(request, exercice_id):
    """Supprimer un exercice"""
    from .models import Exercice

    exercice = get_object_or_404(Exercice, id=exercice_id, eleve=request.user)

    if request.method == 'POST':
        exercice.delete()
        messages.success(request, "Exercice supprimé.")
        return redirect('courses:aide_devoirs')

    return render(request, 'courses/supprimer_exercice.html', {'exercice': exercice})