from django.urls import path

from .views import (
    AdminDashboardView,
    AulaCreateView,
    AulaDeleteView,
    AulaListView,
    AulaUpdateView,
    UsuarioDeleteView,
    UsuarioListView,
)

app_name = 'academico'

urlpatterns = [
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('aulas/', AulaListView.as_view(), name='aula_list'),
    path('aulas/nuevo/', AulaCreateView.as_view(), name='aula_create'),
    path('aulas/<int:pk>/editar/', AulaUpdateView.as_view(), name='aula_update'),
    path('aulas/<int:pk>/eliminar/', AulaDeleteView.as_view(), name='aula_delete'),
    path('usuarios/', UsuarioListView.as_view(), name='usuario_list'),
    path('usuarios/<str:pk>/eliminar/', UsuarioDeleteView.as_view(), name='usuario_delete'),
]