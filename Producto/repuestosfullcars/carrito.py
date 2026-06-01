from decimal import Decimal

from .models import Producto


SESSION_KEY = 'carrito'


def obtener_carrito(request):
    return request.session.setdefault(SESSION_KEY, {})


def guardar_carrito(request, carrito):
    request.session[SESSION_KEY] = carrito
    request.session.modified = True


def agregar_producto(request, producto_id, cantidad=1):
    carrito = obtener_carrito(request)
    key = str(producto_id)
    carrito[key] = carrito.get(key, 0) + cantidad
    guardar_carrito(request, carrito)


def eliminar_producto(request, producto_id):
    carrito = obtener_carrito(request)
    carrito.pop(str(producto_id), None)
    guardar_carrito(request, carrito)


def vaciar_carrito(request):
    guardar_carrito(request, {})


def detalle_carrito(request):
    carrito = obtener_carrito(request)
    productos = Producto.objects.filter(
        id__in=carrito.keys(),
        estado='activo',
    ).select_related('categoria')
    items = []
    total = Decimal('0')
    for producto in productos:
        cantidad = int(carrito.get(str(producto.id), 0))
        if cantidad < 1:
            continue
        subtotal = producto.precio * cantidad
        total += subtotal
        items.append({
            'producto': producto,
            'cantidad': cantidad,
            'subtotal': subtotal,
        })
    return items, total
