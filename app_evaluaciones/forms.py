from decimal import Decimal
from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.db import models

from app_academico.models import AulaVirtual, Estudiante, Matricula
from app_usuarios.models import Usuario

from .models import Actividad, Calificacion, PlanEvaluacion


class PlanEvaluacionForm(forms.ModelForm):
    """Formulario para crear planes con una tabla editable de objetivos y ponderaciones."""

    aula = forms.ModelChoiceField(queryset=AulaVirtual.objects.none(), label='Aula actual', required=True)
    lapso = forms.ChoiceField(choices=[('I', 'I Lapso'), ('II', 'II Lapso'), ('III', 'III Lapso')], label='Lapso', required=True)
    activo = forms.BooleanField(required=False, initial=True, label='Activo')
    objetivo = forms.CharField(required=False, widget=forms.HiddenInput())
    metodo = forms.CharField(required=False, widget=forms.HiddenInput())
    puntuacion_max = forms.DecimalField(required=False, label='Puntuación total', widget=forms.HiddenInput())

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.user = kwargs.pop('user', None)
        self.aula_context = kwargs.pop('aula_context', None)
        super().__init__(*args, **kwargs)

        aulas = AulaVirtual.objects.all()
        if self.user and getattr(self.user, 'rol', '') == 'PROFESOR':
            aulas = aulas.filter(profesor__usuario=self.user)

        if self.aula_context is not None:
            self.fields['aula'].initial = self.aula_context
            self.fields['aula'].queryset = AulaVirtual.objects.filter(pk=self.aula_context.pk)
            self.fields['aula'].widget = forms.HiddenInput()
            used_lapsos = set(
                PlanEvaluacion.objects.filter(aula=self.aula_context).values_list('lapso', flat=True)
            )
            available_lapsos = [
                (value, label)
                for value, label in self.fields['lapso'].choices
                if value not in used_lapsos
            ]
            self.fields['lapso'].choices = available_lapsos
            if not available_lapsos:
                self.fields['lapso'].choices = [('', 'No hay lapsos disponibles')]
        else:
            self.fields['aula'].queryset = aulas
            self.fields['aula'].empty_label = 'Seleccione un aula'
            self.fields['aula'].widget.attrs.update({'class': 'form-select'})

        self.fields['lapso'].widget.attrs.update({'class': 'form-select'})
        self.fields['activo'].widget.attrs.update({'class': 'form-check-input'})

        for index in range(1, 7):
            self.fields[f'objetivo_{index}'] = forms.CharField(required=False, max_length=500, label='Objetivo', widget=forms.TextInput(attrs={'class': 'form-control'}))
            self.fields[f'metodo_{index}'] = forms.CharField(required=False, max_length=150, label='Método', widget=forms.TextInput(attrs={'class': 'form-control'}))
            self.fields[f'puntuacion_{index}'] = forms.DecimalField(required=False, min_value=0, max_value=20, max_digits=4, decimal_places=2, label='Puntos', widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))

        if self.instance and self.instance.pk:
            self.fields['objetivo_1'].initial = self.instance.objetivo
            self.fields['metodo_1'].initial = self.instance.metodo
            self.fields['puntuacion_1'].initial = self.instance.puntuacion_max
            if self.instance.objetivos_detallados:
                for index, row in enumerate(self.instance.objetivos_detallados[:6], start=1):
                    self.fields[f'objetivo_{index}'].initial = row[0] if len(row) > 0 else ''
                    self.fields[f'metodo_{index}'].initial = row[1] if len(row) > 1 else ''
                    self.fields[f'puntuacion_{index}'].initial = row[2] if len(row) > 2 else ''

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        aula = cleaned_data.get('aula')
        total = Decimal('0.00')
        rows: list[tuple[str, str, Decimal]] = []

        for index in range(1, 7):
            objetivo = (cleaned_data.get(f'objetivo_{index}', '') or '').strip()
            metodo = (cleaned_data.get(f'metodo_{index}', '') or '').strip()
            puntuacion = cleaned_data.get(f'puntuacion_{index}')
            if objetivo or metodo or puntuacion is not None:
                if not objetivo:
                    self.add_error(f'objetivo_{index}', 'El objetivo es obligatorio si se registra una fila.')
                if not metodo:
                    self.add_error(f'metodo_{index}', 'El método es obligatorio si se registra una fila.')
                if puntuacion is None:
                    self.add_error(f'puntuacion_{index}', 'La ponderación es obligatoria si se registra una fila.')
                else:
                    total += Decimal(str(puntuacion))
                    rows.append((objetivo, metodo, Decimal(str(puntuacion))))

        if not rows:
            legacy_objetivo = (cleaned_data.get('objetivo') or '').strip()
            legacy_metodo = (cleaned_data.get('metodo') or '').strip()
            legacy_puntuacion = cleaned_data.get('puntuacion_max')
            if legacy_objetivo or legacy_metodo or legacy_puntuacion is not None:
                rows.append((legacy_objetivo, legacy_metodo, Decimal(str(legacy_puntuacion or 0))))
                total = Decimal(str(legacy_puntuacion or 0))

        if len(rows) > 6:
            self.add_error('objetivo_1', 'No puede registrar más de 6 objetivos.')
        if total != Decimal('20.00'):
            self.add_error('puntuacion_max', 'La suma de las ponderaciones debe dar exactamente 20 puntos.')

        if aula is not None:
            lapso = cleaned_data.get('lapso')
            existing_lapso = PlanEvaluacion.objects.filter(aula=aula, lapso=lapso).exclude(pk=self.instance.pk).exists()
            if existing_lapso:
                self.add_error('lapso', 'Ya existe un plan de evaluación para este lapso en el aula seleccionada.')

            if total > Decimal('20.00'):
                self.add_error('puntuacion_max', 'La suma de las ponderaciones debe dar exactamente 20 puntos.')

        cleaned_data['puntuacion_max'] = total
        return cleaned_data

    def save(self, commit: bool = True) -> PlanEvaluacion:
        instance: PlanEvaluacion = super().save(commit=False)
        rows: list[tuple[str, str, Decimal]] = []
        total = Decimal('0.00')
        for index in range(1, 7):
            objetivo = (self.cleaned_data.get(f'objetivo_{index}', '') or '').strip()
            metodo = (self.cleaned_data.get(f'metodo_{index}', '') or '').strip()
            puntuacion = self.cleaned_data.get(f'puntuacion_{index}')
            if not objetivo and not metodo and puntuacion is None:
                continue
            if objetivo and metodo and puntuacion is not None:
                rows.append((objetivo, metodo, Decimal(str(puntuacion))))
                total += Decimal(str(puntuacion))

        if not rows:
            legacy_objetivo = (self.cleaned_data.get('objetivo') or '').strip()
            legacy_metodo = (self.cleaned_data.get('metodo') or '').strip()
            legacy_puntuacion = self.cleaned_data.get('puntuacion_max')
            if legacy_objetivo or legacy_metodo or legacy_puntuacion is not None:
                rows.append((legacy_objetivo, legacy_metodo, Decimal(str(legacy_puntuacion or 0))))
                total = Decimal(str(legacy_puntuacion or 0))

        if not rows:
            instance.objetivo = ''
            instance.metodo = ''
            instance.puntuacion_max = Decimal('0.00')
            instance.objetivos_detallados = []
        else:
            first_row = rows[0]
            instance.objetivo = first_row[0]
            instance.metodo = first_row[1]
            instance.puntuacion_max = total
            serializable_rows: list[list[Any]] = []
            for objetivo, metodo, puntuacion in rows:
                serializable_rows.append([
                    objetivo,
                    metodo,
                    float(puntuacion),
                ])
            instance.objetivos_detallados = serializable_rows
        if commit:
            instance.save()
        return instance

    class Meta:
        model = PlanEvaluacion
        fields = ['aula', 'lapso', 'activo']


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