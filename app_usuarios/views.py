from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .decorators import role_required
from .forms import LoginForm, UsuarioRegistroForm


def login_view(request: HttpRequest) -> HttpResponse:
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('usuarios:redirect_por_rol')

    return render(request, 'registration/login.html', {'form': form})


def register_view(request: HttpRequest) -> HttpResponse:
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
    return redirect('usuarios:dashboard')


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'dashboard.html', {'user': request.user})


@login_required
@role_required('profesor')
def profesor_panel(request: HttpRequest) -> HttpResponse:
    return render(request, 'profesor/home.html', {'user': request.user})
