from django.core.management.base import BaseCommand
from gestion_vehiculos.models import Escuadron

# Utilizo este comando para verificar si existen escuadrones creados en la base de datos
# Para ejecutarlo, se debe correr el comando python manage.py list_escuadrones
class Command(BaseCommand):
    help = 'Lista todos los escuadrones en la base de datos'

    def handle(self, *args, **options):
        escuadrones = Escuadron.objects.all()
        if escuadrones:
            for escuadron in escuadrones:
                self.stdout.write(f'{escuadron.nombre} ({escuadron.tipo})')
        else:
            self.stdout.write('No hay escuadrones registrados.')