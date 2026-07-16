from django import forms
from django.contrib import admin

from app_usuarios.models import Usuario

from .models import AulaVirtual, Estudiante, Matricula, Profesor


class AulaVirtualAdminForm(forms.ModelForm):
    profesor = forms.ModelChoiceField(
        queryset=Usuario.objects.none(),
        label='Profesor',
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = AulaVirtual
        fields = ['año_curso', 'catedra', 'ciclo_escolar', 'profesor', 'activo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profesor'].queryset = Usuario.objects.filter(rol='PROFESOR').order_by('apellidos', 'nombres', 'cedula')
        self.fields['profesor'].label_from_instance = lambda obj: f"{obj.get_full_name()} ({obj.cedula})"
        if self.instance and self.instance.pk and self.instance.profesor_id:
            self.initial['profesor'] = self.instance.profesor.usuario

    def save(self, commit=True):
        usuario_profesor = self.cleaned_data.get('profesor')
        profesor = None
        if usuario_profesor is not None:
            profesor, _ = Profesor.objects.get_or_create(usuario=usuario_profesor)
        instance = super().save(commit=False)
        if profesor is not None:
            instance.profesor = profesor
        if commit:
            instance.save()
        return instance


@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'usuario__email', 'usuario__is_active']
    search_fields = ['usuario__cedula', 'usuario__nombres', 'usuario__apellidos']
    list_filter = ['usuario__is_active']
    
    def usuario__email(self, obj):
        return obj.usuario.email
    usuario__email.short_description = 'Email'
    
    def usuario__is_active(self, obj):
        return obj.usuario.is_active
    usuario__is_active.short_description = 'Activo'


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'representante', 'telefono_representante']
    search_fields = ['usuario__cedula', 'usuario__nombres', 'usuario__apellidos', 'representante']
    list_filter = []


@admin.register(AulaVirtual)
class AulaVirtualAdmin(admin.ModelAdmin):
    form = AulaVirtualAdminForm
    list_display = ['__str__', 'año_curso', 'ciclo_escolar', 'profesor', 'activo', 'fecha_creacion']
    search_fields = ['profesor__usuario__nombres', 'profesor__usuario__apellidos', 'ciclo_escolar']
    list_filter = ['año_curso', 'activo', 'fecha_creacion']


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'estudiante', 'aula', 'fecha_inscripcion']
    search_fields = ['estudiante__usuario__cedula', 'estudiante__usuario__nombres', 'aula__profesor__usuario__nombres']
    list_filter = ['aula__año_curso', 'fecha_inscripcion']