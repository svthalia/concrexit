from rest_framework import permissions


class UnpublishedEventPermissions(permissions.DjangoModelPermissions):
    """Custom permission for the unpublished events route"""

    perms_map = {
        "GET": ["%(app_label)s.add_%(model_name)s"],
    }
