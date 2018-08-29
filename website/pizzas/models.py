from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import events
import members
from members.models import Member
from .tasks import create_send_message
from pushnotifications.models import ScheduledMessage, Category
from utils.tasks import schedule_task, revoke_task
from utils.translation import ModelTranslateMeta, MultilingualField


class PizzaEvent(models.Model):
    start = models.DateTimeField(_("Order from"))
    end = models.DateTimeField(_("Order until"))
    event = models.OneToOneField(events.models.Event, on_delete=models.CASCADE)

    send_notification = models.BooleanField(
        _("Send an order notification"),
        default=True
    )
    task_id = models.CharField(max_length=50, blank=True, null=True)

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
        return (self.has_ended and
                self.end + timezone.timedelta(hours=8) > timezone.now())

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
            ).order_by('start')
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
                Q(end__gte=self.start, end__lte=self.end) |
                Q(start=self.start, start__lte=self.start)):
            if other.pk == self.pk:
                continue
            raise ValidationError({
                'start': _(
                    'This event cannot overlap with {}.').format(other),
                'end': _(
                    'This event cannot overlap with {}.').format(other),
            })

    def clean(self):
        if self.start >= self.end:
            raise ValidationError({
                'start': _('The start is after the end of this event.'),
                'end': _('The end is before the start of this event.'),
            })

    def schedule(self):
        """Schedules a Celery task to send this message"""
        return schedule_task(
            create_send_message,
            args=(self.pk,),
            eta=self.end - timezone.timedelta(minutes=10)
        )

    def save(self, *args, **kwargs):
        if not (self._end == self.end):
            if self.task_id:
                # Revoke that task in case its time has changed
                revoke_task(self.task_id)
            super().save(*args, **kwargs)
            self.task_id = self.schedule()

        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.task_id:
            revoke_task(self.task_id)
        return super().delete(using, keep_parents)

    def __str__(self):
        return 'Pizzas for ' + str(self.event)


class AvailableProductManager(models.Manager):
    """Only shows available products"""

    def get_queryset(self):
        return super().get_queryset().filter(available=True)


class Product(models.Model, metaclass=ModelTranslateMeta):
    objects = models.Manager()
    available_products = AvailableProductManager()

    name = models.CharField(max_length=50)
    description = MultilingualField(models.TextField)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    available = models.BooleanField(default=True)
    restricted = models.BooleanField(
        default=False,
        help_text=_("Only allow to be ordered by people with the "
                    "'order restricted products' permission."))

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name', )
        permissions = (
            ('order_restricted_products', _('Order restricted products')),
        )


class Order(models.Model):
    member = models.ForeignKey(
        members.models.Member,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    paid = models.BooleanField(default=False)

    name = models.CharField(
        max_length=50,
        help_text=_('Use this for non-members'),
        null=True,
        blank=True,
    )

    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    pizza_event = models.ForeignKey(PizzaEvent, on_delete=models.CASCADE)

    def clean(self):
        if ((self.member is None and not self.name) or
                (self.member and self.name)):
            raise ValidationError({
                'member': _('Either specify a member or a name'),
                'name': _('Either specify a member or a name'),
            })

    @property
    def member_name(self):
        if self.member is not None:
            return self.member.get_full_name()
        return self.name

    @property
    def can_be_changed(self):
        return not self.paid and not self.pizza_event.has_ended

    class Meta:
        unique_together = ('pizza_event', 'member',)
