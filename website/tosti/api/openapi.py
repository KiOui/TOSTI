"""
Backwards-compatible schema helpers for the TOSTI API.

The project historically used DRF's built-in OpenAPI generator with a custom
``CustomAutoSchema`` class supporting ``manual_operations``, ``request_schema``,
``response_schema`` and ``manual_field_mappings`` kwargs.

DRF's generator was dropped in favour of drf-spectacular. This module re-exports
``CustomAutoSchema`` so the existing view declarations (``schema = CustomAutoSchema(...)``)
keep working: the kwargs are translated into drf-spectacular's hook points.
"""

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

_LOCATION_MAP = {
    "query": OpenApiParameter.QUERY,
    "path": OpenApiParameter.PATH,
    "header": OpenApiParameter.HEADER,
    "cookie": OpenApiParameter.COOKIE,
}

_TYPE_MAP = {
    "string": OpenApiTypes.STR,
    "integer": OpenApiTypes.INT,
    "number": OpenApiTypes.FLOAT,
    "boolean": OpenApiTypes.BOOL,
    "array": OpenApiTypes.STR,  # fallback; use OpenApiParameter directly for complex types
    "object": OpenApiTypes.OBJECT,
}


def _to_open_api_parameter(raw):
    """Convert a legacy manual-operation dict to an OpenApiParameter."""
    if isinstance(raw, OpenApiParameter):
        return raw
    schema = raw.get("schema", {}) if isinstance(raw.get("schema"), dict) else {}
    openapi_type = _TYPE_MAP.get(schema.get("type", "string"), OpenApiTypes.STR)
    return OpenApiParameter(
        name=raw["name"],
        type=openapi_type,
        location=_LOCATION_MAP.get(raw.get("in", "query"), OpenApiParameter.QUERY),
        required=raw.get("required", False),
        description=raw.get("description", ""),
    )


class CustomAutoSchema(AutoSchema):
    """drf-spectacular-backed compatibility wrapper for the old schema API."""

    def __init__(
        self,
        manual_operations=None,
        request_schema=None,
        response_schema=None,
        manual_field_mappings=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._manual_operations = manual_operations or []
        self._request_schema = request_schema
        self._response_schema = response_schema
        # manual_field_mappings was used with WritableModelSerializer to override
        # individual field schemas. drf-spectacular doesn't have a direct equivalent;
        # the simplest forward path is to apply these mappings in a component hook.
        self._manual_field_mappings = manual_field_mappings or {}

    def get_override_parameters(self):
        """Surface legacy ``manual_operations`` as override parameters."""
        return [_to_open_api_parameter(p) for p in self._manual_operations]

    def get_request_serializer(self):
        """Return a raw schema dict so drf-spectacular uses it verbatim."""
        if self._request_schema is not None:
            # drf-spectacular expects dict keys to be media types; wrap accordingly.
            return {"application/json": self._request_schema}
        return super().get_request_serializer()

    def get_response_serializers(self):
        """Return a raw schema dict so drf-spectacular uses it verbatim."""
        if self._response_schema is not None:
            # drf-spectacular expects status codes as keys here; use 200/201 defaults.
            status_code = "201" if self.method == "POST" else "200"
            return {status_code: self._response_schema}
        return super().get_response_serializers()
