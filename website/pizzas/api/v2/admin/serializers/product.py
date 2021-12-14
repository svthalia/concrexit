from pizzas.models import Product
from thaliawebsite.api.v2.serializers.cleaned_model_serializer import (
    CleanedModelSerializer,
)


class ProductAdminSerializer(CleanedModelSerializer):
    class Meta:
        model = Product
        fields = ("pk", "name", "available", "restricted", "description", "price")
