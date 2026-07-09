from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from typing import Optional, List


class UsuarioManager(BaseUserManager):
    """
    Gestor personalizado para crear usuarios con 'cedula' en lugar de 'username'.
    """
    def create_user(self, cedula: str, email: str, password: Optional[str] = None, **extra_fields):
        if not cedula:
            raise ValueError('La cédula es obligatoria para crear un usuario.')
        
        email = self.normalize_email(email)
        user = self.model(cedula=cedula, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, cedula: str, email: str, password: Optional[str] = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'ADMIN')  # Asigna rol ADMIN por defecto al superusuario
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')

        return self.create_user(cedula, email, password, **extra_fields)


class Usuario(AbstractUser):
    ROL_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('PROFESOR', 'Profesor'),
        ('ESTUDIANTE', 'Estudiante'),
    ]
    
    # Asignamos el gestor personalizado
    objects = UsuarioManager()

    # Eliminamos el campo 'username' heredado de AbstractUser
    username = None 
    
    cedula = models.CharField(max_length=20, primary_key=True, verbose_name="Cédula")
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='ESTUDIANTE')
    
    USERNAME_FIELD = 'cedula'
    REQUIRED_FIELDS = ['email', 'nombres', 'apellidos']

    def __str__(self) -> str:
        return f"{self.cedula} - {self.get_full_name()}"
    
    def get_full_name(self) -> str:
        return f"{self.nombres} {self.apellidos}"
    
    class Meta:
        db_table = 'usuarios'