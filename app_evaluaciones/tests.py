from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from app_academico.models import AulaVirtual, Estudiante, Matricula, Profesor
from app_evaluaciones.forms import ActividadForm, AsignarEstudianteForm, PlanEvaluacionForm
from app_evaluaciones.models import EvaluacionObjetivo, NotaPublicada, PlanEvaluacion
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

    def test_profesor_aula_detail_shows_send_notes_action_when_evaluations_exist(self) -> None:
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
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Objetivo general',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[['Comprender la fotosíntesis', 'Exposición', 10.0]],
        )
        EvaluacionObjetivo.objects.create(
            plan=plan,
            estudiante=student,
            objetivo='Comprender la fotosíntesis',
            objetivo_index=0,
            nota_obtenida=Decimal('7.00'),
            observacion='Bien',
        )

        self.client.force_login(self.profesor_user)
        response = self.client.get(reverse('evaluaciones:profesor_aula_detalle', args=[self.aula.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['puede_enviar_notas'])
        self.assertContains(response, 'Enviar notas al admin')

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

    def test_student_preview_shows_grades_for_closed_or_archived_plan(self) -> None:
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
            activo=False,
            objetivos_detallados=[
                ['Comprender la fotosíntesis', 'Exposición', 8.0],
            ],
        )
        EvaluacionObjetivo.objects.create(
            plan=plan,
            estudiante=student,
            objetivo='Comprender la fotosíntesis',
            objetivo_index=0,
            nota_obtenida=Decimal('7.00'),
            observacion='Bien',
        )
        plan.publicado_para_estudiantes = True
        plan.aprobado_por_admin = True
        plan.save(update_fields=['publicado_para_estudiantes', 'aprobado_por_admin'])

        self.client.force_login(student_user)
        response = self.client.get(reverse('evaluaciones:estudiante_calificaciones'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profesor responsable:')
        self.assertContains(response, '7.00')
        self.assertNotContains(response, 'Objetivo:')

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

    def test_professor_can_reopen_objective_evaluation_and_see_existing_score(self) -> None:
        student_user = Usuario.objects.create_user(
            cedula='E410',
            email='est410@example.com',
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
        EvaluacionObjetivo.objects.create(
            plan=plan,
            estudiante=student,
            objetivo='Comprender la fotosíntesis',
            objetivo_index=0,
            nota_obtenida=Decimal('3.50'),
            observacion='Bien',
        )

        self.client.force_login(self.profesor_user)
        response = self.client.get(reverse('evaluaciones:profesor_objetivo_evaluar', args=[plan.pk, 0]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="3.50"')
        self.assertContains(response, 'value="Bien"')

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

    def test_profesor_can_send_notes_to_admin(self) -> None:
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Objetivo general',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[['Comprender la fotosíntesis', 'Exposición', 20.0]],
        )

        self.client.force_login(self.profesor_user)
        response = self.client.post(reverse('evaluaciones:profesor_enviar_notas_admin', args=[self.aula.pk]))

        self.assertEqual(response.status_code, 302)
        plan.refresh_from_db()
        self.assertTrue(plan.notas_enviadas_al_admin)

    def test_profesor_cannot_evaluate_objectives_after_sending_notes_to_admin(self) -> None:
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Objetivo general',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            notas_enviadas_al_admin=True,
            objetivos_detallados=[['Comprender la fotosíntesis', 'Exposición', 20.0]],
        )

        self.client.force_login(self.profesor_user)
        response = self.client.get(reverse('evaluaciones:profesor_objetivo_evaluar', args=[plan.pk, 0]))

        self.assertRedirects(response, reverse('evaluaciones:profesor_reporte_notas', args=[plan.pk]))

    def test_profesor_aula_detail_shows_report_link_when_notes_are_already_sent(self) -> None:
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Objetivo general',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            notas_enviadas_al_admin=True,
            objetivos_detallados=[['Comprender la fotosíntesis', 'Exposición', 20.0]],
        )

        self.client.force_login(self.profesor_user)
        response = self.client.get(reverse('evaluaciones:profesor_aula_detalle', args=[self.aula.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reporte enviado')
        self.assertContains(response, reverse('evaluaciones:profesor_reporte_notas', args=[plan.pk]))
        self.assertNotContains(response, 'Enviar notas al admin')

    def test_profesor_create_plan_from_aula_prefills_aula_and_hides_selection(self) -> None:
        self.client.force_login(self.profesor_user)
        response = self.client.get(reverse('evaluaciones:profesor_plan_nuevo'), {'aula': self.aula.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aula actual')
        self.assertContains(response, '2° Año')
        self.assertNotContains(response, 'Seleccione un aula')

    def test_profesor_plan_form_excludes_used_lapso_from_available_choices(self) -> None:
        PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Plan inicial',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[['Objetivo 1', 'Método 1', 20.0]],
        )

        self.client.force_login(self.profesor_user)
        response = self.client.get(reverse('evaluaciones:profesor_plan_nuevo'), {'aula': self.aula.pk})

        self.assertEqual(response.status_code, 200)
        choices = dict(response.context['form'].fields['lapso'].choices)
        self.assertNotIn('I', choices)
        self.assertIn('II', choices)
        self.assertIn('III', choices)

    def test_profesor_report_detail_shows_objective_columns_and_total_sum(self) -> None:
        student_user = Usuario.objects.create_user(
            cedula='E550',
            email='est550@example.com',
            password='12345678',
            nombres='Ana',
            apellidos='Duran',
            rol='ESTUDIANTE',
        )
        student = Estudiante.objects.create(
            usuario=student_user,
            representante='Carlos',
            telefono_representante='04141234567',
        )
        Matricula.objects.create(estudiante=student, aula=self.aula)
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Historia de Venezuela',
            metodo='Ensayo',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[
                ['Objetivo 1', 'Método 1', 8.0],
                ['Objetivo 2', 'Método 2', 12.0],
            ],
        )
        EvaluacionObjetivo.objects.create(
            plan=plan,
            estudiante=student,
            objetivo='Objetivo 1',
            objetivo_index=0,
            nota_obtenida=Decimal('3.00'),
        )
        EvaluacionObjetivo.objects.create(
            plan=plan,
            estudiante=student,
            objetivo='Objetivo 2',
            objetivo_index=1,
            nota_obtenida=Decimal('4.50'),
        )

        self.client.force_login(self.profesor_user)
        response = self.client.get(reverse('evaluaciones:profesor_reporte_notas', args=[plan.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Notas de lapso')
        self.assertContains(response, 'Cátedra')
        self.assertContains(response, 'Profesor')
        self.assertContains(response, 'Aula')
        self.assertContains(response, 'Objetivo 1')
        self.assertContains(response, 'Objetivo 2')
        self.assertContains(response, '7.50')

    def test_admin_report_detail_returns_to_admin_aula_detail(self) -> None:
        admin_user = Usuario.objects.create_user(
            cedula='A110',
            email='admin2@example.com',
            password='12345678',
            nombres='Admin',
            apellidos='Reporte',
            rol='ADMIN',
        )
        student_user = Usuario.objects.create_user(
            cedula='E560',
            email='est560@example.com',
            password='12345678',
            nombres='Beatriz',
            apellidos='Rivas',
            rol='ESTUDIANTE',
        )
        student = Estudiante.objects.create(
            usuario=student_user,
            representante='Rafael',
            telefono_representante='04141234567',
        )
        Matricula.objects.create(estudiante=student, aula=self.aula)
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Historia de Venezuela',
            metodo='Ensayo',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[['Objetivo 1', 'Método 1', 8.0]],
            notas_enviadas_al_admin=True,
        )
        EvaluacionObjetivo.objects.create(
            plan=plan,
            estudiante=student,
            objetivo='Objetivo 1',
            objetivo_index=0,
            nota_obtenida=Decimal('3.00'),
        )

        self.client.force_login(admin_user)
        response = self.client.get(reverse('evaluaciones:profesor_reporte_notas', args=[plan.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('academico:aula_detail', args=[self.aula.pk]))

    def test_admin_detail_shows_report_and_publish_action_for_sent_notes(self) -> None:
        admin_user = Usuario.objects.create_user(
            cedula='A100',
            email='admin@example.com',
            password='12345678',
            nombres='Admin',
            apellidos='Sistema',
            rol='ADMIN',
        )
        student_user = Usuario.objects.create_user(
            cedula='E600',
            email='est6@example.com',
            password='12345678',
            nombres='José',
            apellidos='Mora',
            rol='ESTUDIANTE',
        )
        student = Estudiante.objects.create(
            usuario=student_user,
            representante='Ana',
            telefono_representante='04141234567',
        )
        Matricula.objects.create(estudiante=student, aula=self.aula)
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Historia de Venezuela',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[['Historia de Venezuela', 'Ensayo', 20.0]],
            notas_enviadas_al_admin=True,
        )
        EvaluacionObjetivo.objects.create(
            plan=plan,
            estudiante=student,
            objetivo='Historia de Venezuela',
            objetivo_index=0,
            nota_obtenida=Decimal('18.00'),
            observacion='Excelente',
        )

        self.client.force_login(admin_user)
        response = self.client.get(reverse('academico:aula_detail', args=[self.aula.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reporte de notas')
        self.assertContains(response, 'Publicar notas')

    def test_student_preview_shows_summary_for_published_final_grade(self) -> None:
        student_user = Usuario.objects.create_user(
            cedula='E900',
            email='est900@example.com',
            password='12345678',
            nombres='Pedro',
            apellidos='López',
            rol='ESTUDIANTE',
        )
        student = Estudiante.objects.create(
            usuario=student_user,
            representante='Carmen',
            telefono_representante='04141234567',
        )
        Matricula.objects.create(estudiante=student, aula=self.aula)
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Historia de Venezuela',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[['Historia de Venezuela', 'Ensayo', 20.0]],
        )
        NotaPublicada.objects.create(
            plan=plan,
            estudiante=student,
            nota_final=Decimal('18.00'),
        )

        self.client.force_login(student_user)
        response = self.client.get(reverse('evaluaciones:estudiante_calificaciones'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profesor responsable:')
        self.assertContains(response, '18.00')
        self.assertNotContains(response, 'Objetivo:')

    def test_student_preview_groups_multiple_lapsos_from_same_aula_in_single_context(self) -> None:
        self.aula.catedra = 'Informática'
        self.aula.save(update_fields=['catedra'])

        student_user = Usuario.objects.create_user(
            cedula='E910',
            email='est910@example.com',
            password='12345678',
            nombres='Pedro',
            apellidos='López',
            rol='ESTUDIANTE',
        )
        student = Estudiante.objects.create(
            usuario=student_user,
            representante='Carmen',
            telefono_representante='04141234567',
        )
        Matricula.objects.create(estudiante=student, aula=self.aula)

        plan_i = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Historia de Venezuela',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[['Historia de Venezuela', 'Ensayo', 20.0]],
            publicado_para_estudiantes=True,
        )
        plan_ii = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='II',
            objetivo='Historia de Venezuela',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[['Historia de Venezuela', 'Ensayo', 20.0]],
            publicado_para_estudiantes=True,
        )
        NotaPublicada.objects.create(plan=plan_i, estudiante=student, nota_final=Decimal('20.00'))
        NotaPublicada.objects.create(plan=plan_ii, estudiante=student, nota_final=Decimal('17.00'))

        self.client.force_login(student_user)
        response = self.client.get(reverse('evaluaciones:estudiante_calificaciones'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Informática')
        self.assertContains(response, 'Ana García')
        self.assertContains(response, 'I Lapso')
        self.assertContains(response, 'II Lapso')
        self.assertContains(response, '20.00')
        self.assertContains(response, '17.00')
        self.assertEqual(response.content.decode('utf-8').count('Profesor responsable:'), 1)

    def test_admin_can_close_aula_and_publish_notes_to_students(self) -> None:
        admin_user = Usuario.objects.create_user(
            cedula='A100',
            email='admin@example.com',
            password='12345678',
            nombres='Admin',
            apellidos='Sistema',
            rol='ADMIN',
        )
        student_user = Usuario.objects.create_user(
            cedula='E600',
            email='est6@example.com',
            password='12345678',
            nombres='José',
            apellidos='Mora',
            rol='ESTUDIANTE',
        )
        student = Estudiante.objects.create(
            usuario=student_user,
            representante='Ana',
            telefono_representante='04141234567',
        )
        Matricula.objects.create(estudiante=student, aula=self.aula)
        plan = PlanEvaluacion.objects.create(
            aula=self.aula,
            lapso='I',
            objetivo='Objetivo para publicar',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[['Comprender la fotosíntesis', 'Exposición', 20.0]],
            aprobado_por_admin=False,
            publicado_para_estudiantes=False,
        )

        self.client.force_login(admin_user)
        response = self.client.post(
            reverse('academico:aula_detail', args=[self.aula.pk]),
            {'cerrar_aula': '1'},
        )

        self.assertEqual(response.status_code, 302)
        self.aula.refresh_from_db()
        plan.refresh_from_db()
        self.assertFalse(self.aula.activo)
        self.assertTrue(plan.aprobado_por_admin)
        self.assertTrue(plan.publicado_para_estudiantes)

        self.client.force_login(student_user)
        response = self.client.get(reverse('evaluaciones:estudiante_planes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Objetivo para publicar')

    def test_student_preview_shows_objective_evaluations_when_plan_is_finalized(self) -> None:
        student_user = Usuario.objects.create_user(
            cedula='E800',
            email='est800@example.com',
            password='12345678',
            nombres='Rosa',
            apellidos='Mora',
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
            objetivo='Plan final',
            metodo='Proyecto',
            puntuacion_max=Decimal('20.00'),
            activo=True,
            objetivos_detallados=[['Comprender la fotosíntesis', 'Exposición', 20.0]],
        )
        EvaluacionObjetivo.objects.create(
            plan=plan,
            estudiante=student,
            objetivo='Comprender la fotosíntesis',
            objetivo_index=0,
            nota_obtenida=Decimal('18.00'),
            observacion='Excelente',
        )

        self.client.force_login(student_user)
        response = self.client.get(reverse('evaluaciones:estudiante_calificaciones'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profesor responsable:')
        self.assertContains(response, '18.00')
        self.assertNotContains(response, 'Objetivo:')
        self.assertNotContains(response, 'Excelente')

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
