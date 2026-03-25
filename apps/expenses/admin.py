from django.contrib import admin

from .models import QuotaRecord, ReceiptScan, ReceiptScanJob


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


@admin.register(ReceiptScanJob)
class ReceiptScanJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'progress', 'image_filename', 'updated_at')
    list_filter = ('status',)
    search_fields = ('id', 'image_filename')
    readonly_fields = (
        'id',
        'status',
        'progress',
        'error_message',
        'result',
        'image_filename',
        'mime_type',
        'stored_file_path',
        'created_at',
        'updated_at',
    )
