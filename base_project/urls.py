
from django.contrib import admin
from django.urls import path, include

from app_usuarios.views import home_view, login_view

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('usuarios/', include('app_usuarios.urls', namespace='usuarios')),
    path('academico/', include('app_academico.urls', namespace='academico')),
    path('evaluaciones/', include('app_evaluaciones.urls', namespace='evaluaciones')),
]