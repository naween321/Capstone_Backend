import uuid

from django.db import models

from apps.commons.models import TimeStampModel


class ReceiptScan(TimeStampModel):
    """Persists each successful receipt scan and its extracted data."""
    veryfi_document_id = models.CharField(max_length=100, null=True, blank=True)
    vendor = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    veryfi_category = models.CharField(max_length=100, null=True, blank=True)
    image_filename = models.CharField(max_length=255, blank=True)
    raw_response = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default='success')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"ReceiptScan {self.veryfi_document_id or 'unknown'} – {self.vendor or 'unknown vendor'}"


class QuotaRecord(TimeStampModel):
    """Tracks monthly receipt scan usage against the hard cap."""
    month_key = models.CharField(max_length=7, unique=True)  # e.g. "2026-03"
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"QuotaRecord {self.month_key}: {self.count}"


class ReceiptScanJob(TimeStampModel):
    """Tracks asynchronous receipt scan execution and progress."""

    class Status(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        UPLOADING = 'uploading', 'Uploading'
        PROCESSING = 'processing', 'Processing'
        RECEIVING = 'receiving', 'Receiving'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    progress = models.FloatField(default=0.0)
    error_message = models.TextField(blank=True)
    result = models.JSONField(default=dict)
    image_filename = models.CharField(max_length=255, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    stored_file_path = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"ReceiptScanJob {self.id} ({self.status})"
