from oauth2_provider.scopes import get_scopes_backend
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
