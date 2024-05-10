from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import user_passes_test, login_required
from .forms import UsuarioRegistroForm, UsuarioLoginForm, InvitacionForm, RegimientoForm
from .models import Usuario, Regimiento
from django.shortcuts import render, redirect
from django.core.mail import send_mail

def index(request):
    return render(request, 'gestion_vehiculos/index.html')

class UsuarioRegistroView(CreateView):
    model = Usuario
    form_class = UsuarioRegistroForm
    template_name = 'gestion_vehiculos/registro.html'
    success_url = '/'

    def get_initial(self):
        token = self.request.GET.get('token')
        return {'token': token}

class UsuarioLoginView(LoginView):
    template_name = 'gestion_vehiculos/login.html'
    success_url = '/enviar_invitacion/'

class UsuarioLogoutView(LogoutView):
    next_page = reverse_lazy('login')


@user_passes_test(lambda u: u.is_authenticated and u.rol == 'Administrador')
def enviar_invitacion(request):
    regimiento = request.user.regimiento  # Asumimos que el usuario tiene un campo `regimiento`.
    if request.method == 'POST':
        form = InvitacionForm(request.POST)
        if form.is_valid():
            invitacion = form.save(commit=False)
            invitacion.regimiento = regimiento
            invitacion.save()
            # Envía correo electrónico con el token de invitación (puedes personalizar el contenido):
            send_mail(
                'Invitación para unirte al regimiento',
                f'Únete usando el siguiente enlace: http://127.0.0.1:8000/registro/?token={invitacion.token}',
                'admin@example.com',
                [invitacion.email]
            )
            return redirect('invitacion_enviada')
    else:
        form = InvitacionForm()
    return render(request, 'gestion_vehiculos/enviar_invitacion.html')
# Create your views here.

@user_passes_test(lambda u: u.is_superuser)
def crear_regimiento(request):
    if request.method == 'POST':
        form = RegimientoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = RegimientoForm()
    return render(request, 'gestion_vehiculos/crear_regimiento.html', {'form': form})


@login_required
def perfil_administrador(request):
    # Verificar que el usuario tiene el rol correcto
    if request.user.rol != 'Administrador':
        return redirect('index')  # Redirigir si no es administrador

    # Proveer la lógica para el perfil del administrador
    return render(request, 'gestion_vehiculos/perfil_administrador.html')