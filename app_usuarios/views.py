from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .decorators import role_required
from .forms import LoginForm, UsuarioRegistroForm


def home_view(request: HttpRequest) -> HttpResponse:
    """Vista inicial del sistema con acceso a login, registro y paneles principales."""
    selected_role = request.GET.get('rol', '')
    return render(request, 'home.html', {'user': request.user, 'selected_role': selected_role})


def login_view(request: HttpRequest) -> HttpResponse:
    """
    Vista de login adaptada para usar 'cedula' en lugar de 'username'.
    """
    selected_role = request.GET.get('rol', '') or request.POST.get('rol', '')
    form = LoginForm(request)
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('usuarios:redirect_por_rol')

    if selected_role:
        form.fields['username'].help_text = f'Iniciando sesión como {selected_role.lower().title()}'

    return render(request, 'registration/login.html', {'form': form, 'selected_role': selected_role})


def register_view(request: HttpRequest) -> HttpResponse:
    """
    Vista de registro adaptada para usar 'cedula' en lugar de 'username'.
    """
    selected_role = request.GET.get('rol', '') or request.POST.get('rol', '')
    form = UsuarioRegistroForm()
    if selected_role:
        form.fields['rol'].initial = selected_role
    if request.method == 'POST':
        form = UsuarioRegistroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('usuarios:login')

    return render(request, 'registration/signup.html', {'form': form, 'selected_role': selected_role})


@login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect('usuarios:login')


@login_required
def redirect_por_rol(request: HttpRequest) -> HttpResponse:
    """
    Redirige al usuario según su rol después del login.
    """
    user = request.user
    if user.rol == 'ADMIN':
        return redirect('academico:admin_dashboard')
    elif user.rol == 'PROFESOR':
        return redirect('evaluaciones:profesor_dashboard')
    elif user.rol == 'ESTUDIANTE':
        return redirect('evaluaciones:estudiante_dashboard')
    else:
        return redirect('usuarios:dashboard')


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'dashboard.html', {'user': request.user})


@login_required
@role_required('PROFESOR')
def profesor_panel(request: HttpRequest) -> HttpResponse:
    return render(request, 'profesor/home.html', {'user': request.user})