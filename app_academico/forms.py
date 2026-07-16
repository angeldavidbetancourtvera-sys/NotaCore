from django import forms
from django.db.models import QuerySet

from app_usuarios.models import Usuario

from .models import AulaVirtual, Profesor


class AulaVirtualForm(forms.ModelForm):
    profesor = forms.ModelChoiceField(
        queryset=Usuario.objects.none(),
        label='Profesor',
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    ciclo_escolar = forms.CharField(
        required=False,
        max_length=100,
        label='Periodo escolar',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Periodo escolar 2026-2027'}),
    )

    class Meta:
        model = AulaVirtual
        fields = ['año_curso', 'catedra', 'ciclo_escolar', 'activo']
        widgets = {
            'año_curso': forms.Select(attrs={'class': 'form-select'}),
            'catedra': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Matemáticas'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['profesor'].queryset = Usuario.objects.filter(rol='PROFESOR').order_by('apellidos', 'nombres', 'cedula')
        self.fields['profesor'].label_from_instance = lambda obj: f"{obj.get_full_name()} ({obj.cedula})"

        if self.instance and self.instance.pk and self.instance.profesor_id:
            self.initial['profesor'] = self.instance.profesor.usuario

        if self.instance and self.instance.pk and self.instance.ciclo_escolar:
            self.initial['ciclo_escolar'] = self.instance.ciclo_escolar

    def clean_ciclo_escolar(self) -> str:
        return (self.cleaned_data.get('ciclo_escolar') or '').strip()

    def save(self, commit: bool = True) -> AulaVirtual:
        usuario_profesor: Usuario | None = self.cleaned_data.get('profesor')
        profesor: Profesor | None = None
        if usuario_profesor is not None:
            profesor, _ = Profesor.objects.get_or_create(usuario=usuario_profesor)

        instance: AulaVirtual = super().save(commit=False)
        instance.ciclo_escolar = self.cleaned_data.get('ciclo_escolar') or ''
        if profesor is not None:
            instance.profesor = profesor
        if commit:
            instance.save()
        return instance


class UsuarioSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Buscar', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula, nombre o email'}))
