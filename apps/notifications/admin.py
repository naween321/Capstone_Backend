from django.contrib import admin

from apps.notifications.models import DeviceToken


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'platform', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
