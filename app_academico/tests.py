from django.test import SimpleTestCase
from django.urls import reverse

from app_academico.forms import AulaVirtualForm, UsuarioSearchForm


class AcademicoRoutesTest(SimpleTestCase):
    def test_admin_dashboard_route_is_available(self) -> None:
        url = reverse('academico:admin_dashboard')
        self.assertEqual(url, '/academico/admin-dashboard/')

    def test_admin_forms_are_available(self) -> None:
        self.assertTrue(issubclass(AulaVirtualForm, object))
        self.assertTrue(issubclass(UsuarioSearchForm, object))
