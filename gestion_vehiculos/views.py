from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from .forms import UsuarioRegistroForm, UsuarioLoginForm
from .models import Usuario
from django.shortcuts import render

def index(request):
    return render(request, 'gestion_vehiculos/index.html')

class UsuarioRegistroView(CreateView):
    model = Usuario
    form_class = UsuarioRegistroForm
    template_name = 'gestion_vehiculos/registro.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

class UsuarioLoginView(LoginView):
    form_class = UsuarioLoginForm
    template_name = 'gestion_vehiculos/login.html'
    success_url = reverse_lazy('dashboard')

class UsuarioLogoutView(LogoutView):
    next_page = reverse_lazy('login')



# Create your views here.
