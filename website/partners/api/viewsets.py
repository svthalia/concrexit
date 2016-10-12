from rest_framework import viewsets
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.decorators import list_route
from django.utils import timezone
from datetime import datetime

from partners.api.serializers import PartnerEventSerializer
from partners.models import Partner, PartnerEvent


class PartnerViewset(viewsets.ViewSet):
    queryset = Partner.objects.all()

    @list_route()
    def events(self, request):
        try:
            start = timezone.make_aware(
                datetime.strptime(request.query_params['start'], '%Y-%m-%d')
            )
            end = timezone.make_aware(
                datetime.strptime(request.query_params['end'], '%Y-%m-%d')
            )
        except:
            raise ParseError(detail='start or end query parameters invalid')

        queryset = PartnerEvent.objects.filter(
            end__gte=start,
            start__lte=end,
            published=True
        )

        serializer = PartnerEventSerializer(queryset, many=True)
        return Response(serializer.data)
