from rest_framework import serializers

from activemembers.models import MemberGroup
from members.models import Member


class NextCloudMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ('pk', 'username', 'first_name',
                  'last_name', 'is_superuser', 'email')


class NextCloudGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberGroup
        fields = ('pk', 'name', 'members')

    members = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='username'
    )
