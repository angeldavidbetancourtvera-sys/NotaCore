from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.register_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('redirect/', views.redirect_por_rol, name='redirect_por_rol'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profesor/', views.profesor_panel, name='profesor_panel'),
]
