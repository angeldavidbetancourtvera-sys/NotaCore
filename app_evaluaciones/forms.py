from django import forms
from .models import PlanEvaluacion, Actividad, Calificacion  # <-- Agregamos PlanEvaluacion aquí
from app_academico.models import AulaVirtual, Estudiante

class PlanEvaluacionForm(forms.ModelForm):
    """
    Formulario para que los profesores creen el Plan de Evaluación por Lapso.
    """
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
    estudiantes = forms.ModelMultipleChoiceField(
        queryset=Estudiante.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '8'}),
        label="Seleccionar Estudiantes",
        help_text="Mantén presionado Ctrl para seleccionar varios."
    )


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