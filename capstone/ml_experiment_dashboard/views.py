import io
import json
import pandas as pd
from pathlib import PurePosixPath as UploadPath
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError


from .models import User, Experiment, ExperimentResult
from .dataset_commentary import generate_dataset_commentary
from .result_commentary import generate_result_commentary
from .model_training import train_model

def index(request):
    if request.method == "POST":
            uploaded_file = request.FILES["dataset"]
            if not UploadPath(uploaded_file.name).suffix == ".csv":
                return render(request, "ml_experiment_dashboard/index.html", {
                    "message": "Please upload a CSV file."
                })
            
            # If the file is a CSV, but it doesn't have valid data headers
            try:
                df = pd.read_csv(uploaded_file, header=0)
            except pd.errors.EmptyDataError:
                return render(request, "ml_experiment_dashboard/index.html", {
                    "message": "The uploaded CSV file should not be empty and must contain valid data headers."
                })

            if not df.columns.tolist():
                return render(request, "ml_experiment_dashboard/index.html", {
                    "message": "The uploaded CSV file should not be empty and must contain valid data headers."
                })

                
            # If the file is a CSV, but it doesn't have up to 5 rows of data
            if len(df) < 5:
                return render(request, "ml_experiment_dashboard/index.html", {
                    "message": "The uploaded CSV file must contain at least 5 rows of data."
                })

            try:
                commentary = generate_dataset_commentary(df)
            except Exception as e:
                print(f"generate_dataset_commentary failed: {e!r}")
                commentary = "Commentary unavailable."

            # Create the Experiment model
            experiment = Experiment(
                user=request.user,
                name=uploaded_file.name,
                description="Uploaded dataset",
                columns=df.columns.tolist(),
                row_count=len(df),
                preview_rows=json.loads(df.head().to_json(orient="records")),
                commentary=commentary,
            )
            experiment.save()
            # Cache the dataset for 10 minutes to allow the user to run experiments without re-uploading the dataset.
            cache.set(f"dataset_{request.session.session_key}", df.to_json(orient="records"), timeout=600) 

            return render(request, "ml_experiment_dashboard/index.html", {
                "message": f"Successfully uploaded {uploaded_file.name}.",
                "experiment": experiment,
                "can_run_experiment": True,
            })
    else:
        return render(request, "ml_experiment_dashboard/index.html")


def serialize_history(experiments):
    return [
        {
            "name": experiment.name,
            "description": experiment.description,
            "columns": experiment.columns,
            "row_count": experiment.row_count,
            "preview_rows": experiment.preview_rows,
            "commentary": experiment.commentary,
            "created_at": experiment.created_at.isoformat(),
        }
        for experiment in experiments
    ]

@login_required
def history(request):
    experiments = Experiment.objects.filter(user=request.user).order_by("-created_at")
    paginator = Paginator(experiments, 5)  # Show 5 experiments per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "ml_experiment_dashboard/history.html", {
        "page_obj": page_obj,
        "experiments": serialize_history(page_obj.object_list),
    })

@login_required
def run_experiment(request, experiment_id):
    experiment = get_object_or_404(Experiment, id=experiment_id, user=request.user)

    if request.method != "POST":
        return render(request, "ml_experiment_dashboard/run_experiment.html", {
            "experiment": experiment,
        })

    target_column = request.POST.get("target_column")

    cached_data = cache.get(f"dataset_{request.session.session_key}")
    if cached_data is None:
        return render(request, "ml_experiment_dashboard/run_experiment.html", {
            "experiment": experiment,
            "message": "Your uploaded data has expired. Please upload the dataset again to run an experiment.",
        })

    df = pd.read_json(io.StringIO(cached_data), orient="records")

    try:
        result_data = train_model(df, target_column)
    except Exception as e:
        print(f"train_model failed: {e!r}")
        return render(request, "ml_experiment_dashboard/run_experiment.html", {
            "experiment": experiment,
            "message": "Could not run an experiment with that column. Please choose a different target column.",
        })

    try:
        commentary = generate_result_commentary(result_data)
    except Exception as e:
        print(f"generate_result_commentary failed: {e!r}")
        commentary = "Commentary unavailable."

    ExperimentResult.objects.create(experiment=experiment, result_data=result_data)

    return render(request, "ml_experiment_dashboard/run_experiment.html", {
        "experiment": experiment,
        "result": result_data,
        "commentary": commentary,
    })

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
