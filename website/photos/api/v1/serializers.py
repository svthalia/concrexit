from rest_framework import serializers

from photos import services
from photos.models import Album, Photo
from thaliawebsite.api.services import create_image_thumbnail_dict
from thaliawebsite.api.v1.cleaned_model_serializer import CleanedModelSerializer


class PhotoRetrieveSerializer(CleanedModelSerializer):
    """ModelSerializer class to get a Photo object set."""

    file = serializers.SerializerMethodField("_file")

    def _file(self, obj):
        file = None
        if obj:
            file = obj.file
        return create_image_thumbnail_dict(file)

    class Meta:
        """Meta class for PhotoRetrieveSerializer."""

        model = Photo
        fields = ("pk", "album", "file")


class PhotoCreateSerializer(CleanedModelSerializer):
    """ModelSerializer class to create or update a Photo object set."""

    class Meta:
        """Met class for PhotoCreateSerializer."""

        model = Photo
        fields = ("pk", "album", "file")


class AlbumSerializer(CleanedModelSerializer):
    """ModelSerializer for an Album object."""

    photos = serializers.SerializerMethodField("_photos")
    accessible = serializers.SerializerMethodField("_accessible")

    def _accessible(self, obj):
        return services.is_album_accessible(self.context["request"], obj)

    def _photos(self, obj):
        if self._accessible(obj):
            return PhotoRetrieveSerializer(
                obj.photo_set, context=self.context, many=True
            ).data
        return []

    def create(self, validated_data):
        """Create album."""
        photos_data = validated_data.pop("photos")
        album = Album.objects.create(**validated_data)
        for photo_data in photos_data:
            Photo.objects.create(album=album, **photo_data)
        return album

    def update(self, instance, validated_data):
        """Update album."""
        photos_data = validated_data.pop("photos")
        album = Album.objects.update(**validated_data)
        for photo_data in photos_data:
            Photo.objects.update(album=album, **photo_data)
        return album

    class Meta:
        """Meta class for AlbumSerializer."""

        model = Album
        fields = ("pk", "title", "date", "hidden", "shareable", "accessible", "photos")


class AlbumListSerializer(CleanedModelSerializer):
    """ModelSerializer class for a list of Albums."""

    cover = PhotoRetrieveSerializer()
    accessible = serializers.SerializerMethodField("_accessible")

    def _accessible(self, obj):
        return services.is_album_accessible(self.context["request"], obj)

    class Meta:
        """Meta class for AlbumListSerializer."""

        model = Album
        fields = ("pk", "title", "date", "hidden", "shareable", "accessible", "cover")
