"""The models defined by the pizzas package."""
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from events.models import Event
import members
from members.models import Member
from payments.models import Payment, PaymentAmountField
from payments.services import delete_payment
from pushnotifications.models import ScheduledMessage, Category


class CurrentEventManager(models.Manager):
    """Only shows available products."""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                end__gt=timezone.now() - timezone.timedelta(hours=8),
                start__lte=timezone.now() + timezone.timedelta(hours=8),
            )
        )


class FoodEvent(models.Model):
    """Describes an event where food can be ordered."""

    objects = models.Manager()
    current_objects = CurrentEventManager()

    start = models.DateTimeField(_("Order from"))
    end = models.DateTimeField(_("Order until"))
    event = models.OneToOneField(
        Event, on_delete=models.CASCADE, related_name="food_event"
    )

    send_notification = models.BooleanField(
        _("Send an order notification"), default=True
    )
    end_reminder = models.OneToOneField(ScheduledMessage, models.CASCADE, null=True)

    tpay_allowed = models.BooleanField(_("Allow Thalia Pay"), default=True)

    @property
    def title(self):
        return self.event.title

    @property
    def in_the_future(self):
        return self.start > timezone.now()

    @property
    def has_ended(self):
        return self.end < timezone.now()

    @property
    def just_ended(self):
        return (
            self.has_ended and self.end + timezone.timedelta(hours=8) > timezone.now()
        )

    @classmethod
    def current(cls):
        """Get the currently relevant pizza event: the first one that starts within 8 hours from now."""
        try:
            events = FoodEvent.current_objects.order_by("start")
            if events.count() > 1:
                return events.exclude(end__lt=timezone.now()).first()
            return events.get()
        except FoodEvent.DoesNotExist:
            return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._end = self.end

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude)
        for other in FoodEvent.objects.filter(
            Q(end__gte=self.start, end__lte=self.end)
            | Q(start=self.start, start__lte=self.start)
        ):
            if other.pk == self.pk:
                continue
            raise ValidationError(
                {
                    "start": _("This event cannot overlap with {}.").format(other),
                    "end": _("This event cannot overlap with {}.").format(other),
                }
            )

    def clean(self):
        super().clean()

        if self.start >= self.end:
            raise ValidationError(
                {
                    "start": _("The start is after the end of this event."),
                    "end": _("The end is before the start of this event."),
                }
            )

    def save(self, **kwargs):
        if self.send_notification and not self.end_reminder:
            end_reminder = ScheduledMessage()
            end_reminder.title = f"{self.event.title}: Order food"
            end_reminder.body = "You can order food for 10 more minutes"
            end_reminder.category = Category.objects.get(key=Category.PIZZA)
            end_reminder.time = self.end - timezone.timedelta(minutes=10)
            end_reminder.save()

            if self.event.registration_required:
                end_reminder.users.set(
                    self.event.registrations.filter(member__isnull=False)
                    .select_related("member")
                    .values_list("member", flat=True)
                )
            else:
                end_reminder.users.set(Member.current_members.all())

            self.end_reminder = end_reminder
        elif self.send_notification and self.end_reminder and self._end != self.end:
            self.end_reminder.time = self.end
            self.end_reminder.save()
        elif not self.send_notification and self.end_reminder:
            end_reminder = self.end_reminder
            self.end_reminder = None
            if not end_reminder.sent:
                end_reminder.delete()

        super().save(**kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.end_reminder is not None and not self.end_reminder.sent:
            self.end_reminder.delete()
        return super().delete(using, keep_parents)

    def __str__(self):
        return "Food for " + str(self.event)

    class Meta:
        ordering = ("-start",)


class AvailableProductManager(models.Manager):
    """Only shows available products."""

    def get_queryset(self):
        return super().get_queryset().filter(available=True)


class Product(models.Model):
    """Describes a product."""

    objects = models.Manager()
    available_products = AvailableProductManager()

    name = models.CharField(max_length=50)
    description = models.TextField()
    price = PaymentAmountField()
    available = models.BooleanField(default=True)
    restricted = models.BooleanField(
        default=False,
        help_text=_(
            "Only allow to be ordered by people with the "
            "'order restricted products' permission."
        ),
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)
        permissions = (("order_restricted_products", _("Order restricted products")),)


class FoodOrder(models.Model):
    """Describes an order of an item during a food event."""

    member = models.ForeignKey(
        members.models.Member,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    name = models.CharField(
        verbose_name=_("name"),
        max_length=50,
        help_text=_("Use this for non-members"),
        null=True,
        blank=True,
    )

    payment = models.OneToOneField(
        verbose_name=_("payment"),
        to="payments.Payment",
        related_name="food_order",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    product = models.ForeignKey(
        verbose_name=_("product"),
        to=Product,
        on_delete=models.PROTECT,
    )

    food_event = models.ForeignKey(
        verbose_name=_("event"),
        to=FoodEvent,
        on_delete=models.CASCADE,
        related_name="orders",
    )

    def clean(self):
        if (self.member is None and not self.name) or (self.member and self.name):
            raise ValidationError(
                {
                    "member": _("Either specify a member or a name"),
                    "name": _("Either specify a member or a name"),
                }
            )

    @property
    def member_name(self):
        if self.member is not None:
            return self.member.get_full_name()
        return self.name

    @property
    def member_last_name(self):
        if self.member is not None:
            return self.member.last_name
        return " ".join(self.name.split(" ")[1:])

    @property
    def member_first_name(self):
        if self.member is not None:
            return self.member.first_name
        return self.name.strip(" ").split(" ", maxsplit=1)[0]

    @property
    def can_be_changed(self):
        try:
            return (
                not self.payment or self.payment.type == Payment.TPAY
            ) and not self.food_event.has_ended
        except ObjectDoesNotExist:
            return False

    def delete(self, using=None, keep_parents=False):
        if self.payment is not None and self.can_be_changed:
            delete_payment(self)
        return super().delete(using, keep_parents)

    class Meta:
        unique_together = (
            "food_event",
            "member",
        )

    def __str__(self):
        return _("Food order by {member_name}: {product}").format(
            member_name=self.member_name, product=self.product
        )
