from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Regimiento, Usuario

# Registrar el modelo Regimiento
admin.site.register(Regimiento)

# Definir la clase personalizada para UsuarioAdmin
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {'fields': ('regimiento', 'rol')}),
    )

# Registrar el modelo Usuario usando la clase personalizada
admin.site.register(Usuario, UsuarioAdmin)

