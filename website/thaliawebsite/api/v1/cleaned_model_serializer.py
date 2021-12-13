from rest_framework import serializers


class CleanedModelSerializer(serializers.ModelSerializer):
    """Custom ModelSerializer that explicitly clean's a model before it is saved."""

    def validate(self, attrs):
        super().validate(attrs)
        instance = self.Meta.model(**attrs)
        instance.clean()
        return attrs
