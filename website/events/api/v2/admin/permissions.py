from django.db.models import QuerySet
from rest_framework.permissions import BasePermission

from events.models import EventRegistration
from events.services import is_organiser


class IsOrganiser(BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, QuerySet):
            return True
        if not request.member:
            return False
        if isinstance(obj, EventRegistration):
            obj = obj.event
        return is_organiser(request.member, obj)
