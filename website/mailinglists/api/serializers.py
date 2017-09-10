from rest_framework import serializers

from mailinglists.models import MailingList


class MailingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailingList
        fields = ('names', 'prefix', 'archived', 'moderated', 'addresses')

    names = serializers.SerializerMethodField('_names')
    addresses = serializers.SerializerMethodField('_addresses')

    def _names(self, instance):
        return [instance.name] + [x.alias for x in instance.aliasses.all()]

    def _addresses(self, instance):
        return instance.all_addresses()
