from django.http import HttpResponse

from django.shortcuts import render

# Create your views here.


def principal(request):
    return render(request, 'paginas/principal.html')

def index(request):
    return render(request, 'paginas/index.html')

def inventario(request):
    return render(request, 'paginas/inventario.html')

def registro(request):
    return render(request, 'paginas/registro.html')

def producmanual(request):
    return render(request, 'paginas/producmanual.html')


