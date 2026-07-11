from django import forms
from django.core.exceptions import ValidationError
from django.db import models

from .models import PlanEvaluacion, Actividad, Calificacion
from app_academico.models import AulaVirtual, Estudiante, Matricula
from app_usuarios.models import Usuario


class PlanEvaluacionForm(forms.ModelForm):
    """
    Formulario para que los profesores creen el Plan de Evaluación por Lapso.
    """

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        aulas = AulaVirtual.objects.all()
        if self.user and getattr(self.user, 'rol', '') == 'PROFESOR':
            aulas = aulas.filter(profesor__usuario=self.user)

        self.fields['aula'].queryset = aulas
        self.fields['aula'].empty_label = 'Seleccione un aula'

    def clean(self):
        cleaned_data = super().clean()
        aula = cleaned_data.get('aula')
        puntuacion_max = cleaned_data.get('puntuacion_max')
        lapso = cleaned_data.get('lapso')

        if aula and puntuacion_max is not None:
            existing_total = PlanEvaluacion.objects.filter(aula=aula).exclude(pk=self.instance.pk)
            existing_total = existing_total.aggregate(total=models.Sum('puntuacion_max'))['total'] or 0
            if float(existing_total) + float(puntuacion_max) > 20:
                self.add_error('puntuacion_max', 'La suma de los planes de evaluación del aula no puede superar 20 puntos.')

        return cleaned_data

    class Meta:
        model = PlanEvaluacion
        fields = ['aula', 'lapso', 'objetivo', 'metodo', 'puntuacion_max', 'activo']

        widgets = {
            'aula': forms.Select(attrs={'class': 'form-select'}),
            'lapso': forms.Select(attrs={'class': 'form-select'}),
            'objetivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ej. Desarrollar ecuaciones de segundo grado...'}),
            'metodo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Exposición, Taller, Prueba Escrita...'}),
            'puntuacion_max': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Máximo 20.00'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ActividadForm(forms.ModelForm):
    """
    Formulario adaptado a los campos reales del modelo Actividad.
    """

    def __init__(self, *args, **kwargs):
        self.plan = kwargs.pop('plan', None)
        super().__init__(*args, **kwargs)

        if self.plan is not None:
            self.fields['plan'].required = False
            self.fields['plan'].widget = forms.HiddenInput()
            self.fields['plan'].initial = self.plan
            self.fields['plan'].queryset = PlanEvaluacion.objects.filter(pk=self.plan.pk)
        else:
            self.fields['plan'].queryset = PlanEvaluacion.objects.all()

    def clean_puntuacion(self):
        puntuacion = self.cleaned_data.get('puntuacion')
        plan = self.plan or self.cleaned_data.get('plan')
        if puntuacion is not None and plan is not None and puntuacion > plan.puntuacion_max:
            raise ValidationError(f'La actividad no puede superar los {plan.puntuacion_max} puntos del plan.')
        return puntuacion

    class Meta:
        model = Actividad
        fields = ['plan', 'titulo', 'fecha', 'puntuacion', 'descripcion']

        widgets = {
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Examen de Álgebra'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'puntuacion': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ej. 20.00'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalles de la actividad...'}),
        }


class AsignarEstudianteForm(forms.Form):
    """
    Formulario para asignar estudiantes a un Aula Virtual específica.
    """
    aula = forms.ModelChoiceField(
        queryset=AulaVirtual.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Aula Virtual"
    )
    cedula_search = forms.CharField(
        required=False,
        label="Buscar por cédula",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese la cédula'})
    )
    estudiantes = forms.ModelMultipleChoiceField(
        queryset=Usuario.objects.filter(rol='ESTUDIANTE'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '8'}),
        label="Seleccionar Estudiantes",
        help_text="Mantén presionado Ctrl para seleccionar varios."
    )

    def __init__(self, *args, **kwargs):
        self.aula = kwargs.pop('aula', None)
        self.cedula_search_value = kwargs.pop('cedula_search', '')
        super().__init__(*args, **kwargs)
        if self.aula is not None:
            self.fields['aula'].initial = self.aula
            self.fields['aula'].queryset = AulaVirtual.objects.filter(pk=self.aula.pk)
        self.fields['cedula_search'].initial = self.cedula_search_value

        queryset = Usuario.objects.filter(rol='ESTUDIANTE').order_by('apellidos', 'nombres')
        if self.cedula_search_value:
            queryset = queryset.filter(cedula__icontains=self.cedula_search_value)
        if self.aula is not None:
            queryset = queryset.exclude(estudiante__matriculas__aula=self.aula)
        self.fields['estudiantes'].queryset = queryset

    def save(self):
        aula = self.cleaned_data['aula']
        usuarios_estudiantes = self.cleaned_data['estudiantes']
        creados = []
        for usuario in usuarios_estudiantes:
            estudiante, _ = Estudiante.objects.get_or_create(
                usuario=usuario,
                defaults={'representante': '', 'telefono_representante': ''},
            )
            matricula, created = Matricula.objects.get_or_create(estudiante=estudiante, aula=aula)
            if created:
                creados.append(matricula)
        return creados


class CalificacionForm(forms.ModelForm):
    """
    Formulario adaptado para registrar y editar notas de estudiantes.
    """
    class Meta:
        model = Calificacion
        fields = ['actividad', 'estudiante', 'nota_obtenida', 'observacion']
        
        widgets = {
            'actividad': forms.Select(attrs={'class': 'form-select'}),
            'estudiante': forms.Select(attrs={'class': 'form-select'}),
            'nota_obtenida': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ej. 18.50'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Comentarios sobre la nota...'}),
        }