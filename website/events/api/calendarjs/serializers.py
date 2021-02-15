from rest_framework.reverse import reverse

from events import services
from events.models import Event
from thaliawebsite.api.calendarjs.serializers import CalenderJSSerializer


class EventsCalenderJSSerializer(CalenderJSSerializer):
    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _url(self, instance):
        return reverse("events:event", kwargs={"pk": instance.id})

    def _class_names(self, instance):
        class_names = ["regular-event"]
        if self.context["member"] and services.is_user_registered(
            self.context["member"], instance
        ):
            if not services.user_registration_pending(self.context["member"], instance):
                class_names.append("pending-registration")
            else:
                class_names.append("has-registration")
        elif not instance.registration_required:
            class_names.append("no-registration")
        elif not instance.registration_allowed:
            class_names.append("registration-closed")
        return class_names


class UnpublishedEventsCalenderJSSerializer(CalenderJSSerializer):
    """See CalenderJSSerializer, customised classes."""

    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _class_names(self, instance):
        return ["unpublished-event"]

    def _url(self, instance):
        return reverse("admin:events_event_details", kwargs={"pk": instance.id})
