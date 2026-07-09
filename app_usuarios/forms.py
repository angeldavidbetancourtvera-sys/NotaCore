from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import Usuario


class LoginForm(AuthenticationForm):
    """
    Formulario de login adaptado para usar 'cedula' en lugar de 'username'.
    """
    cedula = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su cédula',
            'autofocus': True
        }),
        label="Cédula"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        }),
        label="Contraseña"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Eliminar el campo 'username' heredado de AuthenticationForm
        if 'username' in self.fields:
            del self.fields['username']


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

    class Meta:
        model = Usuario
        fields = ['cedula', 'email', 'nombres', 'apellidos', 'rol', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Eliminar el campo 'username' heredado de UserCreationForm
        if 'username' in self.fields:
            del self.fields['username']
