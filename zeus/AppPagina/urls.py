from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('inventario/', views.inventario, name='inventario'),
    path('principal/', views.principal, name='principal'),
    path('registro/', views.registro, name='registro'),
    path('producmanual/', views.producmanual, name='producmanual'),
    path('perfil/', views.perfil, name='perfil'),
    path('editperfil/', views.editperfil, name='editperfil'),
]