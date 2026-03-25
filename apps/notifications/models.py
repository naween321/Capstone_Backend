from django.db import models

from apps.commons.models import TimeStampModel


class DeviceToken(TimeStampModel):
    token = models.TextField(unique=True)
    platform = models.CharField(max_length=20)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"DeviceToken [{self.platform}] – {self.token[:20]}..."
