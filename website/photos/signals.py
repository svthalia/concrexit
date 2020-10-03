from django.db.models.signals import pre_delete

from utils.models.signals import suspendingreceiver


@suspendingreceiver(
    pre_delete, sender="photos.Photo", dispatch_uid="photos_photo_delete"
)
def pre_photo_delete(sender, instance, **kwargs):
    """Remove main photo file on deletion."""
    instance.file.delete()
