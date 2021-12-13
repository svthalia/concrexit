from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .event import Event


def registration_member_choices_limit():
    """Define queryset filters to only include current members."""
    return Q(membership__until__isnull=True) | Q(
        membership__until__gt=timezone.now().date()
    )


class EventRegistration(models.Model):
    """Describes a registration for an Event."""

    event = models.ForeignKey(Event, models.CASCADE)

    member = models.ForeignKey(
        "members.Member",
        models.CASCADE,
        blank=True,
        null=True,
        limit_choices_to=registration_member_choices_limit,
    )

    name = models.CharField(
        _("name"),
        max_length=50,
        help_text=_("Use this for non-members"),
        null=True,
        blank=True,
    )

    date = models.DateTimeField(_("registration date"), default=timezone.now)
    date_cancelled = models.DateTimeField(_("cancellation date"), null=True, blank=True)

    present = models.BooleanField(_("present"), default=False,)

    payment = models.OneToOneField(
        "payments.Payment",
        related_name="events_registration",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    @property
    def information_fields(self):
        fields = self.event.registrationinformationfield_set.all()
        return [
            {"field": field, "value": field.get_value_for(self)} for field in fields
        ]

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
        return None

    @property
    def is_invited(self):
        return self.is_registered and not self.queue_position

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
        return (
            self.date_cancelled
            and self.event.cancel_deadline
            and self.date_cancelled > self.event.cancel_deadline
            and (
                self.event.max_participants is None
                or self.event.eventregistration_set.filter(
                    (
                        Q(date_cancelled__gte=self.date_cancelled)
                        | Q(date_cancelled=None)
                    )
                    & Q(date__lte=self.date)
                ).count()
                < self.event.max_participants
            )
        )

    def is_paid(self):
        return self.payment

    def would_cancel_after_deadline(self):
        now = timezone.now()
        if not self.event.registration_required:
            return False
        return not self.queue_position and now >= self.event.cancel_deadline

    def clean(self):
        if (self.member is None and not self.name) or (self.member and self.name):
            raise ValidationError(
                {
                    "member": _("Either specify a member or a name"),
                    "name": _("Either specify a member or a name"),
                }
            )

    def save(self, **kwargs):
        self.full_clean()

        super().save(**kwargs)

        if self.event.start_reminder and self.date_cancelled:
            self.event.start_reminder.users.remove(self.member)
        elif (
            self.event.start_reminder
            and self.member is not None
            and not self.event.start_reminder.users.filter(pk=self.member.pk).exists()
        ):
            self.event.start_reminder.users.add(self.member)

    def __str__(self):
        if self.member:
            return "{}: {}".format(self.member.get_full_name(), self.event)
        return "{}: {}".format(self.name, self.event)

    class Meta:
        verbose_name = _("Registration")
        verbose_name_plural = _("Registrations")
        ordering = ("date",)
        unique_together = (("member", "event"),)
