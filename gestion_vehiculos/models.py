from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class Regimiento(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200)

    def __str__(self):
        return self.nombre

class Usuario(AbstractUser):
    regimiento = models.ForeignKey('Regimiento', on_delete=models.CASCADE, null=True, blank=True)
    rol = models.CharField(max_length=100, choices=[('Administrador', 'Administrador'), ('Jefe', 'Jefe de Escuadrón'), ('Sección', 'Jefe de Sección')], default='Administrador')

    def __str__(self):
        return f"{self.username} ({self.rol})"

class Invitacion(models.Model):
    email = models.EmailField(unique=True)
    regimiento = models.ForeignKey('Regimiento', on_delete=models.CASCADE)
    rol = models.CharField(max_length=100, choices=[
        ('Jefe de Regimiento', 'Jefe de Regimiento'),
        ('2do Jefe de Regimiento', '2do Jefe de Regimiento'),
        ('Oficial de Operaciones', 'Oficial de Operaciones'),
        ('Oficial de Materiales', 'Oficial de Materiales'),
        ('Jefe de Escuadrón', 'Jefe de Escuadrón'),
        ('Jefe de Sección', 'Jefe de Sección')
    ])
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    usado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} ({self.rol})"
