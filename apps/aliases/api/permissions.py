import hashlib

from django.utils import timezone
from rest_framework.permissions import BasePermission


class AppInstancePermission(BasePermission):
    """Validates X-Instance-ID + X-Instance-Token request headers.

    Both headers must be present and the token must match the stored
    SHA-256 hash for the given instance UUID. Inactive instances are
    rejected regardless of token correctness.
    """
    message = 'Missing or invalid app instance credentials.'

    def has_permission(self, request, view):
        from apps.aliases.models import AppInstance

        instance_id = request.headers.get('X-Instance-ID', '').strip()
        raw_token = request.headers.get('X-Instance-Token', '').strip()

        if not instance_id or not raw_token:
            return False

        try:
            instance = AppInstance.objects.get(pk=instance_id, is_active=True)
        except (AppInstance.DoesNotExist, ValueError):
            return False

        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        if instance.instance_token_hash != token_hash:
            return False

        # Attach the resolved instance to the request for use in views.
        request.app_instance = instance
        return True
