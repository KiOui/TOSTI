from oauth2_provider.scopes import get_scopes_backend
from rest_framework.reverse import reverse
from rest_framework.schemas.openapi import SchemaGenerator, AutoSchema


class OAuthSchemaGenerator(SchemaGenerator):
    """OAuth Schema Generator."""

    def has_view_permissions(self, path, method, view):
        """
        Check if a view has permissions to be accessed.

        This method has been overridden as some of the views require an object permission. If an object is not defined
        an AttributeError will be thrown.
        """
        try:
            return super().has_view_permissions(path, method, view)
        except AttributeError:
            return True

    def get_schema(self, request=None, public=False):
        """Get schema."""
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
    """OAuth Schema."""

    def get_operation(self, path, method):
        """Get operation."""
        operation = super().get_operation(path, method)
        if self.view and hasattr(self.view, "required_scopes"):
            operation["security"] = {"oauth2": self.view.required_scopes}
        return operation
