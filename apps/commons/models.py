import uuid
from django.db import models
from django.conf import settings


class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = '-updated_at',
        abstract = True


class BaseModel(TimeStampModel):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        ordering = '-updated_at',
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.full_clean()
        return super().save(force_insert=False, force_update=False, using=None,
                            update_fields=None)


class UUIDBaseModel(BaseModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta(BaseModel.Meta):
        abstract = True


class DeviceToken(TimeStampModel):
    PLATFORM_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    ]
    token = models.TextField(unique=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.platform} ({self.token[:20]}...)"
