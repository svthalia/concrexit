from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.text import format_lazy
from tinymce.models import HTMLField

from utils.translation import ModelTranslateMeta, MultilingualField


class Event(models.Model, metaclass=ModelTranslateMeta):
    """Represents events"""

    EVENT_CATEGORIES = (
        ('drinks', _('Drinks')),
        ('activity', _('Activity')),
        ('lunchlecture', _('Lunch Lecture')),
        ('generalmeeting', _('General Meeting')),
        ('workshop', _('Workshop')),
        ('other', _('Other')))

    DEFAULT_NO_REGISTRATION_MESSAGE = _('No registration required')

    title = MultilingualField(
        models.CharField,
        _("title"),
        max_length=100
    )

    description = MultilingualField(
        HTMLField,
        _("description")
    )

    start = models.DateTimeField(_("start time"))

    end = models.DateTimeField(_("end time"))

    organiser = models.ForeignKey(
        'activemembers.Committee',
        models.PROTECT,
        verbose_name=_("organiser")
    )

    category = models.CharField(
        max_length=40,
        choices=EVENT_CATEGORIES,
        verbose_name=_('category'),
        default='other'
    )

    registration_start = models.DateTimeField(
        _("registration start"),
        null=True,
        blank=True,
        help_text=_("If you set a registration period registration will be "
                    "required. If you don't set one, registration won't be "
                    "required.")
    )

    registration_end = models.DateTimeField(
        _("registration end"),
        null=True,
        blank=True,
        help_text=_("If you set a registration period registration will be "
                    "required. If you don't set one, registration won't be "
                    "required.")
    )

    cancel_deadline = models.DateTimeField(
        _("cancel deadline"),
        null=True,
        blank=True
    )

    send_cancel_email = models.BooleanField(
        _('send cancellation notifications'),
        default=True,
        help_text=_("Send an email to the organising party when a member "
                    "cancels their registration after the deadline."),
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
                    'Location of Mercator 1: Toernooiveld 212, Nijmegen. '
                    'Not shown as text!!'),
    )

    price = models.DecimalField(
        _("price"),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[validators.MinValueValidator(0)],
    )

    fine = models.DecimalField(
        _("fine"),
        max_digits=5,
        decimal_places=2,
        default=0,
        # Minimum fine is checked in this model's clean(), as it is only for
        # events that require registration.
        help_text=_("Fine if participant does not show up (at least €5)."),
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
        help_text=(format_lazy("{} {}", _("Default:"),
                               DEFAULT_NO_REGISTRATION_MESSAGE)),
    )

    published = models.BooleanField(_("published"), default=False)

    @property
    def after_cancel_deadline(self):
        return self.cancel_deadline and self.cancel_deadline <= timezone.now()

    @property
    def registration_started(self):
        return self.registration_start <= timezone.now()

    @property
    def registration_required(self):
        return bool(self.registration_start) or bool(self.registration_end)

    def has_fields(self):
        return self.registrationinformationfield_set.count() > 0

    def reached_participants_limit(self):
        """Is this event up to capacity?"""
        return (self.max_participants is not None and
                self.max_participants <= self.registration_set.filter(
                    date_cancelled=None).count())

    @property
    def registrations(self):
        """Queryset with all non-cancelled registrations"""
        return self.registration_set.filter(date_cancelled=None)

    @property
    def participants(self):
        """Return the active participants"""
        if self.max_participants is not None:
            return self.registrations.order_by('date')[:self.max_participants]
        return self.registrations.order_by('date')

    @property
    def queue(self):
        """Return the waiting queue"""
        if self.max_participants is not None:
            return self.registrations.order_by('date')[self.max_participants:]
        return []

    @property
    def cancellations(self):
        """Return a queryset with the cancelled events"""
        return (self.registration_set
                .exclude(date_cancelled=None)
                .order_by('date_cancelled'))

    @property
    def registration_allowed(self):
        now = timezone.now()
        return ((self.registration_start or self.registration_end) and
                self.registration_end > now >= self.registration_start)

    @property
    def cancellation_allowed(self):
        now = timezone.now()
        return ((self.registration_start or self.registration_end)
                and now >= self.registration_start)

    def is_pizza_event(self):
        try:
            self.pizzaevent
            return True
        except ObjectDoesNotExist:
            return False

    def clean(self):
        super().clean()
        errors = {}
        if self.start is None:
            errors.update({
                'start': _("Start cannot have an empty date or time field")
            })
        if self.end is None:
            errors.update({
                'end': _("End cannot have an empty date or time field")
            })
        if self.start is not None and self.end is not None:
            if self.end < self.start:
                errors.update({
                    'end': _("Can't have an event travel back in time")})
            if self.registration_required:
                if self.fine < 5:
                    errors.update({
                        'fine': _("The fine for this event is too low "
                                  "(must be at least €5).")
                    })
                for lang in settings.LANGUAGES:
                    field = 'no_registration_message_' + lang[0]
                    if getattr(self, field):
                        errors.update(
                            {field: _("Doesn't make sense to have this "
                                      "if you require registrations.")})
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
                            "If registration is required, "
                            "you need a deadline for the cancellation")})
                elif self.cancel_deadline > self.start:
                    errors.update(
                        {'cancel_deadline': _(
                            "The cancel deadline should be"
                            " before the start of the event.")})
                if self.registration_start and self.registration_end and (
                        self.registration_start >= self.registration_end):
                    message = _('Registration start should be before '
                                'registration end')
                    errors.update({
                        'registration_start': message,
                        'registration_end': message})
        if (self.organiser is not None and
                self.send_cancel_email and
                self.organiser.contact_mailinglist is None):
            errors.update(
                {'send_cancel_email': _("This organiser does not "
                                        "have a contact mailinglist.")})

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
        permissions = (
            ("override_organiser", "Can access events as if organizing"),
        )


def registration_member_choices_limit():
    return (Q(membership__until__isnull=True) |
            Q(membership__until__gt=timezone.now().date()))


class Registration(models.Model):
    """Event registrations"""

    PAYMENT_CARD = 'card_payment'
    PAYMENT_CASH = 'cash_payment'
    PAYMENT_NONE = 'no_payment'

    PAYMENT_TYPES = (
        (PAYMENT_NONE, _('No payment')),
        (PAYMENT_CASH, _('Paid with cash')),
        (PAYMENT_CARD, _('Paid with card')))

    event = models.ForeignKey(Event, models.CASCADE)

    member = models.ForeignKey(
        'members.Member', models.CASCADE,
        blank=True,
        null=True,
        limit_choices_to=registration_member_choices_limit
    )

    name = models.CharField(
        _('name'),
        max_length=50,
        help_text=_('Use this for non-members'),
        null=True,
        blank=True
    )

    date = models.DateTimeField(_('registration date'),
                                default=timezone.now)
    date_cancelled = models.DateTimeField(_('cancellation date'),
                                          null=True,
                                          blank=True)

    present = models.BooleanField(
        _('present'),
        default=False,
    )

    payment = models.CharField(
        choices=PAYMENT_TYPES,
        default='no_payment',
        verbose_name=_('payment'),
        max_length=20,
    )

    @property
    def information_fields(self):
        fields = self.event.registrationinformationfield_set.all()
        return [{'field': field, 'value': field.get_value_for(self)}
                for field in fields]

    @property
    def is_registered(self):
        return self.date_cancelled is None

    @property
    def queue_position(self):
        if self.event.max_participants is not None:
            try:
                return list(self.event.queue).index(self) + 1
            except ValueError:
                pass
        return 0

    def is_external(self):
        return bool(self.name)

    def is_late_cancellation(self):
        # First check whether or not the user cancelled
        # If the user cancelled then check if this was after the deadline
        # And if there is a max participants number:
        # do a complex check to calculate if this user was on
        # the waiting list at the time of cancellation, since
        # you shouldn't need to pay the costs of something
        # you weren't even able to go to.
        return (self.date_cancelled and
                self.event.cancel_deadline and
                self.date_cancelled > self.event.cancel_deadline and
                (self.event.max_participants is None or
                 self.event.registration_set.filter(
                     (Q(date_cancelled__gte=self.date_cancelled) |
                      Q(date_cancelled=None)) &
                     Q(date__lte=self.date)
                 ).count() < self.event.max_participants))

    def is_paid(self):
        return self.payment in [Registration.PAYMENT_CARD,
                                Registration.PAYMENT_CASH]

    def would_cancel_after_deadline(self):
        now = timezone.now()
        return (self.queue_position == 0 and
                now >= self.event.cancel_deadline)

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
