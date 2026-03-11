import logging
from datetime import datetime, date

import requests
from django.conf import settings
from django.core.cache import cache
from django.db.models import F
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.expenses.api.permissions import PrototypeAppKeyPermission
from apps.expenses.models import QuotaRecord, ReceiptScan

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/gif',
    'image/heic',
    'image/heif',
}
MIN_FILE_SIZE = 250          # bytes
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def _get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def _check_rate_limit(ip, limit=10, window=60):
    """Returns False if the IP has exceeded `limit` requests in `window` seconds."""
    key = f'rl:scan:{ip}'
    count = cache.get(key, 0)
    if count >= limit:
        return False
    cache.set(key, count + 1, timeout=window)
    return True


def _current_month_key():
    return datetime.now().strftime('%Y-%m')


def _call_veryfi(uploaded_file):
    """POST the file to Veryfi synchronously. Returns (response_json, raw_status_code)."""
    veryfi_url = f"{settings.VERYFI_API_BASE_URL.rstrip('/')}/api/v8/partner/documents/"
    headers = {
        'CLIENT-ID': settings.VERYFI_API_CLIENT_ID,
        'AUTHORIZATION': f'apikey {settings.VERYFI_API_USERNAME}:{settings.VERYFI_API_KEY}',
    }
    file_bytes = uploaded_file.read()
    files = {'file': (uploaded_file.name, file_bytes, uploaded_file.content_type)}
    data = {'async_mode': 'false'}

    response = requests.post(
        veryfi_url,
        headers=headers,
        files=files,
        data=data,
        timeout=30,
    )
    return response.json() if response.headers.get('Content-Type', '').startswith('application/json') else {}, response.status_code


def _parse_date(raw):
    """Parse Veryfi date string (YYYY-MM-DD or MM/DD/YYYY) to a date object."""
    if not raw:
        return None
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(raw[:10], fmt[:len(raw[:10])]).date()
        except ValueError:
            continue
    return None


class ReceiptScanView(APIView):
    permission_classes = [PrototypeAppKeyPermission]
    parser_classes = [MultiPartParser]

    def post(self, request):
        ip = _get_client_ip(request)

        # --- Rate limit ---
        if not _check_rate_limit(ip):
            logger.warning('[SCAN] rate limit exceeded ip=%s', ip)
            return Response(
                {'error': 'Too many requests. Please wait before scanning again.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # --- File presence ---
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'error': 'No file provided. Send the image as multipart field "file".'}, status=status.HTTP_400_BAD_REQUEST)

        # --- MIME type ---
        content_type = uploaded_file.content_type or ''
        if content_type not in ALLOWED_MIME_TYPES:
            return Response(
                {'error': f'Unsupported file type "{content_type}". Send a JPEG, PNG, WebP, GIF, or HEIC image.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- File size ---
        file_size = uploaded_file.size
        if file_size < MIN_FILE_SIZE:
            return Response({'error': f'File too small ({file_size} bytes). Minimum is {MIN_FILE_SIZE} bytes.'}, status=status.HTTP_400_BAD_REQUEST)
        if file_size > MAX_FILE_SIZE:
            return Response({'error': f'File too large ({file_size / 1024 / 1024:.1f} MB). Maximum is 20 MB.'}, status=status.HTTP_400_BAD_REQUEST)

        logger.info('[SCAN] file=%s size=%d ip=%s', uploaded_file.name, file_size, ip)

        # --- Quota check ---
        month_key = _current_month_key()
        quota, _ = QuotaRecord.objects.get_or_create(month_key=month_key)
        limit = settings.EXPENSE_SCAN_MONTHLY_QUOTA
        if quota.count >= limit:
            logger.warning('[SCAN] quota exceeded month=%s count=%d', month_key, quota.count)
            return Response(
                {
                    'error': f'Monthly scan quota of {limit} documents reached.',
                    'quota': {
                        'limit': limit,
                        'used': quota.count,
                        'remaining': 0,
                        'monthKey': month_key,
                    },
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # --- Call Veryfi ---
        try:
            veryfi_data, veryfi_status = _call_veryfi(uploaded_file)
        except requests.RequestException as exc:
            logger.error('[SCAN] veryfi request error: %s', exc)
            return Response({'error': 'Receipt processing service unavailable. Please try again.'}, status=status.HTTP_502_BAD_GATEWAY)

        if veryfi_status not in (200, 201):
            logger.error('[SCAN] veryfi error status=%d body=%s', veryfi_status, veryfi_data)
            return Response({'error': 'Receipt processing failed. Please try again.'}, status=status.HTTP_502_BAD_GATEWAY)

        # --- Increment quota (atomic) ---
        QuotaRecord.objects.filter(month_key=month_key).update(count=F('count') + 1)
        quota.refresh_from_db()

        # --- Parse Veryfi response ---
        veryfi_id = str(veryfi_data.get('id', '')) or None
        vendor = veryfi_data.get('vendor', {}).get('name') if isinstance(veryfi_data.get('vendor'), dict) else veryfi_data.get('vendor')
        raw_amount = veryfi_data.get('total') or veryfi_data.get('subtotal')
        amount = float(raw_amount) if raw_amount is not None else None
        raw_date = veryfi_data.get('date') or veryfi_data.get('created_date')
        parsed_date = _parse_date(raw_date)
        veryfi_category = veryfi_data.get('category') or veryfi_data.get('default_category')

        logger.info(
            '[SCAN] success veryfi_id=%s vendor=%s amount=%s category=%s',
            veryfi_id, vendor, amount, veryfi_category,
        )

        # --- Persist scan record ---
        ReceiptScan.objects.create(
            veryfi_document_id=veryfi_id,
            vendor=vendor,
            date=parsed_date,
            amount=amount,
            veryfi_category=veryfi_category,
            image_filename=uploaded_file.name,
            raw_response=veryfi_data,
            status='success',
        )

        used = quota.count
        return Response(
            {
                'amount': amount,
                'date': parsed_date.isoformat() if parsed_date else None,
                'vendor': vendor,
                'veryfiCategory': veryfi_category,
                'veryfiDocumentId': veryfi_id,
                'quota': {
                    'limit': limit,
                    'used': used,
                    'remaining': max(0, limit - used),
                    'monthKey': month_key,
                },
            },
            status=status.HTTP_200_OK,
        )


class QuotaView(APIView):
    permission_classes = [PrototypeAppKeyPermission]

    def get(self, request):
        month_key = _current_month_key()
        quota, _ = QuotaRecord.objects.get_or_create(month_key=month_key)
        limit = settings.EXPENSE_SCAN_MONTHLY_QUOTA
        return Response(
            {
                'limit': limit,
                'used': quota.count,
                'remaining': max(0, limit - quota.count),
                'monthKey': month_key,
            },
            status=status.HTTP_200_OK,
        )
