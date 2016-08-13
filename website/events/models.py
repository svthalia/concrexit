from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class Event(models.Model):
    """Represents events"""

    DEFAULT_NO_REGISTRATION_MESSAGE = _('No registration required')

    title = models.CharField(_("title"), max_length=100)

    description = models.TextField(_("description"))

    start = models.DateTimeField(_("start time"))

    end = models.DateTimeField(_("end time"))

    organiser = models.ForeignKey(
        'committees.Committee',
        models.SET_NULL,
        null=True,
    )

    registration_required = models.BooleanField(
        _('registration required'),
        default=False
    )

    registration_start = models.DateTimeField(
        _("registration start"),
        null=True,
        blank=True,
    )

    registration_end = models.DateTimeField(
        _("registration end"),
        null=True,
        blank=True
    )

    location = models.CharField(_("location"), max_length=255)

    map_location = models.CharField(
        _("location for minimap"),
        max_length=255,
        help_text=_('Location of Huygens: Heyendaalseweg 135, Nijmegen. '
                    'Not shown as text!!'),
    )

    price = models.DecimalField(
        _("price"),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[validators.MinValueValidator(0)],
    )

    cost = models.DecimalField(
        _("cost"),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_("Actual cost of event."),
        validators=[validators.MinValueValidator(0)],
    )

    max_participants = models.PositiveSmallIntegerField(
        _('maximum number of participants'),
        blank=True,
        null=True,
    )

    no_registration_message = models.CharField(
        _('message when there is no registration'),
        max_length=200,
        blank=True,
        null=True,
        help_text=(_("Default: {}").format(DEFAULT_NO_REGISTRATION_MESSAGE)),
    )

    published = models.BooleanField(_("published"), default=False)

    def clean(self):
        super().clean()
        errors = {}
        if self.end < self.start:
            errors.update({
                    'end': _("Can't have an event travel back in time")})
        if self.registration_required:
            if self.no_registration_message:
                errors.update(
                    {'no_registration_message': _(
                        "Doesn't make sense to have this if you require "
                        "registrations.")})
            if not self.registration_start:
                errors.update(
                    {'registration_start': _(
                        "If registration is required, you need a start of "
                        "registration")})
            if not self.registration_end:
                errors.update(
                    {'registration_end': _(
                        "If registration is required, you need an end of "
                        "registration")})
            if self.registration_start and self.registration_end and (
                    self.registration_start >= self.registration_end):
                message = _('Registration start should be before '
                            'registration end')
                errors.update({
                    'registration_start': message,
                    'registration_end': message})
        if errors:
            raise ValidationError(errors)

    def get_absolute_url(self):
        return ''

    def __str__(self):
        return '{}: {}'.format(
            self.title,
            timezone.localtime(self.start).strftime('%Y-%m-%d %H:%M'))

    class Meta:
        ordering = ('-start',)


class RegistrationInformationField(models.Model):
    """Field description to ask for when registering"""
    FIELD_TYPES = (('checkbox', _('checkbox')),
                   ('charfield', _('text field')),
                   ('intfield', _('integer field')))

    event = models.ForeignKey(Event, models.CASCADE)

    type = models.CharField(
        _('field type'),
        choices=FIELD_TYPES,
        max_length=10,
    )

    name = models.CharField(
        _('field name'),
        max_length=100,
    )

    description = models.TextField(
        _('description'),
        null=True,
        blank=True,
    )

    def get_value_for(self, registration):
        if self.type == 'charfield':
            value_set = self.textregistrationinformation_set
        elif self.type == 'checkbox':
            value_set = self.booleanregistrationinformation_set
        elif value_set == 'intfield':
            value_set = self.integerregistrationinformation_set
        try:
            return value_set.get(registration=registration).value
        except (TextRegistrationInformation.DoesNotExist,
                BooleanRegistrationInformation.DoesNotExist,
                IntegerRegistrationInformation.DoesNotExist):
            return None

    class Meta:
        order_with_respect_to = 'event'


class Registration(models.Model):
    """Event registrations"""

    event = models.ForeignKey(Event, models.CASCADE)

    member = models.ForeignKey(
        'members.Member', models.CASCADE,
        blank=True,
        null=True,
        limit_choices_to=(Q(user__membership__until__isnull=True) |
                          Q(user__membership__until__gt=timezone.now()))
    )

    name = models.CharField(
        _('name'),
        max_length=50,
        help_text=_('Use this for non-members'),
        null=True,
        blank=True
    )

    date = models.DateTimeField(_('registration date'), auto_now_add=True)
    date_cancelled = models.DateTimeField(_('cancellation date'),
                                          null=True,
                                          blank=True)

    present = models.BooleanField(
        _('Present'),
        default=False,
    )
    paid = models.BooleanField(
        _('Paid'),
        default=False,
    )

    def registration_information(self):
        fields = self.event.registrationinformationfield_set.all()
        return [{'field': field, 'value': field.get_value_for(self)}
                for field in fields]

    def clean(self):
        if ((self.member is None and not self.name) or
                (self.member and self.name)):
            raise ValidationError({
                'member': _('Either specify a member or a name'),
                'name': _('Either specify a member or a name'),
            })

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude)

    def __str__(self):
        if self.member:
            return '{}: {}'.format(self.member.get_full_name(), self.event)
        else:
            return '{}: {}'.format(self.name, self.event)

    class Meta:
        ordering = ('date',)
        unique_together = (('member', 'event', 'name', 'date_cancelled'),)


class AbstractRegistrationInformation(models.Model):
    """Abstract to contain common things for registration information"""

    registration = models.ForeignKey(Registration, models.CASCADE)
    field = models.ForeignKey(RegistrationInformationField, models.CASCADE)
    changed = models.DateTimeField(_('last changed'), auto_now=True)

    def __str__(self):
        return '{} - {}: {}'.format(self.registration, self.field, self.value)

    class Meta:
        abstract = True


class BooleanRegistrationInformation(AbstractRegistrationInformation):
    """Checkbox information filled in by members when registring"""

    value = models.BooleanField()


class TextRegistrationInformation(AbstractRegistrationInformation):
    """Checkbox information filled in by members when registring"""

    value = models.TextField()


class IntegerRegistrationInformation(AbstractRegistrationInformation):
    """Checkbox information filled in by members when registring"""

    value = models.IntegerField()
