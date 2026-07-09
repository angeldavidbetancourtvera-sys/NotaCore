from django.contrib import admin
from .models import PlanEvaluacion, Actividad, Calificacion


@admin.register(PlanEvaluacion)
class PlanEvaluacionAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'aula', 'lapso', 'puntuacion_max', 'activo']
    search_fields = ['objetivo', 'aula__profesor__usuario__nombres']
    list_filter = ['lapso', 'activo', 'aula__año_curso']


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'plan', 'fecha', 'puntuacion']
    search_fields = ['titulo', 'plan__objetivo']
    list_filter = ['fecha', 'plan__lapso']


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'actividad', 'estudiante', 'nota_obtenida', 'fecha_registro']
    search_fields = ['estudiante__usuario__cedula', 'estudiante__usuario__nombres', 'actividad__titulo']
    list_filter = ['fecha_registro', 'actividad__plan__lapso']