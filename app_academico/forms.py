from django import forms
from .models import AulaVirtual
from app_usuarios.models import Usuario


class AulaVirtualForm(forms.ModelForm):
    lapsos = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. I, II, III'}),
        label='Lapsos',
    )

    class Meta:
        model = AulaVirtual
        fields = ['año_curso', 'lapsos', 'profesor', 'activo']
        widgets = {
            'año_curso': forms.Select(attrs={'class': 'form-select'}),
            'profesor': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.lapsos:
            self.fields['lapsos'].initial = ', '.join(self.instance.lapsos) if isinstance(self.instance.lapsos, list) else self.instance.lapsos

    def clean_lapsos(self):
        lapsos = self.cleaned_data.get('lapsos')
        if isinstance(lapsos, str):
            return [item.strip() for item in lapsos.split(',') if item.strip()]
        return lapsos

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.lapsos = self.cleaned_data.get('lapsos') or []
        if commit:
            instance.save()
        return instance


class UsuarioSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Buscar', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula, nombre o email'}))
