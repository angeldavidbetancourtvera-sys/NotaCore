import json
from decimal import Decimal
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView, View

from app_academico.models import AulaVirtual, Estudiante, Matricula, Profesor

from .forms import ActividadForm, AsignarEstudianteForm, CalificacionForm, PlanEvaluacionForm
from .models import Actividad, Calificacion, PlanEvaluacion


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self) -> bool:
        user_role = getattr(self.request.user, 'rol', '') or ''
        return self.request.user.is_authenticated and user_role.upper() == 'ADMIN'


class ProfesorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self) -> bool:
        user_role = getattr(self.request.user, 'rol', '') or ''
        return self.request.user.is_authenticated and user_role.upper() in {'PROFESOR', 'ADMIN'}


class EstudianteRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self) -> bool:
        user_role = getattr(self.request.user, 'rol', '') or ''
        return self.request.user.is_authenticated and user_role.upper() in {'ESTUDIANTE', 'ADMIN'}

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AulaPropiaMixin:
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        user_role = getattr(request.user, 'rol', '') or ''
        if not request.user.is_authenticated or user_role.upper() not in {'PROFESOR', 'ADMIN'}:
            raise PermissionDenied
        aula_pk = kwargs.get('pk_aula')
        if aula_pk:
            aula = AulaVirtual.objects.filter(pk=aula_pk, profesor__usuario=request.user).first()
            if aula is None:
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ProfesorDashboardView(ProfesorRequiredMixin, TemplateView):
    template_name = 'evaluaciones/profesor_dashboard.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        aulas = AulaVirtual.objects.filter(profesor__usuario=self.request.user).prefetch_related('matriculas')
        context['aulas'] = aulas
        context['estudiantes_mat'] = Matricula.objects.filter(aula__in=aulas).select_related('estudiante').distinct()
        context['planes_por_lapso'] = PlanEvaluacion.objects.filter(aula__in=aulas).values('lapso').annotate(total=__import__('django.db.models').db.models.Count('id'))
        return context


class PlanEvaluacionListView(ProfesorRequiredMixin, ListView):
    model = PlanEvaluacion
    template_name = 'evaluaciones/plan_list.html'
    context_object_name = 'planes'

    def get_queryset(self) -> QuerySet[PlanEvaluacion]:
        return PlanEvaluacion.objects.filter(aula__profesor__usuario=self.request.user).select_related('aula').order_by('-pk')


class PlanEvaluacionCreateView(ProfesorRequiredMixin, CreateView):
    model = PlanEvaluacion
    form_class = PlanEvaluacionForm
    template_name = 'evaluaciones/plan_form.html'
    success_url = reverse_lazy('evaluaciones:profesor_planes')

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class PlanEvaluacionUpdateView(ProfesorRequiredMixin, UpdateView):
    model = PlanEvaluacion
    form_class = PlanEvaluacionForm
    template_name = 'evaluaciones/plan_form.html'
    success_url = reverse_lazy('evaluaciones:profesor_planes')

    def get_queryset(self) -> QuerySet[PlanEvaluacion]:
        return PlanEvaluacion.objects.filter(aula__profesor__usuario=self.request.user)

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class PlanEvaluacionDeleteView(ProfesorRequiredMixin, DeleteView):
    model = PlanEvaluacion
    template_name = 'evaluaciones/confirm_delete.html'
    success_url = reverse_lazy('evaluaciones:profesor_planes')

    def get_queryset(self) -> QuerySet[PlanEvaluacion]:
        return PlanEvaluacion.objects.filter(aula__profesor__usuario=self.request.user)


class ActividadCreateView(ProfesorRequiredMixin, CreateView):
    model = Actividad
    form_class = ActividadForm
    template_name = 'evaluaciones/actividad_form.html'

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.plan = get_object_or_404(PlanEvaluacion, pk=kwargs['plan_pk'], aula__profesor__usuario=request.user)
        if self.plan.aula.profesor.usuario != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['plan'] = self.plan
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['plan'] = self.plan
        return context

    def form_valid(self, form: ActividadForm) -> HttpResponse:
        form.instance.plan = self.plan
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy('evaluaciones:profesor_planes')


class ActividadUpdateView(ProfesorRequiredMixin, UpdateView):
    model = Actividad
    form_class = ActividadForm
    template_name = 'evaluaciones/actividad_form.html'

    def get_queryset(self) -> QuerySet[Actividad]:
        return Actividad.objects.filter(plan__aula__profesor__usuario=self.request.user)

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['plan'] = self.object.plan
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['plan'] = self.object.plan
        return context

    def get_success_url(self) -> str:
        return reverse_lazy('evaluaciones:profesor_planes')


class ActividadDeleteView(ProfesorRequiredMixin, DeleteView):
    model = Actividad
    template_name = 'evaluaciones/confirm_delete.html'

    def get_queryset(self) -> QuerySet[Actividad]:
        return Actividad.objects.filter(plan__aula__profesor__usuario=self.request.user)

    def get_success_url(self) -> str:
        return reverse_lazy('evaluaciones:profesor_planes')


class AsignarEstudianteView(ProfesorRequiredMixin, AulaPropiaMixin, FormView):
    template_name = 'evaluaciones/asignar_estudiante.html'
    form_class = AsignarEstudianteForm
    success_url = reverse_lazy('evaluaciones:profesor_asignar_estudiante')

    def get_aula(self) -> AulaVirtual | None:
        aula_pk = self.kwargs.get('pk_aula') or self.request.GET.get('aula') or self.request.POST.get('aula')
        if not aula_pk:
            return self.request.user.profesor.aulas.first() if hasattr(self.request.user, 'profesor') else None
        return AulaVirtual.objects.filter(pk=aula_pk, profesor__usuario=self.request.user).first()

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['aula'] = self.get_aula()
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['aulas'] = AulaVirtual.objects.filter(profesor__usuario=self.request.user).order_by('año_curso')
        context['aula'] = self.get_aula()
        return context

    def form_valid(self, form: AsignarEstudianteForm) -> HttpResponse:
        form.save()
        return super().form_valid(form)


class MatrizNotasView(ProfesorRequiredMixin, AulaPropiaMixin, TemplateView):
    template_name = 'evaluaciones/matriz_notas.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        aula = get_object_or_404(AulaVirtual, pk=kwargs['pk_aula'], profesor__usuario=self.request.user)
        estudiantes = Estudiante.objects.filter(matriculas__aula=aula).distinct()
        actividades = Actividad.objects.filter(plan__aula=aula).select_related('plan').order_by('plan__lapso', 'fecha', 'titulo')

        matriz: list[dict[str, Any]] = []
        for estudiante in estudiantes:
            filas = []
            for actividad in actividades:
                calificacion = Calificacion.objects.filter(actividad=actividad, estudiante=estudiante).first()
                filas.append({
                    'actividad': actividad,
                    'calificacion': calificacion,
                    'nota': calificacion.nota_obtenida if calificacion else '',
                })
            matriz.append({'estudiante': estudiante, 'filas': filas})

        context['aula'] = aula
        context['estudiantes'] = estudiantes
        context['actividades'] = actividades
        context['matriz'] = matriz
        return context


class GuardarNotasView(ProfesorRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        payload = self._load_payload(request)
        if not payload:
            return JsonResponse({'ok': False, 'error': 'Sin datos'}, status=400)

        created_count = 0
        updated_count = 0
        for item in payload:
            actividad_id = item.get('actividad_id')
            estudiante_id = item.get('estudiante_id')
            nota_valor = item.get('nota')
            observacion = item.get('observacion', '')

            if not actividad_id or not estudiante_id:
                continue

            actividad = get_object_or_404(Actividad, pk=actividad_id, plan__aula__profesor__usuario=request.user)
            estudiante = get_object_or_404(Estudiante, pk=estudiante_id)

            if nota_valor in {None, '', 'null'}:
                continue

            nota = Decimal(str(nota_valor))
            if nota > actividad.puntuacion:
                continue

            calificacion, created = Calificacion.objects.get_or_create(
                actividad=actividad,
                estudiante=estudiante,
                defaults={'nota_obtenida': nota, 'observacion': observacion},
            )
            if created:
                created_count += 1
            else:
                calificacion.nota_obtenida = nota
                calificacion.observacion = observacion
                calificacion.save(update_fields=['nota_obtenida', 'observacion'])
                updated_count += 1

        return JsonResponse({'ok': True, 'created': created_count, 'updated': updated_count})

    def _load_payload(self, request: HttpRequest) -> list[dict[str, Any]]:
        if request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and isinstance(data.get('items'), list):
                    return data['items']
                return [data]
            except json.JSONDecodeError:
                return []
        return []


class EstudianteDashboardView(EstudianteRequiredMixin, TemplateView):
    template_name = 'evaluaciones/estudiante_dashboard.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        estudiante = getattr(self.request.user, 'estudiante', None)
        aulas = AulaVirtual.objects.none()
        planes = PlanEvaluacion.objects.none()
        calificaciones = Calificacion.objects.none()

        if estudiante is not None:
            aulas = AulaVirtual.objects.filter(matriculas__estudiante=estudiante).prefetch_related('matriculas').distinct()
            planes = PlanEvaluacion.objects.filter(aula__in=aulas, activo=True).select_related('aula').order_by('aula__año_curso', 'lapso')
            calificaciones = Calificacion.objects.filter(estudiante=estudiante).select_related('actividad', 'actividad__plan')

        context['aulas'] = aulas
        context['planes'] = planes
        context['calificaciones'] = calificaciones
        context['estudiante'] = estudiante
        return context


class EstudianteDetalleAulaView(EstudianteRequiredMixin, DetailView):
    model = AulaVirtual
    template_name = 'evaluaciones/estudiante_aula_detail.html'
    context_object_name = 'aula'

    def get_queryset(self) -> QuerySet[AulaVirtual]:
        estudiante = getattr(self.request.user, 'estudiante', None)
        if estudiante is None:
            return AulaVirtual.objects.none()
        return AulaVirtual.objects.filter(matriculas__estudiante=estudiante)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        estudiante = getattr(self.request.user, 'estudiante', None)
        planes = PlanEvaluacion.objects.none()
        calificaciones = Calificacion.objects.none()

        if estudiante is not None and self.object is not None:
            planes = PlanEvaluacion.objects.filter(aula=self.object, activo=True).order_by('lapso')
            calificaciones = Calificacion.objects.filter(estudiante=estudiante, actividad__plan__aula=self.object)

        context['planes'] = planes
        context['calificaciones'] = calificaciones
        return context


class EstudiantePreviewCalificacionesView(EstudianteRequiredMixin, TemplateView):
    template_name = 'evaluaciones/preview_calificaciones.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        estudiante = getattr(self.request.user, 'estudiante', None)
        matriculas = Matricula.objects.none()
        resumen: list[dict[str, Any]] = []

        if estudiante is not None:
            matriculas = Matricula.objects.filter(estudiante=estudiante).select_related('aula')

            for matricula in matriculas:
                planes = PlanEvaluacion.objects.filter(aula=matricula.aula, activo=True).order_by('lapso')
                for plan in planes:
                    actividades = Actividad.objects.filter(plan=plan).order_by('fecha')
                    puntos_acumulados = Decimal('0.00')
                    puntos_posibles = Decimal('0.00')
                    detalle: list[dict[str, Any]] = []
                    for actividad in actividades:
                        puntos_posibles += actividad.puntuacion
                        calificacion = Calificacion.objects.filter(actividad=actividad, estudiante=estudiante).first()
                        if calificacion:
                            puntos_acumulados += calificacion.nota_obtenida
                        detalle.append({
                            'actividad': actividad,
                            'calificacion': calificacion,
                            'nota_obtenida': calificacion.nota_obtenida if calificacion else None,
                            'observacion': calificacion.observacion if calificacion else '',
                        })
                    promedio = (puntos_acumulados / puntos_posibles * Decimal('20')) if puntos_posibles else Decimal('0.00')
                    resumen.append({
                        'aula': matricula.aula,
                        'lapso': plan.get_lapso_display(),
                        'plan': plan,
                        'detalle': detalle,
                        'puntos_acumulados': puntos_acumulados,
                        'puntos_posibles': puntos_posibles,
                        'promedio': promedio,
                    })

        context['resumen'] = resumen
        context['estudiante'] = estudiante
        return context
