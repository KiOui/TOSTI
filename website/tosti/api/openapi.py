from oauth2_provider.scopes import get_scopes_backend
from rest_framework.reverse import reverse
from rest_framework.schemas.openapi import SchemaGenerator, AutoSchema


class OpenAPISchemaGenerator(SchemaGenerator):
    """Open API Schema Generator."""

    def has_view_permissions(self, path, method, view):
        """
        Check if a view has permissions to be accessed.

        This method has been overridden as some of the views require an object permission. If an object is not defined
        an AttributeError will be thrown.
        """
        try:
            return super().has_view_permissions(path, method, view)
        except (AttributeError, ValueError):
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


class CustomAutoSchema(AutoSchema):
    """
    Custom Auto Schema.

    Used for creating customized operations on top of the AutoSchema class.
    """

    def __init__(
        self,
        manual_operations=None,
        request_schema=None,
        response_schema=None,
        manual_field_mappings=None,
        *args,
        **kwargs,
    ):
        """
        Initialize CustomAutoSchema.

        :param manual_operations: custom manual operation fields
        :param request_schema: optional custom request schema
        :param response_schema: optional custom response schema
        :param args: arguments
        :param kwargs: keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.manual_operations = [] if manual_operations is None else manual_operations
        self.manual_field_mappings = {} if manual_field_mappings is None else manual_field_mappings
        self.request_schema = request_schema
        self.response_schema = response_schema

    def get_operation(self, path, method):
        """Add manual fields to operation."""
        op = super().get_operation(path, method)
        for manual_field in self.manual_operations:
            op["parameters"].append(manual_field)
        return op

    def get_request_body(self, path, method):
        """Get custom request body."""
        if self.request_schema is None:
            return super().get_request_body(path, method)

        if method not in ("PUT", "PATCH", "POST"):
            return {}

        self.request_media_types = self.map_parsers(path, method)

        return {"content": {ct: {"schema": self.request_schema} for ct in self.request_media_types}}

    def get_responses(self, path, method):
        """Get custom responses."""
        if self.response_schema is None:
            return super().get_responses(path, method)

        if method == "DELETE":
            return {"204": {"description": ""}}

        self.response_media_types = self.map_renderers(path, method)

        status_code = "201" if method == "POST" else "200"

        return {
            status_code: {
                "content": {ct: {"schema": self.response_schema} for ct in self.response_media_types},
                "description": "",
            }
        }

    def map_field(self, field):
        """Get custom field mappings."""
        if field.field_name in self.manual_field_mappings.keys():
            return self.manual_field_mappings[field.field_name]
        else:
            return super().map_field(field)
