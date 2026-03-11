from django.urls import path

from apps.expenses.api.views.receipt_scan import QuotaView, ReceiptScanView

urlpatterns = [
    path('scan-receipt/', ReceiptScanView.as_view(), name='scan_receipt'),
    path('scan-receipt/quota/', QuotaView.as_view(), name='scan_receipt_quota'),
]
