import hashlib
import logging
import secrets

from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.aliases.models import AppInstance
from apps.expenses.api.permissions import PrototypeAppKeyPermission

logger = logging.getLogger(__name__)

_VALID_PLATFORMS = {'android', 'ios', 'web'}


def _check_registration_rate_limit(ip, limit=5, window=3600):
    """Allow at most `limit` registrations per IP per hour."""
    key = f'rl:instance_register:{ip}'
    count = cache.get(key, 0)
    if count >= limit:
        return False
    cache.set(key, count + 1, timeout=window)
    return True


def _get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


class RegisterInstanceView(APIView):
    """POST /api/aliases/instances/register/

    Issues a new anonymous app-instance identity. The raw token is
    returned exactly once and never stored — only its SHA-256 hash
    is persisted. The caller must store both values securely on-device.

    Protected by X-Prototype-App-Key only (no instance headers required).
    Rate-limited to 5 registrations per IP per hour.
    """
    permission_classes = [PrototypeAppKeyPermission]

    def post(self, request):
        ip = _get_client_ip(request)
        if not _check_registration_rate_limit(ip):
            logger.warning('[InstanceRegister] rate limit hit ip=%s', ip)
            return Response(
                {'detail': 'Too many registrations. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        raw_platform = (request.data.get('platform') or '').strip().lower()
        platform = raw_platform if raw_platform in _VALID_PLATFORMS else ''

        raw_secret = secrets.token_hex(32)  # 64-char hex; only ever sent once
        token_hash = hashlib.sha256(raw_secret.encode()).hexdigest()

        instance = AppInstance.objects.create(
            instance_token_hash=token_hash,
            platform=platform,
        )

        logger.info('[InstanceRegister] new instance=%s platform=%s ip=%s',
                    instance.instance_id, platform or 'unknown', ip)

        return Response(
            {
                'instanceId': str(instance.instance_id),
                'instanceToken': raw_secret,
            },
            status=status.HTTP_201_CREATED,
        )
