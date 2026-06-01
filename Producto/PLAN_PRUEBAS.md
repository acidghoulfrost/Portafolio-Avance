# Cobertura de pruebas Full Cars

Este documento resume la cobertura basica priorizada para el ambiente de
pruebas. La suite automatizada se ejecuta con:

```powershell
python manage.py test
```

## Funcionalidad

| Area | Casos cubiertos |
| --- | --- |
| Catalogo | Productos activos, filtros, busqueda, detalle y categorias inactivas |
| Usuarios | Registro, login invalido, permisos de cliente y recuperacion de clave |
| Inventario | Alta, stock no negativo, imagen valida, cambio de estado y eliminacion |
| Compras | Carrito, limite de stock, checkout autenticado, detalle y descuento de stock |
| Despliegue | Migraciones y carga idempotente de categorias iniciales |

## Usabilidad

| Area | Validacion |
| --- | --- |
| Navegacion | Enlace para saltar al contenido y foco visible para teclado |
| Catalogo | Etiquetas asociadas a busqueda y categoria |
| Animaciones | Engranajes en portada e iconos de acceso; se reducen si el sistema solicita menos movimiento |
| Login | Autocompletado y control accesible para mostrar u ocultar contrasena |
| Asistente | Boton con estado expandido, campo etiquetado y mensajes anunciados dinamicamente |

## Seguridad basica

| Area | Validacion |
| --- | --- |
| CSRF | Proteccion en asistente, carrito y formularios POST |
| Metodos HTTP | Logout, cambio de estado y eliminacion no aceptan GET |
| Permisos | Clientes no acceden a inventario ni ventas |
| Entradas | Escape HTML, validacion numerica, imagenes y filtro de categoria |
| Redirecciones | El carrito solo acepta destinos internos |
| Encabezados | `DENY`, `nosniff` y politica de referencia `same-origin` |
| Sesion | Cookies `HttpOnly`; en Render tambien `Secure` y HTTPS |

## Revision manual recomendada

1. Recorrer catalogo, filtro, busqueda y detalle desde computador y telefono.
2. Navegar con `Tab` y comprobar que el foco siempre sea visible.
3. Probar login correcto, incorrecto y recuperacion de contrasena.
4. Crear, editar, desactivar y eliminar un producto como administrador.
5. Agregar productos, modificar cantidades y completar una compra como cliente.
6. Consultar al asistente por saludo, producto existente y producto desconocido.
