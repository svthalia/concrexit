from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from oauth2_provider.settings import oauth2_settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, IsAuthenticated


class IsAuthenticatedOrTokenHasScopeForMethod(BasePermission):
    def has_permission(self, request, view):
        is_authenticated = IsAuthenticated().has_permission(request, view)
        oauth2authenticated = False
        if is_authenticated:
            oauth2authenticated = isinstance(
                request.successful_authenticator, OAuth2Authentication
            )

        token = request.auth
        has_scope = False

        if token and hasattr(token, "scope"):  # OAuth 2
            required_scopes = view.required_scopes_per_method[request.method]

            if token.is_valid(required_scopes):
                has_scope = True

            # Provide information about required scope?
            include_required_scope = (
                oauth2_settings.ERROR_RESPONSE_WITH_SCOPES
                and required_scopes
                and not token.is_expired()
                and not token.allow_scopes(required_scopes)
            )

            if include_required_scope:
                self.message = {
                    "detail": PermissionDenied.default_detail,
                    "required_scopes": list(required_scopes),
                }

        return (is_authenticated and not oauth2authenticated) or has_scope
