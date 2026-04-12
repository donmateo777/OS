from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import hashlib

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    codigo_verificacion = models.CharField(max_length=6, blank=True, null=True)
    
    def __str__(self):
        return f"Perfil de {self.user.username}"

    @property
    def get_foto_url(self):
        """Genera la URL de la foto de perfil basada en el email (Gravatar)"""
        if self.user.email and '@' in self.user.email:
            email = self.user.email.lower().strip().encode('utf-8')
            hash_email = hashlib.md5(email).hexdigest()
            # d=mp devuelve una silueta si no hay foto, evitando el error de carga
            return f"https://www.gravatar.com/avatar/{hash_email}?d=mp&s=400"
        
        # Si no hay email o Gravatar no tiene foto, usamos iniciales
        nombre_limpio = self.user.username.replace(' ', '+')
        return f"https://ui-avatars.com/api/?name={nombre_limpio}&background=00ccff&color=000&size=400"

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    if hasattr(instance, 'perfil'):
        instance.perfil.save()

class Producto(models.Model):
    TALLAS_CHOICES = [
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('Única', 'Única'),
    ]
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50, blank=True, null=True)
    tipo_uniforme = models.CharField(max_length=50, blank=True, null=True)
    pieza = models.CharField(max_length=50, blank=True, null=True)
    genero = models.CharField(max_length=20, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True) # Lo dejamos por si acaso
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    min_stock = models.IntegerField(default=0)
    talla = models.CharField(max_length=10, choices=TALLAS_CHOICES, default='M')
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    
