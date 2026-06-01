# Repuestos Full Cars

Aplicacion web Django para catalogo, inventario, stock, compras y consultas
guiadas mediante un asistente virtual conectado al inventario.

## Funciones

- Catalogo publico con busqueda, filtro por categoria y detalle de producto.
- Estados de disponibilidad: disponible, bajo stock y sin stock.
- Registro, login, logout y recuperacion de contrasena.
- Carrito por sesion, checkout autenticado e historial de compras.
- Panel staff para CRUD de productos, activacion y desactivacion.
- Panel staff para revisar operaciones de compra.
- Asistente virtual para buscar repuestos y consultar stock.

## Ejecucion local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo --with-users
$env:DEBUG='True'
python manage.py runserver
```

Usuarios opcionales creados por `seed_demo --with-users`:

- Administrador: `admin_demo`
- Cliente: `cliente_demo`
- Contrasena local para ambos: `FullCars2026!`

## Validacion

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --no-input
```

## Despliegue

Configurar estas variables de entorno:

- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS=.onrender.com`
- `DATABASE_URL`
- `BREVO_API_KEY`
- `SECURE_SSL_REDIRECT=True`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_HSTS_SECONDS=31536000`
- `SECURE_HSTS_PRELOAD=True`
- `DJANGO_SUPERUSER_USERNAME`
- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`

Comando de build:

```bash
./build.sh
```

Comando de inicio:

```bash
gunicorn full_cars.wsgi:application
```

### Blueprint de pruebas

El repositorio incluye `render.yaml` en su raiz para crear el servicio web y una
base PostgreSQL gratuita desde **New > Blueprint** en Render. Durante el alta,
Render solicita `DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD` sin
guardarlos en Git. El usuario administrativo inicial es `admin`.

El Blueprint fija Python `3.11.11`, ejecuta `bash ./build.sh` desde `Producto`,
carga las categorias iniciales y configura las cookies seguras para HTTPS.
