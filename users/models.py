from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    wca_id = models.CharField(max_length=10, null=True, unique=True)
    elo = models.FloatField(default=1200)