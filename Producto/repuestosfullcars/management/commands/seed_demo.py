from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from repuestosfullcars.models import Categoria, Producto


PRODUCTOS = {
    'Frenos': [
        ('Pastillas de freno ceramicas', 'Juego delantero de alta duracion.', '24990', 4),
        ('Discos de freno ventilados', 'Par de discos para conduccion urbana.', '69990', 12),
    ],
    'Motor': [
        ('Filtro de aceite premium', 'Proteccion confiable para el motor.', '6990', 20),
        ('Kit correa de distribucion', 'Kit completo con tensor y correa.', '89990', 3),
    ],
    'Electricidad': [
        ('Bateria 60 AH', 'Bateria sellada de libre mantencion.', '79990', 8),
        ('Ampolleta LED H4', 'Iluminacion blanca de bajo consumo.', '12990', 0),
    ],
}


class Command(BaseCommand):
    help = 'Carga categorias, productos y usuarios opcionales para una demostracion local.'

    def add_arguments(self, parser):
        parser.add_argument('--with-users', action='store_true')

    def handle(self, *args, **options):
        for categoria_nombre, productos in PRODUCTOS.items():
            categoria, _ = Categoria.objects.get_or_create(
                nombre_categoria=categoria_nombre,
                defaults={'descripcion': f'Repuestos de {categoria_nombre.lower()}.'},
            )
            for nombre, descripcion, precio, stock in productos:
                Producto.objects.get_or_create(
                    nombre_producto=nombre,
                    defaults={
                        'categoria': categoria,
                        'descripcion': descripcion,
                        'precio': Decimal(precio),
                        'stock': stock,
                    },
                )

        if options['with_users']:
            admin, _ = User.objects.get_or_create(
                username='admin_demo',
                defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True},
            )
            admin.is_staff = True
            admin.is_superuser = True
            admin.set_password('FullCars2026!')
            admin.save()

            cliente, _ = User.objects.get_or_create(
                username='cliente_demo',
                defaults={'email': 'cliente@example.com'},
            )
            cliente.set_password('FullCars2026!')
            cliente.save()
            self.stdout.write('Usuarios demo: admin_demo y cliente_demo / FullCars2026!')

        self.stdout.write(self.style.SUCCESS('Datos de demostracion cargados.'))
