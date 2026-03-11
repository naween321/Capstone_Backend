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
