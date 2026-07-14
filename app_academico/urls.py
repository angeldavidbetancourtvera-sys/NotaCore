from django.urls import path

from .views import (
    AdminDashboardView,
    AulaCreateView,
    AulaDeleteView,
    AulaDetailView,
    AulaListView,
    AulaUpdateView,
    EstudianteDetailView,
    EstudianteListView,
    ProfesorDetailView,
    ProfesorListView,
    UsuarioDeleteView,
    UsuarioListView,
)

app_name = 'academico'

urlpatterns = [
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('aulas/', AulaListView.as_view(), name='aula_list'),
    path('aulas/<int:pk>/', AulaDetailView.as_view(), name='aula_detail'),
    path('aulas/nuevo/', AulaCreateView.as_view(), name='aula_create'),
    path('aulas/<int:pk>/editar/', AulaUpdateView.as_view(), name='aula_update'),
    path('aulas/<int:pk>/eliminar/', AulaDeleteView.as_view(), name='aula_delete'),
    path('usuarios/', UsuarioListView.as_view(), name='usuario_list'),
    path('usuarios/<str:pk>/eliminar/', UsuarioDeleteView.as_view(), name='usuario_delete'),
    path('profesores/', ProfesorListView.as_view(), name='profesor_list'),
    path('profesores/<str:pk>/', ProfesorDetailView.as_view(), name='profesor_detail'),
    path('estudiantes/', EstudianteListView.as_view(), name='estudiante_list'),
    path('estudiantes/<str:pk>/', EstudianteDetailView.as_view(), name='estudiante_detail'),
]