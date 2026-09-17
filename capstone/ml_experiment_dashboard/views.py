from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.db import IntegrityError


from .models import User, Experiment, ExperimentResult

def index(request):
    return render(request, 'ml_experiment_dashboard/index.html')


def register(request):
    if request.method == "POST":
        first = request.POST["first"]
        last = request.POST["last"]
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "ml_experiment_dashboard/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(first_name=first, last_name=last, username=username, email=email, password=password)
            user.save()
        except IntegrityError:
            return render(request, "ml_experiment_dashboard/register.html", {
                "message": "Username already taken."
            })
        django_login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "ml_experiment_dashboard/register.html", {
            "current_user": request.user.username if request.user.is_authenticated else None,
        })


def login(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            django_login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "ml_experiment_dashboard/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "ml_experiment_dashboard/login.html")


def logout(request):
    django_logout(request)
    return HttpResponseRedirect(reverse("login"))
