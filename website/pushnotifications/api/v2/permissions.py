from django.db.models import QuerySet

from rest_framework import permissions


class IsAuthenticatedOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, QuerySet) or not request.user:
            return True
        return obj.user == request.user
