from django.conf import settings
from rest_framework import serializers

from members.models import Profile
from thaliawebsite.api.v2.serializers.thumbnail import ThumbnailSerializer


class ProfileSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop("fields", None)
        self.force_show_birthday = kwargs.pop("force_show_birthday", False)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    class Meta:
        model = Profile
        fields = "__all__"
        read_only_fields = ["name", "starting_year", "programme", "birthday"]

    display_name = serializers.SerializerMethodField("_display_name")
    short_display_name = serializers.SerializerMethodField("_short_display_name")
    birthday = serializers.SerializerMethodField("_birthday")

    photo = ThumbnailSerializer(
        size_small=settings.THUMBNAIL_SIZES["small"],
        size_medium=settings.THUMBNAIL_SIZES["medium"],
        size_large=settings.THUMBNAIL_SIZES["avatar_large"],
        placeholder="members/images/default-avatar.jpg",
    )

    def _short_display_name(self, instance):
        return instance.short_display_name()

    def _display_name(self, instance):
        return instance.display_name()

    def _birthday(self, instance):
        if instance.show_birthday or self.force_show_birthday:
            return instance.birthday
        return None
