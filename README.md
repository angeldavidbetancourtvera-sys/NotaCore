# 🏫 Sistema de Gestión Académica y Evaluaciones

Este proyecto es una plataforma web desarrollada en Django para la automatización, control y seguimiento del rendimiento académico. El sistema implementa la gestión de aulas virtuales, planes de evaluación estructurados por lapsos y un control estricto de accesos según el rol del usuario (Administradores, Profesores y Estudiantes).

---

## 👥 Equipo de Trabajo
* **Angel** - Analista
* **Sofia** - Analista
* **Carlos** - Colaborador

---

## 🏛️ Arquitectura del Sistema (Módulos y Modelos)

El proyecto está estructurado modularmente en tres aplicaciones principales:

### 1. `app_usuarios` (Autenticación y Roles)
* **Usuario (AbstractUser):** Sistema de autenticación personalizado que sustituye el `username` clásico por la **Cédula** como credencial primaria. Define los roles: `ADMIN`, `PROFESOR` y `ESTUDIANTE`.

### 2. `app_academico` (Estructura Escolar)
* **Profesor / Estudiante:** Modelos con relación uno a uno vinculados al usuario según su rol. El estudiante almacena información de su representante.
* **AulaVirtual:** Representa los cursos (de 1° a 5° Año), las cátedras y los lapsos (I, II y III Lapso) asignados a un profesor.
* **Matricula:** Relación única entre un Estudiante y un Aula Virtual.

### 3. `app_evaluaciones` (Calificaciones y Planificación)
* **PlanEvaluacion:** Objetivos y ponderaciones de un aula por lapso (Nota máxima limitada a 20 pts).
* **Actividad:** Tareas o exámenes individuales asociados a un plan.
* **EvaluacionObjetivo / Calificacion:** Registro e historial minucioso de notas obtenidas por los estudiantes.
* **NotaPublicada:** Calificaciones consolidadas finales aprobadas y visibles para los alumnos.

---

## 📋 Requisitos Previos

Antes de configurar el entorno, asegúrate de tener instalado:
* **Python 3.10+**
* **Git**
* **Virtualenv**

---

## 🔧 Instalación y Configuración del Entorno Local

Sigue estos pasos en orden secuencial para desplegar el proyecto en tu máquina:

### 1. Clonar el repositorio
```bash
git clone [https://github.com/angeldavidbetancourtvera-sys/NotaCore.git](https://github.com/angeldavidbetancourtvera-sys/NotaCore.git)
cd NotaCore