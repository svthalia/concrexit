"""The models defined by the payments package"""
import uuid

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class Payment(models.Model):
    """
    Describes a payment
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(_('created at'), default=timezone.now)

    NONE = 'no_payment'
    CASH = 'cash_payment'
    CARD = 'card_payment'

    PAYMENT_TYPE = (
        (NONE, _('No payment')),
        (CASH, _('Cash payment')),
        (CARD, _('Card payment')),
    )

    type = models.CharField(
        choices=PAYMENT_TYPE,
        verbose_name=_('type'),
        max_length=20,
        default=NONE
    )

    amount = models.DecimalField(
        blank=False,
        null=False,
        max_digits=5,
        decimal_places=2
    )

    processing_date = models.DateTimeField(
        _('processing date'),
        blank=True,
        null=True,
    )

    paid_by = models.ForeignKey(
        'members.Member',
        models.CASCADE,
        related_name='paid_payment_set',
        blank=False,
        null=True,
    )

    processed_by = models.ForeignKey(
        'members.Member',
        models.CASCADE,
        related_name='processed_payment_set',
        blank=False,
        null=True,
    )

    notes = models.TextField(blank=True, null=True)

    @property
    def processed(self):
        return self.type != self.NONE

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.type != self.NONE and not self.processing_date:
            self.processing_date = timezone.now()
        elif self.type == self.NONE:
            self.processing_date = None
        super().save(force_insert, force_update, using, update_fields)

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (
            content_type.app_label, content_type.model), args=(self.id,))

    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        permissions = (
            ('process_payments', _("Process payments")),
        )
