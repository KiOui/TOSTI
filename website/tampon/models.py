from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Room(models.Model):
    BUILDING_CODES = {
        "hg": "Huygens",
    }

    class Meta:
        unique_together = ("building", "floor_number", "room_number")

    building = models.CharField(max_length=10, choices=BUILDING_CODES, default="hg")
    floor_number = models.IntegerField()
    room_number = models.IntegerField()
    active = models.BooleanField()
    room_code = models.CharField(max_length=7, unique=True, editable=False)

    def save(self, *args, **kwargs):
        building = self.building
        self.room_code = f"{building}{self.floor_number:02d}{self.room_number:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_building_display()} {self.floor_number:02d}.{self.room_number:03d}"


class TamponNotification(models.Model):
    """Notification submitted through the tampon form."""

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    notification_text = models.TextField(
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

    def mark_resolved(self):
        self.is_resolved = True
        if self.resolved_at is None:
            self.resolved_at = timezone.now()
        self.save(update_fields=["is_resolved", "resolved_at"])

    def __str__(self):
        return f"Notification for {self.room} at {self.created_at}"


class Restock(models.Model):
    """Restock record for menstrual products."""

    room = models.ForeignKey(Room, on_delete=models.PROTECT)
    restock_time = models.DateTimeField(auto_now_add=True)
    restocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
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
    name = models.CharField(max_length=100)
    restock_default = models.IntegerField(default=0)
    stock_amount = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class RestockItem(models.Model):
    restock = models.ForeignKey(Restock, on_delete=models.CASCADE)
    stock_data = models.ForeignKey(StockData, on_delete=models.PROTECT)
    quantity = models.IntegerField()

    class Meta:
        unique_together = ("restock", "stock_data")

    def __str__(self):
        return f"{self.quantity} of {self.stock_data.name} for {self.restock}"
