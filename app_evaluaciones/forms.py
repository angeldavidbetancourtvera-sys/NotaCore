from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from app_academico.models import AulaVirtual, Estudiante, Matricula

from .models import Actividad, Calificacion, PlanEvaluacion


class PlanEvaluacionForm(forms.ModelForm):
    class Meta:
        model = PlanEvaluacion
        fields = ['aula', 'lapso', 'objetivo', 'metodo', 'puntuacion_max']

    def __init__(self, *args, user=None, **kwargs) -> None:
        self.user = user
        super().__init__(*args, **kwargs)
        if self.user and getattr(self.user, 'rol', None) == 'PROFESOR':
            self.fields['aula'].queryset = AulaVirtual.objects.filter(
                profesor__usuario=self.user,
                activo=True,
            ).order_by('año_curso')
        else:
            self.fields['aula'].queryset = AulaVirtual.objects.filter(activo=True).order_by('año_curso')

    def clean_puntuacion_max(self) -> Decimal:
        puntuacion_max = self.cleaned_data.get('puntuacion_max')
        if puntuacion_max is None:
            raise forms.ValidationError('La puntuación es obligatoria.')
        if puntuacion_max > Decimal('20.00'):
            raise forms.ValidationError('La puntuación máxima no puede superar 20 puntos.')
        return puntuacion_max

    def clean(self) -> dict:
        cleaned_data = super().clean()
        aula = cleaned_data.get('aula')
        lapso = cleaned_data.get('lapso')
        puntuacion_max = cleaned_data.get('puntuacion_max')

        if aula and lapso and puntuacion_max is not None:
            planes_activos = PlanEvaluacion.objects.filter(aula=aula, lapso=lapso, activo=True)
            if self.instance.pk:
                planes_activos = planes_activos.exclude(pk=self.instance.pk)

            total_actual = sum((plan.puntuacion_max for plan in planes_activos), Decimal('0.00'))
            if total_actual + puntuacion_max > Decimal('20.00'):
                raise ValidationError({
                    'puntuacion_max': (
                        'La suma de planes activos del mismo aula y lapso no puede exceder 20 puntos.'
                    )
                })

        return cleaned_data


class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['titulo', 'fecha', 'puntuacion', 'descripcion']

    def __init__(self, *args, plan=None, **kwargs) -> None:
        self.plan = plan
        super().__init__(*args, **kwargs)
        if self.plan is not None:
            self.instance.plan = self.plan
            self.fields['puntuacion'].help_text = f'Máximo permitido: {self.plan.puntuacion_max}'

    def clean_puntuacion(self) -> Decimal:
        puntuacion = self.cleaned_data.get('puntuacion')
        if puntuacion is None:
            raise forms.ValidationError('La puntuación es obligatoria.')
        if self.plan is not None and puntuacion > self.plan.puntuacion_max:
            raise forms.ValidationError(
                f'La puntuación no puede exceder {self.plan.puntuacion_max} puntos.'
            )
        return puntuacion

    def clean(self) -> dict:
        cleaned_data = super().clean()
        if self.plan is None:
            return cleaned_data
        if cleaned_data.get('puntuacion') and cleaned_data.get('puntuacion') > self.plan.puntuacion_max:
            raise ValidationError({'puntuacion': f'La puntuación no puede exceder {self.plan.puntuacion_max} puntos.'})
        return cleaned_data


class AsignarEstudianteForm(forms.Form):
    cedula_estudiante = forms.CharField(label='Cédula del estudiante', max_length=20)

    def __init__(self, *args, aula=None, **kwargs) -> None:
        self.aula = aula
        super().__init__(*args, **kwargs)

    def clean_cedula_estudiante(self) -> str:
        cedula = self.cleaned_data['cedula_estudiante'].strip()
        estudiante = Estudiante.objects.filter(usuario__cedula=cedula).first()
        if estudiante is None:
            raise forms.ValidationError('No existe un estudiante con esa cédula.')
        self.cleaned_data['estudiante'] = estudiante
        return cedula

    def save(self) -> Estudiante:
        estudiante = self.cleaned_data['estudiante']
        if self.aula is not None:
            Matricula.objects.get_or_create(estudiante=estudiante, aula=self.aula)
        return estudiante


class CalificacionForm(forms.ModelForm):
    class Meta:
        model = Calificacion
        fields = ['nota_obtenida', 'observacion']

    def __init__(self, *args, actividad=None, **kwargs) -> None:
        self.actividad = actividad
        super().__init__(*args, **kwargs)

    def clean_nota_obtenida(self) -> Decimal:
        nota = self.cleaned_data.get('nota_obtenida')
        if nota is None:
            raise forms.ValidationError('La nota es obligatoria.')
        if self.actividad is not None and nota > self.actividad.puntuacion:
            raise forms.ValidationError(
                f'La nota no puede exceder {self.actividad.puntuacion} puntos.'
            )
        return nota
