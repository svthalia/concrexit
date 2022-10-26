from django.utils.html import strip_spaces_between_tags

from rest_framework import serializers

from thaliawebsite.templatetags.bleach_tags import bleach


class CleanedHTMLSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        raise NotImplementedError

    def update(self, instance, validated_data):
        raise NotImplementedError

    def create(self, validated_data):
        raise NotImplementedError

    def to_representation(self, instance):
        return strip_spaces_between_tags(bleach(instance))
