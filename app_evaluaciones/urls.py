from django.urls import path

from .views import (
    ActividadCreateView,
    ActividadDeleteView,
    ActividadUpdateView,
    AsignarEstudianteView,
    EstudianteDashboardView,
    EstudianteDetalleAulaView,
    EstudiantePreviewCalificacionesView,
    GuardarNotasView,
    MatrizNotasView,
    PlanEvaluacionCreateView,
    PlanEvaluacionDeleteView,
    PlanEvaluacionListView,
    PlanEvaluacionUpdateView,
    ProfesorDashboardView,
)

app_name = 'evaluaciones'

urlpatterns = [
    path('profesor/dashboard/', ProfesorDashboardView.as_view(), name='profesor_dashboard'),
    path('profesor/planes/', PlanEvaluacionListView.as_view(), name='profesor_planes'),
    path('profesor/planes/nuevo/', PlanEvaluacionCreateView.as_view(), name='profesor_plan_nuevo'),
    path('profesor/planes/<int:pk>/editar/', PlanEvaluacionUpdateView.as_view(), name='profesor_plan_editar'),
    path('profesor/planes/<int:pk>/eliminar/', PlanEvaluacionDeleteView.as_view(), name='profesor_plan_eliminar'),
    path('profesor/planes/<int:plan_pk>/actividades/nuevo/', ActividadCreateView.as_view(), name='profesor_actividad_nuevo'),
    path('profesor/actividades/<int:pk>/editar/', ActividadUpdateView.as_view(), name='profesor_actividad_editar'),
    path('profesor/actividades/<int:pk>/eliminar/', ActividadDeleteView.as_view(), name='profesor_actividad_eliminar'),
    path('profesor/asignar-estudiante/', AsignarEstudianteView.as_view(), name='profesor_asignar_estudiante'),
    path('profesor/matriz-notas/<int:pk_aula>/', MatrizNotasView.as_view(), name='profesor_matriz_notas'),
    path('profesor/guardar-notas/', GuardarNotasView.as_view(), name='profesor_guardar_notas'),
    path('estudiante/dashboard/', EstudianteDashboardView.as_view(), name='estudiante_dashboard'),
    path('estudiante/aula/<int:pk>/', EstudianteDetalleAulaView.as_view(), name='estudiante_aula_detalle'),
    path('estudiante/calificaciones/', EstudiantePreviewCalificacionesView.as_view(), name='estudiante_calificaciones'),
]