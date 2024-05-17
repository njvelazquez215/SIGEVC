from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, FormView, RedirectView, DeleteView, View
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import UsuarioRegistroForm, UsuarioLoginForm, InvitacionForm, RegimientoForm, SeccionForm
from .models import Usuario, Regimiento, Invitacion, Escuadron, Seccion, Tanque
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

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

    def get_success_url(self):
        usuario = self.request.user
        print(f"Usuario: {usuario.username}, Rol: {usuario.rol}, Escuadron ID: {getattr(usuario.escuadron, 'id', 'No Asignado')}")

        if usuario.rol == 'Administrador':
            print("Redirigiendo al perfil de Administrador.")
            return reverse_lazy('perfil_administrador')

        elif usuario.rol == 'Jefe de Escuadrón':
            if usuario.escuadron:
                url = reverse_lazy('dashboard_escuadron', args=[usuario.escuadron.id])
                print(f"Redirigiendo a Dashboard de Escuadrón: {url}")
                return url
            else:
                messages.error(self.request, "No se ha asignado un escuadrón a tu usuario.")
                print("Error: Jefe de escuadrón sin escuadrón asignado.")
                return reverse_lazy('index')

        elif usuario.rol == 'Jefe de Sección':
            if usuario.seccion:
                url = reverse_lazy('dashboard_seccion', args=[usuario.seccion.id])
                print(f"Redirigiendo a Dashboard de Sección: {url}")
                return url
            else:
                messages.error(self.request, "No se ha asignado una sección a tu usuario.")
                print("Error: Jefe de sección sin sección asignada.")
                return reverse_lazy('index')

        else:
            messages.error(self.request, "Tu usuario no tiene un rol que permita acceso específico.")
            print("Error: Rol de usuario no específico o sin permisos.")
            return reverse_lazy('index')
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

class PerfilAdministradorView(UserPassesTestMixin, LoginRequiredMixin, FormView):
    template_name = 'gestion_vehiculos/perfil_administrador.html'
    form_class = InvitacionForm
    success_url = reverse_lazy('perfil_administrador')

    def test_func(self):
        return self.request.user.rol == 'Administrador'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuarios'] = Usuario.objects.filter(regimiento=self.request.user.regimiento, is_active=True)
        context['invitaciones'] = Invitacion.objects.filter(regimiento=self.request.user.regimiento, usado=False)
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if 'reenviar' in request.POST:
            invitacion_id = request.POST.get('reenviar')
            invitacion = get_object_or_404(Invitacion, id=invitacion_id)
            self.reenviar_invitacion(invitacion)
        elif 'eliminar' in request.POST:
            invitacion_id = request.POST.get('eliminar')
            Invitacion.objects.filter(id=invitacion_id).delete()
        elif form.is_valid():
            email = form.cleaned_data['email']
            invitacion = Invitacion.objects.filter(email=email, usado=False).first()
            if invitacion:
                # Si ya existe, reenviar la invitación existente
                self.reenviar_invitacion(invitacion)
                messages.info(request, "Invitación reenviada.")
            else:
                # Si no existe, crear y enviar nueva invitación
                return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        invitacion = form.save(commit=False)
        invitacion.regimiento = self.request.user.regimiento
        invitacion.save()
        print("Invitación guardada con escuadrón:", invitacion.escuadron)  # Debug para confirmar que se guarda el escuadrón
        return super().form_valid(form)

    def reenviar_invitacion(self, invitacion):
        self.enviar_invitacion(invitacion)
        invitacion.usado = False
        invitacion.save()

    def enviar_invitacion(self, invitacion):
        send_mail(
            'Invitación para unirte al regimiento',
            f'Por favor, utiliza este token para registrarte: {invitacion.token}',
            settings.DEFAULT_FROM_EMAIL,
            [invitacion.email],
            fail_silently=False,
        )

    def form_invalid(self, form):
        messages.error(self.request, "Hubo un error con el formulario de invitación.")
        return super().form_invalid(form)

class UsuarioDeleteView(DeleteView):
    model = Usuario
    success_url = reverse_lazy('perfil_administrador')


class DashboardEscuadronView(TemplateView):
    template_name = 'dashboard_escuadron.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        escuadron = get_object_or_404(Escuadron, id=self.kwargs['escuadron_id'])
        secciones = Seccion.objects.filter(escuadron=escuadron)
        context['escuadron'] = escuadron
        context['secciones'] = secciones
        return context


class EscuadronConfigView(TemplateView):
    template_name = 'escuadron_config.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        escuadron = get_object_or_404(Escuadron, id=self.kwargs['escuadron_id'])
        secciones = Seccion.objects.filter(escuadron=escuadron)
        context['escuadron'] = escuadron
        context['secciones'] = secciones
        return context

class SeccionCreateView(View):
    def get(self, request, *args, **kwargs):
        form = SeccionForm()
        return render(request, 'seccion_form.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = SeccionForm(request.POST)
        if form.is_valid():
            nueva_seccion = form.save(commit=False)
            nueva_seccion.escuadron = get_object_or_404(Escuadron, id=self.kwargs['escuadron_id'])
            nueva_seccion.save()
            return redirect('ver_escuadron', escuadron_id=nueva_seccion.escuadron.id)
        return render(request, 'seccion_form.html', {'form': form})

class SeccionUpdateView(View):
    def get(self, request, pk, *args, **kwargs):
        seccion = get_object_or_404(Seccion, pk=pk)
        form = SeccionForm(instance=seccion)
        return render(request, 'seccion_form.html', {'form': form})

    def post(self, request, pk, *args, **kwargs):
        seccion = get_object_or_404(Seccion, pk=pk)
        form = SeccionForm(request.POST, instance=seccion)
        if form.is_valid():
            form.save()
            return redirect('ver_escuadron', escuadron_id=seccion.escuadron.id)
        return render(request, 'seccion_form.html', {'form': form})

class SeccionDeleteView(View):
    def get(self, request, pk, *args, **kwargs):
        seccion = get_object_or_404(Seccion, pk=pk)
        seccion.delete()
        return redirect('ver_escuadron', escuadron_id=seccion.escuadron.id)

class DashboardSeccionView(TemplateView):
    template_name = 'dashboard_seccion.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seccion_id = self.kwargs['seccion_id']
        seccion = get_object_or_404(Seccion, id=seccion_id)
        tanques = Tanque.objects.filter(seccion=seccion)
        context['seccion'] = seccion
        context['tanques'] = tanques
        return context
