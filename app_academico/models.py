from django.db import models
from django.conf import settings
from typing import Optional
import json


class Profesor(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'PROFESOR'},
        primary_key=True,
        related_name='profesor'
    )
    
    def __str__(self) -> str:
        return self.usuario.get_full_name()
    
    class Meta:
        db_table = 'profesores'


class Estudiante(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'ESTUDIANTE'},
        primary_key=True,
        related_name='estudiante'
    )
    representante = models.CharField(max_length=200)
    telefono_representante = models.CharField(max_length=20)
    
    def __str__(self) -> str:
        return self.usuario.get_full_name()
    
    class Meta:
        db_table = 'estudiantes'


class AulaVirtual(models.Model):
    año_curso = models.IntegerField(choices=[(i, f'{i}° Año') for i in range(1, 6)])
    lapsos = models.JSONField(default=list)  # ['I', 'II', 'III']
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, related_name='aulas')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return f"{self.año_curso}° Año - {self.profesor.usuario.get_full_name()}"
    
    def get_lapsos_display(self) -> str:
        lapsos = self.lapsos
        if lapsos is None:
            return 'Sin lapsos'
        if isinstance(lapsos, str):
            return lapsos
        if isinstance(lapsos, (list, tuple, set)):
            valores = []
            for item in lapsos:
                if item is None:
                    continue
                if isinstance(item, str):
                    valores.append(item)
                else:
                    valores.append(str(item))
            return ', '.join(valores) if valores else 'Sin lapsos'
        if isinstance(lapsos, dict):
            return ', '.join(str(value) for value in lapsos.values()) if lapsos else 'Sin lapsos'
        return str(lapsos)
    
    class Meta:
        db_table = 'aulas_virtuales'
        ordering = ['-fecha_creacion']


class Matricula(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='matriculas')
    aula = models.ForeignKey(AulaVirtual, on_delete=models.CASCADE, related_name='matriculas')
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return f"{self.estudiante.usuario.get_full_name()} - {self.aula}"
    
    class Meta:
        db_table = 'matriculas'
        unique_together = ['estudiante', 'aula']
        ordering = ['-fecha_inscripcion']