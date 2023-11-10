from django.db.models.signals import pre_delete

from utils.models.signals import suspendingreceiver


@suspendingreceiver(
    pre_delete, sender="photos.Photo", dispatch_uid="photos_photo_delete"
)
def pre_photo_delete(sender, instance, **kwargs):
    """Remove main photo file and thumbnails on deletion."""
    name = instance.file.name  # First get the name, it is removed by the next line.
    instance.file.delete()  # Delete the file and its thumbnails.

    # Clean up the source metadata, django-thumbnails does not do this.
    instance.file.metadata_backend.delete_source(name)
