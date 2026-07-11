from django.test import TestCase
from django.urls import reverse

from app_academico.forms import AulaVirtualForm, UsuarioSearchForm
from app_academico.models import AulaVirtual, Profesor
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
                'lapsos': 'I',
                'profesor': str(profesor_user.cedula),
                'activo': 'on',
            },
        )

        aula = AulaVirtual.objects.latest('pk')
        self.assertRedirects(response, reverse('academico:aula_detail', kwargs={'pk': aula.pk}))
