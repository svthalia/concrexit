from django.db.models import QuerySet
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import BasePermission

from events.services import is_organiser
from pizzas.models import FoodEvent, FoodOrder


class IsOrganiser(BasePermission):
    def has_permission(self, request, view):
        event_lookup_field = (
            view.event_lookup_field if hasattr(view, "event_lookup_field") else "pk"
        )
        if event_lookup_field in view.kwargs:
            obj = get_object_or_404(FoodEvent, pk=view.kwargs.get(event_lookup_field))
            return is_organiser(request.member, obj)
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, QuerySet):
            return True
        if not request.member:
            return False
        if isinstance(obj, FoodOrder):
            obj = obj.food_event
        return is_organiser(request.member, obj)
