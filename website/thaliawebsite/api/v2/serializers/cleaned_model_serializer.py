from rest_framework import serializers


class CleanedModelSerializer(serializers.ModelSerializer):
    """Custom ModelSerializer that explicitly clean's a model before it is saved."""

    def create(self, validated_data, **kwargs):
        self.Meta.model(**validated_data).clean()
        return super().create(validated_data)

    def update(self, instance, validated_data, **kwargs):
        for key, val in validated_data.items():
            setattr(instance, key, val)
        instance.clean()
        return super().update(instance, validated_data)
