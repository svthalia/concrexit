from rest_framework.relations import ManyRelatedField, PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from pushnotifications.models import Device, Category


class DeviceSerializer(ModelSerializer):

    receive_category = ManyRelatedField(
        allow_empty=True,
        required=False,
        child_relation=PrimaryKeyRelatedField(allow_empty=True,
                                              queryset=Category.objects.all(),
                                              required=False)
    )

    class Meta:
        model = Device

        fields = (
            'pk',
            'registration_id',
            'active',
            'date_created',
            'type',
            'receive_category'
        )
        read_only_fields = ('date_created',)

        extra_kwargs = {'active': {'default': True}}


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category

        fields = ('key', 'name')
