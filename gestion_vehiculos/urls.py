from django.urls import path
from .views import UsuarioRegistroView, UsuarioLoginView, UsuarioLogoutView, IndexView, CrearRegimientoView, PerfilAdministradorView, UsuarioDeleteView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('registro/', UsuarioRegistroView.as_view(), name='registro'),
    path('login/', UsuarioLoginView.as_view(), name='login'),
    path('logout/', UsuarioLogoutView.as_view(), name='logout'),
    path('crear_regimiento/', CrearRegimientoView.as_view(), name='crear_regimiento'),
    path('perfil/', PerfilAdministradorView.as_view(), name='perfil_administrador'),
    path('usuario/<int:pk>/eliminar/', UsuarioDeleteView.as_view(), name='eliminar_usuario'),
]
