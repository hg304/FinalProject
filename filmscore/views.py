from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout

from .models import Film, RecentlyVisited, SavedFilm
from .forms import LogInForm, SignUpForm

def home_view(request):
    visited = RecentlyVisited.objects.all()
    sorted = visited.order_by('-recentDate')
    first4 = []
    i = 0
    for film in sorted:
        temp = film
        if i < 4:
            first4.append(temp)
            i += 1
        else:
            break

    filmswithuser = []
    i = 0
    for film in sorted:
        temp = film
        users = temp.get_users()
        if i < 4:
            for user in users:
                if user == request.user.username:
                    filmswithuser.append(temp)
                    i += 1
        else:
            break

    return render(request, 'home.html', 
    {
        'visited': first4,
        'userVisited': filmswithuser
    })

def film_view(request):
    return render(request, 'film.html', None)

def selected_film_view(request, name):
    return render(request, 'film.html', {'name': name})

def profile_view(request):
    films = SavedFilm.objects.all()
    filmswithuser = []
    for film in films:
        temp = film
        users = temp.get_users()
        for user in users:
            if user == request.user.username:
                filmswithuser.append(temp)
    return render(request, 'profile.html', {'films': filmswithuser})

def top_films_view(request):
    return render(request, 'topfilms.html', None)

def login_view(request):
    error = False
    if request.method == "POST":
        form = LogInForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('home')
            else:
                error = True
    else:
        form = LogInForm()
    
    context = {
        'form': form,
        'error': error
    }
    return render(request, 'login.html', context)

def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
                data = {
                    "username": form.data["username"],
                    "email": form.data["email"],
                    "firstName": form.data["firstName"],
                    "lastName": form.data["lastName"],
                    "password1": form.data["password1"],
                    "password2": form.data["password2"],
                }
                form.data = data
                user = form.save()
                login(request, user)
                return redirect('home')
    else:
        context = {
            'form': SignUpForm()
        }
        
    return render(request, 'signup.html', context)

def log_out(request):
    logout(request)
    return redirect(reverse('home'))

def health(request):
    return HttpResponse(Film.objects.count())