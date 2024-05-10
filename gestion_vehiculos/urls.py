from django.urls import path
from .views import UsuarioRegistroView, UsuarioLoginView, UsuarioLogoutView, index, enviar_invitacion, crear_regimiento, perfil_administrador

urlpatterns = [
    path('', index, name='index'),
    path('registro/', UsuarioRegistroView.as_view(), name='registro'),
    path('login/', UsuarioLoginView.as_view(), name='login'),
    path('logout/', UsuarioLogoutView.as_view(), name='logout'),
    path('enviar_invitacion/', enviar_invitacion, name='enviar_invitacion'),
    path('crear_regimiento/', crear_regimiento, name='crear_regimiento'),
    path('admin/perfil/', perfil_administrador, name='perfil_administrador'),
]
