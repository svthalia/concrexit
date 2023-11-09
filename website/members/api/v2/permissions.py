from rest_framework.permissions import BasePermission


class HasActiveMembership(BasePermission):
    """DRF permission equivalent of the `@membership_required` view decorator."""
    def has_permission(self, request, view):
        return request.member and request.member.has_active_membership()
