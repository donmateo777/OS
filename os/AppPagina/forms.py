from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Producto

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico', required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicamos el estilo neón y los indicadores visuales a todos los campos
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control-neon'
        
        self.fields['username'].widget.attrs['placeholder'] = 'Mín. 8 caracteres, 1 número y un símbolo (_ # *)'

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 8:
            raise forms.ValidationError("El nombre debe tener al menos 8 letras.")
        if not any(char.isdigit() for char in username):
            raise forms.ValidationError("El nombre debe incluir al menos un número.")
        if not any(char in '_#*' for char in username):
            raise forms.ValidationError("El nombre debe incluir al menos un carácter como barra al piso (_), numeral (#) o asterisco (*).")
        return username

    def clean_email(self):
        """
        Valida que el correo electrónico sea único en la base de datos.
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado. Por favor, utiliza otro.")
        return email

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Correo electrónico', widget=forms.EmailInput(attrs={
        'class': 'form-control-neon',
        'placeholder': 'tu@correo.com'
    }))
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control-neon'}))

class ProfileEditForm(forms.ModelForm):
    email = forms.EmailField(label='Correo electrónico', widget=forms.EmailInput(attrs={
        'class': 'form-control-neon', 
        'placeholder': 'tu@correo.com'
    }))
    current_password = forms.CharField(
        label='Confirmar Cambios (Ingresa tu Contraseña Actual)',
        widget=forms.PasswordInput(attrs={'class': 'form-control-neon', 'placeholder': 'Escribe tu clave actual para guardar'}),
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control-neon',
                'placeholder': 'Mín. 8 caracteres, 1 número y un símbolo (_ # *)'
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 8:
            raise forms.ValidationError("El nombre debe tener al menos 8 letras.")
        if not any(char.isdigit() for char in username):
            raise forms.ValidationError("El nombre debe incluir al menos un número.")
        if not any(char in '_#*' for char in username):
            raise forms.ValidationError("El nombre debe incluir al menos un carácter como barra al piso (_), numeral (#) o asterisco (*).")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso. Por favor, prueba otro.")
        return email

SELECCIONES_CHOICES = [
    ('', 'SELECCIONE UNA SELECCIÓN...'),
    ('Alemania', 'Alemania'),
    ('Argentina', 'Argentina'),
    ('Brasil', 'Brasil'),
    ('Bélgica', 'Bélgica'),
    ('Chile', 'Chile'),
    ('Colombia', 'Colombia'),
    ('Corea del Sur', 'Corea del Sur'),
    ('Croacia', 'Croacia'),
    ('Dinamarca', 'Dinamarca'),
    ('Ecuador', 'Ecuador'),
    ('Egipto', 'Egipto'),
    ('España', 'España'),
    ('Francia', 'Francia'),
    ('Inglaterra', 'Inglaterra'),
    ('Italia', 'Italia'),
    ('Japón', 'Japón'),
    ('Marruecos', 'Marruecos'),
    ('México', 'México'),
    ('Nigeria', 'Nigeria'),
    ('Países Bajos', 'Países Bajos'),
    ('Perú', 'Perú'),
    ('Portugal', 'Portugal'),
    ('Suiza', 'Suiza'),
    ('Uruguay', 'Uruguay'),
    ('USA', 'USA'),
]

CLUBES_COLOMBIA_CHOICES = [
    ('', 'SELECCIONE UN EQUIPO...'),
    ('Alianza FC', 'Alianza FC'),
    ('América de Cali', 'América de Cali'),
    ('Atlético Bucaramanga', 'Atlético Bucaramanga'),
    ('Atlético Nacional', 'Atlético Nacional'),
    ('Boyacá Chicó', 'Boyacá Chicó'),
    ('Deportes Tolima', 'Deportes Tolima'),
    ('Deportivo Cali', 'Deportivo Cali'),
    ('Deportivo Pasto', 'Deportivo Pasto'),
    ('Deportivo Pereira', 'Deportivo Pereira'),
    ('Envigado FC', 'Envigado FC'),
    ('Fortaleza CEIF', 'Fortaleza CEIF'),
    ('Independiente Medellín', 'Independiente Medellín'),
    ('Independiente Santa Fe', 'Independiente Santa Fe'),
    ('Jaguares', 'Jaguares'),
    ('Junior', 'Junior'),
    ('La Equidad', 'La Equidad'),
    ('Millonarios', 'Millonarios'),
    ('Once Caldas', 'Once Caldas'),
    ('Patriotas', 'Patriotas'),
    ('Águilas Doradas', 'Águilas Doradas'),
]

LIGA_ESP_CHOICES = [
    ('', 'SELECCIONE EQUIPO ESPAÑOL...'),
    ('Athletic Club', 'Athletic Club'),
    ('Atlético de Madrid', 'Atlético de Madrid'),
    ('FC Barcelona', 'FC Barcelona'),
    ('Girona FC', 'Girona FC'),
    ('Real Betis', 'Real Betis'),
    ('Real Madrid', 'Real Madrid'),
    ('Real Sociedad', 'Real Sociedad'),
    ('Sevilla FC', 'Sevilla FC'),
    ('Valencia CF', 'Valencia CF'),
    ('Villarreal CF', 'Villarreal CF'),
]

PREMIER_L_CHOICES = [
    ('', 'SELECCIONE EQUIPO PREMIER...'),
    ('Arsenal FC', 'Arsenal FC'),
    ('Aston Villa', 'Aston Villa'),
    ('Chelsea FC', 'Chelsea FC'),
    ('Liverpool FC', 'Liverpool FC'),
    ('Manchester City', 'Manchester City'),
    ('Manchester United', 'Manchester United'),
    ('Newcastle United', 'Newcastle United'),
    ('Tottenham Hotspur', 'Tottenham Hotspur'),
    ('West Ham United', 'West Ham United'),
]

SERIE_A_CHOICES = [
    ('', 'SELECCIONE EQUIPO SERIE A...'),
    ('AC Milan', 'AC Milan'),
    ('AS Roma', 'AS Roma'),
    ('Atalanta BC', 'Atalanta BC'),
    ('Inter de Milán', 'Inter de Milán'),
    ('Juventus FC', 'Juventus FC'),
    ('SS Lazio', 'SS Lazio'),
    ('SSC Napoli', 'SSC Napoli'),
    ('ACF Fiorentina', 'ACF Fiorentina'),
]

BUNDESLIGA_CHOICES = [
    ('', 'SELECCIONE EQUIPO BUNDESLIGA...'),
    ('Bayer Leverkusen', 'Bayer Leverkusen'),
    ('Bayern Múnich', 'Bayern Múnich'),
    ('Borussia Dortmund', 'Borussia Dortmund'),
    ('Eintracht Frankfurt', 'Eintracht Frankfurt'),
    ('RB Leipzig', 'RB Leipzig'),
    ('VfB Stuttgart', 'VfB Stuttgart'),
]

EUROPA_OTROS_CHOICES = [
    ('', 'SELECCIONE OTRO EQUIPO...'),
    ('Al-Nassr', 'Al-Nassr'),
    ('Benfica', 'Benfica'),
    ('Boca Juniors', 'Boca Juniors'),
    ('Inter Miami', 'Inter Miami'),
    ('Olympique Lyon', 'Olympique Lyon'),
    ('Olympique Marsella', 'Olympique Marsella'),
    ('FC Porto', 'FC Porto'),
    ('PSG', 'PSG'),
    ('River Plate', 'River Plate'),
    ('Sporting CP', 'Sporting CP'),
]

EQUIPACION_CHOICES = [
    ('', 'SELECCIONE TIPO DE EQUIPACIÓN...'),
    ('Equipación Local', 'Equipación Local'),
    ('Equipación Visitante', 'Equipación Visitante'),
    ('Tercera Equipación', 'Tercera Equipación'),
    ('Edición Retro', 'Edición Retro'),
    ('Sudadera de Entrenamiento', 'Sudadera de Entrenamiento'),
    ('Chaqueta de Presentación', 'Chaqueta de Presentación'),
    ('Ropa de Entrenamiento', 'Ropa de Entrenamiento'),
]

GENERO_CHOICES = [
    ('', 'SELECCIONE GÉNERO...'),
    ('Hombre', 'Hombre'),
    ('Mujer', 'Mujer'),
]

class ProductoForm(forms.ModelForm):
    tipo_producto = forms.ChoiceField(
        choices=[
            ('seleccion', 'Selección Nacional'),
            ('club', 'Club Colombiano'),
            ('liga_esp', 'La Liga (España)'),
            ('premier', 'Premier League (Inglaterra)'),
            ('serie_a', 'Serie A (Italia)'),
            ('bundesliga', 'Bundesliga (Alemania)'),
            ('europa_otros', 'Otros Equipos/Ligas')
        ],
        label="Categoría de Camiseta",
        widget=forms.Select(attrs={'class': 'form-control-neon', 'id': 'id_tipo_producto'})
    )
    
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'stock', 'min_stock', 'talla']
        widgets = {
            # Dejamos el nombre como Select de selecciones por defecto
            'nombre': forms.Select(choices=SELECCIONES_CHOICES, attrs={'class': 'form-control-neon', 'id': 'id_nombre_seleccion'}),
            'descripcion': forms.Select(choices=EQUIPACION_CHOICES, attrs={'class': 'form-control-neon'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control-neon', 'placeholder': 'Ej:75000'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control-neon', 'placeholder': 'Cantidad total'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control-neon', 'placeholder': 'Stock mínimo para alerta'}),
            'talla': forms.Select(attrs={'class': 'form-control-neon'}),
        }

    # Añadimos el campo de clubes como un campo extra que no está en el modelo
    nombre_club = forms.ChoiceField(
        choices=CLUBES_COLOMBIA_CHOICES,
        required=False,
        label="Equipo de Colombia",
        widget=forms.Select(attrs={'class': 'form-control-neon', 'id': 'id_nombre_club'})
    )

    nombre_liga_esp = forms.ChoiceField(
        choices=LIGA_ESP_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control-neon', 'id': 'id_nombre_liga_esp'})
    )

    nombre_premier = forms.ChoiceField(
        choices=PREMIER_L_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control-neon', 'id': 'id_nombre_premier'})
    )

    nombre_serie_a = forms.ChoiceField(
        choices=SERIE_A_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control-neon', 'id': 'id_nombre_serie_a'})
    )

    nombre_bundesliga = forms.ChoiceField(
        choices=BUNDESLIGA_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control-neon', 'id': 'id_nombre_bundesliga'})
    )

    nombre_europa_otros = forms.ChoiceField(
        choices=EUROPA_OTROS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control-neon', 'id': 'id_nombre_europa_otros'})
    )

    tipo_ropa = forms.CharField(
        label="Pieza",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control-neon', 'id': 'id_tipo_ropa'})
    )

    genero = forms.ChoiceField(
        choices=GENERO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control-neon', 'id': 'id_genero'})
    )

    def __init__(self, *args, **kwargs):
        super(ProductoForm, self).__init__(*args, **kwargs)
        # Hacemos que el nombre no sea obligatorio para que no bloquee si elegimos clubes/ligas
        self.fields['nombre'].required = False

        # Si estamos editando (existe una instancia con ID)
        if self.instance and self.instance.pk:
            # 1. Recuperar el 'tipo_producto' (código interno) a partir de la etiqueta guardada en 'categoria'
            categoria_guardada = self.instance.categoria
            choices_dict = {label: code for code, label in self.fields['tipo_producto'].choices}
            tipo_codigo = choices_dict.get(categoria_guardada)
            
            if tipo_codigo:
                self.initial['tipo_producto'] = tipo_codigo
                
                # 2. Rellenar el selector de equipo correspondiente según la categoría
                mapping_campos = {
                    'seleccion': 'nombre',
                    'club': 'nombre_club',
                    'liga_esp': 'nombre_liga_esp',
                    'premier': 'nombre_premier',
                    'serie_a': 'nombre_serie_a',
                    'bundesliga': 'nombre_bundesliga',
                    'europa_otros': 'nombre_europa_otros',
                }
                campo_destino = mapping_campos.get(tipo_codigo)
                if campo_destino:
                    self.initial[campo_destino] = self.instance.nombre

            # 3. Rellenar los campos de equipación, pieza y género
            self.initial['descripcion'] = self.instance.tipo_uniforme
            self.initial['tipo_ropa'] = self.instance.pieza
            self.initial['genero'] = self.instance.genero

        # Si estamos agregando un producto nuevo (no hay instancia ID),
        # quitamos los campos que se manejarán por talla en el template.
        if not self.instance.pk:
            if 'precio' in self.fields: del self.fields['precio']
            if 'stock' in self.fields: del self.fields['stock']
            if 'min_stock' in self.fields: del self.fields['min_stock']
            if 'talla' in self.fields: del self.fields['talla']