from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('producto/<int:id>/', views.producto_detalle, name='producto_detalle'),

    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('registro/', views.registro, name='registro'),

    path('carrito/', views.ver_carrito, name='carrito'),
    path('carrito/agregar/<int:id>/', views.agregar_carrito, name='agregar_carrito'),
    path('carrito/actualizar/<int:id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('carrito/quitar/<int:id>/', views.quitar_carrito, name='quitar_carrito'),
    path('checkout/', views.checkout, name='checkout'),
    path('mis-compras/', views.mis_compras, name='mis_compras'),

    path('gestion-productos/', views.admin_productos, name='admin_productos'),
    path('producto/<int:id>/estado/', views.cambiar_estado_producto, name='cambiar_estado_producto'),
    path('eliminar-producto/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    path('gestion-compras/', views.admin_compras, name='admin_compras'),

    path('asistente/', views.asistente_virtual, name='asistente_virtual'),

    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='usuarios/password_reset.html',
            email_template_name='usuarios/password_reset_email.html',
            subject_template_name='usuarios/password_reset_subject.txt',
            success_url='/password-reset/done/',
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='usuarios/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='usuarios/password_reset_confirm.html',
            success_url='/password-reset-complete/',
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='usuarios/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
]
