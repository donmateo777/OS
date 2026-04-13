from django.urls import path
from . import views

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
    
    # Recuperación de contraseña personalizada (Nombres en Español)
    path('escribir_correo/', views.escribir_correo, name='escribir_correo'),
    path('verificar_codigo_correo/', views.verificar_codigo_correo, name='verificar_codigo_correo'),
    path('nueva_contrasena/', views.nueva_contrasena, name='nueva_contrasena'),
]