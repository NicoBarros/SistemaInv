from django import forms    
from .models import Producto,Proveedor,Categoria,Cliente,Venta
from django.contrib.auth.models import User

class RegisterForm(forms.Form):
    """
    Formulario de registro para la creación de un nuevo usuario.
    """

    #: Campo para ingresar el nombre de usuario.
    #: - Máximo de 150 caracteres.
    #: - Campo obligatorio.
    #: - Incluye un widget de texto con la clase CSS 'form-control'.
    username = forms.CharField(
        label='Nombre de usuario', 
        max_length=150, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    #: Campo para ingresar la contraseña.
    #: - Campo obligatorio.
    #: - El texto se oculta con un widget de tipo `PasswordInput` con la clase CSS 'form-control'.
    password = forms.CharField(
        label='Contraseña', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        required=True
    )
    
    #: Campo para confirmar la contraseña.
    #: - Campo obligatorio.
    #: - El texto se oculta con un widget de tipo `PasswordInput` con la clase CSS 'form-control'.
    confirm_password = forms.CharField(
        label='Confirmar contraseña', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        required=True
    )

    def clean_username(self):
        """
        Valida el campo `username`.
        
        - Verifica si el nombre de usuario ingresado ya existe en la base de datos.
        - Lanza una excepción si el nombre de usuario ya está en uso.
        
        :return: Nombre de usuario validado.
        :raises ValidationError: Si el nombre de usuario ya existe.
        """
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("¡El nombre de usuario ya existe!.")
        return username

    def clean(self):
        """
        Validación global para los campos del formulario.
        
        - Verifica si las contraseñas ingresadas (`password` y `confirm_password`) coinciden.
        - Lanza una excepción si las contraseñas no coinciden.
        
        :return: Diccionario con los datos validados.
        :raises ValidationError: Si las contraseñas no coinciden.
        """
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("¡Las contraseñas no coinciden!.")
        return cleaned_data


class ProductoForm(forms.ModelForm):
    """
    Formulario para la creación y edición de productos en la base de datos.
    """

    #: Campo 'categoria': lista desplegable basada en las categorías disponibles en la base de datos.
    #: - Muestra todas las categorías de la tabla `Categoria`.
    #: - Incluye un texto por defecto "Seleccione una categoría".
    #: - Utiliza un widget `Select` con la clase CSS 'form-control'.
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        empty_label="Seleccione una categoría",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        """
        Metadatos del formulario.

        - Basado en el modelo `Producto`.
        - Incluye los campos `codigo_producto`, `nombre_producto`, `precio_costo`, 
          `stock_minimo`, `stock_actual` y `categoria`.
        - Define widgets personalizados con estilos Bootstrap para ciertos campos.
        """
        model = Producto
        fields = ['codigo_producto', 'nombre_producto', 'precio_costo', 'stock_minimo', 'stock_actual', 'categoria']
        widgets = {
            'nombre_producto': forms.TextInput(attrs={'class': 'form-control'}),
            'precio_costo': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Constructor del formulario.

        - Permite configurar el campo `codigo_producto` como solo lectura mediante 
          el argumento `readonly_codigo`.
        - Aplica la clase CSS `form-control` al campo `codigo_producto`.
        """
        readonly_codigo = kwargs.pop('readonly_codigo', False)
        super().__init__(*args, **kwargs)

        if readonly_codigo:
            self.fields['codigo_producto'].widget.attrs['readonly'] = 'readonly'

        self.fields['codigo_producto'].widget.attrs['class'] = 'form-control'

    def clean_precio_costo(self):
        """
        Valida que el precio de costo no sea negativo.

        :return: Precio de costo validado.
        :raises ValidationError: Si el precio es menor a 0.
        """
        precio_costo = self.cleaned_data.get('precio_costo')
        if precio_costo < 0:
            raise forms.ValidationError("El precio de costo no puede ser negativo.")
        return precio_costo

    def clean_codigo_producto(self):
        """
        Valida que el código del producto sea un número entero mayor a cero.

        :return: Código de producto validado.
        :raises ValidationError: Si no es un número entero o si es menor o igual a 0.
        """
        codigo_producto = self.cleaned_data.get('codigo_producto')
        try:
            codigo_producto = int(codigo_producto)
        except ValueError:
            raise forms.ValidationError("El código del producto debe ser un número entero.")
        if codigo_producto <= 0:
            raise forms.ValidationError("El código del producto debe ser mayor a 0.")
        return codigo_producto

    def calcular_precio_venta(self):
        """
        Calcula el precio de venta del producto.

        - Aplica un margen de ganancia del 40% y un IVA del 19% al precio de costo.

        :return: Precio de venta calculado, o `None` si no hay precio de costo.
        """
        precio_costo = self.cleaned_data.get('precio_costo')
        if precio_costo is not None:
            margen = 1.40  # Margen de ganancia del 40%.
            iva = 1.19  # IVA del 19%.
            return int(precio_costo * iva * margen)
        return None

    def save(self, commit=True):
        """
        Guarda el producto en la base de datos.

        - Calcula el precio de venta antes de guardar.
        - Permite guardar condicionalmente con `commit=False`.

        :param commit: Si es `True`, guarda el producto en la base de datos.
        :return: Instancia del producto guardada.
        """
        producto = super().save(commit=False)
        producto.precio_venta = self.calcular_precio_venta()
        if commit:
            producto.save()
        return producto


class CategoriaForms(forms.ModelForm):
    """
    Formulario para la creación y edición de categorías en la base de datos.
    """

    class Meta:
        """
        Metadatos del formulario.

        - Basado en el modelo `Categoria`.
        - Incluye los campos `categoria_id` y `nombre`.
        - Define widgets personalizados con estilos Bootstrap para los campos.
        """
        model = Categoria
        fields = ['categoria_id', 'nombre']
        widgets = {
            'categoria_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ProveedorForm(forms.ModelForm):
    """
    Formulario para la creación y edición de proveedores en la base de datos.
    """

    class Meta:
        """
        Metadatos del formulario.

        - Basado en el modelo `Proveedor`.
        - Incluye los campos `nombre`, `direccion`, `telefono` y `detalles`.
        - Define widgets personalizados con estilos Bootstrap para los campos.
        """
        model = Proveedor
        fields = ['nombre', 'direccion', 'telefono', 'detalles']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'detalles': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class ClienteForm(forms.ModelForm):
    """
    Formulario para la creación y edición de clientes en la base de datos.
    """

    class Meta:
        """
        Metadatos del formulario.

        - Basado en el modelo `Cliente`.
        - Incluye los campos `nombre`, `apellido`, `telefono`, `direccion`, `limite_credito`, y `deuda`.
        - Define widgets personalizados con estilos Bootstrap para los campos.
        """
        model = Cliente
        fields = ['nombre', 'apellido', 'telefono', 'direccion', 'limite_credito', 'deuda']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'limite_credito': forms.NumberInput(attrs={'class': 'form-control'}),
            'deuda': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_deuda(self):
        """
        Valida el campo 'deuda'. Verifica que la deuda no exceda el límite de crédito del cliente.

        - Si el límite de crédito es definido y la deuda excede este límite, se genera una excepción de validación.
        - Si el límite de crédito es indefinido o se permite un valor de deuda infinito, no se valida el monto.

        :return: El valor de la deuda después de la validación.
        :raises: forms.ValidationError si la deuda excede el límite de crédito.
        """
        deuda = self.cleaned_data.get('deuda') or 0  # Si no hay deuda, se asigna 0 por defecto.
        limite_credito = self.cleaned_data.get('limite_credito')

        # Si no hay límite de crédito o es -1 (sin límite), se asigna un valor infinito.
        if limite_credito is None or limite_credito == -1:
            limite_credito = float('inf')

        # Verificar que la deuda no exceda el límite de crédito.
        if limite_credito != float('inf') and deuda > limite_credito:
            raise forms.ValidationError('La deuda no puede exceder el límite de crédito.')

        return deuda

class VentaForm(forms.ModelForm):
    """
    Formulario para la creación y edición de ventas en la base de datos.
    """

    class Meta:
        """
        Metadatos del formulario.

        - Basado en el modelo `Venta`.
        - Incluye los campos `metodo_pago` e `id_cliente`.
        - Define un widget personalizado con clases Bootstrap para estilizar los campos.
        """
        model = Venta
        fields = ['metodo_pago', 'id_cliente']
        widgets = {
            'id_cliente': forms.Select(attrs={'class': 'form-control'}),  # Campo de selección de cliente con estilo 'form-control'.
        }

    # Definición del campo 'metodo_pago' como un campo de selección con opciones de pago.
    metodo_pago = forms.ChoiceField(
        choices=[('Efectivo', 'Efectivo'), ('Tarjeta', 'Tarjeta'), ('Transferencia', 'Transferencia'), ('Deuda', 'Deuda')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Método de Pago",
        error_messages={'required': " Por favor, seleccione un método de pago. "}  # Mensaje de error si no se selecciona un método de pago.
    )


