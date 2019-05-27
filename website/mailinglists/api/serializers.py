from rest_framework import serializers

from mailinglists.models import MailingList


class MailingListSerializer(serializers.ModelSerializer):
    """Serializer for serializing mailing lists."""

    class Meta:
        """Meta class for the MailingListSerializer."""

        model = MailingList
        fields = ('names', 'prefix', 'archived', 'moderated', 'addresses',
                  'autoresponse_enabled', 'autoresponse_text')

    names = serializers.SerializerMethodField('_names')
    addresses = serializers.SerializerMethodField('_addresses')

    def _names(self, instance):
        """Return list of names of the the mailing list and its aliases."""
        return [instance.name] + [x.alias for x in instance.aliasses.all()]

    def _addresses(self, instance):
        """Return list of all subscribed addresses."""
        return instance.all_addresses()
