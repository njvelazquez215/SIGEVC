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

    def post(self, request, tanque_id):
        tanque = get_object_or_404(Tanque, id=tanque_id)

        # Coeficientes asignados a cada opción
        coeficientes = {
            'sin novedad': 0,
            'nivel de aceite bajo': 2,
            'requiere service 60': 4,
            'requiere service 120': 8,
            'pastillas fuera de servicio': 5,
            'pastillas desgastadas': 2,
            'con novedad': 3,
            'falta': 4,
            'desgastado': 2,
            'fuera de servicio': 8,
            'servicio limitado': 4,
            'tensión baja': 3,
            'tensión óptima': 0,
        }

        # Obtención de los valores del formulario
        motor_aceite = request.POST.get('motor_aceite', 'sin novedad')
        motor_service = request.POST.get('motor_service', 'sin novedad')
        caja_aceite = request.POST.get('caja_aceite', 'sin novedad')
        caja_service = request.POST.get('caja_service', 'sin novedad')
        sistema_freno_aceite = request.POST.get('sistema_freno_aceite', 'sin novedad')
        sistema_freno_pastillas = request.POST.get('sistema_freno_pastillas', 'sin novedad')
        ventilador_aceite = request.POST.get('ventilador_aceite', 'sin novedad')
        sistema_refrigeracion = request.POST.get('sistema_refrigeracion', 'sin novedad')
        filtro_mecanico_aceite = request.POST.get('filtro_mecanico_aceite', 'sin novedad')
        filtro_aire = request.POST.get('filtro_aire', 'sin novedad')
        tapa_recinto = request.POST.get('tapa_recinto', 'sin novedad')
        rejilla_admision_aire = request.POST.get('rejilla_admision_aire', 'sin novedad')
        corona_tractora = request.POST.get('corona_tractora', 'sin novedad')
        rueda_tractora_aceite = request.POST.get('rueda_tractora_aceite', 'sin novedad')
        oruga_tension = request.POST.get('oruga_tension', 'sin novedad')
        rueda_tensora_aceite = request.POST.get('rueda_tensora_aceite', 'sin novedad')
        rueda_tensora_caucho = request.POST.get('rueda_tensora_caucho', 'sin novedad')
        rodillos_apoyo_aceite = request.POST.get('rodillos_apoyo_aceite', 'sin novedad')
        rodillos_apoyo_caucho = request.POST.get('rodillos_apoyo_caucho', 'sin novedad')
        amortiguadores_soportes = request.POST.get('amortiguadores_soportes', 'sin novedad')
        chapas_cubre_orugas = request.POST.get('chapas_cubre_orugas', 'sin novedad')
        potes_lanza_fumigenos = request.POST.get('potes_lanza_fumigenos', 'sin novedad')
        soportes_lote_abordo = request.POST.get('soportes_lote_abordo', 'sin novedad')
        junta_goma_escotilla_escape = request.POST.get('junta_goma_escotilla_escape', 'sin novedad')
        escotilla_escape = request.POST.get('escotilla_escape', 'sin novedad')
        escotilla_jefe_tanque = request.POST.get('escotilla_jefe_tanque', 'sin novedad')
        escotilla_conductor = request.POST.get('escotilla_conductor', 'sin novedad')
        escotilla_carga = request.POST.get('escotilla_carga', 'sin novedad')
        tapas_inspeccion = request.POST.get('tapas_inspeccion', 'sin novedad')
        bocina = request.POST.get('bocina', 'sin novedad')
        balizas = request.POST.get('balizas', 'sin novedad')
        luces_posicion = request.POST.get('luces_posicion', 'sin novedad')
        luces_giro = request.POST.get('luces_giro', 'sin novedad')
        luz_alta_baja = request.POST.get('luz_alta_baja', 'sin novedad')
        luz_freno = request.POST.get('luz_freno', 'sin novedad')
        luces_combate = request.POST.get('luces_combate', 'sin novedad')
        ojos_gatos_posteriores = request.POST.get('ojos_gatos_posteriores', 'sin novedad')
        freno_servicio = request.POST.get('freno_servicio', 'sin novedad')
        iluminacion_interior = request.POST.get('iluminacion_interior', 'sin novedad')
        bombas_achique = request.POST.get('bombas_achique', 'sin novedad')
        cano_escape = request.POST.get('cano_escape', 'sin novedad')
        multiple_escape = request.POST.get('multiple_escape', 'sin novedad')

        # Cálculo del estado del tanque
        puntuacion = (
            coeficientes[motor_aceite] +
            coeficientes[motor_service] +
            coeficientes[caja_aceite] +
            coeficientes[caja_service] +
            coeficientes[sistema_freno_aceite] +
            coeficientes[sistema_freno_pastillas] +
            coeficientes[ventilador_aceite] +
            coeficientes[sistema_refrigeracion] +
            coeficientes[filtro_mecanico_aceite] +
            coeficientes[filtro_aire] +
            coeficientes[tapa_recinto] +
            coeficientes[rejilla_admision_aire] +
            coeficientes[corona_tractora] +
            coeficientes[rueda_tractora_aceite] +
            coeficientes[oruga_tension] +
            coeficientes[rueda_tensora_aceite] +
            coeficientes[rueda_tensora_caucho] +
            coeficientes[rodillos_apoyo_aceite] +
            coeficientes[rodillos_apoyo_caucho] +
            coeficientes[amortiguadores_soportes] +
            coeficientes[chapas_cubre_orugas] +
            coeficientes[potes_lanza_fumigenos] +
            coeficientes[soportes_lote_abordo] +
            coeficientes[junta_goma_escotilla_escape] +
            coeficientes[escotilla_escape] +
            coeficientes[escotilla_jefe_tanque] +
            coeficientes[escotilla_conductor] +
            coeficientes[escotilla_carga] +
            coeficientes[tapas_inspeccion] +
            coeficientes[bocina] +
            coeficientes[balizas] +
            coeficientes[luces_posicion] +
            coeficientes[luces_giro] +
            coeficientes[luz_alta_baja] +
            coeficientes[luz_freno] +
            coeficientes[luces_combate] +
            coeficientes[ojos_gatos_posteriores] +
            coeficientes[freno_servicio] +
            coeficientes[iluminacion_interior] +
            coeficientes[bombas_achique] +
            coeficientes[cano_escape] +
            coeficientes[multiple_escape]
        )

        # Determinación del estado basado en la puntuación
        if 'requiere service 120' in [motor_service, caja_service]:
            tanque.estado = 'Fuera de servicio'
        elif 'requiere service 60' in [motor_service, caja_service]:
            tanque.estado = 'Servicio limitado'
        elif puntuacion >= 15:  # Umbral para 'Fuera de servicio'
            tanque.estado = 'Fuera de servicio'
        elif 5 <= puntuacion < 15:  # Umbral para 'Servicio limitado'
            tanque.estado = 'Servicio limitado'
        else:
            tanque.estado = 'En servicio'

        tanque.save()

        return redirect('novedades_tanque', tanque_id=tanque.id)

class TablaControl2View(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'gestion_vehiculos/tabla_control_2.html'

    def test_func(self):
        return self.request.user.rol in ['Jefe de Escuadrón', 'Jefe de Sección']

    def get(self, request, tanque_id):
        tanque = get_object_or_404(Tanque, id=tanque_id)
        return render(request, self.template_name, {'tanque': tanque})

    def post(self, request, tanque_id):
        tanque = get_object_or_404(Tanque, id=tanque_id)

        # Coeficientes asignados a cada opción
        coeficientes = {
            'sin novedad': 0,
            'con novedad': 3,
            'falta': 4,
            'desgastado': 2,
            'fuera de servicio': 8,
            'servicio limitado': 4,
        }

        # Obtención de los valores del formulario
        sicte = request.POST.get('sicte', 'sin novedad')
        periscopio_tzf_la = request.POST.get('periscopio_tzf_la', 'sin novedad')
        aparato_tzf_la = request.POST.get('aparato_tzf_la', 'sin novedad')
        soporte_tres_a = request.POST.get('soporte_tres_a', 'sin novedad')
        cartucho_des_humificador = request.POST.get('cartucho_des_humificador', 'sin novedad')
        oculares_ventanas = request.POST.get('oculares_ventanas', 'sin novedad')
        graduacion_diotrica = request.POST.get('graduacion_diotrica', 'sin novedad')
        gomas_oculares = request.POST.get('gomas_oculares', 'sin novedad')
        apoya_frente = request.POST.get('apoya_frente', 'sin novedad')
        perillas_movimiento = request.POST.get('perillas_movimiento', 'sin novedad')
        caja_electronica = request.POST.get('caja_electronica', 'sin novedad')
        cbdt = request.POST.get('cbdt', 'sin novedad')
        disparador = request.POST.get('disparador', 'sin novedad')
        protector_retroceso = request.POST.get('protector_retroceso', 'sin novedad')
        afuste_ametcx = request.POST.get('afuste_ametcx', 'sin novedad')
        cuadrante_nivel = request.POST.get('cuadrante_nivel', 'sin novedad')
        iluminacion_interior_plafonier = request.POST.get('iluminacion_interior_plafonier', 'sin novedad')
        enclavamiento_asiento = request.POST.get('enclavamiento_asiento', 'sin novedad')
        soporte_episcopios = request.POST.get('soporte_episcopios', 'sin novedad')
        conexion_cables_baterias = request.POST.get('conexion_cables_baterias', 'sin novedad')
        tapa_compartimiento_baterias = request.POST.get('tapa_compartimiento_baterias', 'sin novedad')
        escotilla_j_tan = request.POST.get('escotilla_j_tan', 'sin novedad')
        afuste_j_tan = request.POST.get('afuste_j_tan', 'sin novedad')
        contenedor_vainas = request.POST.get('contenedor_vainas', 'sin novedad')
        burletes_goma = request.POST.get('burletes_goma', 'sin novedad')
        conexiones_hidraulicas = request.POST.get('conexiones_hidraulicas', 'sin novedad')
        potes_lanzafumigenos = request.POST.get('potes_lanzafumigenos', 'sin novedad')
        cartucho_antihumedad = request.POST.get('cartucho_antihumedad', 'sin novedad')
        panel_mando_j_tan = request.POST.get('panel_mando_j_tan', 'sin novedad')
        panel_mando_ap = request.POST.get('panel_mando_ap', 'sin novedad')
        panel_mando_carg = request.POST.get('panel_mando_carg', 'sin novedad')
        reloj_azimutal = request.POST.get('reloj_azimutal', 'sin novedad')
        accesorios_provisiones = request.POST.get('accesorios_provisiones', 'sin novedad')
        tuberias_mangueras = request.POST.get('tuberias_mangueras', 'sin novedad')
        tanque_grupo_bomba = request.POST.get('tanque_grupo_bomba', 'sin novedad')
        accionamiento_manual_altura = request.POST.get('accionamiento_manual_altura', 'sin novedad')
        accionamiento_manual_direccion = request.POST.get('accionamiento_manual_direccion', 'sin novedad')
        tapas_inspeccion = request.POST.get('tapas_inspeccion', 'sin novedad')

        # Cálculo del estado del tanque
        puntuacion = (
            coeficientes[sicte] +
            coeficientes[periscopio_tzf_la] +
            coeficientes[aparato_tzf_la] +
            coeficientes[soporte_tres_a] +
            coeficientes[cartucho_des_humificador] +
            coeficientes[oculares_ventanas] +
            coeficientes[graduacion_diotrica] +
            coeficientes[gomas_oculares] +
            coeficientes[apoya_frente] +
            coeficientes[perillas_movimiento] +
            coeficientes[caja_electronica] +
            coeficientes[cbdt] +
            coeficientes[disparador] +
            coeficientes[protector_retroceso] +
            coeficientes[afuste_ametcx] +
            coeficientes[cuadrante_nivel] +
            coeficientes[iluminacion_interior_plafonier] +
            coeficientes[enclavamiento_asiento] +
            coeficientes[soporte_episcopios] +
            coeficientes[conexion_cables_baterias] +
            coeficientes[tapa_compartimiento_baterias] +
            coeficientes[escotilla_j_tan] +
            coeficientes[afuste_j_tan] +
            coeficientes[contenedor_vainas] +
            coeficientes[burletes_goma] +
            coeficientes[conexiones_hidraulicas] +
            coeficientes[potes_lanzafumigenos] +
            coeficientes[cartucho_antihumedad] +
            coeficientes[panel_mando_j_tan] +
            coeficientes[panel_mando_ap] +
            coeficientes[panel_mando_carg] +
            coeficientes[reloj_azimutal] +
            coeficientes[accesorios_provisiones] +
            coeficientes[tuberias_mangueras] +
            coeficientes[tanque_grupo_bomba] +
            coeficientes[accionamiento_manual_altura] +
            coeficientes[accionamiento_manual_direccion] +
            coeficientes[tapas_inspeccion]
        )

        # Determinación del estado basado en la puntuación
        if puntuacion >= 15:  # Umbral para 'Fuera de servicio'
            tanque.estado = 'Fuera de servicio'
        elif 5 <= puntuacion < 15:  # Umbral para 'Servicio limitado'
            tanque.estado = 'Servicio limitado'
        else:
            tanque.estado = 'En servicio'

        tanque.save()

        return redirect('novedades_tanque', tanque_id=tanque.id)

class TablaControl3View(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'gestion_vehiculos/tabla_control_3.html'

    def test_func(self):
        return self.request.user.rol in ['Jefe de Escuadrón', 'Jefe de Sección']

    def get(self, request, tanque_id):
        tanque = get_object_or_404(Tanque, id=tanque_id)
        return render(request, self.template_name, {'tanque': tanque})

    def post(self, request, tanque_id):
        tanque = get_object_or_404(Tanque, id=tanque_id)

        # Coeficientes asignados a cada opción
        coeficientes = {
            'sin novedad': 0,
            'con novedad': 3,
            'falta': 4,
            'desgastado': 2,
            'fuera de servicio': 8,
            'servicio limitado': 4,
        }

        # Obtención de los valores del formulario
        motor_horas = request.POST.get('motor_horas', 0)
        caja_cambios_horas = request.POST.get('caja_cambios_horas', 0)
        filtro_ventiladores = request.POST.get('filtro_ventiladores', 'sin novedad')
        filtro_combustible = request.POST.get('filtro_combustible', 'sin novedad')
        malla_filtrante = request.POST.get('malla_filtrante', 'sin novedad')
        oruga = request.POST.get('oruga', 'sin novedad')
        uniones_laterales = request.POST.get('uniones_laterales', 'sin novedad')
        ruedas_tensoras = request.POST.get('ruedas_tensoras', 'sin novedad')
        tapas_compartimiento = request.POST.get('tapas_compartimiento', 'sin novedad')
        calefactor_conductor = request.POST.get('calefactor_conductor', 'sin novedad')
        freno_servicio = request.POST.get('freno_servicio', 'sin novedad')
        asiento_ruta = request.POST.get('asiento_ruta', 'sin novedad')
        sistema_incendio = request.POST.get('sistema_incendio', 'sin novedad')
        soporte_municion = request.POST.get('soporte_municion', 'sin novedad')
        botellones_incendio = request.POST.get('botellones_incendio', 'sin novedad')
        vehiculo_general = request.POST.get('vehiculo_general', 'sin novedad')
        aisladores_antena = request.POST.get('aisladores_antena', 'sin novedad')
        escotilla_emergencia = request.POST.get('escotilla_emergencia', 'sin novedad')
        tablero_precaleo = request.POST.get('tablero_precaleo', 'sin novedad')
        cables_bornes_torre = request.POST.get('cables_bornes_torre', 'sin novedad')
        cables_bornes_chasis = request.POST.get('cables_bornes_chasis', 'sin novedad')
        equipos_radio = request.POST.get('equipos_radio', 'sin novedad')
        laringofonos = request.POST.get('laringofonos', 'sin novedad')
        cajas_pecho = request.POST.get('cajas_pecho', 'sin novedad')
        funcionamiento_ic = request.POST.get('funcionamiento_ic', 'sin novedad')
        comprobacion_red = request.POST.get('comprobacion_red', 'sin novedad')
        telefono_cola = request.POST.get('telefono_cola', 'sin novedad')
        aisladores_antena_comunicaciones = request.POST.get('aisladores_antena_comunicaciones', 'sin novedad')
        dispositivo_apertura = request.POST.get('dispositivo_apertura', 'sin novedad')
        frontis_lona = request.POST.get('frontis_lona', 'sin novedad')
        compensador_frenos = request.POST.get('compensador_frenos', 'sin novedad')
        extractor_gases = request.POST.get('extractor_gases', 'sin novedad')

        # Cálculo del estado del tanque
        puntuacion = (
            coeficientes[filtro_ventiladores] +
            coeficientes[filtro_combustible] +
            coeficientes[malla_filtrante] +
            coeficientes[oruga] +
            coeficientes[uniones_laterales] +
            coeficientes[ruedas_tensoras] +
            coeficientes[tapas_compartimiento] +
            coeficientes[calefactor_conductor] +
            coeficientes[freno_servicio] +
            coeficientes[asiento_ruta] +
            coeficientes[sistema_incendio] +
            coeficientes[soporte_municion] +
            coeficientes[botellones_incendio] +
            coeficientes[vehiculo_general] +
            coeficientes[aisladores_antena] +
            coeficientes[escotilla_emergencia] +
            coeficientes[tablero_precaleo] +
            coeficientes[cables_bornes_torre] +
            coeficientes[cables_bornes_chasis] +
            coeficientes[equipos_radio] +
            coeficientes[laringofonos] +
            coeficientes[cajas_pecho] +
            coeficientes[funcionamiento_ic] +
            coeficientes[comprobacion_red] +
            coeficientes[telefono_cola] +
            coeficientes[aisladores_antena_comunicaciones] +
            coeficientes[dispositivo_apertura] +
            coeficientes[frontis_lona] +
            coeficientes[compensador_frenos] +
            coeficientes[extractor_gases]
        )

        # Determinación del estado basado en la puntuación
        if puntuacion >= 15:  # Umbral para 'Fuera de servicio'
            tanque.estado = 'Fuera de servicio'
        elif 5 <= puntuacion < 15:  # Umbral para 'Servicio limitado'
            tanque.estado = 'Servicio limitado'
        else:
            tanque.estado = 'En servicio'

        tanque.save()

        return redirect('novedades_tanque', tanque_id=tanque.id)