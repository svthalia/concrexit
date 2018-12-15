from rest_framework import serializers

from activemembers.models import MemberGroup, MemberGroupMembership
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

    members = serializers.SerializerMethodField()

    def get_members(self, obj):
        return (MemberGroupMembership.active_objects.filter(group=obj)
                .values_list('member__username', flat=True))
