from rest_framework.permissions import BasePermission


class CanUsePromotionTools(BasePermission):
    """Allow users that may use the promotion tools.

    A client credentials token has no user; it acts as the owner of its application.
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated) and request.auth is not None:
            user = getattr(getattr(request.auth, "application", None), "user", None)
        return bool(user) and user.has_perm("promotion.use_promotion_tools")
