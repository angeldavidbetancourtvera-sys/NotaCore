from django import forms

from .models import AulaVirtual
from app_usuarios.models import Usuario


class AulaVirtualForm(forms.ModelForm):
    class Meta:
        model = AulaVirtual
        fields = ['año_curso', 'lapsos', 'profesor', 'activo']
        widgets = {
            'lapsos': forms.TextInput(attrs={'class': 'form-control'}),
            'año_curso': forms.Select(attrs={'class': 'form-select'}),
            'profesor': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_lapsos(self):
        lapsos = self.cleaned_data.get('lapsos')
        if isinstance(lapsos, str):
            return [item.strip() for item in lapsos.split(',') if item.strip()]
        return lapsos


class UsuarioSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Buscar', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula, nombre o email'}))
