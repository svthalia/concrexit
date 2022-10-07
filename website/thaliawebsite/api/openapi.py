import warnings

from django.http import HttpRequest
from oauth2_provider.scopes import get_scopes_backend
from rest_framework import exceptions
from rest_framework.request import Request
from rest_framework.reverse import reverse
from rest_framework.schemas.openapi import SchemaGenerator, AutoSchema
from rest_framework.schemas.utils import is_list_view


class OAuthSchemaGenerator(SchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        if "components" in schema:
            schema["components"]["securitySchemes"] = {
                "oauth2": {
                    "type": "oauth2",
                    "description": "OAuth2",
                    "flows": {
                        "implicit": {
                            "authorizationUrl": reverse("oauth2_provider:authorize"),
                            "scopes": get_scopes_backend().get_all_scopes(),
                        }
                    },
                }
            }
        return schema


class OAuthAutoSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if self.view and hasattr(self.view, "required_scopes"):
            operation["security"] = [{"oauth2": self.view.required_scopes}]
        else:
            operation["security"] = [{"oauth2": ["read", "write"]}]
        return operation

    def get_operation_id_base(self, path, method, action):
        name = super().get_operation_id_base(path, method, action)
        if "admin" in path:
            return "Admin" + name.capitalize()
        return name

    def get_operation_id(self, path, method):
        method_name = getattr(self.view, "action", method.lower())
        if is_list_view(path, method, self.view):
            action = "list"
        elif method_name not in self.method_mapping:
            action = self._to_camel_case(
                f"{self.method_mapping[method.lower()]}_{method_name}"
            )
        else:
            action = self.method_mapping[method.lower()]

        name = self.get_operation_id_base(path, method, action)

        return action + name

    def get_serializer(self, path, method):
        view = self.view
        http_request = HttpRequest()
        http_request.method = method
        http_request.path = path
        view.request = Request(http_request)
        view.request.member = view.request.user

        if not hasattr(view, "get_serializer"):
            return None

        try:
            return view.get_serializer()
        except exceptions.APIException:
            warnings.warn(
                f"{view.__class__.__name__}.get_serializer() raised an "
                "exception during schema generation. Serializer fields "
                f"will not be generated for {method} {path}."
            )
            return None
