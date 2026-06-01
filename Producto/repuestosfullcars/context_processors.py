from .carrito import detalle_carrito


def carrito(request):
    items, total = detalle_carrito(request)
    return {
        'carrito_cantidad': sum(item['cantidad'] for item in items),
        'carrito_total': total,
    }
