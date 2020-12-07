from events.api.calendarjs.serializers import CalenderJSSerializer
from partners.models import PartnerEvent


class PartnerEventCalendarJSSerializer(CalenderJSSerializer):
    """Partner event calender serializer."""

    class Meta(CalenderJSSerializer.Meta):
        """Meta class for partner event calendar serializer."""

        model = PartnerEvent

    def _title(self, instance):
        if instance.partner:
            return "{} ({})".format(instance.title, instance.partner.name)
        return "{} ({})".format(instance.title, instance.other_partner)

    def _class_names(self, instance):
        """Return the color of the background."""
        return ["partner-event"]

    def _url(self, instance):
        """Return the url of the partner event."""
        return instance.url

    def _target_blank(self, instance):
        """Return whether the anchor tag should have 'target="_blank"'."""
        return True
