from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class User(AbstractUser):
    pass

class Experiment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    columns = models.JSONField(default=list)
    row_count = models.IntegerField(default=0)
    preview_rows = models.JSONField(default=list)
    commentary = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name}'s experiment on {self.name}"

class ExperimentResult(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    result_data = models.JSONField()
    commentary = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result for {self.experiment.name} at {self.created_at}"
