from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models, router
from django.db.models.deletion import Collector
from django.urls import reverse
from django.utils import timezone
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField

from announcements.models import Slide
from events.models.categories import EVENT_CATEGORIES
from members.models import Member
from payments.models import PaymentAmountField
from pushnotifications.models import ScheduledMessage, Category


class Event(models.Model):
    """Describes an event."""

    DEFAULT_NO_REGISTRATION_MESSAGE = _("No registration required")

    title = models.CharField(_("title"), max_length=100)

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

    organiser = models.ForeignKey(
        "activemembers.MemberGroup", models.PROTECT, verbose_name=_("organiser")
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

    registration_reminder = models.ForeignKey(
        ScheduledMessage,
        on_delete=models.deletion.SET_NULL,
        related_name="registration_event",
        blank=True,
        null=True,
    )
    start_reminder = models.ForeignKey(
        ScheduledMessage,
        on_delete=models.deletion.SET_NULL,
        related_name="start_event",
        blank=True,
        null=True,
    )

    documents = models.ManyToManyField(
        "documents.Document",
        verbose_name=_("documents"),
        blank=True,
    )

    slide = models.ForeignKey(
        Slide,
        verbose_name="slide",
        help_text=_(
            "Change the header-image on the event's info-page to one "
            "specific to this event."
        ),
        blank=True,
        on_delete=models.deletion.SET_NULL,
        null=True,
    )

    tpay_allowed = models.BooleanField(_("Allow Thalia Pay"), default=True)

    shift = models.OneToOneField("sales.Shift", models.SET_NULL, null=True, blank=True)

    @property
    def cancel_too_late_message(self):
        return _(
            "Cancellation isn't possible anymore without having to pay "
            "the full costs of €" + str(self.fine) + ". Also note that "
            "you will be unable to re-register. Note: If you have any "
            "COVID-19 symptoms you will not have to pay these fees. "
            "Let us know via info@thalia.nu that this is this reason "
            "for your cancellation."
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

    def reached_participants_limit(self):
        """Is this event up to capacity?."""
        return (
            self.max_participants is not None
            and self.max_participants
            <= self.eventregistration_set.filter(date_cancelled=None).count()
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

    def clean_changes(self, changed_data):
        """Check if changes from `changed_data` are allowed.

        This method should be run from a form clean() method, where changed_data
        can be retrieved from self.changed_data
        """
        errors = {}
        if self.published:
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

        try:
            if (
                self.organiser is not None
                and self.send_cancel_email
                and self.organiser.contact_mailinglist is None
            ):
                errors.update(
                    {
                        "send_cancel_email": _(
                            "This organiser does not have a contact mailinglist."
                        )
                    }
                )
        except ObjectDoesNotExist:
            pass

        if errors:
            raise ValidationError(errors)

    def get_absolute_url(self):
        return reverse("events:event", args=[str(self.pk)])

    def save(self, **kwargs):
        delete_collector = Collector(
            using=router.db_for_write(self.__class__, instance=self)
        )

        if not self.pk:
            super().save(**kwargs)

        if self.published:
            if self.registration_required:
                registration_reminder_time = (
                    self.registration_start - timezone.timedelta(hours=1)
                )
                registration_reminder = ScheduledMessage()
                if (
                    self.registration_reminder is not None
                    and not self.registration_reminder.sent
                ):
                    registration_reminder = self.registration_reminder

                if registration_reminder_time > timezone.now():
                    registration_reminder.title = "Event registration"
                    registration_reminder.body = (
                        "Registration for '{}' " "starts in 1 hour".format(self.title)
                    )
                    registration_reminder.category = Category.objects.get(
                        key=Category.EVENT
                    )
                    registration_reminder.time = registration_reminder_time
                    registration_reminder.url = (
                        f"{settings.BASE_URL}"
                        f'{reverse("events:event", args=[self.id])}'
                    )

                    registration_reminder.save()
                    self.registration_reminder = registration_reminder
                    self.registration_reminder.users.set(Member.current_members.all())
                elif registration_reminder.pk is not None:
                    delete_collector.collect([self.registration_reminder])
                    self.registration_reminder = None

            start_reminder_time = self.start - timezone.timedelta(hours=1)
            start_reminder = ScheduledMessage()
            if self.start_reminder is not None and not self.start_reminder.sent:
                start_reminder = self.start_reminder

            if start_reminder_time > timezone.now():
                start_reminder.title = "Event"
                start_reminder.body = f"'{self.title}' starts in 1 hour"
                start_reminder.category = Category.objects.get(key=Category.EVENT)
                start_reminder.time = start_reminder_time
                start_reminder.save()
                self.start_reminder = start_reminder
                if self.registration_required:
                    self.start_reminder.users.set(
                        [r.member for r in self.participants if r.member]
                    )
                else:
                    self.start_reminder.users.set(Member.current_members.all())
            elif start_reminder.pk is not None:
                delete_collector.collect([self.start_reminder])
                self.start_reminder = None
        else:
            if (
                self.registration_reminder is not None
                and not self.registration_reminder.sent
            ):
                delete_collector.collect([self.registration_reminder])
                self.registration_reminder = None

            if self.start_reminder is not None and not self.start_reminder.sent:
                delete_collector.collect([self.start_reminder])
                self.start_reminder = None

        super().save()
        delete_collector.delete()

    def delete(self, using=None, keep_parents=False):
        using = using or router.db_for_write(self.__class__, instance=self)
        collector = Collector(using=using)
        collector.collect([self], keep_parents=keep_parents)

        if (
            self.registration_reminder is not None
            and not self.registration_reminder.sent
        ):
            collector.collect([self.registration_reminder], keep_parents=keep_parents)
        if self.start_reminder is not None and not self.start_reminder.sent:
            collector.collect([self.start_reminder], keep_parents=keep_parents)
        if self.has_food_event:
            collector.add([self.food_event])

        return collector.delete()

    def __str__(self):
        return "{}: {}".format(
            self.title, timezone.localtime(self.start).strftime("%Y-%m-%d %H:%M")
        )

    class Meta:
        ordering = ("-start",)
        permissions = (("override_organiser", "Can access events as if organizing"),)
