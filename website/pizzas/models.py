from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import events
import members
from utils.translation import ModelTranslateMeta, MultilingualField


class PizzaEvent(models.Model):
    start = models.DateTimeField(_("Order from"))
    end = models.DateTimeField(_("Order until"))
    event = models.OneToOneField(events.models.Event, on_delete=models.CASCADE)

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
        try:
            return PizzaEvent.objects.get(
                end__gt=timezone.now() - timezone.timedelta(hours=8)
            )
        except PizzaEvent.DoesNotExist:
            return None

    def clean(self):
        for other in PizzaEvent.objects.all():
            if self.start <= other.end and other.start >= self.end:
                raise ValidationError({
                    'start': _('This event cannot overlap with ') + str(other),
                    'end': _('This event cannot overlap with ') + str(other),
                })

    def __str__(self):
        return 'Pizzas for ' + str(self.event)


class Product(models.Model, metaclass=ModelTranslateMeta):
    name = models.CharField(max_length=50)
    description = MultilingualField(models.TextField)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name', )


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
        unique_together = ('pizza_event', 'member')
