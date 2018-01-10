from django.forms import ModelForm

from .models import Order, Product


class AddOrderForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.available_products.all()

    class Meta:
        model = Order
        fields = ['name', 'product']
