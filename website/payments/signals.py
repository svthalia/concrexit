from django.conf import settings
from django.db.models.signals import post_save

from members.models import Member
from payments.models import PaymentUser, PaymentUserCache
from utils.models.signals import receiver, suspendingreceiver


@receiver(post_save, sender=Member)
def give_new_users_tpay_permissions(instance, created, **kwargs):
    """If a new user is created, give this user Thalia Pay permissions."""
    if created and settings.THALIA_PAY_FOR_NEW_MEMBERS:
        allow_tpay = PaymentUser.allow_tpay
        allow_tpay(instance)

        # Note that because Django does not support accessing the instance
        # in the PaymentUser proxy model in this signal, we rely on the fact
        # that allow_tpay actually does not really require a PaymentUser

        # This signal will not work when triggered by the UserAdmin, because
        # after this signal call (triggered by the model's `save()`), a
        # `save_related()` will be called which will override the permissions
        # again.


@suspendingreceiver(post_save, sender="payments.BankAccount")
def clear_enabled_cache(sender, instance, **kwargs):
    cache = PaymentUserCache.objects.filter(user=instance.owner).first()
    if cache is not None:
        cache.enabled = None
        cache.save()


@suspendingreceiver(post_save, sender="auth.Permission")
def clear_allowed_cache(sender, instance, **kwargs):
    if instance.name != "tpay_allowed":
        return

    for user in instance.user_set:
        cache = PaymentUserCache.objects.filter(user=user).first()
        if cache is not None:
            cache.allowed = None
            cache.enabled = None
        cache.save()


@suspendingreceiver(post_save, sender="payments.Payment")
def clear_balance_cache(sender, instance, **kwargs):
    cache = PaymentUserCache.objects.filter(user=instance.paid_by).first()
    if cache is not None:
        cache.enabled = None
        cache.save()
