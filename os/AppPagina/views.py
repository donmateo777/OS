from django.http import HttpResponse
from decimal import Decimal, InvalidOperation
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib import messages
from .forms import UserRegisterForm, ProductoForm, LoginForm, ProfileEditForm
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
            user.email = form.cleaned_data['email']  # 🔥 AGREGA ESTA LÍNEA
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
            # Si el formulario no es válido, extraemos los errores y los mostramos como alertas
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
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
    if not request.user.is_authenticated:
        return redirect('index')
        
    user = request.user
    email_original = user.email
    perfil_obj = user.perfil

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            current_password = form.cleaned_data.get('current_password')
            
            # 1. Validar identidad con la contraseña
            if not request.user.check_password(current_password):
                messages.error(request, 'Contraseña incorrecta. No se guardaron los cambios.')
                return render(request, 'paginas/editperfil.html', {'form': form})

            nuevo_email = form.cleaned_data.get('email').lower().strip()
            nuevo_username = form.cleaned_data.get('username')

            # 2. Si el correo cambió, no guardamos NADA en User todavía
            if nuevo_email != email_original.lower().strip():
                codigo = str(random.randint(100000, 999999))
                perfil_obj.codigo_verificacion = codigo
                perfil_obj.email_temp = nuevo_email
                perfil_obj.username_temp = nuevo_username
                perfil_obj.save()
                
                send_mail(
                    'Verifica tus cambios - OS Store',
                    f'Tu código para validar el cambio de correo es: {codigo}',
                    settings.DEFAULT_FROM_EMAIL,
                    [nuevo_email],
                    fail_silently=False,
                )
                messages.warning(request, 'Confirma el código enviado a tu nuevo correo para aplicar todos los cambios.')
                return redirect('verificar_cambio_email')
            
            # 3. Si el email NO cambió, guardamos el nombre inmediatamente
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'paginas/editperfil.html', {'form': form})

def verificar_cambio_email(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo').strip()
        perfil_obj = request.user.perfil
        if perfil_obj.codigo_verificacion == codigo and perfil_obj.email_temp:
            user = request.user
            # Aplicamos los cambios que estaban en espera
            user.email = perfil_obj.email_temp
            user.username = perfil_obj.username_temp
            user.save()
            
            # Limpiamos los campos temporales
            perfil_obj.codigo_verificacion = ""
            perfil_obj.email_temp = ""
            perfil_obj.username_temp = ""
            perfil_obj.save()
            messages.success(request, '¡Correo actualizado con éxito!')
            return redirect('perfil')
        error = "Código incorrecto o expirado."
        return render(request, 'paginas/verificar_cambio_email.html', {'error': error})
    return render(request, 'paginas/verificar_cambio_email.html')

def escribir_correo(request):
    if request.method == 'POST':
        email = request.POST.get('email').lower().strip()
        try:
            user = User.objects.get(email=email)
            codigo = str(random.randint(100000, 999999))
            perfil = user.perfil
            perfil.codigo_verificacion = codigo
            perfil.save()
            
            send_mail(
                'Código de Restablecimiento OS Store',
                f'Hola {user.username}, tu código para cambiar tu contraseña es: {codigo}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            request.session['email_reset_pass'] = email
            return redirect('verificar_codigo_correo')
        except User.DoesNotExist:
            messages.error(request, "No existe ninguna cuenta asociada a este correo.")
    return render(request, 'paginas/escribir_correo.html')

def verificar_codigo_correo(request):
    email = request.session.get('email_reset_pass')
    if not email: return redirect('escribir_correo')

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo')
        user = User.objects.get(email=email)
        if user.perfil.codigo_verificacion == codigo_ingresado:
            request.session['codigo_reset_verificado'] = True
            return redirect('nueva_contrasena')
        else:
            messages.error(request, "El código ingresado es incorrecto.")
            
    return render(request, 'paginas/verificar_codigo_correo.html', {'email': email})

def nueva_contrasena(request):
    email = request.session.get('email_reset_pass')
    if not email or not request.session.get('codigo_reset_verificado'):
        return redirect('escribir_correo')

    user = User.objects.get(email=email)
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            user.perfil.codigo_verificacion = "" # Limpiar código
            user.perfil.save()
            request.session.flush() # Limpiar sesión por seguridad
            messages.success(request, "¡Contraseña actualizada! Ya puedes iniciar sesión.")
            return redirect('index')
    else:
        form = SetPasswordForm(user)
    # Aplicar clase neon a los campos del form
    for field in form.fields.values(): field.widget.attrs['class'] = 'form-control-neon'
    return render(request, 'paginas/nueva_contrasena.html', {'form': form})