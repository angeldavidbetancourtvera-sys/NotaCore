from django.contrib import admin
from .models import Usuario


@admin.register(Usuario)

class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('cedula', 
                    'username', 
                    'email', 
                    'nombres', 
                    'apellidos', 
                    'is_staff')
    search_fields = ('cedula', 'username', 'email', 'nombres', 'apellidos')
