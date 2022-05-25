from datetime import timedelta

from django.template.defaultfilters import date
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse

from events import services
from events.models import Event, EventRegistration
from events.models.external_event import ExternalEvent
from thaliawebsite.api.calendarjs.serializers import CalenderJSSerializer


class EventsCalenderJSSerializer(CalenderJSSerializer):
    class Meta(CalenderJSSerializer.Meta):
        model = Event

    def _url(self, instance):
        return reverse("events:event", kwargs={"pk": instance.id})

    def _class_names(self, instance):
        if self.context["member"] and instance.member_registration:
            if services.user_registration_pending(self.context["member"], instance):
                return ["regular-event-pending-registration"]
            return ["regular-event-has-registration"]
        if (not instance.registration_required) or instance.registration_allowed:
            return ["regular-event-registration-open"]
        # I think this handles the case that registration is needed, but not yet possible
        return ["regular-event-registration-closed"]

    def _registration_info(self, instance):
        # TODO: fetch registration using a prefetch_related/select_related/annotate
        if self.context["member"]:
            try:
                registration = instance.eventregistration_set.get(member=self.context["member"])
            except EventRegistration.DoesNotExist:
                registration = None
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
