from django.urls import path
from .views import UsuarioRegistroView, UsuarioLoginView, UsuarioLogoutView, index

urlpatterns = [
    path('', index, name='index'),
    path('registro/', UsuarioRegistroView.as_view(), name='registro'),
    path('login/', UsuarioLoginView.as_view(), name='login'),
    path('logout/', UsuarioLogoutView.as_view(), name='logout'),
]
