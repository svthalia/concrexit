from rest_framework.reverse import reverse

from events import services
from events.models import Event, status
from events.models.external_event import ExternalEvent
from thaliawebsite.api.calendarjs.serializers import CalenderJSSerializer


class EventsCalenderJSSerializer(CalenderJSSerializer):
    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _url(self, instance):
        return reverse("events:event", kwargs={"slug": instance.slug})

    def _class_names(self, instance):
        if self.context["member"] and len(instance.member_registration) > 0:
            registration = instance.member_registration[-1]
        else:
            registration = None
        reg_status = services.registration_status(
            instance, registration, self.context["member"]
        )
        return [status.calendarjs_class_name(reg_status)]

    def _registration_info(self, instance):
        if self.context["member"] and len(instance.member_registration) > 0:
            registration = instance.member_registration[-1]
        else:
            registration = None

        status = services.registration_status(
            instance, registration, self.context["member"]
        )
        return services.registration_status_string(
            status,
            instance,
            registration,
        )


class UnpublishedEventsCalenderJSSerializer(CalenderJSSerializer):
    """See CalenderJSSerializer, customised classes."""

    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _class_names(self, instance):
        return ["unpublished-event"]

    def _url(self, instance):
        return reverse("admin:events_event_details", kwargs={"pk": instance.id})

    def _registration_info(self, instance):
        return "Unpublished event"


class ExternalEventCalendarJSSerializer(CalenderJSSerializer):
    """External event calender serializer."""

    class Meta(CalenderJSSerializer.Meta):
        """Meta class for partner event calendar serializer."""

        model = ExternalEvent

    def _title(self, instance):
        return f"{instance.title} ({instance.organiser})"

    def _class_names(self, instance):
        """Return the color of the background."""
        return ["external-event"]

    def _url(self, instance):
        """Return the url of the partner event."""
        return instance.url

    def _target_blank(self, instance):
        """Return whether the anchor tag should have 'target="_blank"'."""
        return True
