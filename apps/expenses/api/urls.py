from django.urls import path

from apps.expenses.api.views.receipt_scan import (
    QuotaView,
    ReceiptScanJobCreateView,
    ReceiptScanJobStatusView,
    ReceiptScanView,
)

urlpatterns = [
    path('scan-receipt/', ReceiptScanView.as_view(), name='scan_receipt'),
    path('scan-receipt/jobs/', ReceiptScanJobCreateView.as_view(), name='scan_receipt_job_create'),
    path('scan-receipt/jobs/<uuid:job_id>/', ReceiptScanJobStatusView.as_view(), name='scan_receipt_job_status'),
    path('scan-receipt/quota/', QuotaView.as_view(), name='scan_receipt_quota'),
]
