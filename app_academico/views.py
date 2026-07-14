from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, QuerySet
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView

from app_evaluaciones.models import PlanEvaluacion

# TODO: Cuando P1 termine, descomenta la siguiente línea y borra LoginRequiredMixin
# from app_usuarios.permisos import AdminRequiredMixin

from app_usuarios.models import Usuario

from .forms import AulaVirtualForm, UsuarioSearchForm
from .models import AulaVirtual, Estudiante, Matricula, Profesor


# --- DASHBOARD ADMIN ---
class AdminDashboardView(LoginRequiredMixin, TemplateView): # TODO: Cambiar a AdminRequiredMixin
    template_name = 'admin/dashboard.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['total_aulas'] = AulaVirtual.objects.count()
        context['total_profesores'] = Usuario.objects.filter(rol='PROFESOR').count()
        context['total_estudiantes'] = Usuario.objects.filter(rol='ESTUDIANTE').count()
        context['aulas_por_anio'] = AulaVirtual.objects.values('año_curso').annotate(total=Count('id')).order_by('año_curso')
        return context


# --- CRUD AULAS ---
class AulaListView(LoginRequiredMixin, ListView): # TODO: Cambiar a AdminRequiredMixin
    model = AulaVirtual
    template_name = 'admin/aula_list.html'
    context_object_name = 'aulas'
    paginate_by = 10

    def get_queryset(self) -> QuerySet[AulaVirtual]:
        queryset = super().get_queryset()
        año = self.request.GET.get('año')
        if año:
            queryset = queryset.filter(año_curso=año)
        return queryset


class AulaDetailView(LoginRequiredMixin, DetailView): # TODO: Cambiar a AdminRequiredMixin
    model = AulaVirtual
    template_name = 'admin/aula_detail.html'
    context_object_name = 'aula'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        for plan in self.object.planes.all():
            approved = f'aprobado_{plan.pk}' in request.POST
            plan.aprobado_por_admin = approved
            plan.save(update_fields=['aprobado_por_admin'])
        return redirect('academico:aula_list')


class AulaCreateView(LoginRequiredMixin, CreateView): # TODO: Cambiar a AdminRequiredMixin
    model = AulaVirtual
    form_class = AulaVirtualForm
    template_name = 'admin/aula_form.html'

    def get_success_url(self) -> str:
        return reverse_lazy('academico:aula_detail', kwargs={'pk': self.object.pk})


class AulaUpdateView(LoginRequiredMixin, UpdateView): # TODO: Cambiar a AdminRequiredMixin
    model = AulaVirtual
    form_class = AulaVirtualForm
    template_name = 'admin/aula_form.html'

    def get_success_url(self) -> str:
        return reverse_lazy('academico:aula_detail', kwargs={'pk': self.object.pk})

    def get_initial(self) -> dict[str, Any]:
        initial = super().get_initial()
        if self.object.lapsos:
            initial['lapsos'] = self.object.lapsos
        return initial


class AulaDeleteView(LoginRequiredMixin, DeleteView): # TODO: Cambiar a AdminRequiredMixin
    model = AulaVirtual
    template_name = 'admin/aula_confirm_delete.html'
    success_url = reverse_lazy('academico:aula_list')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['aula'] = self.object
        return context


# --- LISTA DE USUARIOS ---
class UsuarioListView(LoginRequiredMixin, ListView): # TODO: Cambiar a AdminRequiredMixin
    model = Usuario
    template_name = 'admin/usuario_list.html'
    context_object_name = 'usuarios'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_form = UsuarioSearchForm(self.request.GET)
        if search_form.is_valid():
            q = search_form.cleaned_data.get('q')
            if q:
                queryset = queryset.filter(
                    Q(cedula__icontains=q) | 
                    Q(nombres__icontains=q) | 
                    Q(apellidos__icontains=q) | 
                    Q(email__icontains=q)
                )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = UsuarioSearchForm(self.request.GET)
        return context


class UsuarioDeleteView(LoginRequiredMixin, DeleteView): # TODO: Cambiar a AdminRequiredMixin
    model = Usuario
    template_name = 'admin/usuario_confirm_delete.html'
    success_url = reverse_lazy('academico:usuario_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = self.object
        return context


class ProfesorListView(LoginRequiredMixin, ListView):
    model = Profesor
    template_name = 'admin/profesor_list.html'
    context_object_name = 'profesores'


class ProfesorDetailView(LoginRequiredMixin, DetailView):
    model = Profesor
    template_name = 'admin/profesor_detail.html'
    context_object_name = 'profesor'

    def get_object(self, queryset=None):
        queryset = queryset or self.get_queryset()
        pk = self.kwargs.get(self.pk_url_kwarg)
        return queryset.filter(pk=pk).first()


class EstudianteListView(LoginRequiredMixin, ListView):
    model = Estudiante
    template_name = 'admin/estudiante_list.html'
    context_object_name = 'estudiantes'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('usuario').order_by('usuario__apellidos', 'usuario__nombres', 'usuario__cedula')
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(usuario__cedula__icontains=q) |
                Q(usuario__nombres__icontains=q) |
                Q(usuario__apellidos__icontains=q)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context


class EstudianteDetailView(LoginRequiredMixin, DetailView):
    model = Estudiante
    template_name = 'admin/estudiante_detail.html'
    context_object_name = 'estudiante'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        representante = request.POST.get('representante', '').strip()
        telefono_representante = request.POST.get('telefono_representante', '').strip()

        self.object.representante = representante
        self.object.telefono_representante = telefono_representante
        self.object.save(update_fields=['representante', 'telefono_representante'])
        return redirect('academico:estudiante_list')