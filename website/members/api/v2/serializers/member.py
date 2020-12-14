from rest_framework import serializers

from members.models import Member


# @todo This file is only here for placeholder purposes
class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = "__all__"
