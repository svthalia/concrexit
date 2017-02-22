from datetime import datetime

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from events.api.serializers import EventSerializer
from events.models import Event


class EventViewset(viewsets.ViewSet):
    queryset = Event.objects.all()

    def list(self, request):
        try:
            start = timezone.make_aware(
                datetime.strptime(request.query_params['start'], '%Y-%m-%d')
            )
            end = timezone.make_aware(
                datetime.strptime(request.query_params['end'], '%Y-%m-%d')
            )
        except:
            raise ParseError(detail='start or end query parameters invalid')

        queryset = self.queryset.filter(
            end__gte=start,
            start__lte=end,
            published=True
        )

        serializer = EventSerializer(queryset, many=True,
                                     context={'user': request.user})
        return Response(serializer.data)
