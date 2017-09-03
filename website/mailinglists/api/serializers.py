from rest_framework import serializers

from mailinglists.models import MailingList


class MailingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailingList
        fields = ('name', 'prefix', 'archived', 'moderated', 'addresses')

    addresses = serializers.SerializerMethodField('_addresses')

    def _addresses(self, instance):
        return instance.all_addresses()
