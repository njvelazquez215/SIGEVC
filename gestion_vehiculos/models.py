from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class Regimiento(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200)

class Usuario(AbstractUser):
    regimiento = models.ForeignKey(Regimiento, on_delete=models.SET_NULL, null=True, blank=True)
    rol = models.CharField(max_length=100, choices=[('Super', 'Superusuario'), ('Admin', 'Administrador'), ('Jefe', 'Jefe de Escuadrón'), ('Seccion', 'Jefe de Sección')])

    def __str__(self):
        return f"{self.username} ({self.rol})"

class Invitacion(models.Model):
    email = models.EmailField(unique=True)
    regimiento = models.ForeignKey('Regimiento', on_delete=models.CASCADE)
    rol = models.CharField(max_length=100, choices=[('Admin', 'Administrador'), ('Jefe', 'Jefe de Escuadrón'), ('Seccion', 'Jefe de Sección')])
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    usado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} ({self.rol})"