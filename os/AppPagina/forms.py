from django import forms
from .models import Producto, Categoria
from django.contrib.auth.forms import UserCreationForm

# Reutilizamos el UserRegisterForm existente si ya lo tienes,
# si no, puedes definirlo aquí o asegurarte de que exista.
class UserRegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['categoria', 'nombre', 'descripcion', 'precio', 'imagen', 'stock', 'disponible']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-control-neon'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control-neon', 'placeholder': 'Ej: Camiseta Local 2024'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control-neon', 'rows': 3, 'placeholder': 'Detalles del material, talla, etc.'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control-neon', 'placeholder': '0.00'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control-neon', 'placeholder': 'Cantidad inicial'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }