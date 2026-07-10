from django.db import models
from django.core.exceptions import ValidationError
from app_academico.models import AulaVirtual, Estudiante
from typing import Optional
from decimal import Decimal


class PlanEvaluacion(models.Model):
    aula = models.ForeignKey(AulaVirtual, on_delete=models.CASCADE, related_name='planes')
    lapso = models.CharField(
        max_length=10,
        choices=[('I', 'I Lapso'), ('II', 'II Lapso'), ('III', 'III Lapso')]
    )
    objetivo = models.TextField()
    metodo = models.CharField(max_length=100)
    puntuacion_max = models.DecimalField(max_digits=4, decimal_places=2)
    activo = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.aula} - {self.get_lapso_display()} - {self.objetivo[:30]}"

    class Meta:
        db_table = 'planes_evaluacion'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(puntuacion_max__lte=20),
                name='puntuacion_max_menor_igual_20'
            )
        ]


class Actividad(models.Model):
    plan = models.ForeignKey(PlanEvaluacion, on_delete=models.CASCADE, related_name='actividades')
    titulo = models.CharField(max_length=200)
    fecha = models.DateField()
    puntuacion = models.DecimalField(max_digits=4, decimal_places=2)
    descripcion = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.titulo} - {self.puntuacion} pts"

    def clean(self) -> None:
        if self.plan_id is None:
            return
        if self.puntuacion is not None and self.puntuacion > self.plan.puntuacion_max:
            raise ValidationError(
                f"La puntuación no puede exceder {self.plan.puntuacion_max}"
            )

    class Meta:
        db_table = 'actividades'
        ordering = ['fecha']


class Calificacion(models.Model):
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='calificaciones')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='calificaciones')
    nota_obtenida = models.DecimalField(max_digits=4, decimal_places=2)
    observacion = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.estudiante.usuario.get_full_name()} - {self.actividad.titulo}: {self.nota_obtenida}"

    def clean(self) -> None:
        super().clean()
        if self.actividad_id and self.nota_obtenida is not None:
            if self.nota_obtenida > self.actividad.puntuacion:
                raise ValidationError({
                    'nota_obtenida': (
                        f"La nota ({self.nota_obtenida}) no puede exceder "
                        f"la puntuación de la actividad ({self.actividad.puntuacion})."
                    )
                })

    class Meta:
        db_table = 'calificaciones'
        unique_together = ['actividad', 'estudiante']
        ordering = ['-fecha_registro']
        # ✅ AQUÍ NO HAY CheckConstraint cruzado
        # La validación se hace en clean() arriba