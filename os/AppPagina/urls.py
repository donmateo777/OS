from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('principal/', views.principal, name='principal'),
    path('', views.index, name='index'),
    path('inventario/', views.inventario, name='inventario'),
    path('registro/', views.registro, name='registro'),
    path('verificar/', views.verificar_email, name='verificar_email'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('producmanual/', views.producmanual, name='producmanual'),
    path('exportar_pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('editar_producto/<int:id>/', views.editar_producto, name='editar_producto'),
    path('eliminar_producto/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    path('perfil/', views.perfil, name='perfil'),
    path('editperfil/', views.editperfil, name='editperfil'),
    path('verificar_cambio_email/', views.verificar_cambio_email, name='verificar_cambio_email'),
    
    # Recuperación de contraseña con Django
    path(
    'password_reset/',
    auth_views.PasswordResetView.as_view(
        template_name='password_reset_form.html'
    ),
    name='password_reset'
),

path(
    'password_reset_done/',
    auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'
    ),
    name='password_reset_done'
),

path(
    'reset/<uidb64>/<token>/',
    auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html'
    ),
    name='password_reset_confirm'
),

path(
    'reset_complete/',
    auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ),
    name='password_reset_complete'
),
]