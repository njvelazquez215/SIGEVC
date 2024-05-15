from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario, Invitacion, Regimiento, Seccion, Escuadron


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
        user.escuadron = invitacion.escuadron  # Asignar el escuadron desde la invitación
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
    escuadron = forms.ModelChoiceField(
        queryset=Escuadron.objects.all(),  # Asegura cargar todos los escuadrones disponibles
        required=False,
        empty_label="Seleccione un escuadrón"
    )

    class Meta:
        model = Invitacion
        fields = ['email', 'rol', 'escuadron']

    def __init__(self, *args, **kwargs):
        super(InvitacionForm, self).__init__(*args, **kwargs)
        self.fields['escuadron'].queryset = Escuadron.objects.all()  # Carga inicial de todos los escuadrones

        if 'rol' in self.data:
            try:
                rol = self.data.get('rol')
                if rol in ['Jefe de Escuadrón', 'Jefe de Sección']:
                    self.fields['escuadron'].queryset = Escuadron.objects.all()
                else:
                    self.fields['escuadron'].queryset = Escuadron.objects.none()  # Vaciar si no son estos roles
            except (ValueError, TypeError):
                pass  # entrada inválida; no actualiza queryset
        elif self.instance.pk:
            self.fields['escuadron'].queryset = self.instance.escuadron_set.order_by('nombre')

class RegimientoForm(forms.ModelForm):
    class Meta:
        model = Regimiento
        fields = ['nombre', 'ubicacion']


class SeccionForm(forms.ModelForm):
    class Meta:
        model = Seccion
        fields = ['nombre', 'jefe']  # Asegúrate de que el modelo Seccion tenga estos campos