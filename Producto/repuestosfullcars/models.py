from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Categoria(models.Model):
    ESTADOS = (
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    )

    nombre_categoria = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='activo')

    class Meta:
        ordering = ('nombre_categoria',)

    def __str__(self):
        return self.nombre_categoria

class Producto(models.Model):
    ESTADOS = (
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    )

    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    nombre_producto = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    imagen_url = models.ImageField(upload_to='productos/', null=True, blank=True)
    stock = models.IntegerField(validators=[MinValueValidator(0)])
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='activo')

    class Meta:
        ordering = ('nombre_producto',)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(precio__gte=0),
                name='producto_precio_no_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(stock__gte=0),
                name='producto_stock_no_negativo',
            ),
        ]

    def __str__(self):
        return self.nombre_producto

    @property
    def disponibilidad(self):
        if self.stock == 0:
            return 'Sin stock'
        if self.stock <= 5:
            return 'Bajo stock'
        return 'Disponible'

class Compra(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    )
    METODOS_PAGO = (
        ('transferencia', 'Transferencia bancaria'),
        ('efectivo', 'Efectivo al retirar'),
    )

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_compra = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    estado_compra = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente',
    )
    metodo_pago = models.CharField(max_length=50, choices=METODOS_PAGO)
    direccion_envio = models.TextField()

    class Meta:
        ordering = ('-fecha_compra',)

    def __str__(self):
        return f"Compra {self.id} - {self.usuario.username}"

class DetalleCompra(models.Model):
    compra = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE,
        related_name='detalles',
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    nombre_producto = models.CharField(max_length=200)
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    def __str__(self):
        return f'{self.cantidad} x {self.nombre_producto}'
