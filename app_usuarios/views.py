from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .decorators import role_required
from .forms import LoginForm, UsuarioRegistroForm


def login_view(request: HttpRequest) -> HttpResponse:
    """
    Vista de login adaptada para usar 'cedula' en lugar de 'username'.
    """
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cedula = form.cleaned_data['cedula']
            password = form.cleaned_data['password']
            # ✅ CORRECTO: Usar 'cedula' en lugar de 'username'
            user = authenticate(request, cedula=cedula, password=password)
            if user is not None:
                login(request, user)
                return redirect('usuarios:redirect_por_rol')
            else:
                form.add_error(None, "Cédula o contraseña incorrectos.")

    return render(request, 'registration/login.html', {'form': form})


def register_view(request: HttpRequest) -> HttpResponse:
    """
    Vista de registro adaptada para usar 'cedula' en lugar de 'username'.
    """
    form = UsuarioRegistroForm()
    if request.method == 'POST':
        form = UsuarioRegistroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('usuarios:login')

    return render(request, 'registration/signup.html', {'form': form})


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
@role_required('profesor')
def profesor_panel(request: HttpRequest) -> HttpResponse:
    return render(request, 'profesor/home.html', {'user': request.user})