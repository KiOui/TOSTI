from import_export import resources
from import_export.fields import Field

from qualifications import models


class BasicBorrelBrevetResource(resources.ModelResource):
    """Basic Borrel Brevet Resource."""

    user__full_name = Field(attribute="user__full_name", column_name="full_name")
    user__first_name = Field(attribute="user__first_name", column_name="first_name")
    user__last_name = Field(attribute="user__last_name", column_name="last_name")
    user__username = Field(attribute="user__username", column_name="username")
    user__email = Field(attribute="user__email", column_name="email")

    class Meta:
        """Meta class."""

        model = models.BasicBorrelBrevet
        fields = [
            "user__full_name",
            "user__first_name",
            "user__last_name",
            "user__username",
            "user__email",
            "registered_on",
        ]
        export_order = [
            "user__full_name",
            "user__first_name",
            "user__last_name",
            "user__username",
            "user__email",
            "registered_on",
        ]
