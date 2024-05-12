from django.urls import path
from .views import (UsuarioRegistroView, UsuarioLoginView, UsuarioLogoutView,
                    IndexView, CrearRegimientoView, PerfilAdministradorView, UsuarioDeleteView, EscuadronView,
                    SeccionCreateView, SeccionUpdateView, SeccionDeleteView)
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
    path('escuadron/<int:escuadron_id>/', EscuadronView.as_view(), name='ver_escuadron'),
    path('escuadron/<int:escuadron_id>/nueva-seccion/', SeccionCreateView.as_view(), name='nueva_seccion'),
    path('seccion/<int:pk>/editar/', SeccionUpdateView.as_view(), name='editar_seccion'),
    path('seccion/<int:pk>/eliminar/', SeccionDeleteView.as_view(), name='eliminar_seccion'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
