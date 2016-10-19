from django.forms import ModelForm

from .models import Order


class AddOrderForm(ModelForm):
    class Meta:
        model = Order
        fields = ['name', 'product']
