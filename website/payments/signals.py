from django.conf import settings
from django.db.models.signals import post_save

from payments.models import PaymentUser
from utils.models.signals import receiver


@receiver(post_save, sender=PaymentUser)
def give_new_users_tpay_permissions(sender, instance, created, **kwargs):
    """If a new user is created, give this user Thalia Pay permissions."""
    if created and settings.THALIA_PAY_FOR_NEW_MEMBERS:
        u = PaymentUser.objects.get(pk=instance.pk)
        u.allow_tpay()
