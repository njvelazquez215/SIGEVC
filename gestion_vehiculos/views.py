from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import user_passes_test
from .forms import UsuarioRegistroForm, UsuarioLoginForm, InvitacionForm
from .models import Usuario
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
    form_class = UsuarioLoginForm
    template_name = 'gestion_vehiculos/login.html'
    success_url = reverse_lazy('dashboard')

class UsuarioLogoutView(LogoutView):
    next_page = reverse_lazy('login')


@user_passes_test(lambda u: u.is_superuser or u.rol == 'Admin')
def enviar_invitacion(request):
    if request.method == 'POST':
        form = InvitacionForm(request.POST)
        if form.is_valid():
            invitacion = form.save()
            send_mail(
                'Invitación para unirte al sistema',
                f'Únete usando el siguiente enlace: http://127.0.0.1:8000/registro/?token={invitacion.token}',
                'admin@example.com',
                [invitacion.email],
            )
            return redirect('invitacion_enviada')
    else:
        form = InvitacionForm()
    return render(request, 'gestion_vehiculos/enviar_invitacion.html', {'form': form})
# Create your views here.
