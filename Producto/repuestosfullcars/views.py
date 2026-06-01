import json
import unicodedata
from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .carrito import (
    agregar_producto as agregar_producto_al_carrito,
    detalle_carrito,
    eliminar_producto as eliminar_producto_del_carrito,
    guardar_carrito,
    obtener_carrito,
    vaciar_carrito,
)
from .forms import CheckoutForm, ProductoForm, RegistroForm
from .models import Categoria, Compra, DetalleCompra, Producto


def index(request):
    categorias = Categoria.objects.filter(estado='activo')
    productos = Producto.objects.filter(
        estado='activo',
        categoria__estado='activo',
    ).select_related('categoria')
    categoria_filtro = request.GET.get('categoria', '').strip()
    busqueda = request.GET.get('q', '').strip()

    if categoria_filtro.isdigit():
        productos = productos.filter(categoria_id=categoria_filtro)
    elif categoria_filtro:
        productos = productos.none()
    if busqueda:
        productos = productos.filter(
            Q(nombre_producto__icontains=busqueda)
            | Q(descripcion__icontains=busqueda)
            | Q(categoria__nombre_categoria__icontains=busqueda)
        )

    categorias_con_productos = []
    for categoria in categorias:
        productos_categoria = [
            producto
            for producto in productos
            if producto.categoria_id == categoria.id
        ]
        if productos_categoria:
            categorias_con_productos.append({
                'categoria': categoria,
                'productos': productos_categoria,
            })

    return render(request, 'repuestosfullcars/home.html', {
        'categorias': categorias,
        'categorias_con_productos': categorias_con_productos,
        'categoria_filtro': categoria_filtro,
        'busqueda': busqueda,
    })


def producto_detalle(request, id):
    producto = get_object_or_404(
        Producto.objects.select_related('categoria'),
        id=id,
        estado='activo',
        categoria__estado='activo',
    )
    relacionados = Producto.objects.filter(
        categoria=producto.categoria,
        estado='activo',
    ).exclude(id=producto.id)[:4]
    return render(request, 'repuestosfullcars/producto_detalle.html', {
        'producto': producto,
        'relacionados': relacionados,
    })


def registro(request):
    if request.user.is_authenticated:
        return redirect('index')
    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        messages.success(
            request,
            f'Bienvenido {usuario.username}. Ya puedes iniciar sesion.',
        )
        return redirect('login')
    return render(request, 'usuarios/registro.html', {'form': form})


@require_POST
def cerrar_sesion(request):
    logout(request)
    messages.success(request, 'Tu sesion se cerro correctamente.')
    return redirect('index')


@require_POST
def agregar_carrito(request, id):
    producto = get_object_or_404(Producto, id=id, estado='activo')
    cantidad = _cantidad_post(request)
    carrito = obtener_carrito(request)
    cantidad_actual = int(carrito.get(str(producto.id), 0))
    if producto.stock == 0:
        messages.error(request, f'{producto.nombre_producto} no tiene stock disponible.')
    elif cantidad_actual + cantidad > producto.stock:
        carrito[str(producto.id)] = producto.stock
        guardar_carrito(request, carrito)
        messages.warning(request, 'Se ajusto la cantidad al stock disponible.')
    else:
        agregar_producto_al_carrito(request, producto.id, cantidad)
        messages.success(request, f'{producto.nombre_producto} se agrego al carrito.')
    return redirect(request.POST.get('next') or 'carrito')


@require_POST
def actualizar_carrito(request, id):
    producto = get_object_or_404(Producto, id=id, estado='activo')
    cantidad = _cantidad_post(request)
    carrito = obtener_carrito(request)
    if cantidad > producto.stock:
        cantidad = producto.stock
        messages.warning(request, 'Se ajusto la cantidad al stock disponible.')
    if cantidad < 1:
        eliminar_producto_del_carrito(request, producto.id)
    else:
        carrito[str(producto.id)] = cantidad
        guardar_carrito(request, carrito)
    return redirect('carrito')


@require_POST
def quitar_carrito(request, id):
    eliminar_producto_del_carrito(request, id)
    messages.success(request, 'Producto retirado del carrito.')
    return redirect('carrito')


def ver_carrito(request):
    items, total = detalle_carrito(request)
    return render(request, 'repuestosfullcars/carrito.html', {
        'items': items,
        'total': total,
    })


@login_required
def checkout(request):
    items, total = detalle_carrito(request)
    if not items:
        messages.warning(request, 'Agrega productos antes de continuar.')
        return redirect('carrito')

    form = CheckoutForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                compra = form.save(commit=False)
                compra.usuario = request.user
                compra.total = Decimal('0')
                compra.save()
                total_confirmado = Decimal('0')

                for item in items:
                    producto = Producto.objects.select_for_update().get(
                        id=item['producto'].id,
                        estado='activo',
                    )
                    cantidad = item['cantidad']
                    if cantidad > producto.stock:
                        raise ValueError(
                            f'El stock de {producto.nombre_producto} cambio. '
                            'Revisa tu carrito.'
                        )
                    subtotal = producto.precio * cantidad
                    DetalleCompra.objects.create(
                        compra=compra,
                        producto=producto,
                        nombre_producto=producto.nombre_producto,
                        precio_unitario=producto.precio,
                        cantidad=cantidad,
                        subtotal=subtotal,
                    )
                    producto.stock -= cantidad
                    producto.save(update_fields=('stock', 'fecha_actualizacion'))
                    total_confirmado += subtotal

                compra.total = total_confirmado
                compra.save(update_fields=('total',))
        except (Producto.DoesNotExist, ValueError) as error:
            messages.error(request, str(error))
            return redirect('carrito')

        vaciar_carrito(request)
        messages.success(request, f'Compra #{compra.id} registrada correctamente.')
        return redirect('mis_compras')

    return render(request, 'repuestosfullcars/checkout.html', {
        'form': form,
        'items': items,
        'total': total,
    })


@login_required
def mis_compras(request):
    compras = Compra.objects.filter(usuario=request.user).prefetch_related('detalles')
    return render(request, 'repuestosfullcars/mis_compras.html', {'compras': compras})


@staff_member_required
def admin_productos(request):
    producto_edit = None
    edit_id = request.GET.get('edit')
    if edit_id:
        producto_edit = get_object_or_404(Producto, id=edit_id)

    form = ProductoForm(request.POST or None, request.FILES or None, instance=producto_edit)
    if request.method == 'POST' and form.is_valid():
        producto = form.save()
        accion = 'actualizado' if producto_edit else 'agregado'
        messages.success(
            request,
            f"Producto '{producto.nombre_producto}' {accion} correctamente.",
        )
        return redirect('admin_productos')

    productos = Producto.objects.select_related('categoria').order_by('-fecha_actualizacion')
    return render(request, 'repuestosfullcars/admin_productos.html', {
        'productos': productos,
        'producto_edit': producto_edit,
        'form': form,
    })


@staff_member_required
@require_POST
def cambiar_estado_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.estado = 'inactivo' if producto.estado == 'activo' else 'activo'
    producto.save(update_fields=('estado', 'fecha_actualizacion'))
    messages.success(request, f"Estado de '{producto.nombre_producto}' actualizado.")
    return redirect('admin_productos')


@staff_member_required
@require_POST
def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    nombre = producto.nombre_producto
    producto.delete()
    messages.warning(request, f"Producto '{nombre}' eliminado.")
    return redirect('admin_productos')


@staff_member_required
def admin_compras(request):
    compras = Compra.objects.select_related('usuario').prefetch_related('detalles')
    return render(request, 'repuestosfullcars/admin_compras.html', {'compras': compras})


@require_POST
def asistente_virtual(request):
    try:
        datos = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        datos = request.POST
    pregunta = str(datos.get('pregunta', '')).strip()
    if not pregunta:
        return JsonResponse({'respuesta': 'Escribe una consulta para poder ayudarte.'}, status=400)
    return JsonResponse({'respuesta': _responder_asistente(pregunta)})


def _cantidad_post(request):
    try:
        return max(1, int(request.POST.get('cantidad', 1)))
    except (TypeError, ValueError):
        return 1


def _normalizar(texto):
    texto = unicodedata.normalize('NFD', texto.lower())
    return ''.join(char for char in texto if unicodedata.category(char) != 'Mn')


def _productos_mencionados(pregunta):
    ignorar = {
        'stock', 'tiene', 'tienen', 'busco', 'buscar', 'quiero', 'para',
        'repuesto', 'repuestos', 'producto', 'productos', 'disponible',
        'disponibilidad', 'cuanto', 'cuantos', 'hola', 'necesito', 'hay',
    }
    tokens = {
        token.strip('.,;:!?')
        for token in _normalizar(pregunta).split()
        if len(token.strip('.,;:!?')) > 2 and token not in ignorar
    }
    coincidencias = []
    for producto in Producto.objects.filter(estado='activo').select_related('categoria'):
        texto = _normalizar(
            f'{producto.nombre_producto} {producto.categoria.nombre_categoria}'
        )
        puntaje = sum(token in texto for token in tokens)
        if puntaje:
            coincidencias.append((puntaje, producto))
    coincidencias.sort(key=lambda item: (-item[0], item[1].nombre_producto))
    return [producto for _, producto in coincidencias[:4]]


def _responder_asistente(pregunta):
    texto = _normalizar(pregunta)
    productos = _productos_mencionados(pregunta)
    if any(saludo in texto for saludo in ('hola', 'buenas', 'ayuda')):
        return (
            'Hola. Puedo ayudarte a buscar repuestos y consultar stock. '
            'Prueba escribiendo: "stock de pastillas de freno".'
        )
    if any(palabra in texto for palabra in ('stock', 'disponible', 'disponibilidad', 'hay')):
        if not productos:
            return 'Indica el nombre del repuesto para consultar su disponibilidad.'
        return ' | '.join(
            f'{producto.nombre_producto}: {producto.disponibilidad} ({producto.stock} unidades)'
            for producto in productos
        )
    if productos:
        return 'Encontre: ' + ' | '.join(
            f'{producto.nombre_producto} a ${producto.precio:,.0f}'
            for producto in productos
        )
    if any(palabra in texto for palabra in ('compra', 'carrito', 'pagar')):
        return (
            'Agrega productos desde el catalogo, abre tu carrito y confirma '
            'la compra iniciando sesion.'
        )
    return (
        'Puedo buscar repuestos, consultar disponibilidad y orientarte con '
        'el carrito. Intenta incluir el nombre del producto.'
    )
