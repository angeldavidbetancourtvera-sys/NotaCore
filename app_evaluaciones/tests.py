from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from app_academico.models import AulaVirtual, Estudiante, Matricula, Profesor
from app_evaluaciones.forms import ActividadForm, AsignarEstudianteForm, PlanEvaluacionForm
from app_evaluaciones.models import EvaluacionObjetivo, PlanEvaluacion
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

    def test_plan_form_allows_second_plan_when_each_plan_sums_20_points(self) -> None:
        PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Plan inicial',
            metodo='Prueba',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[['Objetivo 1', 'Método 1', 20.0]],
        )

        form = PlanEvaluacionForm(
            data={
                'aula': self.aula.pk,
                'lapso': 'II',
                'objetivo_1': 'Objetivo nuevo',
                'metodo_1': 'Método nuevo',
                'puntuacion_1': '20.00',
                'activo': 'on',
            },
            user=self.profesor_user,
        )

        self.assertTrue(form.is_valid(), form.errors)

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

    def test_plan_form_accepts_multiple_objectives_totaling_20_points(self) -> None:
        form = PlanEvaluacionForm(
            data={
                'aula': self.aula.pk,
                'lapso': 'I',
                'objetivo_1': 'Comprender la fotosíntesis',
                'metodo_1': 'Exposición',
                'puntuacion_1': '8.00',
                'objetivo_2': 'Resolver ejercicios de respiración',
                'metodo_2': 'Taller',
                'puntuacion_2': '12.00',
                'activo': 'on',
            },
            user=self.profesor_user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['puntuacion_max'], 20)

    def test_plan_form_allows_one_plan_per_different_lapso_in_same_aula(self) -> None:
        form_i = PlanEvaluacionForm(
            data={
                'aula': self.aula.pk,
                'lapso': 'I',
                'objetivo_1': 'Objetivo I',
                'metodo_1': 'Método I',
                'puntuacion_1': '20.00',
                'activo': 'on',
            },
            user=self.profesor_user,
        )
        form_ii = PlanEvaluacionForm(
            data={
                'aula': self.aula.pk,
                'lapso': 'II',
                'objetivo_1': 'Objetivo II',
                'metodo_1': 'Método II',
                'puntuacion_1': '20.00',
                'activo': 'on',
            },
            user=self.profesor_user,
        )
        form_iii = PlanEvaluacionForm(
            data={
                'aula': self.aula.pk,
                'lapso': 'III',
                'objetivo_1': 'Objetivo III',
                'metodo_1': 'Método III',
                'puntuacion_1': '20.00',
                'activo': 'on',
            },
            user=self.profesor_user,
        )

        self.assertTrue(form_i.is_valid(), form_i.errors)
        self.assertTrue(form_ii.is_valid(), form_ii.errors)
        self.assertTrue(form_iii.is_valid(), form_iii.errors)

    def test_plan_form_rejects_second_plan_for_same_lapso_in_same_aula(self) -> None:
        PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Plan inicial',
            metodo='Prueba',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[['Objetivo inicial', 'Método', 20.0]],
        )

        form = PlanEvaluacionForm(
            data={
                'aula': self.aula.pk,
                'lapso': 'I',
                'objetivo_1': 'Otro objetivo',
                'metodo_1': 'Otro método',
                'puntuacion_1': '20.00',
                'activo': 'on',
            },
            user=self.profesor_user,
        )

        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn('lapso', form.errors)

    def test_plan_form_saves_rows_as_json_without_decimal_errors(self) -> None:
        form = PlanEvaluacionForm(
            data={
                'aula': self.aula.pk,
                'lapso': 'I',
                'objetivo_1': 'Comprender la fotosíntesis',
                'metodo_1': 'Exposición',
                'puntuacion_1': '8.00',
                'objetivo_2': 'Resolver ejercicios de respiración',
                'metodo_2': 'Taller',
                'puntuacion_2': '12.00',
                'activo': 'on',
            },
            user=self.profesor_user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        plan = form.save()
        self.assertEqual(plan.puntuacion_max, Decimal('20.00'))
        self.assertEqual(len(plan.objetivos_detallados), 2)
        self.assertEqual(plan.objetivos_detallados[0][0], 'Comprender la fotosíntesis')
        self.assertEqual(plan.objetivos_detallados[1][2], 12.0)

    def test_evaluations_are_stored_per_objective_row(self) -> None:
        student_user = Usuario.objects.create_user(
            cedula='E700',
            email='est700@example.com',
            password='12345678',
            nombres='María',
            apellidos='Pérez',
            rol='ESTUDIANTE',
        )
        student = Estudiante.objects.create(
            usuario=student_user,
            representante='Luis',
            telefono_representante='04141234567',
        )
        Matricula.objects.create(estudiante=student, aula=self.aula)
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Plan de evaluación',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[
                ['Participación', 'Clase', 10.0],
                ['Participación', 'Taller', 10.0],
            ],
        )

        self.client.force_login(self.profesor_user)
        response = self.client.post(
            reverse('evaluaciones:profesor_objetivo_evaluar', kwargs={'pk': plan.pk, 'objetivo_index': 0}),
            {
                f'nota_{student.pk}': '4.00',
                f'observacion_{student.pk}': 'Bien',
            },
        )
        self.assertEqual(response.status_code, 302)

        response = self.client.post(
            reverse('evaluaciones:profesor_objetivo_evaluar', kwargs={'pk': plan.pk, 'objetivo_index': 1}),
            {
                f'nota_{student.pk}': '6.00',
                f'observacion_{student.pk}': 'Muy bien',
            },
        )
        self.assertEqual(response.status_code, 302)

        evaluations = EvaluacionObjetivo.objects.filter(plan=plan, estudiante=student).order_by('objetivo_index')
        self.assertEqual(evaluations.count(), 2)
        self.assertEqual(evaluations[0].nota_obtenida, Decimal('4.00'))
        self.assertEqual(evaluations[1].nota_obtenida, Decimal('6.00'))

    def test_profesor_aula_detail_shows_plan_table(self) -> None:
        self.client.force_login(self.profesor_user)
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Objetivo general',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[
                ['Comprender la fotosíntesis', 'Exposición', 10.0],
                ['Resolver ejercicios', 'Taller', 10.0],
            ],
        )

        response = self.client.get(reverse('evaluaciones:profesor_aula_detalle', args=[self.aula.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comprender la fotosíntesis')
        self.assertContains(response, 'Resolver ejercicios')
        self.assertContains(response, 'Exposición')
        self.assertContains(response, 'Taller')

    def test_student_aula_detail_shows_plan_for_their_classroom(self) -> None:
        student_user = Usuario.objects.create_user(
            cedula='E300',
            email='est3@example.com',
            password='12345678',
            nombres='Carlos',
            apellidos='Rojas',
            rol='ESTUDIANTE',
        )
        student = Estudiante.objects.create(
            usuario=student_user,
            representante='Marta',
            telefono_representante='04141234567',
        )
        Matricula.objects.create(estudiante=student, aula=self.aula)
        PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Objetivo general',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[
                ['Comprender la fotosíntesis', 'Exposición', 10.0],
                ['Resolver ejercicios', 'Taller', 10.0],
            ],
        )

        self.client.force_login(student_user)
        response = self.client.get(reverse('evaluaciones:estudiante_aula_detalle', args=[self.aula.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comprender la fotosíntesis')
        self.assertContains(response, 'Resolver ejercicios')

    def test_student_aula_detail_shows_evaluated_and_accumulated_points_summary(self) -> None:
        student_user = Usuario.objects.create_user(
            cedula='E450',
            email='est450@example.com',
            password='12345678',
            nombres='Lucía',
            apellidos='Silva',
            rol='ESTUDIANTE',
        )
        student = Estudiante.objects.create(
            usuario=student_user,
            representante='José',
            telefono_representante='04141234567',
        )
        Matricula.objects.create(estudiante=student, aula=self.aula)
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Objetivo general',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[
                ['Comprender la fotosíntesis', 'Exposición', 8.0],
                ['Resolver ejercicios', 'Taller', 4.0],
            ],
        )
        EvaluacionObjetivo.objects.create(
            plan=plan,
            estudiante=student,
            objetivo='Comprender la fotosíntesis',
            nota_obtenida=Decimal('7.00'),
            observacion='Bien',
        )

        self.client.force_login(student_user)
        response = self.client.get(reverse('evaluaciones:estudiante_aula_detalle', args=[self.aula.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '8.00/7.00')

    def test_professor_can_evaluate_objective_and_save_student_grade(self) -> None:
        student_user = Usuario.objects.create_user(
            cedula='E400',
            email='est4@example.com',
            password='12345678',
            nombres='Marta',
            apellidos='Lopez',
            rol='ESTUDIANTE',
        )
        student = Estudiante.objects.create(
            usuario=student_user,
            representante='Rosa',
            telefono_representante='04141234567',
        )
        Matricula.objects.create(estudiante=student, aula=self.aula)
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Objetivo general',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[
                ['Comprender la fotosíntesis', 'Exposición', 4.0],
            ],
        )

        self.client.force_login(self.profesor_user)
        response = self.client.post(
            reverse('evaluaciones:profesor_objetivo_evaluar', args=[plan.pk, 0]),
            {'nota_{}'.format(student.pk): '3.5', 'finalizado': 'on'},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(EvaluacionObjetivo.objects.filter(plan=plan, estudiante=student, objetivo='Comprender la fotosíntesis').exists())
        evaluation = EvaluacionObjetivo.objects.get(plan=plan, estudiante=student, objetivo='Comprender la fotosíntesis')
        self.assertEqual(evaluation.nota_obtenida, Decimal('3.50'))
        plan.refresh_from_db()
        self.assertTrue(plan.finalizado)

    def test_student_plan_detail_shows_objective_grade(self) -> None:
        student_user = Usuario.objects.create_user(
            cedula='E500',
            email='est5@example.com',
            password='12345678',
            nombres='Elena',
            apellidos='Pérez',
            rol='ESTUDIANTE',
        )
        student = Estudiante.objects.create(
            usuario=student_user,
            representante='Sara',
            telefono_representante='04141234567',
        )
        Matricula.objects.create(estudiante=student, aula=self.aula)
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Objetivo general',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[
                ['Comprender la fotosíntesis', 'Exposición', 4.0],
                ['Resolver ejercicios', 'Taller', 6.0],
            ],
        )
        EvaluacionObjetivo.objects.create(
            plan=plan,
            estudiante=student,
            objetivo='Comprender la fotosíntesis',
            nota_obtenida=Decimal('3.50'),
            observacion='Bien',
        )

        self.client.force_login(student_user)
        response = self.client.get(reverse('evaluaciones:estudiante_plan_detalle', args=[plan.pk]))
        objetivos_con_evaluaciones = response.context['objetivos_con_evaluaciones']

        self.assertEqual(response.status_code, 200)
        self.assertEqual(objetivos_con_evaluaciones[0]['objetivo'], 'Comprender la fotosíntesis')
        self.assertEqual(objetivos_con_evaluaciones[0]['evaluacion'].nota_obtenida, Decimal('3.50'))
        self.assertIsNone(objetivos_con_evaluaciones[1]['evaluacion'])
        self.assertContains(response, '3.50')
        self.assertContains(response, 'Bien')

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
