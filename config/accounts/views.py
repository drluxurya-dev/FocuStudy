# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from .models import User
from courses.models import Cours, ReponseEleve


def home(request):
    """Page d'accueil"""
    stats = {}

    if request.user.is_authenticated:
        # Statistiques de l'utilisateur
        stats = {
            'total_cours': Cours.objects.filter(eleve=request.user).count(),
            'total_revisions': Cours.objects.filter(eleve=request.user).aggregate(
                total=Count('nombre_revisions')
            )['total'] or 0,
            'questions_reussies': ReponseEleve.objects.filter(
                eleve=request.user,
                est_correcte=True
            ).count(),
            'taux_reussite': 0,
        }

        # Calcul du taux de réussite
        total_reponses = ReponseEleve.objects.filter(eleve=request.user).count()
        if total_reponses > 0:
            stats['taux_reussite'] = round(
                (stats['questions_reussies'] / total_reponses) * 100,
                1
            )

    return render(request, 'home.html', {'stats': stats})


def signup(request):
    """Page d'inscription"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        # Récupération des données
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        # Validation
        if password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'accounts/signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
            return render(request, 'accounts/signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return render(request, 'accounts/signup.html')

        # Création de l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )

        # Connexion automatique
        login(request, user)
        messages.success(request, f"Bienvenue {user.get_nom_complet()} ! Complète ton profil pour commencer.")
        return redirect('accounts:complete_profil')

    return render(request, 'accounts/signup.html')


def user_login(request):
    """Page de connexion"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Bon retour {user.get_nom_complet()} ! 👋")

            # Redirection vers la page demandée ou home
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")

    return render(request, 'accounts/login.html')


@login_required
def user_logout(request):
    """Déconnexion"""
    logout(request)
    messages.info(request, "Tu as été déconnecté. À bientôt ! 👋")
    return redirect('home')


@login_required
def profil(request):
    """Page de profil utilisateur"""
    # Statistiques du profil
    stats = {
        'total_cours': request.user.cours.count(),
        'cours_traites': request.user.cours.filter(statut='traite').count(),
        'bonnes_reponses': request.user.reponses.filter(est_correcte=True).count(),
        'cours_favoris': request.user.cours.filter(favori=True).count(),
    }

    return render(request, 'accounts/profil.html', {'stats': stats})


@login_required
def complete_profil(request):
    """Compléter le profil élève"""
    if request.method == 'POST':
        user = request.user

        user.niveau = request.POST.get('niveau')
        user.classe = request.POST.get('classe')
        user.pays = request.POST.get('pays')
        user.telephone = request.POST.get('telephone', '')

        # Photo de profil
        if 'photo_profil' in request.FILES:
            user.photo_profil = request.FILES['photo_profil']

        user.profil_complete = True
        user.save()

        messages.success(request, "Ton profil est maintenant complet ! 🎉")
        return redirect('home')

    return render(request, 'accounts/complete_profil.html')


@login_required
def modifier_profil(request):
    """Modifier le profil"""
    if request.method == 'POST':
        user = request.user

        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.niveau = request.POST.get('niveau')
        user.classe = request.POST.get('classe')
        user.pays = request.POST.get('pays')
        user.telephone = request.POST.get('telephone', '')

        if 'photo_profil' in request.FILES:
            user.photo_profil = request.FILES['photo_profil']

        user.save()

        messages.success(request, "Profil mis à jour avec succès ! ✅")
        return redirect('accounts:profil')

    return render(request, 'accounts/modifier_profil.html')