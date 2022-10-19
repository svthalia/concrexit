from datetime import timedelta

from django.contrib.humanize.templatetags.humanize import naturaltime
from django.template.defaultfilters import date
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse

from events import services
from events.models import Event
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

    def _registration_info(self, instance: Event):
        # If registered in some way
        if self.context["member"] and instance.member_registration:
            queue_pos = services.user_registration_pending(
                self.context["member"], instance
            )
            # In waiting list
            if isinstance(queue_pos, int):
                return _("In waiting list at position {queue_pos}").format(
                    queue_pos=queue_pos
                )
            # Actually registered
            return _("You are registered for this event")
        # Optional registration possible
        if instance.optional_registration_allowed:
            return _("Registering for this event is optional")
        # No places left
        if (
            instance.max_participants is not None
            and instance.max_participants <= instance.number_regs
        ):
            return _("You can put yourself on the waiting list for this event")
        # Registration still possible
        if instance.registration_allowed:
            return _("You can register for this event")
        # Not registration time yet
        if instance.registration_end:
            now = timezone.now()
            if instance.registration_end < now:
                return _("Registrations have been closed")
            if instance.registration_start <= now + timedelta(days=2):
                return _("Registrations open {at_time}").format(
                    at_time=naturaltime(instance.registration_start)
                )
            return _("Registrations open {date}").format(
                date=date(instance.registration_start)
            )
        return None


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
