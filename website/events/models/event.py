import uuid

from django.conf import settings
from django.core import validators
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models, router
from django.db.models import Count, Q
from django.db.models.deletion import Collector
from django.urls import reverse
from django.utils import timezone
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from queryable_properties.managers import QueryablePropertiesManager
from queryable_properties.properties import AggregateProperty
from tinymce.models import HTMLField

from events.models import status
from events.models.categories import EVENT_CATEGORIES
from payments.models import PaymentAmountField


class Event(models.Model):
    """Describes an event."""

    objects = QueryablePropertiesManager()

    DEFAULT_NO_REGISTRATION_MESSAGE = _("No registration required")

    title = models.CharField(_("title"), max_length=100)

    slug = models.SlugField(
        verbose_name=_("slug"),
        help_text=_(
            "A short name for the event, used in the URL. For example: thalia-weekend-2023. "
            "Note that the slug must be unique."
        ),
        unique=True,
        blank=True,
        null=True,
    )

    description = HTMLField(
        _("description"),
    )

    caption = models.TextField(
        _("caption"),
        max_length=500,
        null=False,
        blank=False,
        help_text=_(
            "A short text of max 500 characters for promotion and the newsletter."
        ),
    )

    start = models.DateTimeField(_("start time"))

    end = models.DateTimeField(_("end time"))

    organisers = models.ManyToManyField(
        "activemembers.MemberGroup",
        verbose_name=_("organisers"),
        related_name=_("event_organiser"),
    )

    category = models.CharField(
        max_length=40,
        choices=EVENT_CATEGORIES,
        verbose_name=_("category"),
        help_text=_(
            "Alumni: Events organised for alumni, "
            "Education: Education focused events, "
            "Career: Career focused events, "
            "Leisure: borrels, parties, game activities etc., "
            "Association Affairs: general meetings or "
            "any other board related events, "
            "Other: anything else."
        ),
    )

    registration_start = models.DateTimeField(
        _("registration start"),
        null=True,
        blank=True,
        help_text=_(
            "If you set a registration period registration will be "
            "required. If you don't set one, registration won't be "
            "required. Prefer times when people don't have lectures, "
            "e.g. 12:30 instead of 13:37."
        ),
    )

    registration_end = models.DateTimeField(
        _("registration end"),
        null=True,
        blank=True,
        help_text=_(
            "If you set a registration period registration will be "
            "required. If you don't set one, registration won't be "
            "required."
        ),
    )

    cancel_deadline = models.DateTimeField(_("cancel deadline"), null=True, blank=True)

    send_cancel_email = models.BooleanField(
        _("send cancellation notifications"),
        default=True,
        help_text=_(
            "Send an email to the organising party when a member "
            "cancels their registration after the deadline."
        ),
    )

    registration_without_membership = models.BooleanField(
        _("registration without membership"),
        default=False,
        help_text=_(
            "Users without a currently active membership (such as past members) "
            "are allowed to register for this event. This is useful for "
            "events aimed at alumni, for example."
        ),
    )

    optional_registrations = models.BooleanField(
        _("allow optional registrations"),
        default=True,
        help_text=_(
            "Participants can indicate their optional presence, even though "
            "registration is not actually required. This ignores registration "
            "start and end time or cancellation deadlines, optional "
            "registration will be enabled directly after publishing until the "
            "end of the event."
        ),
    )

    location = models.CharField(
        _("location"),
        max_length=255,
    )

    map_location = models.CharField(
        _("location for minimap"),
        max_length=255,
        help_text=_(
            "Location of Huygens: Heyendaalseweg 135, Nijmegen. "
            "Location of Mercator 1: Toernooiveld 212, Nijmegen. "
            "Use the input 'discord' or 'online' for special placeholders. "
            "Not shown as text!!"
        ),
    )

    show_map_location = models.BooleanField(
        _("show url for location"),
        default=True,
    )

    price = PaymentAmountField(
        verbose_name=_("price"),
        allow_zero=True,
        default=0,
        validators=[validators.MinValueValidator(0)],
    )

    fine = PaymentAmountField(
        verbose_name=_("fine"),
        allow_zero=True,
        default=0,
        # Minimum fine is checked in this model's clean(), as it is only for
        # events that require registration.
        help_text=_("Fine if participant does not show up (at least €5)."),
        validators=[validators.MinValueValidator(0)],
    )

    max_participants = models.PositiveSmallIntegerField(
        _("maximum number of participants"),
        blank=True,
        null=True,
    )

    no_registration_message = models.CharField(
        _("message when there is no registration"),
        max_length=200,
        blank=True,
        null=True,
        help_text=(
            format_lazy(
                "{} {}. {}",
                _("Default:"),
                DEFAULT_NO_REGISTRATION_MESSAGE,
                _(
                    'This field accepts HTML tags as well, e.g. links with &lta href="https://example.com" target="_blank"&gthttps://example.com&lt/a&gt'
                ),
            )
        ),
    )

    published = models.BooleanField(_("published"), default=False)

    documents = models.ManyToManyField(
        "documents.Document",
        verbose_name=_("documents"),
        blank=True,
    )

    tpay_allowed = models.BooleanField(_("Allow Thalia Pay"), default=True)

    shift = models.OneToOneField("sales.Shift", models.SET_NULL, null=True, blank=True)

    mark_present_url_token = models.UUIDField(
        unique=True, default=uuid.uuid4, editable=False
    )

    @property
    def mark_present_url(self):
        """Return a url that a user can use to mark themselves present."""
        return settings.BASE_URL + reverse(
            "events:mark-present",
            kwargs={
                "pk": self.pk,
                "token": self.mark_present_url_token,
            },
        )

    @property
    def cancel_too_late_message(self):
        return _(
            "Cancellation isn't possible anymore without having to pay "
            "the full costs of €" + str(self.fine) + ". Also note that "
            "you will be unable to re-register."
        )

    @property
    def after_cancel_deadline(self):
        return self.cancel_deadline and self.cancel_deadline <= timezone.now()

    @property
    def registration_started(self):
        return self.registration_start <= timezone.now()

    @property
    def registration_required(self):
        return bool(self.registration_start) or bool(self.registration_end)

    @property
    def payment_required(self):
        return self.price != 0

    @property
    def has_fields(self):
        return self.registrationinformationfield_set.count() > 0

    participant_count = AggregateProperty(
        Count(
            "eventregistration",
            filter=Q(eventregistration__date_cancelled=None),
        )
    )

    def reached_participants_limit(self):
        """Is this event up to capacity?."""
        return (
            self.max_participants is not None
            and self.max_participants <= self.participant_count
        )

    @property
    def registrations(self):
        """Queryset with all non-cancelled registrations."""
        return self.eventregistration_set.filter(date_cancelled=None)

    @property
    def participants(self):
        """Return the active participants."""
        if self.max_participants is not None:
            return self.registrations.order_by("date")[: self.max_participants]
        return self.registrations.order_by("date")

    @property
    def queue(self):
        """Return the waiting queue."""
        if self.max_participants is not None:
            return self.registrations.order_by("date")[self.max_participants :]
        return []

    @property
    def cancellations(self):
        """Return a queryset with the cancelled events."""
        return self.eventregistration_set.exclude(date_cancelled=None).order_by(
            "date_cancelled"
        )

    @property
    def registration_allowed(self):
        now = timezone.now()
        return (
            bool(self.registration_start or self.registration_end)
            and self.registration_end > now >= self.registration_start
        )

    @property
    def cancellation_allowed(self):
        now = timezone.now()
        return (
            bool(self.registration_start or self.registration_end)
            and self.registration_start <= now < self.start
        )

    @property
    def optional_registration_allowed(self):
        return (
            self.optional_registrations
            and not self.registration_required
            and self.end >= timezone.now()
        )

    @property
    def has_food_event(self):
        # pylint: disable=pointless-statement
        try:
            self.food_event
            return True
        except ObjectDoesNotExist:
            return False

    @property
    def location_link(self):
        """Return the link to the location on google maps."""
        if self.show_map_location is False:
            return None
        return "https://www.google.com/maps/place/" + self.map_location.replace(
            " ", "+"
        )

    def clean_changes(self, changed_data):
        """Check if changes from `changed_data` are allowed.

        This method should be run from a form clean() method, where changed_data
        can be retrieved from self.changed_data
        """
        errors = {}
        if self.published or self.participant_count > 0:
            for field in ("price", "registration_start"):
                if (
                    field in changed_data
                    and self.registration_start
                    and self.registration_start <= timezone.now()
                ):
                    errors.update(
                        {
                            field: _(
                                "You cannot change this field after "
                                "the registration has started."
                            )
                        }
                    )

        if errors:
            raise ValidationError(errors)

    def clean(self):
        # pylint: disable=too-many-branches
        super().clean()
        errors = {}
        if self.start is None:
            errors.update({"start": _("Start cannot have an empty date or time field")})
        if self.end is None:
            errors.update({"end": _("End cannot have an empty date or time field")})
        if self.start is not None and self.end is not None:
            if self.end < self.start:
                errors.update({"end": _("Can't have an event travel back in time")})
            if self.registration_required:
                if self.optional_registrations:
                    errors.update(
                        {
                            "optional_registrations": _(
                                "This is not possible when actual registrations are required."
                            )
                        }
                    )
                if self.fine < 5:
                    errors.update(
                        {
                            "fine": _(
                                "The fine for this event is too low "
                                "(must be at least €5)."
                            )
                        }
                    )
                if self.no_registration_message:
                    errors.update(
                        {
                            "no_registration_message": _(
                                "Doesn't make sense to have this "
                                "if you require registrations."
                            )
                        }
                    )
                if not self.registration_start:
                    errors.update(
                        {
                            "registration_start": _(
                                "If registration is required, you need a start of "
                                "registration"
                            )
                        }
                    )
                if not self.registration_end:
                    errors.update(
                        {
                            "registration_end": _(
                                "If registration is required, you need an end of "
                                "registration"
                            )
                        }
                    )
                if not self.cancel_deadline:
                    errors.update(
                        {
                            "cancel_deadline": _(
                                "If registration is required, "
                                "you need a deadline for the cancellation"
                            )
                        }
                    )
                elif self.cancel_deadline > self.start:
                    errors.update(
                        {
                            "cancel_deadline": _(
                                "The cancel deadline should be"
                                " before the start of the event."
                            )
                        }
                    )
                if (
                    self.registration_start
                    and self.registration_end
                    and (self.registration_start >= self.registration_end)
                ):
                    message = _("Registration start should be before registration end")
                    errors.update(
                        {"registration_start": message, "registration_end": message}
                    )

        if errors:
            raise ValidationError(errors)

    def get_absolute_url(self):
        if self.slug is None:
            return reverse("events:event", kwargs={"pk": self.pk})
        return reverse("events:event", kwargs={"slug": self.slug})

    def delete(self, using=None, keep_parents=False):
        using = using or router.db_for_write(self.__class__, instance=self)
        collector = Collector(using=using)
        collector.collect([self], keep_parents=keep_parents)

        if self.has_food_event:
            collector.add([self.food_event])
        return collector.delete()

    def __str__(self):
        return f"{self.title}: {timezone.localtime(self.start):%Y-%m-%d %H:%M}"

    DEFAULT_STATUS_MESSAGE = {
        status.STATUS_WILL_OPEN: _("Registration will open {regstart}."),
        status.STATUS_EXPIRED: _("Registration is not possible anymore."),
        status.STATUS_OPEN: _("You can register now."),
        status.STATUS_FULL: _(
            "Registrations are full, but you can join the waiting list."
        ),
        status.STATUS_WAITINGLIST: _("You are in queue position {pos}."),
        status.STATUS_REGISTERED: _("You are registered for this event."),
        status.STATUS_CANCELLED: _(
            "Your registration for this event is cancelled. You may still re-register."
        ),
        status.STATUS_CANCELLED_FINAL: _(
            "Your registration for this event is cancelled. Note that you cannot re-register."
        ),
        status.STATUS_CANCELLED_LATE: _(
            "Your registration is cancelled after the deadline and you will pay a fine of €{fine}."
        ),
        status.STATUS_OPTIONAL: _("You can optionally register for this event."),
        status.STATUS_OPTIONAL_REGISTERED: _(
            "You are optionally registered for this event."
        ),
        status.STATUS_NONE: DEFAULT_NO_REGISTRATION_MESSAGE,
        status.STATUS_LOGIN: _(
            "You have to log in before you can register for this event."
        ),
    }

    STATUS_MESSAGE_FIELDS = {
        status.STATUS_WILL_OPEN: "registration_msg_will_open",
        status.STATUS_EXPIRED: "registration_msg_expired",
        status.STATUS_OPEN: "registration_msg_open",
        status.STATUS_FULL: "registration_msg_full",
        status.STATUS_WAITINGLIST: "registration_msg_waitinglist",
        status.STATUS_REGISTERED: "registration_msg_registered",
        status.STATUS_CANCELLED_FINAL: "registration_msg_cancelled_final",
        status.STATUS_CANCELLED: "registration_msg_cancelled",
        status.STATUS_CANCELLED_LATE: "registration_msg_cancelled_late",
        status.STATUS_OPTIONAL: "registration_msg_optional",
        status.STATUS_OPTIONAL_REGISTERED: "registration_msg_optional_registered",
        status.STATUS_NONE: "no_registration_message",
    }

    registration_msg_will_open = models.CharField(
        _(
            "message when registrations are still closed (and the user is not registered)"
        ),
        max_length=200,
        blank=True,
        null=True,
        help_text=format_lazy(
            "{} {}",
            _("Default:"),
            DEFAULT_STATUS_MESSAGE[status.STATUS_WILL_OPEN],
        ),
    )
    registration_msg_expired = models.CharField(
        _(
            "message when the registration deadline expired and the user is not registered"
        ),
        max_length=200,
        blank=True,
        null=True,
        help_text=format_lazy(
            "{} {}",
            _("Default:"),
            DEFAULT_STATUS_MESSAGE[status.STATUS_EXPIRED],
        ),
    )
    registration_msg_open = models.CharField(
        _("message when registrations are open and the user is not registered"),
        max_length=200,
        blank=True,
        null=True,
        help_text=format_lazy(
            "{} {}",
            _("Default:"),
            DEFAULT_STATUS_MESSAGE[status.STATUS_OPEN],
        ),
    )
    registration_msg_full = models.CharField(
        _(
            "message when registrations are open, but full and the user is not registered"
        ),
        max_length=200,
        blank=True,
        null=True,
        help_text=format_lazy(
            "{} {}",
            _("Default:"),
            DEFAULT_STATUS_MESSAGE[status.STATUS_FULL],
        ),
    )
    registration_msg_waitinglist = models.CharField(
        _("message when user is on the waiting list"),
        max_length=200,
        blank=True,
        null=True,
        help_text=format_lazy(
            "{} {}",
            _("Default:"),
            DEFAULT_STATUS_MESSAGE[status.STATUS_WAITINGLIST],
        ),
    )
    registration_msg_registered = models.CharField(
        _("message when user is registered"),
        max_length=200,
        blank=True,
        null=True,
        help_text=format_lazy(
            "{} {}",
            _("Default:"),
            DEFAULT_STATUS_MESSAGE[status.STATUS_REGISTERED],
        ),
    )
    registration_msg_cancelled = models.CharField(
        _("message when user cancelled their registration in time"),
        max_length=200,
        blank=True,
        null=True,
        help_text=format_lazy(
            "{} {}",
            _("Default:"),
            DEFAULT_STATUS_MESSAGE[status.STATUS_CANCELLED],
        ),
    )
    registration_msg_cancelled_final = models.CharField(
        _(
            "message when user cancelled their registration in time and cannot re-register"
        ),
        max_length=200,
        blank=True,
        null=True,
        help_text=format_lazy(
            "{} {}",
            _("Default:"),
            DEFAULT_STATUS_MESSAGE[status.STATUS_CANCELLED_FINAL],
        ),
    )
    registration_msg_cancelled_late = models.CharField(
        _("message when user cancelled their registration late and will pay a fine"),
        max_length=200,
        blank=True,
        null=True,
        help_text=format_lazy(
            "{} {}",
            _("Default:"),
            DEFAULT_STATUS_MESSAGE[status.STATUS_CANCELLED_LATE],
        ),
    )
    registration_msg_optional = models.CharField(
        _("message when registrations are optional and the user is not registered"),
        max_length=200,
        blank=True,
        null=True,
        help_text=format_lazy(
            "{} {}",
            _("Default:"),
            DEFAULT_STATUS_MESSAGE[status.STATUS_OPTIONAL],
        ),
    )
    registration_msg_optional_registered = models.CharField(
        _("message when registrations are optional and the user is registered"),
        max_length=200,
        blank=True,
        null=True,
        help_text=format_lazy(
            "{} {}",
            _("Default:"),
            DEFAULT_STATUS_MESSAGE[status.STATUS_OPTIONAL_REGISTERED],
        ),
    )

    class Meta:
        ordering = ("-start",)
        permissions = (("override_organiser", "Can access events as if organizing"),)
