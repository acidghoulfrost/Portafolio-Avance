from django.contrib import admin
from .models import Categoria, Compra, DetalleCompra, Producto

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    # Usamos los nombres exactos de los campos en models.py
    list_display = ('nombre_producto', 'categoria', 'precio', 'stock', 'estado')
    list_filter = ('categoria', 'estado')
    search_fields = ('nombre_producto',)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre_categoria', 'estado')
    list_filter = ('estado',)
    search_fields = ('nombre_categoria',)


class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 0
    readonly_fields = ('nombre_producto', 'precio_unitario', 'cantidad', 'subtotal')


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_compra', 'total', 'estado_compra')
    list_filter = ('estado_compra', 'metodo_pago')
    search_fields = ('usuario__username',)
    inlines = (DetalleCompraInline,)
