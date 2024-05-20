from django.urls import path
from .views import (UsuarioRegistroView, UsuarioLoginView, UsuarioLogoutView, IndexView, CrearRegimientoView,
                    PerfilAdministradorView, UsuarioDeleteView, DashboardEscuadronView, EscuadronConfigView,
                    SeccionCreateView, SeccionUpdateView, SeccionDeleteView, DashboardSeccionView, VerTanqueView,
                    EditarTanqueView, EliminarTanqueView, NovedadesTanqueView)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('registro/', UsuarioRegistroView.as_view(), name='registro'),
    path('login/', UsuarioLoginView.as_view(), name='login'),
    path('logout/', UsuarioLogoutView.as_view(), name='logout'),
    path('crear_regimiento/', CrearRegimientoView.as_view(), name='crear_regimiento'),
    path('perfil/', PerfilAdministradorView.as_view(), name='perfil_administrador'),
    path('usuario/<int:pk>/eliminar/', UsuarioDeleteView.as_view(), name='eliminar_usuario'),
    path('escuadron/<int:escuadron_id>/dashboard/', DashboardEscuadronView.as_view(), name='dashboard_escuadron'),
    path('escuadron/<int:escuadron_id>/config/', EscuadronConfigView.as_view(), name='escuadron_config'),
    path('escuadron/<int:escuadron_id>/nueva-seccion/', SeccionCreateView.as_view(), name='nueva_seccion'),
    path('seccion/<int:pk>/editar/', SeccionUpdateView.as_view(), name='editar_seccion'),
    path('seccion/<int:pk>/eliminar/', SeccionDeleteView.as_view(), name='eliminar_seccion'),
    path('seccion/<int:seccion_id>/dashboard/', DashboardSeccionView.as_view(), name='dashboard_seccion'),
    path('tanque/<int:tanque_id>/ver/', VerTanqueView.as_view(), name='ver_tanque'),
    path('tanque/<int:pk>/editar/', EditarTanqueView.as_view(), name='editar_tanque'),
    path('tanque/<int:pk>/eliminar/', EliminarTanqueView.as_view(), name='eliminar_tanque'),
    path('tanque/<int:tanque_id>/novedades/', NovedadesTanqueView.as_view(), name='novedades_tanque'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)