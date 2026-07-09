from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    # 1. Definimos los grupos de campos para la edición (quitando 'username')
    fieldsets = (
        (None, {'fields': ('cedula', 'password')}),
        ('Información personal', {'fields': ('nombres', 'apellidos', 'email', 'rol')}),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )

    # 2. Definimos los campos para la creación de nuevos usuarios
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('cedula', 'nombres', 'apellidos', 'email', 'rol', 'password1', 'password2'),
        }),
    )

    # 3. Configuración de la lista (quitando 'username')
    list_display = ('cedula', 'nombres', 'apellidos', 'email', 'rol', 'is_staff')
    search_fields = ('cedula', 'nombres', 'apellidos', 'email')
    ordering = ('cedula',)  