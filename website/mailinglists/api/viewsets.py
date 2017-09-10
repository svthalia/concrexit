from rest_framework import viewsets

from mailinglists import services
from mailinglists.api.permissions import MailingListPermission
from mailinglists.api.serializers import MailingListSerializer
from mailinglists.models import MailingList


class MailingListViewset(viewsets.ReadOnlyModelViewSet):
    permission_classes = [MailingListPermission]
    queryset = MailingList.objects.all()
    serializer_class = MailingListSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        automatic_lists = services.get_automatic_lists()
        if automatic_lists is not None:
            response.data = list(response.data) + automatic_lists
        return response
