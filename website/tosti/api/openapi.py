from oauth2_provider.scopes import get_scopes_backend
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.reverse import reverse
from rest_framework.schemas.openapi import SchemaGenerator, AutoSchema

from tosti.api.serializers import WritableModelSerializer


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

        if self.view and hasattr(self.view, "required_scopes"):
            op["security"] = {"oauth2": self.view.required_scopes}
        elif self.view and hasattr(self.view, "required_scopes_for_method"):
            op["security"] = {"oauth2": self.view.required_scopes_for_method[method]}

        return op

    def get_request_body(self, path, method):
        """Get custom request body."""
        if method not in ("PUT", "PATCH", "POST"):
            return {}

        self.request_media_types = self.map_parsers(path, method)

        if self.request_schema is not None:
            return {"content": {ct: {"schema": self.request_schema} for ct in self.request_media_types}}

        serializer = self.get_request_serializer(path, method)

        if not isinstance(serializer, WritableModelSerializer):
            return super().get_request_body(path, method)

        content = self.map_writable_model_serializer(serializer)
        item_schema = content

        return {"content": {ct: {"schema": item_schema} for ct in self.request_media_types}}

    def map_writable_model_serializer(self, serializer):
        """Maps a WritableModelSerializer"""
        # Assuming we have a valid serializer instance.
        required = []
        properties = {}

        for field in serializer.get_writable_fields():
            if isinstance(field, serializers.HiddenField):
                continue

            if field.required:
                required.append(field.field_name)

            schema = self.map_field(field)
            if field.write_only:
                schema["writeOnly"] = True
            if field.allow_null:
                schema["nullable"] = True
            if field.default is not None and field.default != empty and not callable(field.default):
                schema["default"] = field.default
            if field.help_text:
                schema["description"] = str(field.help_text)
            self.map_field_validators(field, schema)

            properties[field.field_name] = schema

        result = {"type": "object", "properties": properties}
        if required:
            result["required"] = required

        return result

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
