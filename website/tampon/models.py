from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class Room(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True)
    active = models.BooleanField()

    def __str__(self):
        return self.name


class TamponNotification(models.Model):
    """Notification submitted through the tampon form."""

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    comment = models.TextField(
        blank=True,
        max_length=500,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Tampon notification"
        verbose_name_plural = "Tampon notifications"
        permissions = [
            ("manage_tamponnotification", "Can manage Tampon notifications"),
        ]

    def save(self, *args, **kwargs):
        if self.is_resolved and self.resolved_at is None:
            self.resolved_at = timezone.now()
            if "update_fields" in kwargs:
                kwargs["update_fields"] = [*kwargs["update_fields"], "resolved_at"]
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Notification for {self.room} at {self.created_at}"


class Restock(models.Model):
    """Restock record for menstrual products."""

    """A restock record is created when a tampon notification is resolved,
    and contains the details of the restock that was done.
    It is linked to the room and to multiple individual RestockItem's that were restocked."""
    room = models.ForeignKey(Room, on_delete=models.PROTECT)
    restock_time = models.DateTimeField(auto_now_add=True)
    restocked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    stock_items = models.ManyToManyField(
        "StockData",
        through="RestockItem",
        related_name="restocks",
    )

    class Meta:
        ordering = ["-restock_time"]
        verbose_name = "Restock record"
        verbose_name_plural = "Restock records"

    def __str__(self):
        return f"Restock for {self.room} at {self.restock_time}"


class StockData(models.Model):
    """Data about a specific type of stock that can be restocked"""

    name = models.CharField(max_length=100)
    restock_default = models.IntegerField(default=0)
    stock_amount = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class RestockItem(models.Model):
    """Through model for the many-to-many relationship between Restock
    and StockData, containing the quantity of each stock that was restocked in a Restock.
    """

    restock = models.ForeignKey(Restock, on_delete=models.CASCADE)
    stock_data = models.ForeignKey(StockData, on_delete=models.PROTECT)
    quantity = models.IntegerField()

    class Meta:
        unique_together = ("restock", "stock_data")

    def __str__(self):
        return f"{self.quantity} of {self.stock_data.name} for {self.restock}"
