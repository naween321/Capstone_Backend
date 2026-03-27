import re
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.commons.models import TimeStampModel

VALID_CATEGORIES = [
    'GROCERY', 'HOUSEHOLD', 'BEAUTY_CARE', 'PHARMACY', 'CLOTHING',
    'KIDS', 'BOOKS_OFFICE', 'ELECTRONICS', 'HOME_DECOR', 'DINING',
    'PET_SUPPLIES', 'FUEL_AUTO', 'TRAVEL', 'FEES_TAX', 'OTHER',
]

CATEGORY_CHOICES = [(c, c.replace('_', ' ').title()) for c in VALID_CATEGORIES]

# Rejects control characters and HTML tags; allows common punctuation.
_SAFE_TEXT_RE = re.compile(r'^[\w\s\-\.,:;\'\"()&/!@#%+]+$', re.UNICODE)


def validate_safe_text(value):
    if not _SAFE_TEXT_RE.match(value):
        raise ValidationError('Contains disallowed characters.')


class AppInstance(TimeStampModel):
    """Anonymous per-install identity issued on first launch.

    No PII is collected. The raw token is returned exactly once at
    registration and never stored — only its SHA-256 hash is kept.
    """
    instance_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )
    instance_token_hash = models.CharField(
        max_length=64,
        help_text='SHA-256 hex digest of the raw secret. Never store the raw token.',
    )
    platform = models.CharField(max_length=20, blank=True)  # 'android' | 'ios' | 'web'
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'AppInstance {self.instance_id} (active={self.is_active})'


class GlobalProductAlias(TimeStampModel):
    """One row per alias string, pointing to a canonical product.

    Denormalized so that a product with 5 aliases becomes 6 rows
    (canonical name + each alias). Enables efficient GIN trigram lookup.
    """
    canonical_name = models.CharField(max_length=255, validators=[validate_safe_text])
    alias_text = models.CharField(max_length=255)
    alias_text_upper = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    source = models.CharField(max_length=50, default='seed')

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['canonical_name', 'alias_text_upper'],
                name='uq_canonical_alias',
            ),
        ]

    def save(self, *args, **kwargs):
        self.alias_text_upper = self.alias_text.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.alias_text} → {self.canonical_name} [{self.category}]'



class StoreAlias(TimeStampModel):
    """Maps a vendor/store name to a primary expense category."""
    vendor_name = models.CharField(max_length=255, validators=[validate_safe_text])
    vendor_name_upper = models.CharField(max_length=255, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    source = models.CharField(max_length=20, default='system')
    created_by = models.ForeignKey(
        AppInstance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )

    class Meta:
        verbose_name = 'Global Store Alias'
        verbose_name_plural = 'Global Store Aliases'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['vendor_name_upper'], name='idx_store_vendor_upper'),
        ]

    def save(self, *args, **kwargs):
        self.vendor_name_upper = self.vendor_name.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.vendor_name} → {self.category}'


class AliasDonation(TimeStampModel):
    """Staging queue for instance-donated aliases awaiting staff review."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        DUPLICATE = 'duplicate', 'Duplicate'

    class DonationType(models.TextChoices):
        PRODUCT = 'product', 'Product'
        STORE = 'store', 'Store'

    donation_type = models.CharField(max_length=20, choices=DonationType.choices)
    donated_by = models.ForeignKey(
        AppInstance,
        on_delete=models.SET_NULL,
        null=True,
        related_name='alias_donations',
    )
    receipt_acronym = models.CharField(max_length=255)
    decoded_name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    # reviewed_by stays as a User FK — only staff review via Django admin
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alias_reviews',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    donor_trust_score = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at'], name='idx_donation_status'),
        ]

    def __str__(self):
        return f'[{self.status}] {self.receipt_acronym} → {self.decoded_name}'


class UserPreference(TimeStampModel):
    """Per-instance donate-aliases preference, stored server-side.

    We keep this on the backend rather than trusting a client-supplied flag
    because the donation decision is made inside the categorize-all endpoint.
    Storing it here means:
      1. The preference survives client restarts and SharedPreferences wipes.
      2. A malicious client cannot forge donations by flipping the flag per-request.
      3. The decision is in one place — the backend — not duplicated across clients.

    The Flutter app mirrors this value to SharedPreferences for instant UI reads
    and syncs changes via PATCH /api/aliases/preferences/.
    """
    app_instance = models.OneToOneField(
        AppInstance,
        on_delete=models.CASCADE,
        related_name='alias_preferences',
    )
    donate_aliases = models.BooleanField(default=False)

    def __str__(self):
        return f'Preferences for {self.app_instance_id} (donate={self.donate_aliases})'
