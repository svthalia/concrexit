from datetime import date, timedelta

from django.test import TestCase

from members.models import Member, Membership, Profile
from members.views import MembersIndex


class MembersIndexText(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Add 10 members with default membership
        members = [Member(id=i, username=i) for i in range(7)]
        Member.objects.bulk_create(members)
        profiles = [Profile(user_id=i) for i in range(7)]
        Profile.objects.bulk_create(profiles)

        Membership(
            user_id=0, type=Membership.HONORARY, until=date.today() + timedelta(days=1)
        ).save()

        Membership(
            user_id=1,
            type=Membership.BENEFACTOR,
            until=date.today() + timedelta(days=1),
        ).save()

        Membership(
            user_id=2, type=Membership.MEMBER, until=date.today() + timedelta(days=1)
        ).save()

        Membership(
            user_id=3, type=Membership.MEMBER, until=date.today() + timedelta(days=1)
        ).save()
        Membership(
            user_id=3,
            type=Membership.MEMBER,
            until=date.today() - timedelta(days=365 * 10),
        ).save()

        Membership(
            user_id=4,
            type=Membership.BENEFACTOR,
            until=date.today() + timedelta(days=1),
        ).save()
        Membership(
            user_id=4,
            type=Membership.MEMBER,
            until=date.today() - timedelta(days=365 * 10),
        ).save()

        Membership(
            user_id=5,
            type=Membership.MEMBER,
            until=date.today() - timedelta(days=365 * 10),
        ).save()

        # user_id=6 has no memberships at all

    def test_honorary_query_filter(self):
        view = MembersIndex()
        view.query_filter = "honorary"
        view.year_range = [date.today().year]
        members = view.get_queryset()
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].id, 0)

    def test_former_query_filter(self):
        view = MembersIndex()
        view.query_filter = "former"
        view.year_range = [date.today().year]
        members = view.get_queryset()
        self.assertEqual(len(members), 3)
        for member in members:
            self.assertIn(member.id, {4, 5, 6})
