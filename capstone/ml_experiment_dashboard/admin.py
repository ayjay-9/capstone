from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Experiment, ExperimentResult, User


admin.site.register(User, UserAdmin)
admin.site.register(Experiment)
admin.site.register(ExperimentResult)
