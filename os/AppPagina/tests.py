from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Producto, Perfil
from django.contrib.messages import get_messages
from decimal import Decimal
from unittest.mock import patch

class AutenticacionTests(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('AppPagina.views.send_mail')
    def test_tc04_registro_con_email_duplicado(self, mock_mail):
        """Caso TC-04: Validar que no se permitan correos repetidos"""
        # Crear primer usuario
        User.objects.create_user(username='user1', email='test@os.com', password='pass123')
        
        # Intentar registrar otro con mismo email
        response = self.client.post(reverse('registro'), {
            'username': 'user2',
            'email': 'test@os.com',
            'password': 'pass123',
            'password2': 'pass123'
        }, follow=True)
        
        # Verificar el mensaje de error directamente
        messages = list(get_messages(response.wsgi_request))
        # Verificamos que al menos uno de los mensajes contenga el error esperado
        self.assertTrue(any("ya está registrado" in str(m) for m in messages))
        self.assertTrue(any(m.tags == "error" for m in messages))

    @patch('AppPagina.views.send_mail')
    def test_tc05_verificacion_de_cuenta(self, mock_mail):
        """Caso TC-05: Validar que el código active al usuario"""
        user = User.objects.create_user(username='newuser', email='new@os.com', password='pass123', is_active=False)
        perfil = user.perfil
        perfil.codigo_verificacion = "123456"
        perfil.save()

        # IMPORTANTE: Inyectar el ID en la sesión para que la vista lo reconozca
        session = self.client.session
        session['user_id_verificar'] = user.id
        session.save()

        # Simular ingreso de código
        response = self.client.post(reverse('verificar_email'), {'codigo': '123456'}, follow=True)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        
        # Verificar el mensaje de éxito directamente
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "¡Cuenta creada exitosamente! Ya puedes iniciar sesión.")
        self.assertEqual(messages[0].tags, "success")
        
        self.assertNotIn('user_id_verificar', self.client.session) # Asegurarse de que la sesión se limpió

class InventarioTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='admin', email='a@a.com', password='123')
        self.client.login(username='admin', password='123')

    def test_tc01_filtrado_stock_bajo(self):
        """Caso TC-01: Validar filtro de stock <= min_stock"""
        Producto.objects.create(nombre="A", precio=10, stock=2, min_stock=5, talla="M") # Bajo
        Producto.objects.create(nombre="B", precio=10, stock=10, min_stock=5, talla="M") # Normal
        
        response = self.client.get(reverse('inventario'), {'low_stock': 'on'})
        self.assertEqual(len(response.context['productos']), 1)
        self.assertEqual(response.context['productos'][0].nombre, "A")

    def test_tc02_creacion_producto_por_tallas(self):
        """Caso TC-02: Validar creación múltiple de tallas"""
        data = {
            'tipo_producto': 'seleccion',
            'nombre': 'Colombia',
            'descripcion': 'Equipación Local',
            'tipo_ropa': 'Camiseta',
            'genero': 'Hombre',
            'stock_S': '5',
            'precio_S': '50000',
            'min_stock_S': '1',
            'stock_M': '10',
            'precio_M': '50000',
            'min_stock_M': '2',
        }
        self.client.post(reverse('producmanual'), data)
        # Deben existir 2 productos ahora
        self.assertEqual(Producto.objects.filter(nombre="Colombia").count(), 2)

    def test_tc03_validacion_precio_negativo(self):
        """Caso TC-03: Validar que no acepte precios menores a 0"""
        data = {
            'tipo_producto': 'seleccion',
            'nombre': 'Colombia',
            'descripcion': 'Equipación Local',
            'tipo_ropa': 'Camiseta',
            'genero': 'Hombre',
            'stock_M': '10',
            'precio_M': '-100', # Error aquí
            'min_stock_M': '1',
        }
        response = self.client.post(reverse('producmanual'), data, follow=True)
        
        # Verificar el mensaje de error directamente
        messages = list(get_messages(response.wsgi_request))
        # Buscamos si el mensaje existe en la lista de mensajes de Django
        self.assertTrue(any("no puede ser negativo" in str(m) for m in messages))
        self.assertTrue(any(m.tags == "error" for m in messages))
        self.assertEqual(Producto.objects.filter(nombre="Colombia").count(), 0) # Corregido el nombre del filtro