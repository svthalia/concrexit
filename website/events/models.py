from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, string_concat
from utils.translation import MultilingualField, ModelTranslateMeta


class Event(models.Model, metaclass=ModelTranslateMeta):
    """Represents events"""

    REGISTRATION_NOT_NEEDED = -1
    REGISTRATION_NOT_YET_OPEN = 0
    REGISTRATION_OPEN = 1
    REGISTRATION_OPEN_NO_CANCEL = 2
    REGISTRATION_CLOSED = 3
    REGISTRATION_CLOSED_CANCEL_ONLY = 4

    DEFAULT_NO_REGISTRATION_MESSAGE = _('No registration required')

    title = MultilingualField(
        models.CharField,
        _("title"),
        max_length=100
    )

    description = MultilingualField(
        models.TextField,
        _("description")
    )

    start = models.DateTimeField(_("start time"))

    end = models.DateTimeField(_("end time"))

    organiser = models.ForeignKey(
        'activemembers.Committee',
        models.SET_NULL,
        null=True,
        verbose_name=_("organiser")
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

    cancel_deadline = models.DateTimeField(
        _("cancel deadline"),
        null=True,
        blank=True
    )

    location = MultilingualField(
        models.CharField,
        _("location"),
        max_length=255,
    )

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

    no_registration_message = MultilingualField(
        models.CharField,
        _('message when there is no registration'),
        max_length=200,
        blank=True,
        null=True,
        help_text=(string_concat(_("Default: "),
                                 DEFAULT_NO_REGISTRATION_MESSAGE)),
    )

    published = models.BooleanField(_("published"), default=False)

    def after_cancel_deadline(self):
        return self.cancel_deadline <= timezone.now()

    def registration_required(self):
        return bool(self.registration_start) or bool(self.registration_end)

    def has_fields(self):
        return self.registrationinformationfield_set.count() > 0

    def reached_participants_limit(self):
        return self.max_participants <= self.registration_set.count()

    @property
    def status(self):
        now = timezone.now()
        if bool(self.registration_start) or bool(self.registration_end):
            if now <= self.registration_start:
                return Event.REGISTRATION_NOT_YET_OPEN
            elif self.registration_end <= now < self.cancel_deadline:
                return Event.REGISTRATION_CLOSED_CANCEL_ONLY
            elif self.cancel_deadline <= now < self.registration_end:
                return Event.REGISTRATION_OPEN_NO_CANCEL
            elif now >= self.registration_end and now >= self.cancel_deadline:
                return Event.REGISTRATION_CLOSED
            else:
                return Event.REGISTRATION_OPEN
        else:
            return Event.REGISTRATION_NOT_NEEDED

    def clean(self):
        super().clean()
        errors = {}
        if self.end is not None and self.start is not None and (
                    self.end < self.start):
            errors.update({
                'end': _("Can't have an event travel back in time")})
        if self.registration_required():
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
            if not self.cancel_deadline:
                errors.update(
                    {'cancel_deadline': _(
                        "If registration is required, you need a deadline for "
                        "the cancellation")})
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
        return reverse('events:event', args=[str(self.pk)])

    def __str__(self):
        return '{}: {}'.format(
            self.title,
            timezone.localtime(self.start).strftime('%Y-%m-%d %H:%M'))

    class Meta:
        ordering = ('-start',)


class RegistrationInformationField(models.Model, metaclass=ModelTranslateMeta):
    """Field description to ask for when registering"""
    BOOLEAN_FIELD = 'boolean'
    INTEGER_FIELD = 'integer'
    TEXT_FIELD = 'text'

    FIELD_TYPES = ((BOOLEAN_FIELD, _('Checkbox')),
                   (TEXT_FIELD, _('Text')),
                   (INTEGER_FIELD, _('Integer')),)

    event = models.ForeignKey(Event, models.CASCADE)

    type = models.CharField(
        _('field type'),
        choices=FIELD_TYPES,
        max_length=10,
    )

    name = MultilingualField(
        models.CharField,
        _('field name'),
        max_length=100,
    )

    description = MultilingualField(
        models.TextField,
        _('description'),
        null=True,
        blank=True,
    )

    required = models.BooleanField(
        _('required'),
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
        except (TextRegistrationInformation.DoesNotExist,
                BooleanRegistrationInformation.DoesNotExist,
                IntegerRegistrationInformation.DoesNotExist):
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
        order_with_respect_to = 'event'


class Registration(models.Model):
    """Event registrations"""

    event = models.ForeignKey(Event, models.CASCADE)

    member = models.ForeignKey(
        'members.Member', models.CASCADE,
        blank=True,
        null=True,
        limit_choices_to=(Q(user__membership__until__isnull=True) |
                          Q(user__membership__until__gt=timezone.now().date()))
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
        _('present'),
        default=False,
    )
    paid = models.BooleanField(
        _('paid'),
        default=False,
    )

    def registration_information(self):
        fields = self.event.registrationinformationfield_set.all()
        return [{'field': field, 'value': field.get_value_for(self)}
                for field in fields]

    def is_external(self):
        return bool(self.name)

    def is_late_cancellation(self):
        return (self.date_cancelled and
                self.date_cancelled > self.event.cancel_deadline and
                self.event.registration_set.filter(
                    (Q(date_cancelled__gte=self.date_cancelled) |
                     Q(date_cancelled=None)) &
                    Q(date__lte=self.date)
                ).count() < self.event.max_participants)

    def is_registered(self):
        return self.date_cancelled is None

    def queue_position(self):
        if self.event.max_participants is None:
            return 0

        return max(self.event.registration_set.filter(
            date_cancelled=None,
            date__lte=self.date
        ).count() - self.event.max_participants, 0)

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
    """Checkbox information filled in by members when registering"""

    value = models.BooleanField()


class TextRegistrationInformation(AbstractRegistrationInformation):
    """Checkbox information filled in by members when registering"""
    value = models.TextField()


class IntegerRegistrationInformation(AbstractRegistrationInformation):
    """Checkbox information filled in by members when registering"""
    value = models.IntegerField()
