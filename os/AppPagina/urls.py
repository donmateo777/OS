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
    path('perfil/', views.perfil, name='perfil'),
    path('editperfil/', views.editperfil, name='editperfil'),
]