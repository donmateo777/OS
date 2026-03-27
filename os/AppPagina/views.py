from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.core.mail import send_mail
from django.contrib import messages
from .forms import UserRegisterForm
from .models import Perfil, Producto, Categoria
import random
import openpyxl # Para leer archivos Excel


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
    if request.method == 'POST':
        if 'inventory_file' in request.FILES:
            excel_file = request.FILES['inventory_file']
            if not excel_file.name.endswith('.xlsx'):
                messages.error(request, 'Por favor, sube un archivo Excel válido (.xlsx).')
                return redirect('inventario')

            try:
                workbook = openpyxl.load_workbook(excel_file)
                sheet = workbook.active
                
                # Asumiendo que la primera fila son los encabezados
                # Limpiamos los encabezados para que sean más fáciles de comparar (minúsculas y sin espacios)
                header = [str(cell.value).strip().lower() if cell.value else "" for cell in sheet[1]]
                
                # Diccionario para encontrar la posición de cada columna requerida
                col_map = {}
                for i, h in enumerate(header):
                    if 'nom' in h: col_map['nombre'] = i
                    elif 'pre' in h: col_map['precio'] = i
                    elif 'sto' in h: col_map['stock'] = i
                    elif 'des' in h: col_map['descripcion'] = i
                    elif 'cat' in h: col_map['categoria'] = i

                # Validación básica para columnas requeridas
                if not all(k in col_map for k in ['nombre', 'precio', 'stock']):
                    messages.error(request, 'El archivo Excel debe contener las columnas "Nombre", "Precio" y "Stock".')
                    return redirect('inventario')

                products_added = 0
                for row_idx in range(2, sheet.max_row + 1): # Empezar desde la segunda fila (después de los encabezados)
                    row = [cell.value for cell in sheet[row_idx]]
                    if not row or not any(row): continue # Saltar filas vacías
                    
                    try:
                        nombre = str(row[col_map['nombre']])
                        precio = float(row[col_map['precio']])
                        stock = int(row[col_map['stock']])
                        
                        # Opcionales
                        desc = str(row[col_map['descripcion']]) if 'descripcion' in col_map and row[col_map['descripcion']] else ""
                        cat_name = str(row[col_map['categoria']]) if 'categoria' in col_map and row[col_map['categoria']] else "General"
                        
                        categoria, _ = Categoria.objects.get_or_create(nombre=cat_name)
                        
                        Producto.objects.create(
                            categoria=categoria, nombre=nombre, descripcion=desc,
                            precio=precio, stock=stock, disponible=True # Por defecto disponible al importar
                        )
                        products_added += 1
                    except Exception as e:
                        messages.warning(request, f'Error al procesar la fila {row_idx}: {e}. Se omitió este producto.')
                        continue
                messages.success(request, f'Se importaron {products_added} productos exitosamente.')
                return redirect('inventario')
            except Exception as e:
                messages.error(request, f'Error al leer el archivo Excel: {e}')
                return redirect('inventario')
    productos = Producto.objects.all().order_by('nombre') # Ordenar productos para una visualización consistente
    return render(request, 'paginas/inventario.html', {'productos': productos})

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

from .forms import ProductoForm # Importa el formulario de producto

def producmanual(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('inventario')
    else:
        form = ProductoForm()
    return render(request, 'paginas/producmanual.html', {'form': form})

def perfil(request):
    return render(request, 'paginas/perfil.html')

def editperfil(request):
    return render(request, 'paginas/editperfil.html')
