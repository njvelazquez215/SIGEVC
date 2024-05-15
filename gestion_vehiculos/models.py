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
    rol = models.CharField(max_length=100, choices=[('Administrador', 'Administrador'), ('Jefe de Escuadrón', 'Jefe de Escuadrón'), ('Jefe de Sección', 'Jefe de Sección')], default='Administrador')
    escuadron = models.ForeignKey('Escuadron', on_delete=models.SET_NULL, null=True, blank=True, related_name='jefes')

    def __str__(self):
        return f"{self.username} ({self.rol})"

class Invitacion(models.Model):
    ESTADOS = (
        ('enviada', 'Enviada'),
        ('cancelada', 'Cancelada'),
        ('pendiente', 'Pendiente'),
    )
    email = models.EmailField()
    regimiento = models.ForeignKey('Regimiento', on_delete=models.CASCADE)
    rol = models.CharField(max_length=100, choices=[
        ('Jefe de Regimiento', 'Jefe de Regimiento'),
        ('2do Jefe de Regimiento', '2do Jefe de Regimiento'),
        ('Oficial de Operaciones', 'Oficial de Operaciones'),
        ('Oficial de Materiales', 'Oficial de Materiales'),
        ('Jefe de Escuadrón', 'Jefe de Escuadrón'),
        ('Jefe de Sección', 'Jefe de Sección')
    ])
    escuadron = models.ForeignKey('Escuadron', on_delete=models.SET_NULL, null=True, blank=True)  # Nuevo campo opcional para escuadrón
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    usado = models.BooleanField(default=False)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente')

    def __str__(self):
        return f"{self.email} ({self.rol})"

class Escuadron(models.Model):
    regimiento = models.ForeignKey(Regimiento, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=100)  # Ejemplo: "Escuadrón de Tanques A", "Escuadrón Comando y Servicios"

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"

class Seccion(models.Model):
    escuadron = models.ForeignKey(Escuadron, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)  # Ejemplo: "1ra Sección de Tanques", "2da Sección de Tanques"
    jefe = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='jefe_seccion')

    def __str__(self):
        return self.nombre

class Tanque(models.Model):
    seccion = models.ForeignKey(Seccion, on_delete=models.CASCADE)
    NI = models.CharField(max_length=100, unique=True)  # Número de Identificación del Tanque
    estado = models.CharField(max_length=100, choices=[('En servicio', 'En servicio'), ('Servicio limitado', 'Servicio limitado'), ('Fuera de servicio', 'Fuera de servicio')])
    responsable = models.CharField(max_length=100)  # Nombre del responsable del tanque

    def __str__(self):
        return f"{self.NI} - {self.estado}"

