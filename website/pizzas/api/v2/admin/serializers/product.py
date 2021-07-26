from rest_framework import serializers

from pizzas.models import Product


class ProductAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("pk", "name", "available", "restricted", "description", "price")
