from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import Usuario


class LoginForm(AuthenticationForm):
    """
    Formulario de login adaptado para usar 'cedula' en lugar de 'username'.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        }),
        label="Contraseña"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Cédula"
        self.fields['username'].widget = forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su cédula',
            'autofocus': True
        })


class UsuarioRegistroForm(UserCreationForm):
    """
    Formulario de registro adaptado para usar 'cedula' en lugar de 'username'.
    """
    cedula = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su cédula'
        }),
        label="Cédula"
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su email'
        }),
        label="Email"
    )
    nombres = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese sus nombres'
        }),
        label="Nombres"
    )
    apellidos = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese sus apellidos'
        }),
        label="Apellidos"
    )
    rol = forms.ChoiceField(
        choices=Usuario.ROL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Rol"
    )
    clave_maestra = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese la clave maestra'}),
        label='Clave maestra'
    )

    class Meta:
        model = Usuario
        fields = ['cedula', 'email', 'nombres', 'apellidos', 'rol', 'clave_maestra', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get('rol')
        clave_maestra = cleaned_data.get('clave_maestra', '')
        if rol in {'ADMIN', 'PROFESOR'} and clave_maestra != getattr(settings, 'CLAVE_ADMINISTRATIVA_MAESTRA', ''):
            self.add_error('clave_maestra', 'La clave maestra es obligatoria para este rol.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = self.cleaned_data.get('rol', user.rol)
        if commit:
            user.save()
        return user
