from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, F, Q
from django.db.models.functions import Greatest, NullIf
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from queryable_properties.managers import QueryablePropertiesManager
from queryable_properties.properties import AnnotationProperty

from events import emails
from payments.models import Payment, PaymentAmountField

from .event import Event


def registration_member_choices_limit():
    """Define queryset filters to only include current members."""
    return Q(membership__until__isnull=True) | Q(
        membership__until__gt=timezone.now().date()
    )


class EventRegistration(models.Model):
    """Describes a registration for an Event."""

    objects = QueryablePropertiesManager()

    event = models.ForeignKey(Event, models.CASCADE)

    member = models.ForeignKey(
        "members.Member",
        models.CASCADE,
        blank=True,
        null=True,
    )

    name = models.CharField(
        _("name"),
        max_length=50,
        help_text=_("Use this for non-members"),
        null=True,
        blank=True,
    )

    alt_email = models.EmailField(
        _("email"),
        help_text=_("Email address for non-members"),
        max_length=254,
        null=True,
        blank=True,
    )

    alt_phone_number = models.CharField(
        max_length=20,
        verbose_name=_("Phone number"),
        help_text=_("Phone number for non-members"),
        validators=[
            validators.RegexValidator(
                regex=r"^\+?\d+$",
                message=_("Please enter a valid phone number"),
            )
        ],
        null=True,
        blank=True,
    )

    date = models.DateTimeField(_("registration date"), default=timezone.now)
    date_cancelled = models.DateTimeField(_("cancellation date"), null=True, blank=True)

    present = models.BooleanField(
        _("present"),
        default=False,
    )

    special_price = PaymentAmountField(
        verbose_name=_("special price"),
        blank=True,
        null=True,
        validators=[validators.MinValueValidator(0)],
    )

    remarks = models.TextField(_("remarks"), null=True, blank=True)

    payment = models.OneToOneField(
        Payment,
        related_name="events_registration",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    @property
    def phone_number(self):
        if self.member:
            return self.member.profile.phone_number
        return self.alt_phone_number

    @property
    def email(self):
        if self.member:
            return self.member.email
        return self.alt_email

    @property
    def information_fields(self):
        fields = self.event.registrationinformationfield_set.all()
        return [
            {"field": field, "value": field.get_value_for(self)} for field in fields
        ]

    @property
    def is_registered(self):
        return self.date_cancelled is None

    queue_position = AnnotationProperty(
        # Get queue position by counting amount of registrations with lower date and in case of same date lower id
        # Subsequently cast to None if this is 0 or lower, in which case it isn't in the queue
        NullIf(
            Greatest(
                Count(
                    "event__eventregistration",
                    filter=Q(event__eventregistration__date_cancelled=None)
                    & (
                        Q(event__eventregistration__date__lt=F("date"))
                        | Q(event__eventregistration__id__lte=F("id"))
                        & Q(event__eventregistration__date__exact=F("date"))
                    ),
                )
                - F("event__max_participants"),
                0,
            ),
            0,
        )
    )

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

    @property
    def payment_amount(self):
        return self.event.price if not self.special_price else self.special_price

    def would_cancel_after_deadline(self):
        now = timezone.now()
        if not self.event.registration_required:
            return False
        return not self.queue_position and now >= self.event.cancel_deadline

    def clean(self):
        errors = {}
        if (self.member is None and not self.name) or (self.member and self.name):
            errors.update(
                {
                    "member": _("Either specify a member or a name"),
                    "name": _("Either specify a member or a name"),
                }
            )
        if self.member and self.alt_email:
            errors.update(
                {"alt_email": _("Email should only be specified for non-members")}
            )
        if self.member and self.alt_phone_number:
            errors.update(
                {
                    "alt_phone_number": _(
                        "Phone number should only be specified for non-members"
                    )
                }
            )
        if (
            self.payment
            and self.special_price
            and self.special_price != self.payment.amount
        ):
            errors.update(
                {
                    "special_price": _(
                        "Cannot change price of already paid registration"
                    ),
                }
            )

        if errors:
            raise ValidationError(errors)

    def save(self, **kwargs):
        self.full_clean()

        created = self.pk is None
        super().save(**kwargs)

        if (
            created
            and self.is_registered
            and self.email
            and self.event.registration_required
        ):
            if (
                self.member is not None
                and not self.member.profile.receive_registration_confirmation
            ):
                return  # Don't send email if the user doesn't want them.

            emails.notify_registration(self)

    def __str__(self):
        if self.member:
            return f"{self.member.get_full_name()}: {self.event}"
        return f"{self.name}: {self.event}"

    class Meta:
        verbose_name = _("Registration")
        verbose_name_plural = _("Registrations")
        ordering = ("date",)
        unique_together = (("member", "event"),)
        get_latest_by = "pk"
