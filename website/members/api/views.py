from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from members.api.permissions import SentryIdentityPermission
from members.api.serializers import SentryIdentitySerializer


class SentryIdentityView(APIView):
    permission_classes = (IsAuthenticated, SentryIdentityPermission)

    def get(self, request, format=None):
        serializer = SentryIdentitySerializer(request.user)
        return Response(serializer.data)
