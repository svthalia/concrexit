from rest_framework.permissions import BasePermission


class HasActiveMembership(BasePermission):
    def has_permission(self, request, view):
        return request.member and request.member.has_active_membership()
