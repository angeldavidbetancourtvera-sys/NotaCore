from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from app_academico.models import AulaVirtual, Estudiante, Matricula

from .models import Actividad, Calificacion, PlanEvaluacion


class PlanEvaluacionForm(forms.ModelForm):
    class Meta:
        model = PlanEvaluacion
        fields = ['aula', 'lapso', 'objetivo', 'metodo', 'puntuacion_max', 'activo']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None and getattr(user, 'rol', None) == 'PROFESOR':
            self.fields['aula'].queryset = AulaVirtual.objects.filter(profesor__usuario=user)

    def clean_puntuacion_max(self):
        puntuacion_max = self.cleaned_data.get('puntuacion_max')
        if puntuacion_max is not None and puntuacion_max > Decimal('20.00'):
            raise ValidationError('La puntuación máxima no puede exceder 20 puntos.')
        return puntuacion_max

    def clean(self):
        cleaned_data = super().clean()
        aula = cleaned_data.get('aula')
        lapso = cleaned_data.get('lapso')
        puntuacion_max = cleaned_data.get('puntuacion_max')

        if not aula or not lapso or puntuacion_max is None:
            return cleaned_data

        planes_existentes = PlanEvaluacion.objects.filter(aula=aula, lapso=lapso)
        if self.instance.pk:
            planes_existentes = planes_existentes.exclude(pk=self.instance.pk)

        total_actual = sum((plan.puntuacion_max or Decimal('0.00')) for plan in planes_existentes)
        if total_actual + puntuacion_max > Decimal('20.00'):
            self.add_error(
                'puntuacion_max',
                'La suma de las puntuaciones máximas de los planes para este lapso no puede exceder 20 puntos.',
            )

        return cleaned_data


class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['titulo', 'fecha', 'puntuacion', 'descripcion']

    def __init__(self, *args, plan=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.plan = plan

    def clean_puntuacion(self):
        puntuacion = self.cleaned_data.get('puntuacion')
        if self.plan is not None and puntuacion is not None and puntuacion > self.plan.puntuacion_max:
            raise ValidationError(
                f'La puntuación no puede exceder el límite del plan ({self.plan.puntuacion_max}).'
            )
        return puntuacion


class CalificacionForm(forms.ModelForm):
    class Meta:
        model = Calificacion
        fields = ['nota_obtenida', 'observacion']


class AsignarEstudianteForm(forms.Form):
    estudiante = forms.ModelChoiceField(
        queryset=Estudiante.objects.none(),
        label='Estudiante',
        required=True,
    )

    def __init__(self, *args, aula=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.aula = aula
        if aula is not None:
            self.fields['estudiante'].queryset = (
                Estudiante.objects.exclude(matriculas__aula=aula)
                .select_related('usuario')
                .order_by('usuario__nombres', 'usuario__apellidos')
            )
        else:
            self.fields['estudiante'].queryset = Estudiante.objects.select_related('usuario').order_by('usuario__nombres', 'usuario__apellidos')

    def save(self, commit=True):
        if self.aula is None:
            raise ValueError('Se requiere un aula para asignar el estudiante.')

        matricula = Matricula(estudiante=self.cleaned_data['estudiante'], aula=self.aula)
        if commit:
            matricula.save()
        return matricula
