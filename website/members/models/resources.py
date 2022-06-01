from import_export import resources, fields

from members.models import Member
from django.contrib.auth.models import User


class MemberEmailListResource(resources.ModelResource):
    class Meta:
        model = Member
        fields = ("first_name", "last_name", "email")
