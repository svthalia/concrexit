from django.templatetags.static import static

from rest_framework.fields import FileField

from thaliawebsite.api.services import create_image_thumbnail_dict


class ThumbnailSerializer(FileField):
    options = {}

    def __init__(
        self,
        instance=None,
        data=None,
        placeholder=None,
        size_small="small",
        size_medium="medium",
        size_large="large",
        **kwargs
    ):
        super().__init__(**kwargs)

        self.placeholder = placeholder
        self.options = {
            "size_small": size_small,
            "size_medium": size_medium,
            "size_large": size_large,
        }

    def to_representation(self, value):
        placeholder = self.placeholder
        if not value and placeholder:
            placeholder = self.context["request"].build_absolute_uri(
                static(self.placeholder)
            )

        return create_image_thumbnail_dict(value, placeholder, **self.options)

    def to_internal_value(self, data):
        if data == "":
            return None
        return super().to_internal_value(data)
