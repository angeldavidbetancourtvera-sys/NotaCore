from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from app_academico.models import AulaVirtual, Estudiante, Profesor
from app_evaluaciones.forms import ActividadForm, AsignarEstudianteForm, PlanEvaluacionForm
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

    def test_profesor_and_student_routes_are_available(self) -> None:
        self.assertEqual(reverse('evaluaciones:profesor_aulas'), '/evaluaciones/profesor/aulas/')
        self.assertEqual(reverse('evaluaciones:profesor_estudiantes'), '/evaluaciones/profesor/estudiantes/')
        self.assertEqual(reverse('evaluaciones:estudiante_planes'), '/evaluaciones/estudiante/planes/')

    def test_assign_student_form_filters_by_cedula(self) -> None:
        Usuario.objects.create_user(
            cedula='E100',
            email='est1@example.com',
            password='12345678',
            nombres='Luis',
            apellidos='Márquez',
            rol='ESTUDIANTE',
        )
        Usuario.objects.create_user(
            cedula='E200',
            email='est2@example.com',
            password='12345678',
            nombres='María',
            apellidos='Pérez',
            rol='ESTUDIANTE',
        )

        form = AsignarEstudianteForm(aula=self.aula, cedula_search='E100')
        queryset = form.fields['estudiantes'].queryset

        self.assertTrue(queryset.filter(cedula='E100').exists())
        self.assertFalse(queryset.filter(cedula='E200').exists())
