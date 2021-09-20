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
        if self.context["member"] and services.is_user_registered(
            self.context["member"], instance
        ):
            if services.user_registration_pending(self.context["member"], instance):
                return ["regular-event-pending-registration"]
            else:
                return ["regular-event-has-registration"]
        elif (not instance.registration_required) or instance.registration_allowed:
            return ["regular-event-registration-open"]
        else:
            # I think this handles the case that registration is needed, but not yet possible
            return ["regular-event-registration-closed"]


class UnpublishedEventsCalenderJSSerializer(CalenderJSSerializer):
    """See CalenderJSSerializer, customised classes."""

    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _class_names(self, instance):
        return ["unpublished-event"]

    def _url(self, instance):
        return reverse("admin:events_event_details", kwargs={"pk": instance.id})
