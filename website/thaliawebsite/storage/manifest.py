from django.conf import settings
from django.contrib.staticfiles.storage import (
    ManifestStaticFilesStorage as ParentStorage,
)


class ManifestStaticFilesStorage(ParentStorage):
    def __init__(self, *args, **kwargs):
        self.manifest_strict = settings.STATICFILES_STORAGE_STRICT
        super().__init__(*args, **kwargs)
