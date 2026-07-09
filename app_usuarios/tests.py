from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import PermissionDenied

from .models import Usuario
from .decorators import role_required


class UsuarioTests(TestCase):
    def test_crear_usuario_con_rol(self) -> None:
        usuario = Usuario.objects.create_user(
            username='docente1',
            email='docente@example.com',
            password='segura123',
            cedula='12345678',
            nombres='Ana',
            apellidos='Pérez',
            rol='profesor',
        )

        self.assertEqual(usuario.rol, 'profesor')
        self.assertTrue(usuario.check_password('segura123'))

    def test_decorador_role_required_bloquea_acceso(self) -> None:
        @role_required('profesor')
        def dummy_view(request):
            return None

        request = self.client.request().wsgi_request
        request.user = Usuario.objects.create_user(
            username='estudiante1',
            email='estudiante@example.com',
            password='segura123',
            cedula='87654321',
            nombres='Luis',
            apellidos='Márquez',
            rol='estudiante',
        )

        with self.assertRaises(PermissionDenied):
            dummy_view(request)
