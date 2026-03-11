from django.contrib import admin

from .models import QuotaRecord, ReceiptScan


@admin.register(ReceiptScan)
class ReceiptScanAdmin(admin.ModelAdmin):
    list_display = ('id', 'veryfi_document_id', 'vendor', 'amount', 'date', 'veryfi_category', 'status', 'created_at')
    list_filter = ('status', 'veryfi_category')
    search_fields = ('vendor', 'veryfi_document_id')
    readonly_fields = ('raw_response', 'created_at', 'updated_at')


@admin.register(QuotaRecord)
class QuotaRecordAdmin(admin.ModelAdmin):
    list_display = ('month_key', 'count', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
