from rest_framework import serializers

from pizzas.models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("pk", "name", "description", "price")
