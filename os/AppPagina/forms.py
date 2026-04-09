from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Producto

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico', required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'stock', 'min_stock', 'talla']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control-neon', 'placeholder': 'Ej: Camiseta de la Selección Colombia'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control-neon', 'rows': 3, 'placeholder': 'Ej: Equipación local, visitante, etc...'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control-neon', 'placeholder': 'Ej:75000'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control-neon', 'placeholder': 'Cantidad total'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control-neon', 'placeholder': 'Stock mínimo para alerta'}),
            'talla': forms.Select(attrs={'class': 'form-control-neon'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductoForm, self).__init__(*args, **kwargs)
        # Si estamos agregando un producto nuevo (no hay instancia ID),
        # quitamos los campos que se manejarán por talla en el template.
        if not self.instance.pk:
            if 'precio' in self.fields: del self.fields['precio']
            if 'stock' in self.fields: del self.fields['stock']
            if 'min_stock' in self.fields: del self.fields['min_stock']
            if 'talla' in self.fields: del self.fields['talla']