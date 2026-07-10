from decimal import Decimal

from django.test import TestCase

from app_academico.models import AulaVirtual, Estudiante, Profesor
from app_evaluaciones.forms import ActividadForm, PlanEvaluacionForm
from app_evaluaciones.models import PlanEvaluacion
from app_usuarios.models import Usuario


class EvaluacionFormsTestCase(TestCase):
    def setUp(self) -> None:
        self.profesor_user = Usuario.objects.create_user(
            cedula='P001',
            email='profesor@example.com',
            password='12345678',
            nombres='Ana',
            apellidos='García',
            rol='PROFESOR',
        )
        self.profesor = Profesor.objects.create(usuario=self.profesor_user)
        self.aula = AulaVirtual.objects.create(año_curso=2, lapsos=['I', 'II'], profesor=self.profesor)

    def test_plan_form_rejects_total_score_above_20(self) -> None:
        PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Plan inicial',
            metodo='Prueba',
            puntuacion_max=Decimal('12.00'),
            activo=True,
        )

        form = PlanEvaluacionForm(
            data={
                'aula': self.aula.pk,
                'lapso': 'I',
                'objetivo': 'Otro plan',
                'metodo': 'Proyecto',
                'puntuacion_max': '10.00',
            },
            user=self.profesor_user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('puntuacion_max', form.errors)

    def test_actividad_form_rejects_score_higher_than_plan_limit(self) -> None:
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Plan de evaluación',
            metodo='Ensayo',
            puntuacion_max=Decimal('10.00'),
            activo=True,
        )

        form = ActividadForm(
            data={
                'titulo': 'Actividad 1',
                'fecha': '2026-07-10',
                'puntuacion': '12.00',
                'descripcion': 'Sin descripción',
            },
            plan=plan,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('puntuacion', form.errors)
