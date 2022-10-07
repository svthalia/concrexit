from django.db.models import QuerySet

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, QuerySet):
            return True
        # must be the owner to view the object
        return obj.user == request.user
