from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate

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
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'paginas/registro.html', {'form': form})

def cerrar_sesion(request):
    logout(request)
    return redirect('index')

def producmanual(request):
    return render(request, 'paginas/producmanual.html')

def perfil(request):
    return render(request, 'paginas/perfil.html')

def editperfil(request):
    return render(request, 'paginas/editperfil.html')
