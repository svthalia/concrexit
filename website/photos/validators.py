import magic
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class ArchiveFileTypeValidator:
    types = ["application/gzip", "application/zip", "application/x-gzip"]
    message = _("Only zip and tar files are allowed.")

    def __init__(self, types=None, message=None):
        if types is not None:
            self.types = types
        if message is not None:
            self.message = message

    def __call__(self, value):
        """
        Validate that the input contains (or does *not* contain, if
        inverse_match is True) a match for the regular expression.
        """

        if magic.from_buffer(value.read(1024), mime=True) not in self.types:
            raise ValidationError(self.message)

    def __eq__(self, other):
        return (
            isinstance(other, ArchiveFileTypeValidator)
            and self.types == other.types
            and (self.message == other.message)
        )
