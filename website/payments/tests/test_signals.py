from django.test import TestCase

from django.test import override_settings

from members.models import Member, Profile
from payments.models import PaymentUser


class SignalsTest(TestCase):
    @override_settings(
        THALIA_PAY_FOR_NEW_MEMBERS=True, THALIA_PAY_ENABLED_PAYMENT_METHOD=True
    )
    def test_give_new_users_tpay_permissions(self):
        member = Member.objects.create(username="test", first_name="", last_name="")
        Profile.objects.create(
            user_id=member.pk,
            initials=None,
            nickname=None,
            display_name_preference="full",
        )
        self.assertTrue(PaymentUser.objects.get(pk=member.pk).tpay_allowed)
