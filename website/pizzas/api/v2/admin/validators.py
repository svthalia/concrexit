from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError


class MutuallyExclusiveValidator:
    """Validator that corresponds to `unique=True` on a model field.

    Should be applied to an individual field on the serializer.
    """

    message = _("The fields {field_names} are mutually exclusive.")
    missing_message = _("This field is required.")
    requires_context = True

    def __init__(self, fields):
        self.fields = fields

    def __call__(self, attrs, serializer):
        sources = [serializer.fields[field_name].source for field_name in self.fields]

        # If this is an update, then any unprovided field should
        # have it's value set based on the existing instance attribute.
        if serializer.instance is not None:
            for source in sources:
                if source not in attrs:
                    attrs[source] = getattr(serializer.instance, source)

        field_present = False
        for field in self.fields:
            if field in attrs and attrs[field] is not None:
                if field_present:
                    field_names = ", ".join(self.fields)
                    message = self.message.format(field_names=field_names)
                    raise ValidationError(message, code="exclusive")
                field_present = True
