from rest_framework import permissions


class UnpublishedEventPermissions(permissions.DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.add_%(model_name)s'],
    }
