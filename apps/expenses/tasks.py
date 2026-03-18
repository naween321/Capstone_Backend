import logging
import os
from datetime import datetime

import requests
from celery import shared_task
from django.conf import settings
from django.db.models import F

from apps.expenses.models import QuotaRecord, ReceiptScan, ReceiptScanJob

logger = logging.getLogger(__name__)


def _parse_date(raw):
    if not raw:
        return None
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(raw[:10], fmt[: len(raw[:10])]).date()
        except ValueError:
            continue
    return None


def _call_veryfi_from_path(file_path, original_filename, content_type):
    veryfi_url = f"{settings.VERYFI_API_BASE_URL.rstrip('/')}/api/v8/partner/documents/"
    headers = {
        'CLIENT-ID': settings.VERYFI_API_CLIENT_ID,
        'AUTHORIZATION': f"apikey {settings.VERYFI_API_USERNAME}:{settings.VERYFI_API_KEY}",
    }

    with open(file_path, 'rb') as f:
        files = {'file': (original_filename, f.read(), content_type)}
        response = requests.post(
            veryfi_url,
            headers=headers,
            files=files,
            timeout=30,
        )

    data = (
        response.json()
        if response.headers.get('Content-Type', '').startswith('application/json')
        else {}
    )
    return data, response.status_code


@shared_task(bind=True)
def process_receipt_scan_job(self, job_id):
    try:
        job = ReceiptScanJob.objects.get(id=job_id)
    except ReceiptScanJob.DoesNotExist:
        logger.error('[SCAN JOB] Missing job id=%s', job_id)
        return

    month_key = datetime.now().strftime('%Y-%m')
    limit = settings.EXPENSE_SCAN_MONTHLY_QUOTA

    try:
        job.status = ReceiptScanJob.Status.UPLOADING
        job.progress = 0.2
        job.save(update_fields=['status', 'progress', 'updated_at'])

        quota, _ = QuotaRecord.objects.get_or_create(month_key=month_key)
        if quota.count >= limit:
            job.status = ReceiptScanJob.Status.FAILED
            job.progress = 1.0
            job.error_message = f'Monthly scan quota of {limit} documents reached.'
            job.save(update_fields=['status', 'progress', 'error_message', 'updated_at'])
            return

        job.status = ReceiptScanJob.Status.PROCESSING
        job.progress = 0.55
        job.save(update_fields=['status', 'progress', 'updated_at'])

        veryfi_data, veryfi_status = _call_veryfi_from_path(
            job.stored_file_path,
            job.image_filename or os.path.basename(job.stored_file_path),
            job.mime_type or 'image/jpeg',
        )

        if veryfi_status not in (200, 201):
            logger.error('[SCAN JOB] veryfi error status=%d body=%s', veryfi_status, veryfi_data)
            job.status = ReceiptScanJob.Status.FAILED
            job.progress = 1.0
            job.error_message = 'Receipt processing failed. Please try again.'
            job.save(update_fields=['status', 'progress', 'error_message', 'updated_at'])
            return

        job.status = ReceiptScanJob.Status.RECEIVING
        job.progress = 0.82
        job.save(update_fields=['status', 'progress', 'updated_at'])

        QuotaRecord.objects.filter(month_key=month_key).update(count=F('count') + 1)
        quota.refresh_from_db()

        veryfi_id = str(veryfi_data.get('id', '')) or None
        vendor = (
            veryfi_data.get('vendor', {}).get('name')
            if isinstance(veryfi_data.get('vendor'), dict)
            else veryfi_data.get('vendor')
        )
        raw_amount = veryfi_data.get('total') or veryfi_data.get('subtotal')
        amount = float(raw_amount) if raw_amount is not None else None
        raw_date = veryfi_data.get('date') or veryfi_data.get('created_date')
        parsed_date = _parse_date(raw_date)
        veryfi_category = veryfi_data.get('category') or veryfi_data.get('default_category')

        ReceiptScan.objects.create(
            veryfi_document_id=veryfi_id,
            vendor=vendor,
            date=parsed_date,
            amount=amount,
            veryfi_category=veryfi_category,
            image_filename=job.image_filename,
            raw_response=veryfi_data,
            status='success',
        )

        used = quota.count
        result_payload = {
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
        }

        job.status = ReceiptScanJob.Status.COMPLETED
        job.progress = 1.0
        job.result = result_payload
        job.error_message = ''
        job.save(update_fields=['status', 'progress', 'result', 'error_message', 'updated_at'])

    except requests.RequestException as exc:
        logger.error('[SCAN JOB] veryfi request error job=%s err=%s', job_id, exc)
        job.status = ReceiptScanJob.Status.FAILED
        job.progress = 1.0
        job.error_message = 'Receipt processing service unavailable. Please try again.'
        job.save(update_fields=['status', 'progress', 'error_message', 'updated_at'])
    except Exception as exc:
        logger.exception('[SCAN JOB] unexpected error job=%s err=%s', job_id, exc)
        job.status = ReceiptScanJob.Status.FAILED
        job.progress = 1.0
        job.error_message = 'Unexpected scan error. Please try again.'
        job.save(update_fields=['status', 'progress', 'error_message', 'updated_at'])
    finally:
        try:
            if job.stored_file_path and os.path.exists(job.stored_file_path):
                os.remove(job.stored_file_path)
        except Exception as cleanup_exc:
            logger.warning('[SCAN JOB] cleanup failed job=%s err=%s', job_id, cleanup_exc)
