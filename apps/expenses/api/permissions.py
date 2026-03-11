from django.conf import settings
from rest_framework.permissions import BasePermission


class PrototypeAppKeyPermission(BasePermission):
    """
    Rejects requests that do not supply the correct X-Prototype-App-Key header.
    This is soft prototype protection — not a substitute for real authentication.
    """
    message = 'Missing or invalid X-Prototype-App-Key.'

    def has_permission(self, request, view):
        expected = settings.PROTOTYPE_APP_KEY
        if not expected:
            # If no key is configured, deny all to prevent accidental open access.
            return False
        provided = request.headers.get('X-Prototype-App-Key', '')
        return provided == expected
