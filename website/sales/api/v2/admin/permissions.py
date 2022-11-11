from django.db.models import QuerySet

from rest_framework.generics import get_object_or_404
from rest_framework.permissions import BasePermission

from sales.models.order import Order
from sales.models.shift import Shift
from sales.services import is_manager


class IsManager(BasePermission):
    def has_permission(self, request, view):
        shift_lookup_field = (
            view.shift_lookup_field if hasattr(view, "shift_lookup_field") else None
        )
        if shift_lookup_field and shift_lookup_field in view.kwargs:
            obj = get_object_or_404(Shift, pk=view.kwargs.get(shift_lookup_field))
            return is_manager(request.member, obj)
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, QuerySet):
            return True
        if not request.member:
            return False
        if isinstance(obj, Order):
            obj = obj.shift
        return is_manager(request.member, obj)
