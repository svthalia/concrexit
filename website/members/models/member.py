import logging
import operator
from datetime import timedelta
from functools import reduce

from django.contrib.auth.models import User, UserManager
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from activemembers.models import MemberGroup, MemberGroupMembership
from members.models.membership import Membership

logger = logging.getLogger(__name__)


class MemberManager(UserManager):
    """Get all members, i.e. all users with a profile."""

    def get_queryset(self):
        return super().get_queryset().exclude(profile=None)


class ActiveMemberManager(MemberManager):
    """Get all active members, i.e. who have a committee membership."""

    def get_queryset(self):
        """Select all committee members."""
        active_memberships = MemberGroupMembership.active_objects.filter(
            group__board=None
        ).filter(group__society=None)

        return (
            super()
            .get_queryset()
            .filter(membergroupmembership__in=active_memberships)
            .distinct()
        )


class CurrentMemberManager(MemberManager):
    """Get all members with an active membership."""

    def get_queryset(self):
        """Select all members who have a current membership."""
        return (
            super()
            .get_queryset()
            .exclude(membership=None)
            .filter(
                Q(membership__until__isnull=True)
                | Q(membership__until__gt=timezone.now().date())
            )
            .distinct()
        )

    def with_birthdays_in_range(self, from_date, to_date):
        """Select all who are currently a Thalia member and have a birthday within the specified range.

        :param from_date: the start of the range (inclusive)
        :param to_date: the end of the range (inclusive)
        :paramtype from_date: datetime
        :paramtype to_date: datetime

        :return: the filtered queryset
        :rtype: Queryset
        """
        queryset = self.get_queryset().filter(profile__birthday__lte=to_date)

        if (to_date - from_date).days >= 366:
            # 366 is important to also account for leap years
            # Everyone that's born before to_date has a birthday
            return queryset

        delta = to_date - from_date
        dates = [from_date + timedelta(days=i) for i in range(delta.days + 1)]
        monthdays = [
            {"profile__birthday__month": d.month, "profile__birthday__day": d.day}
            for d in dates
        ]
        # Don't get me started (basically, we are making a giant OR query with
        # all days and months that are in the range)
        query = reduce(operator.or_, [Q(**d) for d in monthdays])
        return queryset.filter(query)


class Member(User):
    class Meta:
        proxy = True
        ordering = ("first_name", "last_name")

    objects = MemberManager()
    current_members = CurrentMemberManager()
    active_members = ActiveMemberManager()

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    def refresh_from_db(self, **kwargs):
        # Clear the cached current- and latest_membership
        if hasattr(self, "_current_membership"):
            del self._current_membership
        if hasattr(self, "current_membership"):
            del self.current_membership
        if hasattr(self, "latest_membership"):
            del self.latest_membership

        return super().refresh_from_db(**kwargs)

    @cached_property
    def current_membership(self) -> Membership | None:
        """Return the currently active membership of the user, None if not active.

        This might not be the latest membership, as a latest membership may be in the future.

        Warning: this property is cached.
        You can use `refresh_from_db` to clear it.
        """
        # Use membership from a Prefetch object if available.
        if hasattr(self, "_current_membership"):
            if not self._current_membership:
                return None
            return self._current_membership[0]

        today = timezone.now().date()
        try:
            return self.membership_set.filter(
                Q(until__isnull=True) | Q(until__gt=today),
                since__lte=today,
            ).latest("since")
        except Membership.DoesNotExist:
            return None

    @cached_property
    def latest_membership(self) -> Membership | None:
        """Get the most recent (potentially future) membership of this user.

        Warning: this property is cached.
        You can use `refresh_from_db` to clear it.
        """
        if not self.membership_set.exists():
            return None
        return self.membership_set.latest("since")

    @property
    def earliest_membership(self) -> Membership | None:
        """Get the earliest membership of this user."""
        if not self.membership_set.exists():
            return None
        return self.membership_set.earliest("since")

    def has_been_member(self) -> bool:
        """Has this user ever been a member?."""
        return self.membership_set.filter(type="member").exists()

    def has_been_honorary_member(self) -> bool:
        """Has this user ever been an honorary member?."""
        return self.membership_set.filter(type="honorary").exists()

    def has_active_membership(self) -> bool:
        """Is this member currently active.

        Tested by checking if the expiration date has passed.
        """
        return self.current_membership is not None

    # Special properties for admin site
    has_active_membership.boolean = True
    has_active_membership.short_description = _("Is this user currently active")

    @classmethod
    def all_with_membership(cls, membership_type):
        """Get all users who have a specific membership.

        :param membership_type: The membership to select by
        :return: List of users
        :rtype: [Member]
        """
        return [
            x
            for x in cls.objects.all()
            if x.current_membership and x.current_membership.type == membership_type
        ]

    @property
    def can_attend_events(self):
        """May this user attend events."""
        if not self.profile:
            return False

        return (
            self.profile.event_permissions in ("all", "no_drinks")
            and self.has_active_membership()
        )

    @property
    def can_attend_events_without_membership(self):
        if not self.profile:
            return False

        return self.profile.event_permissions in ("all", "no_drinks")

    def get_member_groups(self):
        """Get the groups this user is a member of."""
        now = timezone.now()
        return MemberGroup.objects.filter(
            Q(membergroupmembership__member=self),
            Q(membergroupmembership__until=None)
            | Q(
                membergroupmembership__since__lte=now,
                membergroupmembership__until__gte=now,
            ),
            active=True,
        )

    def get_absolute_url(self):
        return reverse("members:profile", args=[str(self.pk)])
