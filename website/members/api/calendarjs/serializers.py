from rest_framework.reverse import reverse

from members.models import Member
from thaliawebsite.api.calendarjs.serializers import CalenderJSSerializer


class MemberBirthdaySerializer(CalenderJSSerializer):
    """Serializer that renders the member birthdays to the CalendarJS format."""

    class Meta(CalenderJSSerializer.Meta):
        model = Member

    def _start(self, instance):
        return instance.profile.birthday

    def _end(self, instance):
        pass

    def _all_day(self, instance):
        return True

    def _is_birthday(self, instance):
        return True

    def _url(self, instance):
        return reverse("members:profile", kwargs={"pk": instance.pk})

    def _title(self, instance):
        return instance.profile.display_name()

    def _description(self, instance):
        membership = instance.current_membership
        if membership and membership.type == "honorary":
            return membership.get_type_display()
        return ""

    def _class_names(self, instance):
        class_names = ["birthday-event"]
        membership = instance.current_membership
        if membership and membership.type == "honorary":
            class_names.append("honorary")
        return class_names
