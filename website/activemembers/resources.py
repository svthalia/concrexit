from import_export import resources
from import_export.fields import Field

from activemembers.models import MemberGroupMembership


class MemberGroupMembershipResource(resources.ModelResource):
    first_name = Field(column_name="First name")
    last_name = Field(column_name="Last name")
    email = Field(column_name="Email")
    group = Field(attribute="group", column_name="Group")
    since = Field(attribute="since", column_name="Member since")
    until = Field(attribute="until", column_name="Member until")
    chair = Field(attribute="chair", column_name="Chair of the group")
    role = Field(attribute="role", column_name="Role")

    class Meta:
        model = MemberGroupMembership
        fields = (
            "first_name",
            "last_name",
            "email",
            "group",
            "since",
            "until",
            "chair",
            "role",
        )
        export_order = fields

    def dehydrate_first_name(self, membership):
        return membership.member.first_name

    def dehydrate_last_name(self, membership):
        return membership.member.last_name

    def dehydrate_email(self, membership):
        return membership.member.email
