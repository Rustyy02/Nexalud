from django.contrib.auth.models import AbstractUser
from django.db import models

# Aquí se crean los modelos personalizados de usuario si es necesario.

class User(AbstractUser):
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True)
