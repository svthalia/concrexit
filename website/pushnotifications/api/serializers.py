from __future__ import absolute_import

from rest_framework.serializers import ModelSerializer

from pushnotifications.models import Device


class DeviceSerializer(ModelSerializer):
    class Meta:
        model = Device

        fields = ('pk', 'registration_id', 'active', 'date_created', 'type')
        read_only_fields = ('date_created',)

        extra_kwargs = {'active': {'default': True}}
