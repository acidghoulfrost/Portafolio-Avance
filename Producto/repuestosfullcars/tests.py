import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Categoria, Compra, DetalleCompra, Producto


class CatalogoTests(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre_categoria='Frenos')
        self.producto = Producto.objects.create(
            categoria=self.categoria,
            nombre_producto='Pastillas delanteras',
            descripcion='Pastillas ceramicas',
            precio=Decimal('24990'),
            stock=4,
        )
        self.inactivo = Producto.objects.create(
            categoria=self.categoria,
            nombre_producto='Producto oculto',
            precio=Decimal('1000'),
            stock=10,
            estado='inactivo',
        )

    def test_home_muestra_solo_productos_activos(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, self.producto.nombre_producto)
        self.assertNotContains(response, self.inactivo.nombre_producto)

    def test_busqueda_y_filtro_por_categoria(self):
        response = self.client.get(reverse('index'), {'q': 'Pastillas', 'categoria': self.categoria.id})
        self.assertContains(response, self.producto.nombre_producto)

    def test_filtro_invalido_no_genera_error(self):
        response = self.client.get(reverse('index'), {'categoria': "' OR '1'='1"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.producto.nombre_producto)

    def test_detalle_rechaza_producto_inactivo(self):
        response = self.client.get(reverse('producto_detalle', args=[self.inactivo.id]))
        self.assertEqual(response.status_code, 404)

    def test_asistente_informa_stock_real(self):
        response = self.client.post(
            reverse('asistente_virtual'),
            data=json.dumps({'pregunta': 'stock de pastillas'}),
            content_type='application/json',
        )
        self.assertContains(response, 'Bajo stock')
        self.assertContains(response, '4 unidades')


class UsuariosTests(TestCase):
    def test_registro_crea_cliente_sin_permisos_staff(self):
        response = self.client.post(reverse('registro'), {
            'username': 'cliente',
            'email': 'cliente@example.com',
            'password1': 'ClaveSegura123!',
            'password2': 'ClaveSegura123!',
        })
        self.assertRedirects(response, reverse('login'))
        self.assertFalse(User.objects.get(username='cliente').is_staff)

    def test_registro_rechaza_contrasenas_distintas(self):
        response = self.client.post(reverse('registro'), {
            'username': 'cliente',
            'email': 'cliente@example.com',
            'password1': 'ClaveSegura123!',
            'password2': 'OtraClave123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='cliente').exists())

    def test_login_invalido_muestra_error(self):
        response = self.client.post(reverse('login'), {
            'username': 'nadie',
            'password': 'incorrecta',
        })
        self.assertContains(response, 'Usuario o contrasena incorrectos')


class InventarioAdminTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('admin', password='Clave123!', is_staff=True)
        self.cliente = User.objects.create_user('cliente', password='Clave123!')
        self.categoria = Categoria.objects.create(nombre_categoria='Motor')
        self.producto = Producto.objects.create(
            categoria=self.categoria,
            nombre_producto='Filtro de aceite',
            precio=Decimal('6990'),
            stock=8,
        )

    def test_cliente_no_puede_entrar_al_inventario(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('admin_productos'))
        self.assertEqual(response.status_code, 302)

    def test_staff_crea_producto_valido(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('admin_productos'), {
            'nombre_producto': 'Bateria 60 AH',
            'categoria': self.categoria.id,
            'descripcion': 'Bateria sellada',
            'precio': '79990',
            'stock': '3',
            'estado': 'activo',
        })
        self.assertRedirects(response, reverse('admin_productos'))
        self.assertTrue(Producto.objects.filter(nombre_producto='Bateria 60 AH').exists())

    def test_staff_no_puede_crear_stock_negativo(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('admin_productos'), {
            'nombre_producto': 'Producto invalido',
            'categoria': self.categoria.id,
            'precio': '1000',
            'stock': '-1',
            'estado': 'activo',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Producto.objects.filter(nombre_producto='Producto invalido').exists())

    def test_constraint_impide_precio_negativo(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Producto.objects.create(
                    categoria=self.categoria,
                    nombre_producto='Precio invalido',
                    precio=Decimal('-1'),
                    stock=1,
                )

    def test_cambiar_estado_oculta_producto_del_home(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('cambiar_estado_producto', args=[self.producto.id]))
        response = self.client.get(reverse('index'))
        self.assertNotContains(
            response,
            reverse('producto_detalle', args=[self.producto.id]),
        )

    def test_eliminacion_requiere_post(self):
        self.client.force_login(self.staff)
        url = reverse('eliminar_producto', args=[self.producto.id])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.assertFalse(Producto.objects.filter(id=self.producto.id).exists())

    def test_rechaza_archivo_que_no_es_imagen(self):
        self.client.force_login(self.staff)
        archivo = SimpleUploadedFile('archivo.txt', b'no es una imagen', content_type='text/plain')
        response = self.client.post(reverse('admin_productos'), {
            'nombre_producto': 'Producto con archivo',
            'categoria': self.categoria.id,
            'precio': '1000',
            'stock': '1',
            'estado': 'activo',
            'imagen_url': archivo,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Producto.objects.filter(nombre_producto='Producto con archivo').exists())


class CompraTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('comprador', password='Clave123!')
        self.staff = User.objects.create_user('admin', password='Clave123!', is_staff=True)
        self.categoria = Categoria.objects.create(nombre_categoria='Electricidad')
        self.producto = Producto.objects.create(
            categoria=self.categoria,
            nombre_producto='Bateria 60 AH',
            precio=Decimal('79990'),
            stock=5,
        )

    def test_agregar_producto_al_carrito(self):
        response = self.client.post(reverse('agregar_carrito', args=[self.producto.id]))
        self.assertRedirects(response, reverse('carrito'))
        response = self.client.get(reverse('carrito'))
        self.assertContains(response, self.producto.nombre_producto)

    def test_checkout_exige_sesion(self):
        self.client.post(reverse('agregar_carrito', args=[self.producto.id]))
        response = self.client.get(reverse('checkout'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('checkout')}")

    def test_checkout_registra_compra_detalle_y_descuenta_stock(self):
        self.client.force_login(self.usuario)
        self.client.post(reverse('agregar_carrito', args=[self.producto.id]), {'cantidad': 2})
        response = self.client.post(reverse('checkout'), {
            'metodo_pago': 'transferencia',
            'direccion_envio': 'Av. Siempre Viva 123',
        })
        compra = Compra.objects.get(usuario=self.usuario)
        detalle = DetalleCompra.objects.get(compra=compra)
        self.assertRedirects(response, reverse('mis_compras'))
        self.assertEqual(compra.total, Decimal('159980'))
        self.assertEqual(detalle.cantidad, 2)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 3)

    def test_checkout_ajusta_carrito_al_stock_disponible(self):
        self.client.post(reverse('agregar_carrito', args=[self.producto.id]), {'cantidad': 99})
        response = self.client.get(reverse('carrito'))
        self.assertContains(response, 'value="5"', html=False)

    def test_cliente_no_puede_ver_panel_de_ventas(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse('admin_compras'))
        self.assertEqual(response.status_code, 302)

    def test_staff_puede_ver_panel_de_ventas(self):
        Compra.objects.create(
            usuario=self.usuario,
            total=Decimal('1000'),
            metodo_pago='efectivo',
            direccion_envio='Retiro en tienda',
        )
        self.client.force_login(self.staff)
        response = self.client.get(reverse('admin_compras'))
        self.assertContains(response, self.usuario.username)


class SeguridadYRecuperacionTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            'cliente',
            email='cliente@example.com',
            password='Clave123!',
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_no_revela_si_correo_existe(self):
        url = reverse('password_reset')
        registrado = self.client.post(url, {'email': 'cliente@example.com'})
        desconocido = self.client.post(url, {'email': 'nadie@example.com'})
        self.assertRedirects(registrado, reverse('password_reset_done'))
        self.assertRedirects(desconocido, reverse('password_reset_done'))

    def test_token_invalido_no_muestra_formulario(self):
        response = self.client.get(
            reverse('password_reset_confirm', args=['uid-invalido', 'token-invalido'])
        )
        self.assertContains(response, 'Enlace no valido')
        self.assertNotContains(response, 'Guardar nueva contrasena')

    def test_asistente_rechaza_post_sin_csrf(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse('asistente_virtual'),
            data=json.dumps({'pregunta': 'stock de bateria'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)


class SeedCategoriesTests(TestCase):
    def test_carga_categorias_sin_duplicarlas(self):
        call_command('seed_categories')
        cantidad_inicial = Categoria.objects.count()
        call_command('seed_categories')

        self.assertEqual(cantidad_inicial, 6)
        self.assertEqual(Categoria.objects.count(), cantidad_inicial)
