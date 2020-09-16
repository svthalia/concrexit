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
from members.models import Member
from pushnotifications.models import ScheduledMessage, Category
from utils.translation import ModelTranslateMeta, MultilingualField


class Event(models.Model, metaclass=ModelTranslateMeta):
    """Describes an event"""

    CATEGORY_ALUMNI = "alumni"
    CATEGORY_EDUCATION = "education"
    CATEGORY_CAREER = "career"
    CATEGORY_LEISURE = "leisure"
    CATEGORY_ASSOCIATION = "association"
    CATEGORY_OTHER = "other"

    EVENT_CATEGORIES = (
        (CATEGORY_ALUMNI, _("Alumni")),
        (CATEGORY_EDUCATION, _("Education")),
        (CATEGORY_CAREER, _("Career")),
        (CATEGORY_LEISURE, _("Leisure")),
        (CATEGORY_ASSOCIATION, _("Association Affairs")),
        (CATEGORY_OTHER, _("Other")),
    )

    DEFAULT_NO_REGISTRATION_MESSAGE = _(
        "No registration required / Geen aanmelding vereist"
    )

    title = MultilingualField(models.CharField, _("title"), max_length=100)

    description = MultilingualField(HTMLField, _("description"),)

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

    location = MultilingualField(models.CharField, _("location"), max_length=255,)

    map_location = models.CharField(
        _("location for minimap"),
        max_length=255,
        help_text=_(
            "Location of Huygens: Heyendaalseweg 135, Nijmegen. "
            "Location of Mercator 1: Toernooiveld 212, Nijmegen. "
            "Not shown as text!!"
        ),
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
        _("maximum number of participants"), blank=True, null=True,
    )

    no_registration_message = MultilingualField(
        models.CharField,
        _("message when there is no registration"),
        max_length=200,
        blank=True,
        null=True,
        help_text=(
            format_lazy("{} {}", _("Default:"), DEFAULT_NO_REGISTRATION_MESSAGE)
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
        "documents.Document", verbose_name=_("documents"), blank=True,
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._price = self.price
        self._registration_start = self.registration_start

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
        return (
            self.max_participants is not None
            and self.max_participants
            <= self.eventregistration_set.filter(date_cancelled=None).count()
        )

    @property
    def registrations(self):
        """Queryset with all non-cancelled registrations"""
        return self.eventregistration_set.filter(date_cancelled=None)

    @property
    def participants(self):
        """Return the active participants"""
        if self.max_participants is not None:
            return self.registrations.order_by("date")[: self.max_participants]
        return self.registrations.order_by("date")

    @property
    def queue(self):
        """Return the waiting queue"""
        if self.max_participants is not None:
            return self.registrations.order_by("date")[self.max_participants :]
        return []

    @property
    def cancellations(self):
        """Return a queryset with the cancelled events"""
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
            errors.update({"start": _("Start cannot have an empty date or time field")})
        if self.end is None:
            errors.update({"end": _("End cannot have an empty date or time field")})
        if self.start is not None and self.end is not None:
            if self.end < self.start:
                errors.update({"end": _("Can't have an event travel back in time")})
            if self.registration_required:
                if self.fine < 5:
                    errors.update(
                        {
                            "fine": _(
                                "The fine for this event is too low "
                                "(must be at least €5)."
                            )
                        }
                    )
                for lang in settings.LANGUAGES:
                    field = "no_registration_message_" + lang[0]
                    if getattr(self, field):
                        errors.update(
                            {
                                field: _(
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

        if self.published:
            if (
                self.price != self._price
                and self._registration_start
                and self._registration_start <= timezone.now()
            ):
                errors.update(
                    {
                        "price": _(
                            "You cannot change this field after "
                            "the registration has started."
                        )
                    }
                )
            if (
                self._registration_start
                and self.registration_start != self._registration_start
                and self._registration_start <= timezone.now()
            ):
                errors.update(
                    {
                        "registration_start": _(
                            "You cannot change this field after "
                            "the registration has started."
                        )
                    }
                )

        if errors:
            raise ValidationError(errors)

    def get_absolute_url(self):
        return reverse("events:event", args=[str(self.pk)])

    def save(self, *args, **kwargs):
        delete_collector = Collector(
            using=router.db_for_write(self.__class__, instance=self)
        )

        if not self.pk:
            super().save(*args, **kwargs)

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
                    registration_reminder.title_en = "Event registration"
                    registration_reminder.body_en = (
                        "Registration for '{}' "
                        "starts in 1 hour".format(self.title_en)
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
                    delete_collector.add([self.registration_reminder])
                    self.registration_reminder = None

            start_reminder_time = self.start - timezone.timedelta(hours=1)
            start_reminder = ScheduledMessage()
            if self.start_reminder is not None and not self.start_reminder.sent:
                start_reminder = self.start_reminder

            if start_reminder_time > timezone.now():
                start_reminder.title_en = "Event"
                start_reminder.body_en = f"'{self.title_en}' starts in 1 hour"
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
                delete_collector.add([self.start_reminder])
                self.start_reminder = None
        else:
            if (
                self.registration_reminder is not None
                and not self.registration_reminder.sent
            ):
                delete_collector.add([self.registration_reminder])
                self.registration_reminder = None

            if self.start_reminder is not None and not self.start_reminder.sent:
                delete_collector.add([self.start_reminder])
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
            collector.add([self.registration_reminder])
        if self.start_reminder is not None and not self.start_reminder.sent:
            collector.add([self.start_reminder])
        if self.is_pizza_event():
            collector.add([self.pizzaevent])

        return collector.delete()

    def __str__(self):
        return "{}: {}".format(
            self.title, timezone.localtime(self.start).strftime("%Y-%m-%d %H:%M")
        )

    class Meta:
        ordering = ("-start",)
        permissions = (("override_organiser", "Can access events as if organizing"),)
