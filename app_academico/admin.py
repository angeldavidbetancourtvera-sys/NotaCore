from django.contrib import admin
from .models import Profesor, Estudiante, AulaVirtual, Matricula


@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'usuario__email', 'usuario__is_active']
    search_fields = ['usuario__cedula', 'usuario__nombres', 'usuario__apellidos']
    list_filter = ['usuario__is_active']
    
    def usuario__email(self, obj):
        return obj.usuario.email
    usuario__email.short_description = 'Email'
    
    def usuario__is_active(self, obj):
        return obj.usuario.is_active
    usuario__is_active.short_description = 'Activo'


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'representante', 'telefono_representante']
    search_fields = ['usuario__cedula', 'usuario__nombres', 'usuario__apellidos', 'representante']
    list_filter = []


@admin.register(AulaVirtual)
class AulaVirtualAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'año_curso', 'get_lapsos_display', 'profesor', 'activo', 'fecha_creacion']
    search_fields = ['profesor__usuario__nombres', 'profesor__usuario__apellidos']
    list_filter = ['año_curso', 'activo', 'fecha_creacion']
    
    def get_lapsos_display(self, obj):
        return ', '.join(obj.lapsos) if obj.lapsos else 'Sin lapsos'
    get_lapsos_display.short_description = 'Lapsos'


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'estudiante', 'aula', 'fecha_inscripcion']
    search_fields = ['estudiante__usuario__cedula', 'estudiante__usuario__nombres', 'aula__profesor__usuario__nombres']
    list_filter = ['aula__año_curso', 'fecha_inscripcion']