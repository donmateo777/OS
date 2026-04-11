from django.http import HttpResponse
from decimal import Decimal, InvalidOperation
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.core.mail import send_mail
from django.contrib import messages
from .forms import UserRegisterForm, ProductoForm
from .models import Perfil, Producto
from django.core.paginator import Paginator
from django.db.models import F
from django.db.models.functions import Lower
from django.conf import settings
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
    letra_query = request.GET.get('letra', 'Todas')
    talla_query = request.GET.get('talla', 'Todas')
    q = request.GET.get('q', '')
    sort_by = request.GET.get('sort_by', 'nombre') # Por defecto ordenar por nombre
    order = request.GET.get('order', 'asc') # Por defecto orden ascendente
    low_stock_filter = request.GET.get('low_stock', 'off') # Por defecto filtro de stock bajo desactivado

    # Aplicar filtro por letra inicial
    if letra_query and letra_query != "Todas":
        productos = productos.filter(nombre__istartswith=letra_query)

    # Aplicar búsqueda por texto
    if q:
        productos = productos.filter(nombre__icontains=q)

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

    # Paginación: 10 productos por página
    paginator = Paginator(productos, 10)
    page_number = request.GET.get('page')
    productos_paginados = paginator.get_page(page_number)

    context = {
        'productos': productos_paginados,
        'letra_seleccionada': letra_query,
        'talla_seleccionada': talla_query,
        'sort_by': sort_by,
        'order': order,
        'low_stock_filter': low_stock_filter == 'on', # Convertir a booleano para el checkbox
        'search_query': q,
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
                settings.DEFAULT_FROM_EMAIL,
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
        form = ProductoForm(request.POST) # Este formulario solo contendrá nombre y descripción
        if form.is_valid():
            # Guardamos los datos base (nombre y descripción) sin persistir aún en DB
            p_base = form.save(commit=False)

            # Mapeo de categorías a campos de formulario
            mapping_campos = {
                'seleccion': 'nombre',
                'club': 'nombre_club',
                'liga_esp': 'nombre_liga_esp',
                'premier': 'nombre_premier',
                'serie_a': 'nombre_serie_a',
                'bundesliga': 'nombre_bundesliga',
                'europa_otros': 'nombre_europa_otros',
            }

            tipo = form.cleaned_data['tipo_producto']
            
            # Obtenemos el nombre legible de la categoría (ej: "Premier League")
            p_base.categoria = dict(form.fields['tipo_producto'].choices).get(tipo)

            if tipo in mapping_campos:
                p_base.nombre = form.cleaned_data[mapping_campos[tipo]]

            # Asignamos los nuevos campos específicos
            p_base.tipo_uniforme = form.cleaned_data.get('descripcion') # Usamos el select de equipación
            p_base.pieza = form.cleaned_data.get('tipo_ropa')
            p_base.genero = form.cleaned_data.get('genero')

            creado_al_menos_uno = False
            errores_por_talla = []
            tallas_data_for_template = [] # Para repoblar el formulario en caso de error

            # Recorremos las tallas definidas en el modelo
            for talla_val, talla_label in Producto.TALLAS_CHOICES:
                cantidad_str = request.POST.get(f'stock_{talla_val}', '0')
                precio_str = request.POST.get(f'precio_{talla_val}', '')
                min_stock_str = request.POST.get(f'min_stock_{talla_val}', '0')
                
                current_cantidad = 0
                current_precio = None
                current_min_stock = 0

                # Almacenar la entrada actual para repoblar el formulario si hay errores
                tallas_data_for_template.append({
                    'talla_val': talla_val,
                    'talla_label': talla_label,
                    'stock': cantidad_str,
                    'precio': precio_str,
                    'min_stock': min_stock_str,
                })

                # Validar cantidad (stock)
                try:
                    current_cantidad = int(cantidad_str)
                    if current_cantidad < 0:
                        errores_por_talla.append(f'La cantidad para la talla {talla_label} no puede ser negativa.')
                        continue
                except ValueError:
                    if cantidad_str and cantidad_str.strip() != '0': # Solo error si no está vacío y no es '0'
                        errores_por_talla.append(f'La cantidad para la talla {talla_label} debe ser un número entero válido.')
                    continue

                # Validar precio
                if precio_str.strip(): # Solo validar si no está vacío
                    try:
                        precio_str = precio_str.replace(',', '.') # Manejar formato decimal es-co
                        current_precio = Decimal(precio_str)
                        if current_precio < 0:
                            errores_por_talla.append(f'El precio para la talla {talla_label} no puede ser negativo.')
                            continue
                    except InvalidOperation:
                        errores_por_talla.append(f'El precio para la talla {talla_label} debe ser un número válido.')
                        continue
                
                # Validar stock mínimo
                try:
                    current_min_stock = int(min_stock_str)
                    if current_min_stock < 0:
                        errores_por_talla.append(f'El stock mínimo para la talla {talla_label} no puede ser negativo.')
                        continue
                except ValueError:
                    if min_stock_str and min_stock_str.strip() != '0': # Solo error si no está vacío y no es '0'
                        errores_por_talla.append(f'El stock mínimo para la talla {talla_label} debe ser un número entero válido.')
                    continue

                # Solo crear un producto si la cantidad es mayor que 0
                if current_cantidad > 0:
                    if current_precio is None: # El precio es obligatorio si hay stock
                        errores_por_talla.append(f'El precio es obligatorio para la talla {talla_label} si la cantidad es mayor a 0.')
                        continue
                    
                    Producto.objects.create(
                        nombre=p_base.nombre,
                        categoria=p_base.categoria,
                        tipo_uniforme=p_base.tipo_uniforme,
                        pieza=p_base.pieza,
                        genero=p_base.genero,
                        precio=current_precio, # Usar precio específico por talla
                        min_stock=current_min_stock, # Usar stock mínimo específico por talla
                        talla=talla_val,
                        stock=current_cantidad # Usar stock específico por talla
                    )
                    creado_al_menos_uno = True
            
            if errores_por_talla:
                for error in errores_por_talla:
                    messages.error(request, error)
                # Volver a renderizar el formulario con los datos existentes y los errores
                context = {'form': form, 'tallas_data_for_template': tallas_data_for_template}
                return render(request, 'paginas/producmanual.html', context)

            if creado_al_menos_uno:
                messages.success(request, 'Productos agregados correctamente al inventario.')
                return redirect('inventario')
            else:
                messages.error(request, 'Debes ingresar al menos una cantidad en alguna talla para crear un producto.')
                # Volver a renderizar el formulario con los datos existentes
                context = {'form': form, 'tallas_data_for_template': tallas_data_for_template}
                return render(request, 'paginas/producmanual.html', context)
        else: # El formulario principal (nombre/descripción) no es válido
            messages.error(request, 'Por favor, corrige los errores en los campos principales.')
            # También pasar las entradas específicas por talla si estaban presentes
            tallas_data_for_template = []
            for talla_val, talla_label in Producto.TALLAS_CHOICES:
                tallas_data_for_template.append({
                    'talla_val': talla_val, 'talla_label': talla_label,
                    'stock': request.POST.get(f'stock_{talla_val}', ''),
                    'precio': request.POST.get(f'precio_{talla_val}', ''),
                    'min_stock': request.POST.get(f'min_stock_{talla_val}', ''),
                })
            context = {'form': form, 'tallas_data_for_template': tallas_data_for_template}
            return render(request, 'paginas/producmanual.html', context)
    else:
        form = ProductoForm()
        # Inicializar tallas_data_for_template para la solicitud GET
        tallas_data_for_template = []
        for talla_val, talla_label in Producto.TALLAS_CHOICES:
            tallas_data_for_template.append({
                'talla_val': talla_val,
                'talla_label': talla_label,
                'stock': '',
                'precio': '',
                'min_stock': '',
            })
    return render(request, 'paginas/producmanual.html', {'form': form, 'tallas_data_for_template': tallas_data_for_template})

def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            p_edit = form.save(commit=False)

            # Aplicar la misma lógica de mapeo que en producmanual
            mapping_campos = {
                'seleccion': 'nombre',
                'club': 'nombre_club',
                'liga_esp': 'nombre_liga_esp',
                'premier': 'nombre_premier',
                'serie_a': 'nombre_serie_a',
                'bundesliga': 'nombre_bundesliga',
                'europa_otros': 'nombre_europa_otros',
            }

            tipo = form.cleaned_data['tipo_producto']
            p_edit.categoria = dict(form.fields['tipo_producto'].choices).get(tipo)

            if tipo in mapping_campos:
                p_edit.nombre = form.cleaned_data[mapping_campos[tipo]]

            p_edit.tipo_uniforme = form.cleaned_data.get('descripcion')
            p_edit.pieza = form.cleaned_data.get('tipo_ropa')
            p_edit.genero = form.cleaned_data.get('genero')

            p_edit.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('inventario')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
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
