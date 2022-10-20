"""DRF viewsets defined by the members package."""

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters, viewsets

from activemembers.api.v1.serializers import MemberGroupSerializer
from activemembers.models import MemberGroup


class MemberGroupViewset(viewsets.ReadOnlyModelViewSet):
    """Viewset that renders or edits a member."""

    required_scopes = ["activemembers:read"]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    queryset = MemberGroup.active_objects.all()
    serializer_class = MemberGroupSerializer
    filter_backends = (
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = ("name", "contact_email", "contact_mailinglist__name")
    lookup_field = "pk"
