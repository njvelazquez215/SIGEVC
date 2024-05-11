from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, FormView, RedirectView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import UsuarioRegistroForm, UsuarioLoginForm, InvitacionForm, RegimientoForm
from .models import Usuario, Regimiento, Invitacion
from django.core.mail import send_mail
from django.conf import settings

class IndexView(TemplateView):
    template_name = 'gestion_vehiculos/index.html'

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

class CrearRegimientoView(UserPassesTestMixin, FormView):
    form_class = RegimientoForm
    template_name = 'gestion_vehiculos/crear_regimiento.html'
    success_url = reverse_lazy('index')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class PerfilAdministradorView(LoginRequiredMixin, FormView):
    template_name = 'gestion_vehiculos/perfil_administrador.html'
    form_class = InvitacionForm
    success_url = reverse_lazy('perfil_administrador')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invitaciones'] = Invitacion.objects.filter(regimiento=self.request.user.regimiento, usado=False)
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        invitacion = form.save(commit=False)
        invitacion.regimiento = self.request.user.regimiento
        invitacion.save()
        send_mail(
            'Invitación para unirte al regimiento',
            f'Por favor, utiliza este token para registrarte: {invitacion.token}',
            settings.DEFAULT_FROM_EMAIL,
            [invitacion.email],
            fail_silently=False,
        )
        return super().form_valid(form)
