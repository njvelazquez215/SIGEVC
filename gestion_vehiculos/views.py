from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, TemplateView, FormView, RedirectView, DeleteView, View, UpdateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import UsuarioRegistroForm, UsuarioLoginForm, InvitacionForm, RegimientoForm, SeccionForm, TanqueForm
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
        print(f"Usuario: {usuario.username}, Rol: {usuario.rol}, Escuadron ID: {usuario.escuadron.id if usuario.escuadron else 'No Asignado'}")

        if usuario.rol == 'Administrador':
            print("Redirigiendo al perfil de Administrador.")
            return reverse_lazy('perfil_administrador')
        elif usuario.rol == 'Jefe de Escuadrón':
            if usuario.escuadron:
                print(f"Redirigiendo a Dashboard de Escuadrón: /escuadron/{usuario.escuadron.id}/dashboard/")
                return reverse_lazy('dashboard_escuadron', args=[usuario.escuadron.id])
            else:
                print("Error: Jefe de escuadrón sin escuadrón asignado.")
                messages.error(self.request, "No se ha asignado un escuadrón a tu usuario.")
                return reverse_lazy('index')
        elif usuario.rol == 'Jefe de Sección':
            seccion = Seccion.objects.filter(jefe=usuario).first()
            if seccion:
                print(f"Redirigiendo a Dashboard de Sección: /seccion/{seccion.id}/dashboard/")
                return reverse_lazy('dashboard_seccion', args=[seccion.id])
            else:
                print("Error: Jefe de sección sin sección asignada.")
                messages.error(self.request, "No se ha asignado una sección a tu usuario.")
                return reverse_lazy('index')
        else:
            print("Error: Rol de usuario no reconocido.")
            messages.error(self.request, "Tu usuario no tiene un rol que permita acceso específico.")
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


class DashboardEscuadronView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'gestion_vehiculos/dashboard_escuadron.html'

    def test_func(self):
        return self.request.user.rol == 'Jefe de Escuadrón'

    def get(self, request, escuadron_id):
        escuadron = get_object_or_404(Escuadron, id=escuadron_id)
        secciones = Seccion.objects.filter(escuadron=escuadron)
        tanques = Tanque.objects.filter(seccion__in=secciones)

        estado_general = {
            'total': tanques.count(),
            'en_servicio': tanques.filter(estado='En servicio').count(),
            'servicio_limitado': tanques.filter(estado='Servicio limitado').count(),
            'fuera_servicio': tanques.filter(estado='Fuera de servicio').count(),
        }

        context = {
            'escuadron': escuadron,
            'secciones': secciones,
            'tanques': tanques,
            'estado_general': estado_general,
        }
        return render(request, self.template_name, context)

class EscuadronConfigView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'gestion_vehiculos/escuadron_config.html'

    def test_func(self):
        return self.request.user.rol == 'Jefe de Escuadrón' and self.request.user.escuadron

    def get(self, request, escuadron_id):
        escuadron = get_object_or_404(Escuadron, id=escuadron_id)
        seccion_form = SeccionForm()
        tanque_form = TanqueForm()
        return render(request, self.template_name, {
            'escuadron': escuadron,
            'seccion_form': seccion_form,
            'tanque_form': tanque_form
        })

    def post(self, request, escuadron_id):
        escuadron = get_object_or_404(Escuadron, id=escuadron_id)
        seccion_form = SeccionForm(request.POST)
        tanque_form = TanqueForm(request.POST)

        if 'crear_seccion' in request.POST and seccion_form.is_valid():
            seccion = seccion_form.save(commit=False)
            seccion.escuadron = escuadron
            seccion.save()
            return redirect('escuadron_config', escuadron_id=escuadron.id)

        if 'crear_tanque' in request.POST and tanque_form.is_valid():
            seccion_id = request.POST.get('seccion_id')
            seccion = get_object_or_404(Seccion, id=seccion_id)
            tanque = tanque_form.save(commit=False)
            tanque.seccion = seccion
            tanque.save()
            return redirect('escuadron_config', escuadron_id=escuadron.id)

        return render(request, self.template_name, {
            'escuadron': escuadron,
            'seccion_form': seccion_form,
            'tanque_form': tanque_form
        })

class SeccionCreateView(View):
    def get(self, request, *args, **kwargs):
        form = SeccionForm()
        return render(request, 'gestion_vehiculos/seccion_form.html', {'form': form})

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


class DashboardSeccionView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'gestion_vehiculos/dashboard_seccion.html'

    def test_func(self):
        return self.request.user.rol == 'Jefe de Sección'

    def get(self, request, seccion_id):
        seccion = get_object_or_404(Seccion, id=seccion_id)
        tanques = Tanque.objects.filter(seccion=seccion)

        estado_general = {
            'total': tanques.count(),
            'en_servicio': tanques.filter(estado='En servicio').count(),
            'servicio_limitado': tanques.filter(estado='Servicio limitado').count(),
            'fuera_servicio': tanques.filter(estado='Fuera de servicio').count(),
        }

        context = {
            'seccion': seccion,
            'tanques': tanques,
            'estado_general': estado_general,
        }
        return render(request, self.template_name, context)


class VerTanqueView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'gestion_vehiculos/ver_tanque.html'

    def test_func(self):
        # Permitir acceso sólo a los jefes de escuadrón y jefes de sección
        return self.request.user.rol in ['Jefe de Escuadrón', 'Jefe de Sección']

    def get(self, request, tanque_id):
        tanque = get_object_or_404(Tanque, id=tanque_id)
        rol_usuario = request.user.rol
        dashboard_url = 'dashboard_escuadron' if rol_usuario == 'Jefe de Escuadrón' else 'dashboard_seccion'
        context = {
            'tanque': tanque,
            'dashboard_url': dashboard_url
        }
        return render(request, self.template_name, context)

class EditarTanqueView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Tanque
    fields = ['NI', 'estado', 'responsable']
    template_name = 'gestion_vehiculos/editar_tanque.html'

    def get_success_url(self):
        return reverse_lazy('escuadron_config', kwargs={'escuadron_id': self.object.seccion.escuadron.id})

    def test_func(self):
        return self.request.user.rol == 'Jefe de Escuadrón'

class EliminarTanqueView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Tanque
    template_name = 'gestion_vehiculos/eliminar_tanque.html'

    def get_success_url(self):
        escuadron_id = self.object.seccion.escuadron.id
        return reverse_lazy('escuadron_config', kwargs={'escuadron_id': escuadron_id})

    def test_func(self):
        return self.request.user.rol == 'Jefe de Escuadrón'


class NovedadesTanqueView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'gestion_vehiculos/novedades_tanque.html'

    def test_func(self):
        return self.request.user.rol == 'Jefe de Sección'

    def get(self, request, tanque_id):
        tanque = get_object_or_404(Tanque, id=tanque_id)
        context = {
            'tanque': tanque,
        }
        return render(request, self.template_name, context)


class TablaControl1View(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'gestion_vehiculos/tabla_control_1.html'

    def test_func(self):
        return self.request.user.rol in ['Jefe de Escuadrón', 'Jefe de Sección']

    def get(self, request, tanque_id):
        tanque = get_object_or_404(Tanque, id=tanque_id)
        return render(request, self.template_name, {'tanque': tanque})

class TablaControl2View(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'gestion_vehiculos/tabla_control_2.html'

    def test_func(self):
        return self.request.user.rol in ['Jefe de Escuadrón', 'Jefe de Sección']

    def get(self, request, tanque_id):
        tanque = get_object_or_404(Tanque, id=tanque_id)
        return render(request, self.template_name, {'tanque': tanque})

class TablaControl3View(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'gestion_vehiculos/tabla_control_3.html'

    def test_func(self):
        return self.request.user.rol in ['Jefe de Escuadrón', 'Jefe de Sección']

    def get(self, request, tanque_id):
        tanque = get_object_or_404(Tanque, id=tanque_id)
        return render(request, self.template_name, {'tanque': tanque})