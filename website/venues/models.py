from django.db import models


class Venue(models.Model):
    name = models.CharField(max_length=50, unique=True, blank=False, null=False)
    image = models.ImageField(upload_to="venues/images/", blank=True, null=True)

    active = models.BooleanField(default=True, null=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-active", "name"]
