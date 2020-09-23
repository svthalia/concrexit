"""DRF serializers defined by the activemembers package"""
from rest_framework import serializers

from activemembers.models import MemberGroup
from members.api.serializers import MemberListSerializer


class MemberGroupSerializer(serializers.ModelSerializer):
    """MemberGroup serializer"""

    members = MemberListSerializer(many=True)

    class Meta:
        """Meta class for the serializer"""

        model = MemberGroup
        fields = ("pk", "name", "since", "until", "contact_address", "photo", "members")
