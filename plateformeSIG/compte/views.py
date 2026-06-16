from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import InscriptionForm, ConnexionForm, ProfilForm


def inscription(request):
    if request.user.is_authenticated:
        return redirect('accueil')
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Compte créé avec succès. Bienvenue !")
            return redirect('accueil')
    else:
        form = InscriptionForm()
    return render(request, 'compte/inscription.html', {'form': form})


def connexion(request):
    if request.user.is_authenticated:
        return redirect('accueil')
    if request.method == 'POST':
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('accueil')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = ConnexionForm()
    return render(request, 'compte/connexion.html', {'form': form})


def deconnexion(request):
    logout(request)
    return redirect('connexion')


def accueil(request):
    return render(request, 'accueil/accueil.html')


@login_required(login_url='connexion')
def dashboard(request):
    return render(request, 'dashboard/dashboard.html')


@login_required(login_url='connexion')
def profil(request):
    if request.method == 'POST':
        form = ProfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('profil')
    else:
        form = ProfilForm(instance=request.user)
    return render(request, 'compte/profil.html', {'form': form})
