from django.core.exceptions import ValidationError

from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.serializers import raise_errors_on_nested_writes
from rest_framework.utils import model_meta


class CleanedModelSerializer(serializers.ModelSerializer):
    """Custom ModelSerializer that explicitly clean's a model before it is saved."""

    def create(self, validated_data):
        """Reraise ValidationErrors as DRF validation errors.

        No need to explicitly clean(), because under the hood, DRF uses
        .create() which does perform a clean().
        """
        try:
            return super().create(validated_data)
        except ValidationError as e:
            raise DRFValidationError(e)

    def update(self, instance, validated_data, **kwargs):
        """Override the default implementation of DRF's ModelSerializer.

        Adds `instance.clean()` to make sure all updates still clean().
        Also re-raises ValidationErrors to DRF ValidationErrors.
        """
        raise_errors_on_nested_writes("update", self, validated_data)
        info = model_meta.get_field_info(instance)

        # Simply set each attribute on the instance, and then save it.
        # Note that unlike `.create()` we don't need to treat many-to-many
        # relationships as being a special case. During updates we already
        # have an instance pk for the relationships to be associated with.
        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                setattr(instance, attr, value)

        try:
            instance.clean()
        except ValidationError as e:
            raise DRFValidationError(e)

        instance.save()

        # Note that many-to-many fields are set after updating instance.
        # Setting m2m fields triggers signals which could potentially change
        # updated instance and we do not want it to collide with .update()
        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)

        return instance
