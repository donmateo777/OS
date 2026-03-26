from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.core.mail import send_mail
from django.contrib import messages
from .forms import UserRegisterForm
from .models import Perfil
import random

# Create your views here.


def principal(request):
    return render(request, 'paginas/principal.html')

def index(request):
    if request.user.is_authenticated:
        return redirect('principal')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('principal')
    else:
        form = AuthenticationForm()
    return render(request, 'paginas/index.html', {'form': form})

def inventario(request):
    return render(request, 'paginas/inventario.html')

def registro(request):
    if request.user.is_authenticated:
        return redirect('principal')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # El usuario no puede entrar hasta verificar
            user.save()
            
            # Generar código de 6 dígitos
            codigo = str(random.randint(100000, 999999))
            Perfil.objects.create(user=user, codigo_verificacion=codigo)
            
            # Enviar el "correo"
            send_mail(
                'Código de Verificación OS Store',
                f'Tu código de seguridad es: {codigo}',
                'noreply@osstore.com',
                [user.email],
                fail_silently=False,
            )
            
            # Guardamos el ID en la sesión para saber a quién verificar
            request.session['user_id_verificar'] = user.id
            return redirect('verificar_email')
    else:
        form = UserRegisterForm()
    return render(request, 'paginas/registro.html', {'form': form})

def verificar_email(request):
    user_id = request.session.get('user_id_verificar')
    if not user_id:
        return redirect('registro')
        
    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo')
        try:
            perfil = Perfil.objects.get(user_id=user_id, codigo_verificacion=codigo_ingresado)
            user = perfil.user
            user.is_active = True
            user.save()
            perfil.delete() # El código ya no es necesario
            
            # Agregamos el mensaje de éxito
            messages.success(request, '¡Cuenta creada exitosamente! Ya puedes iniciar sesión.')
            
            # Limpiamos el ID de la sesión de verificación
            request.session.pop('user_id_verificar', None)
            
            return redirect('index')
        except Perfil.DoesNotExist:
            return render(request, 'paginas/verificar_email.html', {'error': 'Código incorrecto o expirado'})
            
    return render(request, 'paginas/verificar_email.html')

def cerrar_sesion(request):
    logout(request)
    return redirect('index')

def producmanual(request):
    return render(request, 'paginas/producmanual.html')

def perfil(request):
    return render(request, 'paginas/perfil.html')

def editperfil(request):
    return render(request, 'paginas/editperfil.html')
