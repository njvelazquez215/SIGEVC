from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario, Invitacion

class UsuarioRegistroForm(UserCreationForm):
    token = forms.UUIDField()

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_token(self):
        token = self.cleaned_data.get('token')
        invitacion = Invitacion.objects.filter(token=token, usado=False).first()
        if not invitacion:
            raise forms.ValidationError("Invitación inválida o ya utilizada.")
        return token

    def save(self, commit=True):
        user = super().save(commit=False)
        token = self.cleaned_data.get('token')
        invitacion = Invitacion.objects.get(token=token)
        user.regimiento = invitacion.regimiento
        user.rol = invitacion.rol
        if commit:
            user.save()
            invitacion.usado = True
            invitacion.save()
        return user

class UsuarioLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError("Cuenta desactivada", code='inactive')

class InvitacionForm(forms.ModelForm):
    class Meta:
        model = Invitacion
        fields = ['email', 'regimiento', 'rol']