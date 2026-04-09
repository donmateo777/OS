from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.core.mail import send_mail
from django.contrib import messages
from .forms import UserRegisterForm, ProductoForm
from .models import Perfil, Producto
from django.db.models import F
from django.db.models.functions import Lower
import random
import string

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
    productos = Producto.objects.all() # Inicia con todos los productos

    # Obtener parámetros de filtro y ordenamiento de la URL
    letra_query = request.GET.get('letra')
    talla_query = request.GET.get('talla')
    sort_by = request.GET.get('sort_by', 'nombre') # Por defecto ordenar por nombre
    order = request.GET.get('order', 'asc') # Por defecto orden ascendente
    low_stock_filter = request.GET.get('low_stock', 'off') # Por defecto filtro de stock bajo desactivado

    # Aplicar filtro por letra inicial
    if letra_query and letra_query != "Todas":
        productos = productos.filter(nombre__istartswith=letra_query)

    # Aplicar filtro por talla
    if talla_query and talla_query != "Todas":
        productos = productos.filter(talla=talla_query)

    # Aplicar filtro de stock bajo
    if low_stock_filter == 'on':
        productos = productos.filter(stock__lte=F('min_stock'))

    # Preparar el ordenamiento (Normalizamos a minúsculas para el nombre)
    productos = productos.annotate(nombre_min=Lower('nombre'))
    
    if sort_by == 'precio':
        criterio = 'precio'
    elif sort_by == 'talla':
        criterio = 'talla'
    else:
        criterio = 'nombre_min'

    # Aplicar dirección
    if order == 'desc':
        productos = productos.order_by(f'-{criterio}')
    else:
        productos = productos.order_by(criterio)

    context = {
        'productos': productos,
        'letra_seleccionada': letra_query,
        'talla_seleccionada': talla_query,
        'sort_by': sort_by,
        'order': order,
        'low_stock_filter': low_stock_filter == 'on', # Convertir a booleano para el checkbox
        'abecedario': string.ascii_uppercase, # Pasa las letras A-Z al template
        'tallas_disponibles': [c[0] for c in Producto.TALLAS_CHOICES], # Obtiene las tallas del modelo
    }
    return render(request, 'paginas/inventario.html', context)

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
            # El perfil ya se creó automáticamente por el signal, solo lo actualizamos
            perfil = user.perfil
            perfil.codigo_verificacion = codigo
            perfil.save()
            
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
            perfil.codigo_verificacion = "" # Limpiamos el código en lugar de borrar el perfil
            perfil.save()
            
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
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto agregado correctamente al inventario.')
            return redirect('inventario')
    else:
        form = ProductoForm()
    return render(request, 'paginas/producmanual.html', {'form': form})

def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('inventario')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'paginas/producmanual.html', {'form': form, 'editando': True})

def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.delete()
    messages.success(request, 'Producto eliminado del inventario.')
    return redirect('inventario')

def exportar_pdf(request):
    productos = Producto.objects.all()
    template_path = 'paginas/pdf_inventario.html'
    context = {'productos': productos}
    
    # Crear la respuesta HTTP con el tipo de contenido PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Inventario_OS_Store.pdf"'
    
    # Buscar la plantilla y renderizarla con el contexto
    template = get_template(template_path)
    html = template.render(context)

    # Crear el PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
       return HttpResponse('Error al generar el PDF <pre>' + html + '</pre>')
    return response

def perfil(request):
    return render(request, 'paginas/perfil.html')

def editperfil(request):
    return render(request, 'paginas/editperfil.html')
