from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app_usuarios.urls', namespace='usuarios')),
    path('academico/', include('app_academico.urls', namespace='academico')),
    path('evaluaciones/', include('app_evaluaciones.urls', namespace='evaluaciones')),
    path('accounts/', include('django.contrib.auth.urls')),
]
