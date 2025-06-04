from django import forms

from sales.models.product import ProductListItem


class ProductItemField(forms.IntegerField):
    def get_productlistitem(self):
        return self._productlistitem

    def get_product(self):
        return self._productlistitem.product

    def set_productlistitem(self, product_list_item):
        self._productlistitem = product_list_item


class ProductOrderForm(forms.Form):
    def __init__(self, product_list, is_adult, *args, **kwargs):
        super().__init__(*args, **kwargs)
        product_list_items = ProductListItem.objects.filter(product_list=product_list)
        for item in product_list_items:
            field = ProductItemField(
                label=item.product.name,
                required=False,
                min_value=0,
                max_value=5,
            )
            field.set_productlistitem(item)
            if not is_adult and item.product.age_restricted:
                field.disabled = True
            self.fields[f"product_{item.product.pk}"] = field
