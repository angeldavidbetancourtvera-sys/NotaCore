from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    cedula = models.CharField(max_length=20, unique=True, primary_key=True)
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    rol = models.CharField(
        max_length=20,
        choices=[('estudiante', 'Estudiante'), ('profesor', 'Profesor')],
        default='estudiante',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'cedula', 'nombres', 'apellidos']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self) -> str:
        return f"{self.nombres} {self.apellidos}"
