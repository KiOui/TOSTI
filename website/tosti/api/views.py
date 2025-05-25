from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from rest_framework.generics import (
    CreateAPIView,
    UpdateAPIView,
    DestroyAPIView,
    RetrieveUpdateAPIView,
    ListCreateAPIView,
    RetrieveDestroyAPIView,
    RetrieveUpdateDestroyAPIView,
)

from tosti.utils import log_action, ModelDiffCalculator


class LoggedCreateAPIView(CreateAPIView):
    """CreateAPIView with logged actions."""

    def perform_create(self, serializer):
        """Log the addition."""
        super().perform_create(serializer)
        log_action(
            self.request.user,
            serializer.instance,
            ADDITION,
            [
                {
                    "added": {
                        "name": str(serializer.instance._meta.verbose_name),
                        "object": str(serializer.instance),
                    }
                }
            ],
        )


class LoggedListCreateAPIView(LoggedCreateAPIView, ListCreateAPIView):
    """ListCreateAPIView with logged actions."""

    pass


class LoggedUpdateAPIView(UpdateAPIView):
    """UpdateAPIView with logged actions."""

    def perform_update(self, serializer):
        """Log the update."""
        helper = ModelDiffCalculator(self.get_object())
        super().perform_update(serializer)
        log_action(
            self.request.user,
            serializer.instance,
            CHANGE,
            [
                {
                    "changed": {
                        "name": str(serializer.instance._meta.verbose_name),
                        "object": str(serializer.instance),
                        "fields": helper.set_changed_model(
                            serializer.instance
                        ).changed_fields,
                    }
                }
            ],
        )


class LoggedRetrieveUpdateAPIView(LoggedUpdateAPIView, RetrieveUpdateAPIView):
    """RetrieveUpdateAPIView with logged actions."""

    pass


class LoggedDestroyAPIView(DestroyAPIView):
    """DestroyAPIView with logged actions."""

    def perform_destroy(self, instance):
        """Log the deletion."""
        log_message = [
            {
                "deleted": {
                    "name": str(instance._meta.verbose_name),
                    "object": str(instance),
                }
            }
        ]
        super().perform_destroy(instance)
        log_action(self.request.user, instance, DELETION, log_message)


class LoggedRetrieveDestroyAPIView(LoggedDestroyAPIView, RetrieveDestroyAPIView):
    """RetrieveDestroyAPIView with logged actions."""

    pass


class LoggedRetrieveUpdateDestroyAPIView(
    LoggedUpdateAPIView, LoggedDestroyAPIView, RetrieveUpdateDestroyAPIView
):
    """RetrieveUpdateDestroyAPIView with logged actions."""

    pass
