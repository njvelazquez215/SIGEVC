from django.core.management.base import BaseCommand
from gestion_vehiculos.models import Escuadron, Regimiento

# Utilizo este comando para agregar escuadrones a la base de datos si no existen
# Para ejecutarlo, se debe correr el comando python manage.py add_escuadrones
class Command(BaseCommand):
    help = 'Agrega escuadrones a la base de datos si no existen'

    def handle(self, *args, **options):
        # Asegúrate de tener al menos un regimiento creado
        regimiento = Regimiento.objects.first()
        if not regimiento:
            self.stdout.write(self.style.ERROR('No hay regimientos registrados. Por favor, crea uno primero.'))
            return

        # Nombres y tipos de los escuadrones a crear
        escuadrones_data = [
            ("Escuadrón de Tanques A", "Tanques"),
            ("Escuadrón de Tanques B", "Tanques"),
            ("Escuadrón Comando y Servicio", "Servicios")
        ]

        for nombre, tipo in escuadrones_data:
            escuadron, created = Escuadron.objects.get_or_create(
                nombre=nombre,
                tipo=tipo,
                regimiento=regimiento
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Escuadrón {nombre} creado exitosamente.'))
            else:
                self.stdout.write(f'El escuadrón {nombre} ya existe.')