from django.core.management.base import BaseCommand

from repuestosfullcars.models import Categoria


CATEGORIAS = {
    'Accesorios': 'Accesorios y complementos para el vehiculo.',
    'Aceites y filtros': 'Lubricantes, filtros y productos de mantencion.',
    'Electricidad': 'Baterias, ampolletas y componentes electricos.',
    'Frenos': 'Repuestos para el sistema de frenado.',
    'Motor': 'Componentes y repuestos para el motor.',
    'Suspension': 'Repuestos para suspension y direccion.',
}


class Command(BaseCommand):
    help = 'Carga las categorias iniciales requeridas por el catalogo.'

    def handle(self, *args, **options):
        creadas = 0
        for nombre, descripcion in CATEGORIAS.items():
            _, creada = Categoria.objects.get_or_create(
                nombre_categoria=nombre,
                defaults={'descripcion': descripcion},
            )
            creadas += int(creada)

        self.stdout.write(
            self.style.SUCCESS(
                f'Categorias disponibles: {len(CATEGORIAS)} ({creadas} nuevas).'
            )
        )
