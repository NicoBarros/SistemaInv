from django.db import models, transaction
from django.db.models import F, Sum
from django.contrib.auth.models import User
from decimal import Decimal
from django.core.exceptions import ValidationError


class Categoria(models.Model):
    """
    Modelo que representa una categoría en la base de datos.
    """
    
    #: Clave primaria autoincremental para identificar de manera única cada categoría.
    categoria_id = models.AutoField(primary_key=True)
    
    #: Almacena el nombre de la categoría, con un máximo de 50 caracteres.
    nombre = models.CharField(max_length=50)

    def __str__(self):
        """
        Retorna la representación en cadena de una instancia de la categoría.

        :return: El nombre de la categoría.
        :rtype: str
        """
        return self.nombre

    class Meta:
        """
        Configuración adicional para el modelo.
        """
        #: Indica que Django no debe gestionar la creación/modificación de la tabla en la base de datos.
        managed = False
        #: Nombre explícito de la tabla en la base de datos que se usará para este modelo.
        db_table = 'categoria'


class Cliente(models.Model):
    """
    Modelo que representa a un cliente en la base de datos.
    """
    
    #: Clave primaria autoincremental para identificar de manera única a cada cliente.
    id_cliente = models.AutoField(primary_key=True)
    
    #: Almacena el nombre del cliente, con un máximo de 100 caracteres.
    nombre = models.CharField(max_length=100)
    
    #: Almacena el apellido del cliente, con un máximo de 100 caracteres.
    apellido = models.CharField(max_length=100)
    
    #: Almacena el número de teléfono del cliente, con un máximo de 20 caracteres. 
    #: Puede estar vacío o nulo.
    telefono = models.CharField(max_length=20, blank=True, null=True)
    
    #: Almacena la dirección del cliente, con un máximo de 255 caracteres. 
    #: Puede estar vacío o nulo.
    direccion = models.CharField(max_length=255, blank=True, null=True)
    
    #: Almacena el límite de crédito del cliente. Puede ser nulo.
    limite_credito = models.IntegerField(blank=True, null=True)
    
    #: Almacena la deuda del cliente. Puede ser nulo.
    deuda = models.IntegerField(blank=True, null=True)

    def clean(self):
        """
        Valida los campos antes de guardar el objeto en la base de datos.

        :raises ValidationError: Si la deuda excede el límite de crédito o si los campos no son valores válidos.
        """
        try:
            limite_credito = float('inf') if self.limite_credito == -1 else float(self.limite_credito)
            deuda = int(self.deuda) if self.deuda is not None else 0

            if limite_credito != float('inf') and deuda > limite_credito:
                raise ValidationError("La deuda no puede exceder el límite de crédito.")
        except ValueError:
            raise ValidationError('Límite de crédito y deuda deben ser valores numéricos.')

    def __str__(self):
        """
        Retorna la representación en cadena de una instancia del cliente.

        :return: El nombre del cliente.
        :rtype: str
        """
        return self.nombre

    def abonar_deuda(self, monto):
        """
        Permite realizar un abono a la deuda del cliente.

        :param monto: Monto a abonar.
        :type monto: float
        :raises ValueError: Si el monto es negativo.
        """
        if monto < 0:
            raise ValueError("El monto a abonar debe ser positivo.")
        if self.deuda is None:
            self.deuda = 0
        self.deuda = max(0, self.deuda - monto)
        self.save()

    class Meta:
        """
        Configuración adicional para el modelo.
        """
        #: Indica que Django no debe gestionar la creación/modificación de la tabla en la base de datos.
        managed = False
        #: Nombre explícito de la tabla en la base de datos que se usará para este modelo.
        db_table = 'cliente'


class Producto(models.Model):
    """
    Modelo que representa un producto en la base de datos.
    """
    
    #: Clave primaria que identifica de manera única cada producto.
    codigo_producto = models.IntegerField(primary_key=True)
    
    #: Almacena el nombre del producto, con un máximo de 100 caracteres.
    nombre_producto = models.CharField(max_length=100)
    
    #: Almacena el precio de costo del producto.
    precio_costo = models.IntegerField()
    
    #: Almacena el precio de venta del producto.
    precio_venta = models.IntegerField()
    
    #: Almacena la cantidad mínima de stock requerida para el producto.
    stock_minimo = models.IntegerField()
    
    #: Almacena la cantidad actual de stock disponible del producto.
    stock_actual = models.IntegerField()
    
    #: Relación de clave foránea con el modelo Categoria.
    #: Si se elimina una categoría, se eliminan los productos asociados.
    categoria = models.ForeignKey(Categoria, models.CASCADE, blank=True, null=True)

    @classmethod
    def contar_productos_totales(cls):
        """
        Cuenta el total de productos registrados en la base de datos.

        :return: Número total de productos.
        :rtype: int
        """
        return cls.objects.count()

    @classmethod
    def sumar_precio_costo_total(cls):
        """
        Calcula el costo total de los productos en stock.

        Utiliza la función de agregación `Sum` para multiplicar el precio de costo por el stock actual de cada producto.

        :return: Costo total de los productos en stock.
        :rtype: int
        """
        return cls.objects.aggregate(
            total_precio_costo=Sum(F('precio_costo') * F('stock_actual'))
        )['total_precio_costo'] or 0

    class Meta:
        """
        Configuración adicional para el modelo.
        """
        #: Indica que Django no debe gestionar la creación/modificación de la tabla en la base de datos.
        managed = False
        #: Nombre explícito de la tabla en la base de datos que se usará para este modelo.
        db_table = 'producto'


class Proveedor(models.Model):
    """
    Modelo que representa un proveedor en la base de datos.
    """
    
    #: Almacena el nombre del proveedor, con un máximo de 100 caracteres.
    nombre = models.CharField(max_length=100)
    
    #: Almacena la dirección del proveedor, con un máximo de 100 caracteres.
    #: Este campo puede estar vacío o nulo.
    direccion = models.CharField(max_length=100, blank=True, null=True)
    
    #: Almacena el número de teléfono del proveedor, con un máximo de 100 caracteres.
    #: Este campo también puede estar vacío o nulo.
    telefono = models.CharField(max_length=100, blank=True, null=True)
    
    #: Almacena detalles adicionales sobre el proveedor en formato de texto.
    #: Este campo puede estar vacío o nulo.
    detalles = models.TextField(blank=True, null=True)

    class Meta:
        """
        Configuración adicional para el modelo.
        """
        #: Indica que Django no debe gestionar la creación/modificación de la tabla en la base de datos.
        managed = False
        #: Nombre explícito de la tabla en la base de datos que se usará para este modelo.
        db_table = 'proveedor'


class Venta(models.Model):
    """
    Modelo que representa una venta realizada en la base de datos.
    """
    
    #: Clave primaria autoincremental que identifica de manera única cada venta.
    id_venta = models.AutoField(primary_key=True)
    
    #: Almacena la fecha y hora de la venta.
    fecha = models.DateTimeField()
    
    #: Almacena el total de la venta (monto total de la transacción).
    total = models.IntegerField()
    
    #: Almacena el método de pago utilizado (por ejemplo, 'Efectivo', 'Tarjeta', 'Deuda').
    metodo_pago = models.CharField(max_length=13)
    
    #: Relación de clave foránea con el modelo `Cliente`. 
    #: Puede ser nulo si la venta no está asociada a un cliente.
    id_cliente = models.ForeignKey(
        Cliente, models.DO_NOTHING, db_column='id_cliente', blank=True, null=True
    )
    
    #: Relación de clave foránea con el modelo `User` (usuario), que representa al vendedor.
    #: Si el vendedor se elimina, la relación se establece como nula.
    vendedor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        """
        Configuración adicional para el modelo.
        """
        #: Indica que Django no debe gestionar la creación/modificación de la tabla en la base de datos.
        managed = False
        #: Nombre explícito de la tabla en la base de datos que se usará para este modelo.
        db_table = 'venta'

    def save(self, *args, **kwargs):
        """
        Sobreescribe el método `save` para agregar una validación antes de guardar la venta.

        - Si la venta está asociada a un cliente y el método de pago es 'Deuda',
          verifica que el cliente no supere su límite de crédito antes de actualizar su deuda.
        """
        if self.id_cliente and self.metodo_pago == 'Deuda':
            with transaction.atomic():
                cliente = self.id_cliente
                if cliente.limite_credito != -1:  # Límite de crédito no infinito
                    if (cliente.deuda or 0) + self.total > (cliente.limite_credito or 0):
                        raise ValueError("El cliente ha superado su límite de crédito.")
                cliente.deuda = (cliente.deuda or 0) + self.total
                cliente.save()
        super().save(*args, **kwargs)

    @classmethod
    def contar_ventas(cls):
        """
        Cuenta el total de ventas registradas en la base de datos.
        
        :return: Número total de ventas registradas.
        """
        return cls.objects.count()

    @classmethod
    def sumar_totales(cls):
        """
        Calcula la suma de todos los totales de ventas registradas.
        
        :return: Suma total de los valores del campo `total` en las ventas registradas.
        """
        return cls.objects.aggregate(suma_total=Sum('total'))['suma_total'] or 0

