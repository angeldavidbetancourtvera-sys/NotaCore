import json
from decimal import Decimal
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView, View

from app_academico.models import AulaVirtual, Estudiante, Matricula, Profesor

from .forms import ActividadForm, AsignarEstudianteForm, CalificacionForm, PlanEvaluacionForm
from .models import Actividad, Calificacion, EvaluacionObjetivo, PlanEvaluacion


def is_plan_visible_for_student(plan: PlanEvaluacion, estudiante: Estudiante | None) -> bool:
    if estudiante is None:
        return False

    is_enrolled_in_aula = Matricula.objects.filter(estudiante=estudiante, aula=plan.aula).exists()
    if is_enrolled_in_aula:
        return True

    if plan.publicado_para_estudiantes or plan.aprobado_por_admin or plan.finalizado or not plan.aula.activo:
        return True

    has_objective_evaluations = EvaluacionObjetivo.objects.filter(plan=plan, estudiante=estudiante).exists()
    has_activity_califications = Calificacion.objects.filter(actividad__plan=plan, estudiante=estudiante).exists()
    return has_objective_evaluations or has_activity_califications


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
        aulas = AulaVirtual.objects.filter(profesor__usuario=self.request.user)
        context['aulas'] = aulas
        context['aulas_count'] = aulas.count()
        context['estudiantes_count'] = Matricula.objects.filter(aula__in=aulas).values('estudiante').distinct().count()
        context['planes_por_lapso'] = PlanEvaluacion.objects.filter(aula__in=aulas).values('lapso').annotate(total=Count('id')).order_by('lapso')
        return context


class ProfesorAulaListView(ProfesorRequiredMixin, ListView):
    model = AulaVirtual
    template_name = 'evaluaciones/profesor_aula_list.html'
    context_object_name = 'aulas'

    def get_queryset(self) -> QuerySet[AulaVirtual]:
        return AulaVirtual.objects.filter(profesor__usuario=self.request.user).order_by('-fecha_creacion')


class ProfesorAulaDetailView(ProfesorRequiredMixin, DetailView):
    model = AulaVirtual
    template_name = 'evaluaciones/profesor_aula_detail.html'
    context_object_name = 'aula'

    def get_queryset(self) -> QuerySet[AulaVirtual]:
        return AulaVirtual.objects.filter(profesor__usuario=self.request.user)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['estudiantes'] = Estudiante.objects.filter(matriculas__aula=self.object).distinct()
        context['planes'] = PlanEvaluacion.objects.filter(aula=self.object).order_by('lapso')
        context['puede_enviar_notas'] = any(
            plan.finalizado
            or EvaluacionObjetivo.objects.filter(plan=plan).exists()
            or Calificacion.objects.filter(actividad__plan=plan).exists()
            for plan in context['planes']
        )
        context['lapsos_estado'] = []
        lapsos_ocupados = {plan.lapso for plan in context['planes']}
        for value, label in PlanEvaluacion._meta.get_field('lapso').choices:
            context['lapsos_estado'].append({
                'valor': value,
                'label': label,
                'ocupado': value in lapsos_ocupados,
            })
        return context


class ProfesorEstudianteListView(ProfesorRequiredMixin, ListView):
    model = Estudiante
    template_name = 'evaluaciones/profesor_estudiante_list.html'
    context_object_name = 'estudiantes'

    def get_queryset(self) -> QuerySet[Estudiante]:
        return Estudiante.objects.filter(matriculas__aula__profesor__usuario=self.request.user).distinct().order_by('usuario__apellidos', 'usuario__nombres')


class ProfesorEstudianteDetailView(ProfesorRequiredMixin, DetailView):
    model = Estudiante
    template_name = 'evaluaciones/profesor_estudiante_detail.html'
    context_object_name = 'estudiante'

    def get_queryset(self) -> QuerySet[Estudiante]:
        return Estudiante.objects.filter(matriculas__aula__profesor__usuario=self.request.user).distinct()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['aulas'] = AulaVirtual.objects.filter(matriculas__estudiante=self.object).order_by('año_curso')
        context['calificaciones'] = Calificacion.objects.filter(estudiante=self.object).select_related('actividad', 'actividad__plan')
        return context


class PlanEvaluacionListView(ProfesorRequiredMixin, ListView):
    model = PlanEvaluacion
    template_name = 'evaluaciones/plan_list.html'
    context_object_name = 'planes'

    def get_queryset(self) -> QuerySet[PlanEvaluacion]:
        return PlanEvaluacion.objects.filter(aula__profesor__usuario=self.request.user).select_related('aula').order_by('-pk')


class PlanEvaluacionDetailView(ProfesorRequiredMixin, DetailView):
    model = PlanEvaluacion
    template_name = 'evaluaciones/plan_detail.html'
    context_object_name = 'plan'

    def get_queryset(self) -> QuerySet[PlanEvaluacion]:
        return PlanEvaluacion.objects.filter(aula__profesor__usuario=self.request.user).select_related('aula')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['actividades'] = Actividad.objects.filter(plan=self.object).order_by('fecha')
        return context


class EvaluarObjetivoView(ProfesorRequiredMixin, View):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        plan = get_object_or_404(PlanEvaluacion, pk=kwargs['pk'], aula__profesor__usuario=request.user)
        objetivo_index = int(kwargs.get('objetivo_index', 0))
        objetivos = plan.objetivos_detallados or []
        if objetivo_index < 0 or objetivo_index >= len(objetivos):
            raise PermissionDenied
        objetivo = objetivos[objetivo_index]
        estudiantes = Estudiante.objects.filter(matriculas__aula=plan.aula).distinct()
        evaluations = list(EvaluacionObjetivo.objects.filter(plan=plan, objetivo_index=objetivo_index).order_by('estudiante__usuario__apellidos', 'estudiante__usuario__nombres'))
        context = {
            'plan': plan,
            'objetivo': objetivo,
            'objetivo_index': objetivo_index,
            'estudiantes': estudiantes,
            'evaluations': evaluations,
            'finalizado': plan.finalizado,
        }
        return render(request, 'evaluaciones/evaluar_objetivo.html', context)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        plan = get_object_or_404(PlanEvaluacion, pk=kwargs['pk'], aula__profesor__usuario=request.user)
        objetivo_index = int(kwargs.get('objetivo_index', 0))
        objetivos = plan.objetivos_detallados or []
        if objetivo_index < 0 or objetivo_index >= len(objetivos):
            raise PermissionDenied
        objetivo = objetivos[objetivo_index]
        estudiantes = Estudiante.objects.filter(matriculas__aula=plan.aula).distinct()
        for estudiante in estudiantes:
            raw = request.POST.get(f'nota_{estudiante.pk}')
            if raw in {None, ''}:
                continue
            nota = Decimal(str(raw))
            ponderacion = Decimal(str(objetivo[2])) if len(objetivo) > 2 else Decimal('0.00')
            if nota > ponderacion:
                continue
            evaluacion, created = EvaluacionObjetivo.objects.update_or_create(
                plan=plan,
                estudiante=estudiante,
                objetivo_index=objetivo_index,
                defaults={
                    'objetivo': objetivo[0],
                    'nota_obtenida': nota,
                    'observacion': request.POST.get(f'observacion_{estudiante.pk}', ''),
                    'finalizado': False,
                },
            )
        plan.finalizado = bool(request.POST.get('finalizado'))
        plan.publicado_para_estudiantes = plan.publicado_para_estudiantes or plan.finalizado
        plan.notas_enviadas_al_admin = plan.notas_enviadas_al_admin or plan.finalizado
        plan.save(update_fields=['finalizado', 'publicado_para_estudiantes', 'notas_enviadas_al_admin'])
        return redirect('evaluaciones:profesor_plan_detalle', pk=plan.pk)


class PlanEvaluacionCreateView(ProfesorRequiredMixin, CreateView):
    model = PlanEvaluacion
    form_class = PlanEvaluacionForm
    template_name = 'evaluaciones/plan_form.html'

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        aula = self.object.aula
        return reverse_lazy('evaluaciones:profesor_aula_detalle', kwargs={'pk': aula.pk})


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
        kwargs['cedula_search'] = self.request.GET.get('cedula_search', '') or self.request.POST.get('cedula_search', '')
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['aulas'] = AulaVirtual.objects.filter(profesor__usuario=self.request.user).order_by('año_curso')
        context['aula'] = self.get_aula()
        context['cedula_search'] = self.request.GET.get('cedula_search', '')
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


class EvaluarPlanView(ProfesorRequiredMixin, TemplateView):
    template_name = 'evaluaciones/evaluar_plan.html'

    def _save_calificacion(self, actividad: Actividad, estudiante: Estudiante, nota_valor: str | None, observacion: str) -> None:
        if nota_valor in {None, '', 'null'}:
            return
        nota = Decimal(str(nota_valor))
        if nota > actividad.puntuacion:
            return
        calificacion, created = Calificacion.objects.get_or_create(
            actividad=actividad,
            estudiante=estudiante,
            defaults={'nota_obtenida': nota, 'observacion': observacion},
        )
        if created:
            return
        calificacion.nota_obtenida = nota
        calificacion.observacion = observacion
        calificacion.save(update_fields=['nota_obtenida', 'observacion'])

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        plan = get_object_or_404(PlanEvaluacion, pk=kwargs['pk'], aula__profesor__usuario=self.request.user)
        estudiantes = Estudiante.objects.filter(matriculas__aula=plan.aula).distinct()
        actividades = Actividad.objects.filter(plan=plan).order_by('fecha')
        evaluaciones: list[dict[str, Any]] = []

        for estudiante in estudiantes:
            items = []
            for actividad in actividades:
                calificacion = Calificacion.objects.filter(actividad=actividad, estudiante=estudiante).first()
                items.append({
                    'actividad': actividad,
                    'calificacion': calificacion,
                    'nota': calificacion.nota_obtenida if calificacion else '',
                    'observacion': calificacion.observacion if calificacion else '',
                })
            evaluaciones.append({'estudiante': estudiante, 'items': items})

        context['plan'] = plan
        context['aula'] = plan.aula
        context['estudiantes'] = estudiantes
        context['actividades'] = actividades
        context['evaluaciones'] = evaluaciones
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        plan = get_object_or_404(PlanEvaluacion, pk=kwargs['pk'], aula__profesor__usuario=request.user)
        estudiantes = Estudiante.objects.filter(matriculas__aula=plan.aula).distinct()
        created_count = 0
        updated_count = 0

        for estudiante in estudiantes:
            for actividad in Actividad.objects.filter(plan=plan):
                nota_raw = request.POST.get(f'nota_{estudiante.pk}_{actividad.pk}')
                observacion = request.POST.get(f'observacion_{estudiante.pk}_{actividad.pk}', '')
                existing = Calificacion.objects.filter(actividad=actividad, estudiante=estudiante).first()
                if existing is None:
                    created_count += 1
                else:
                    updated_count += 1
                self._save_calificacion(actividad, estudiante, nota_raw, observacion)

        return redirect('evaluaciones:profesor_plan_detalle', pk=plan.pk)


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

            existing = Calificacion.objects.filter(actividad=actividad, estudiante=estudiante).first()
            if existing is None:
                created_count += 1
            else:
                updated_count += 1
            self._save_calificacion(actividad, estudiante, nota_valor, observacion)

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


class EnviarNotasAdminView(ProfesorRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        aula = get_object_or_404(AulaVirtual, pk=kwargs['pk_aula'], profesor__usuario=request.user)
        planes = PlanEvaluacion.objects.filter(aula=aula)
        for plan in planes:
            plan.notas_enviadas_al_admin = True
            plan.save(update_fields=['notas_enviadas_al_admin'])
        return redirect('evaluaciones:profesor_aula_detalle', pk=aula.pk)


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


class EstudianteAulasListView(EstudianteRequiredMixin, ListView):
    model = AulaVirtual
    template_name = 'evaluaciones/estudiante_aulas.html'
    context_object_name = 'aulas'

    def get_queryset(self) -> QuerySet[AulaVirtual]:
        estudiante = getattr(self.request.user, 'estudiante', None)
        if estudiante is None:
            return AulaVirtual.objects.none()
        return AulaVirtual.objects.filter(matriculas__estudiante=estudiante).select_related('profesor__usuario').order_by('año_curso', 'fecha_creacion')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        estudiante = getattr(self.request.user, 'estudiante', None)
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
        evaluaciones_objetivo = EvaluacionObjetivo.objects.none()
        plan_rows: list[dict[str, Any]] = []

        if estudiante is not None and self.object is not None:
            planes = PlanEvaluacion.objects.filter(
                aula=self.object,
            ).order_by('lapso')
            planes = [plan for plan in planes if is_plan_visible_for_student(plan, estudiante)]
            calificaciones = Calificacion.objects.filter(estudiante=estudiante, actividad__plan__aula=self.object).select_related('actividad', 'actividad__plan')
            evaluaciones_objetivo = EvaluacionObjetivo.objects.filter(estudiante=estudiante, plan__aula=self.object)
            for plan in planes:
                evaluaciones_por_objetivo = {
                    evaluacion.objetivo_index: evaluacion
                    for evaluacion in evaluaciones_objetivo.filter(plan=plan)
                }
                filas = []
                puntos_evaluados = Decimal('0.00')
                puntos_acumulados = Decimal('0.00')
                for objetivo_index_row, objetivo_row in enumerate(plan.objetivos_detallados or []):
                    objetivo_text = objetivo_row[0] if len(objetivo_row) > 0 else ''
                    evaluacion = evaluaciones_por_objetivo.get(objetivo_index_row)
                    if evaluacion is not None:
                        ponderacion = Decimal(str(objetivo_row[2] if len(objetivo_row) > 2 else 0))
                        puntos_evaluados += ponderacion
                        puntos_acumulados += evaluacion.nota_obtenida
                    filas.append({
                        'objetivo': objetivo_text,
                        'metodo': objetivo_row[1] if len(objetivo_row) > 1 else '',
                        'puntuacion': objetivo_row[2] if len(objetivo_row) > 2 else 0,
                        'evaluacion': evaluacion,
                    })
                plan_rows.append({
                    'plan': plan,
                    'filas': filas,
                    'puntos_evaluados': puntos_evaluados,
                    'puntos_acumulados': puntos_acumulados,
                })

        context['planes'] = planes
        context['calificaciones'] = calificaciones
        context['evaluaciones_objetivo'] = evaluaciones_objetivo
        context['plan_rows'] = plan_rows
        return context


class EstudiantePlanesView(EstudianteRequiredMixin, ListView):
    model = PlanEvaluacion
    template_name = 'evaluaciones/estudiante_planes.html'
    context_object_name = 'planes'

    def get_queryset(self) -> QuerySet[PlanEvaluacion]:
        estudiante = getattr(self.request.user, 'estudiante', None)
        if estudiante is None:
            return PlanEvaluacion.objects.none()
        plans = PlanEvaluacion.objects.filter(aula__matriculas__estudiante=estudiante).select_related('aula').order_by('aula__año_curso', 'lapso')
        return [plan for plan in plans if is_plan_visible_for_student(plan, estudiante)]


class EstudiantePlanDetailView(EstudianteRequiredMixin, DetailView):
    model = PlanEvaluacion
    template_name = 'evaluaciones/estudiante_plan_detail.html'
    context_object_name = 'plan'

    def get_queryset(self) -> QuerySet[PlanEvaluacion]:
        estudiante = getattr(self.request.user, 'estudiante', None)
        if estudiante is None:
            return PlanEvaluacion.objects.none()
        return PlanEvaluacion.objects.filter(aula__matriculas__estudiante=estudiante)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        estudiante = getattr(self.request.user, 'estudiante', None)
        if self.object is None or not is_plan_visible_for_student(self.object, estudiante):
            context['actividades'] = []
            context['calificaciones'] = []
            context['evaluaciones_objetivo'] = []
            context['objetivos_con_evaluaciones'] = []
            return context
        evaluaciones_objetivo = list(EvaluacionObjetivo.objects.filter(estudiante=estudiante, plan=self.object))
        evaluaciones_por_objetivo = {evaluacion.objetivo_index: evaluacion for evaluacion in evaluaciones_objetivo}
        objetivos_con_evaluaciones = []

        for objetivo_index_row, objetivo_row in enumerate(self.object.objetivos_detallados or []):
            objetivo_text = objetivo_row[0] if len(objetivo_row) > 0 else ''
            objetivos_con_evaluaciones.append({
                'objetivo': objetivo_text,
                'metodo': objetivo_row[1] if len(objetivo_row) > 1 else '',
                'puntuacion': objetivo_row[2] if len(objetivo_row) > 2 else 0,
                'evaluacion': evaluaciones_por_objetivo.get(objetivo_index_row),
            })

        context['actividades'] = Actividad.objects.filter(plan=self.object).order_by('fecha')
        context['calificaciones'] = Calificacion.objects.filter(estudiante=estudiante, actividad__plan=self.object)
        context['evaluaciones_objetivo'] = evaluaciones_objetivo
        context['objetivos_con_evaluaciones'] = objetivos_con_evaluaciones
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
                planes = PlanEvaluacion.objects.filter(
                    aula=matricula.aula,
                ).order_by('lapso')
                planes = [plan for plan in planes if is_plan_visible_for_student(plan, estudiante)]
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
                            'tipo': 'actividad',
                            'titulo': actividad.titulo,
                            'actividad': actividad,
                            'calificacion': calificacion,
                            'nota_obtenida': calificacion.nota_obtenida if calificacion else None,
                            'observacion': calificacion.observacion if calificacion else '',
                            'ponderacion': actividad.puntuacion,
                        })

                    evaluaciones_objetivo = EvaluacionObjetivo.objects.filter(plan=plan, estudiante=estudiante).order_by('objetivo_index')
                    objetivos_detallados = plan.objetivos_detallados or []
                    for objetivo_index, objetivo_row in enumerate(objetivos_detallados):
                        objetivo_text = objetivo_row[0] if len(objetivo_row) > 0 else ''
                        evaluacion = evaluaciones_objetivo.filter(objetivo_index=objetivo_index).first()
                        detalle.append({
                            'tipo': 'objetivo',
                            'titulo': objetivo_text or f'Objetivo {objetivo_index + 1}',
                            'objetivo': objetivo_text,
                            'calificacion': evaluacion,
                            'nota_obtenida': evaluacion.nota_obtenida if evaluacion else None,
                            'observacion': evaluacion.observacion if evaluacion else '',
                            'ponderacion': objetivo_row[2] if len(objetivo_row) > 2 else None,
                        })

                    if not detalle and not actividades:
                        detalle.append({
                            'tipo': 'info',
                            'titulo': 'Sin registros aún',
                            'nota_obtenida': None,
                            'observacion': 'Aún no hay calificaciones ni actividades disponibles para este plan.',
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
