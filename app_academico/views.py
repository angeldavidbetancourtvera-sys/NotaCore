from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin  # ✅ USAMOS ESTO TEMPORALMENTE
from django.db.models import Count, Q

# TODO: Cuando P1 termine, descomenta la siguiente línea y borra LoginRequiredMixin
# from app_usuarios.permisos import AdminRequiredMixin 

from .models import AulaVirtual, Matricula, Profesor, Estudiante
from app_usuarios.models import Usuario
from .forms import AulaVirtualForm, UsuarioSearchForm


# --- DASHBOARD ADMIN ---
class AdminDashboardView(LoginRequiredMixin, TemplateView): # TODO: Cambiar a AdminRequiredMixin
    template_name = 'admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
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

    def get_queryset(self):
        queryset = super().get_queryset()
        año = self.request.GET.get('año')
        if año:
            queryset = queryset.filter(año_curso=año)
        return queryset


class AulaCreateView(LoginRequiredMixin, CreateView): # TODO: Cambiar a AdminRequiredMixin
    model = AulaVirtual
    form_class = AulaVirtualForm
    template_name = 'admin/aula_form.html'
    success_url = reverse_lazy('academico:aula_list')


class AulaUpdateView(LoginRequiredMixin, UpdateView): # TODO: Cambiar a AdminRequiredMixin
    model = AulaVirtual
    form_class = AulaVirtualForm
    template_name = 'admin/aula_form.html'
    success_url = reverse_lazy('academico:aula_list')

    def get_initial(self):
        initial = super().get_initial()
        if self.object.lapsos:
            initial['lapsos'] = self.object.lapsos
        return initial


class AulaDeleteView(LoginRequiredMixin, DeleteView): # TODO: Cambiar a AdminRequiredMixin
    model = AulaVirtual
    template_name = 'admin/aula_confirm_delete.html'
    success_url = reverse_lazy('academico:aula_list')


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