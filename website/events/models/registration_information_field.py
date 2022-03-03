from django.db import models
from django.utils.translation import gettext_lazy as _

from . import Event, EventRegistration


class RegistrationInformationField(models.Model):
    """Describes a field description to ask for when registering."""

    BOOLEAN_FIELD = "boolean"
    INTEGER_FIELD = "integer"
    TEXT_FIELD = "text"

    FIELD_TYPES = (
        (BOOLEAN_FIELD, _("Checkbox")),
        (TEXT_FIELD, _("Text")),
        (INTEGER_FIELD, _("Integer")),
    )

    event = models.ForeignKey(Event, models.CASCADE)

    type = models.CharField(
        _("field type"),
        choices=FIELD_TYPES,
        max_length=10,
    )

    name = models.CharField(
        _("field name"),
        max_length=100,
    )

    description = models.TextField(
        _("description"),
        null=True,
        blank=True,
    )

    required = models.BooleanField(
        _("required"),
    )

    def get_value_for(self, registration):
        if self.type == self.TEXT_FIELD:
            value_set = self.textregistrationinformation_set
        elif self.type == self.BOOLEAN_FIELD:
            value_set = self.booleanregistrationinformation_set
        elif self.type == self.INTEGER_FIELD:
            value_set = self.integerregistrationinformation_set

        try:
            return value_set.get(registration=registration).value
        except (
            TextRegistrationInformation.DoesNotExist,
            BooleanRegistrationInformation.DoesNotExist,
            IntegerRegistrationInformation.DoesNotExist,
        ):
            return None

    def set_value_for(self, registration, value):
        if self.type == self.TEXT_FIELD:
            value_set = self.textregistrationinformation_set
        elif self.type == self.BOOLEAN_FIELD:
            value_set = self.booleanregistrationinformation_set
        elif self.type == self.INTEGER_FIELD:
            value_set = self.integerregistrationinformation_set

        try:
            field_value = value_set.get(registration=registration)
        except BooleanRegistrationInformation.DoesNotExist:
            field_value = BooleanRegistrationInformation()
        except TextRegistrationInformation.DoesNotExist:
            field_value = TextRegistrationInformation()
        except IntegerRegistrationInformation.DoesNotExist:
            field_value = IntegerRegistrationInformation()

        field_value.registration = registration
        field_value.field = self
        field_value.value = value
        field_value.save()

    def __str__(self):
        return "{} ({})".format(self.name, dict(self.FIELD_TYPES)[self.type])

    class Meta:
        order_with_respect_to = "event"


class AbstractRegistrationInformation(models.Model):
    """Abstract to contain common things for registration information."""

    registration = models.ForeignKey(EventRegistration, models.CASCADE)
    field = models.ForeignKey(RegistrationInformationField, models.CASCADE)
    changed = models.DateTimeField(_("last changed"), auto_now=True)

    def __str__(self):
        return "{} - {}: {}".format(self.registration, self.field, self.value)

    class Meta:
        abstract = True


class BooleanRegistrationInformation(AbstractRegistrationInformation):
    """Checkbox information filled in by members when registering."""

    value = models.BooleanField()


class TextRegistrationInformation(AbstractRegistrationInformation):
    """Checkbox information filled in by members when registering."""

    value = models.TextField()


class IntegerRegistrationInformation(AbstractRegistrationInformation):
    """Checkbox information filled in by members when registering."""

    value = models.IntegerField()
