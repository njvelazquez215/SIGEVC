from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario

class UsuarioRegistroForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'rol', 'regimiento']

class UsuarioLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError("Cuenta desactivada", code='inactive')
