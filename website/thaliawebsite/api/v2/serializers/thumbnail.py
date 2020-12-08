from django.conf import settings
from django.templatetags.static import static
from django.utils.html import strip_spaces_between_tags
from rest_framework import serializers

from thaliawebsite.api.services import create_image_thumbnail_dict
from thaliawebsite.templatetags.bleach_tags import bleach


class ThumbnailSerializer(serializers.BaseSerializer):
    options = {}

    def __init__(
        self,
        instance=None,
        data=None,
        placeholder=None,
        size_small=settings.THUMBNAIL_SIZES["small"],
        size_medium=settings.THUMBNAIL_SIZES["medium"],
        size_large=settings.THUMBNAIL_SIZES["large"],
        fit_small=True,
        fit_medium=True,
        fit_large=True,
        **kwargs
    ):
        super().__init__(instance, data, **kwargs)

        self.placeholder = placeholder
        self.options = {
            "size_small": size_small,
            "size_medium": size_medium,
            "size_large": size_large,
            "fit_small": fit_small,
            "fit_medium": fit_medium,
            "fit_large": fit_large,
        }

    def to_representation(self, instance):
        placeholder = self.placeholder
        if not instance and placeholder:
            placeholder = self.context["request"].build_absolute_uri(
                static(self.placeholder)
            )

        return create_image_thumbnail_dict(
            self.context["request"], instance, placeholder, **self.options
        )

    def to_internal_value(self, data):
        pass

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class CleanedHTMLSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        pass

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def to_representation(self, instance):
        return strip_spaces_between_tags(bleach(instance))
