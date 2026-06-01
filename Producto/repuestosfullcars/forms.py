from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Compra, Producto


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electronico')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return email


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = (
            'nombre_producto',
            'categoria',
            'descripcion',
            'precio',
            'stock',
            'estado',
            'imagen_url',
        )
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'precio': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'min': 0}),
            'imagen_url': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ('metodo_pago', 'direccion_envio')
        widgets = {
            'direccion_envio': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Direccion de entrega o retiro',
                }
            ),
        }
