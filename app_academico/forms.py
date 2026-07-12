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
    lapsos = forms.MultipleChoiceField(
        required=False,
        choices=AulaVirtual.LAPSO_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label='Lapsos',
    )

    class Meta:
        model = AulaVirtual
        fields = ['año_curso', 'lapsos', 'activo']
        widgets = {
            'año_curso': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['profesor'].queryset = Usuario.objects.filter(rol='PROFESOR').order_by('apellidos', 'nombres', 'cedula')
        self.fields['profesor'].label_from_instance = lambda obj: f"{obj.get_full_name()} ({obj.cedula})"

        if self.instance and self.instance.pk and self.instance.profesor_id:
            self.initial['profesor'] = self.instance.profesor.usuario

        if self.instance and self.instance.pk and self.instance.lapsos:
            initial_lapsos = self.instance.lapsos if isinstance(self.instance.lapsos, list) else [self.instance.lapsos]
            self.fields['lapsos'].initial = initial_lapsos

    def clean_lapsos(self) -> list[str]:
        lapsos = self.cleaned_data.get('lapsos') or []
        return list(lapsos)

    def save(self, commit: bool = True) -> AulaVirtual:
        usuario_profesor: Usuario | None = self.cleaned_data.get('profesor')
        profesor: Profesor | None = None
        if usuario_profesor is not None:
            profesor, _ = Profesor.objects.get_or_create(usuario=usuario_profesor)

        instance: AulaVirtual = super().save(commit=False)
        instance.lapsos = self.cleaned_data.get('lapsos') or []
        if profesor is not None:
            instance.profesor = profesor
        if commit:
            instance.save()
        return instance


class UsuarioSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Buscar', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula, nombre o email'}))
