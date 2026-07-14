from django import forms
from django.test import TestCase
from django.urls import reverse

from app_academico.forms import AulaVirtualForm, UsuarioSearchForm
from app_academico.models import AulaVirtual, Estudiante, Matricula, Profesor
from app_evaluaciones.models import PlanEvaluacion
from app_usuarios.models import Usuario


class AcademicoRoutesTest(TestCase):
    def test_admin_dashboard_route_is_available(self) -> None:
        url = reverse('academico:admin_dashboard')
        self.assertEqual(url, '/academico/admin-dashboard/')

    def test_admin_forms_are_available(self) -> None:
        self.assertTrue(issubclass(AulaVirtualForm, object))
        self.assertTrue(issubclass(UsuarioSearchForm, object))

    def test_admin_profesor_and_estudiante_routes_are_available(self) -> None:
        self.assertEqual(reverse('academico:profesor_list'), '/academico/profesores/')
        self.assertEqual(reverse('academico:estudiante_list'), '/academico/estudiantes/')

    def test_admin_estudiante_list_renders_for_existing_students(self) -> None:
        admin_user = Usuario.objects.create_user(
            cedula='A004',
            email='admin4@example.com',
            password='12345678',
            nombres='Admin',
            apellidos='Test',
            rol='ADMIN',
        )
        student_user = Usuario.objects.create_user(
            cedula='E400',
            email='estudiante400@example.com',
            password='12345678',
            nombres='Carlos',
            apellidos='Pérez',
            rol='ESTUDIANTE',
        )
        Estudiante.objects.create(usuario=student_user, representante='R', telefono_representante='123')

        self.client.force_login(admin_user)
        response = self.client.get(reverse('academico:estudiante_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Carlos Pérez')

    def test_admin_can_update_student_contact_fields(self) -> None:
        admin_user = Usuario.objects.create_user(
            cedula='A005',
            email='admin5@example.com',
            password='12345678',
            nombres='Admin',
            apellidos='Test',
            rol='ADMIN',
        )
        student_user = Usuario.objects.create_user(
            cedula='E500',
            email='estudiante500@example.com',
            password='12345678',
            nombres='Pedro',
            apellidos='López',
            rol='ESTUDIANTE',
        )
        student = Estudiante.objects.create(usuario=student_user, representante='', telefono_representante='')

        self.client.force_login(admin_user)
        response = self.client.post(
            reverse('academico:estudiante_detail', args=[student_user.cedula]),
            {'representante': 'María López', 'telefono_representante': '04141234567'},
            follow=False,
        )

        student.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(student.representante, 'María López')
        self.assertEqual(student.telefono_representante, '04141234567')

    def test_admin_aula_create_view_renders_form(self) -> None:
        user = Usuario.objects.create_user(
            cedula='A001',
            email='admin@example.com',
            password='12345678',
            nombres='Admin',
            apellidos='Test',
            rol='ADMIN',
        )
        self.client.force_login(user)
        response = self.client.get(reverse('academico:aula_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="año_curso"')

    def test_admin_aula_create_redirects_to_detail_after_save(self) -> None:
        user = Usuario.objects.create_user(
            cedula='A002',
            email='admin2@example.com',
            password='12345678',
            nombres='Admin',
            apellidos='Test',
            rol='ADMIN',
        )
        profesor_user = Usuario.objects.create_user(
            cedula='P100',
            email='profesor100@example.com',
            password='12345678',
            nombres='Pedro',
            apellidos='Pérez',
            rol='PROFESOR',
        )
        Profesor.objects.create(usuario=profesor_user)
        self.client.force_login(user)

        response = self.client.post(
            reverse('academico:aula_create'),
            {
                'año_curso': '3',
                'lapsos': ['I', 'II'],
                'profesor': str(profesor_user.cedula),
                'activo': 'on',
            },
        )

        aula = AulaVirtual.objects.latest('pk')
        self.assertRedirects(response, reverse('academico:aula_detail', kwargs={'pk': aula.pk}))

    def test_admin_aula_detail_shows_professor_students_and_plan_checkbox(self) -> None:
        admin_user = Usuario.objects.create_user(
            cedula='A003',
            email='admin3@example.com',
            password='12345678',
            nombres='Admin',
            apellidos='Test',
            rol='ADMIN',
        )
        profesor_user = Usuario.objects.create_user(
            cedula='P200',
            email='profesor200@example.com',
            password='12345678',
            nombres='Pedro',
            apellidos='Pérez',
            rol='PROFESOR',
        )
        profesor = Profesor.objects.create(usuario=profesor_user)
        aula = AulaVirtual.objects.create(año_curso=3, lapsos=['I', 'II'], profesor=profesor, activo=True)
        student_user = Usuario.objects.create_user(
            cedula='E200',
            email='estudiante200@example.com',
            password='12345678',
            nombres='Luis',
            apellidos='Márquez',
            rol='ESTUDIANTE',
        )
        student = Estudiante.objects.create(usuario=student_user, representante='R', telefono_representante='123')
        Matricula.objects.create(estudiante=student, aula=aula)
        PlanEvaluacion.objects.create(
            aula=aula,
            lapso='I',
            objetivo='Plan general',
            metodo='Proyecto',
            puntuacion_max='20.00',
            activo=True,
        )

        self.client.force_login(admin_user)
        response = self.client.get(reverse('academico:aula_detail', kwargs={'pk': aula.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pedro Pérez')
        self.assertContains(response, 'Luis Márquez')
        self.assertContains(response, 'Aprob por admin')

    def test_aula_virtual_form_uses_checkbox_widget_for_lapsos(self) -> None:
        form = AulaVirtualForm()
        self.assertIsInstance(form.fields['lapsos'].widget, forms.CheckboxSelectMultiple)
        self.assertEqual(form.fields['lapsos'].choices, [('I', 'I Lapso'), ('II', 'II Lapso'), ('III', 'III Lapso')])

    def test_aula_virtual_form_profesor_queryset_only_includes_profesores(self) -> None:
        profesor_user = Usuario.objects.create_user(
            cedula='P101',
            email='profesor101@example.com',
            password='12345678',
            nombres='Ana',
            apellidos='López',
            rol='PROFESOR',
        )
        Profesor.objects.create(usuario=profesor_user)
        estudiante_user = Usuario.objects.create_user(
            cedula='E101',
            email='estudiante101@example.com',
            password='12345678',
            nombres='Luis',
            apellidos='Márquez',
            rol='ESTUDIANTE',
        )
        Estudiante.objects.create(usuario=estudiante_user, representante='R', telefono_representante='123')

        form = AulaVirtualForm()
        queryset = form.fields['profesor'].queryset
        self.assertEqual(queryset.count(), 1)
        self.assertTrue(queryset.filter(cedula=profesor_user.cedula).exists())
