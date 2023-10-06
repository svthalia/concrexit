from import_export import resources
from import_export.fields import Field

from members.models import Member


class MemberEmailListResource(resources.ModelResource):
    first_name = Field(attribute="first_name", column_name="First name")
    last_name = Field(attribute="last_name", column_name="Last name")
    email = Field(attribute="email", column_name="Email")

    class Meta:
        model = Member
        fields = ("first_name", "last_name", "email")
        export_order = ("first_name", "last_name", "email")
        name = "Export first name, last name and email of selected users"


class MemberListResource(resources.ModelResource):
    first_name = Field(attribute="first_name", column_name="First name")
    last_name = Field(attribute="last_name", column_name="Last name")

    class Meta:
        model = Member
        fields = (
            "first_name",
            "last_name",
        )
        export_order = (
            "first_name",
            "last_name",
        )
        name = "Export first name and last name of selected users"
