"""The models defined by the pizzas package"""
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.template.defaulttags import date

from events.models import Event
import members
from members.models import Member
from payments.models import Payment, Payable
from pushnotifications.models import ScheduledMessage, Category
from utils.translation import ModelTranslateMeta, MultilingualField


class PizzaEvent(models.Model):
    """Describes an event where pizzas can be ordered"""

    start = models.DateTimeField(_("Order from"))
    end = models.DateTimeField(_("Order until"))
    event = models.OneToOneField(Event, on_delete=models.CASCADE)

    send_notification = models.BooleanField(
        _("Send an order notification"), default=True
    )
    end_reminder = models.OneToOneField(ScheduledMessage, models.CASCADE, null=True)

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
        """
        Get the currently relevant pizza event: the first one
        that starts within 8 hours from now.
        """

        try:
            events = PizzaEvent.objects.filter(
                end__gt=timezone.now() - timezone.timedelta(hours=8),
                start__lte=timezone.now() + timezone.timedelta(hours=8),
            ).order_by("start")
            if events.count() > 1:
                return events.exclude(end__lt=timezone.now()).first()
            else:
                return events.get()
        except PizzaEvent.DoesNotExist:
            return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._end = self.end

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude)
        for other in PizzaEvent.objects.filter(
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

    def save(self, *args, **kwargs):
        if self.send_notification and not self.end_reminder:
            end_reminder = ScheduledMessage()
            end_reminder.title_en = "Order pizza"
            end_reminder.body_en = "You can order pizzas for 10 more minutes"
            end_reminder.category = Category.objects.get(key=Category.PIZZA)
            end_reminder.time = self.end - timezone.timedelta(minutes=10)
            end_reminder.save()

            if self.event.registration_required:
                end_reminder.users.set(
                    self.event.registrations.select_related("member").values_list(
                        "member", flat=True
                    )
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

        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.end_reminder is not None and not self.end_reminder.sent:
            self.end_reminder.delete()
        return super().delete(using, keep_parents)

    def __str__(self):
        return "Pizzas for " + str(self.event)

    class Meta:
        ordering = ("-start",)


class AvailableProductManager(models.Manager):
    """Only shows available products"""

    def get_queryset(self):
        return super().get_queryset().filter(available=True)


class Product(models.Model, metaclass=ModelTranslateMeta):
    """Describes a product"""

    objects = models.Manager()
    available_products = AvailableProductManager()

    name = models.CharField(max_length=50)
    description = MultilingualField(models.TextField)
    price = models.DecimalField(max_digits=5, decimal_places=2)
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


class Order(models.Model, Payable):
    """Describes an order of an item during an event"""

    member = models.ForeignKey(
        members.models.Member, on_delete=models.CASCADE, blank=True, null=True,
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
        related_name="pizzas_order",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    product = models.ForeignKey(
        verbose_name=_("product"), to=Product, on_delete=models.PROTECT,
    )

    pizza_event = models.ForeignKey(
        verbose_name=_("event"), to=PizzaEvent, on_delete=models.CASCADE
    )

    @property
    def payment_amount(self):
        return self.product.price

    @property
    def payment_topic(self):
        start_date = date(self.pizza_event.start, "Y-m-d")
        return f"Pizzas {self.pizza_event.event.title_en} [{start_date}]"

    @property
    def payment_notes(self):
        return (
            f"Pizza order by {self.member_name} "
            f"for {self.pizza_event.event.title_en}"
        )

    @property
    def payment_payer(self):
        return self.member

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
        return self.name.strip(" ").split(" ")[0]

    @property
    def can_be_changed(self):
        try:
            return (
                not self.payment or self.payment.type == Payment.TPAY
            ) and not self.pizza_event.has_ended
        except ObjectDoesNotExist:
            return False

    class Meta:
        unique_together = (
            "pizza_event",
            "member",
        )

    def __str__(self):
        return _("Order by {member_name}: {product}").format(
            member_name=self.member_name, product=self.product
        )
