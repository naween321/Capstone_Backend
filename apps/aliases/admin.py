from django.contrib import admin

from apps.aliases.models import (
    AliasDonation,
    AppInstance,
    GlobalProductAlias,
    StoreAlias,
    UserPreference,
)


@admin.register(AppInstance)
class AppInstanceAdmin(admin.ModelAdmin):
    list_display = ['instance_id', 'platform', 'is_active', 'last_seen_at', 'created_at']
    list_filter = ['platform', 'is_active']
    readonly_fields = ['instance_id', 'instance_token_hash', 'created_at', 'updated_at']
    actions = ['deactivate_instances']

    @admin.action(description='Deactivate selected instances')
    def deactivate_instances(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} instance(s) deactivated.')


@admin.register(GlobalProductAlias)
class GlobalProductAliasAdmin(admin.ModelAdmin):
    list_display = ['alias_text', 'canonical_name', 'category', 'source', 'created_at']
    list_filter = ['category', 'source']
    search_fields = ['alias_text', 'canonical_name']
    readonly_fields = ['alias_text_upper', 'created_at', 'updated_at']



@admin.register(StoreAlias)
class StoreAliasAdmin(admin.ModelAdmin):
    list_display = ['vendor_name', 'category', 'source', 'created_by', 'created_at']
    list_filter = ['category', 'source']
    search_fields = ['vendor_name']
    readonly_fields = ['vendor_name_upper', 'created_at', 'updated_at']


@admin.register(AliasDonation)
class AliasDonationAdmin(admin.ModelAdmin):
    list_display = [
        'receipt_acronym', 'decoded_name', 'category',
        'donation_type', 'status', 'donated_by', 'created_at',
    ]
    list_filter = ['status', 'donation_type', 'category']
    search_fields = ['receipt_acronym', 'decoded_name']
    readonly_fields = ['donor_trust_score', 'created_at', 'updated_at']
    actions = ['approve_selected', 'reject_selected']

    @admin.action(description='Approve selected donations')
    def approve_selected(self, request, queryset):
        from django.utils import timezone
        from apps.aliases.models import GlobalProductAlias as GPA

        approved = 0
        for donation in queryset.filter(status=AliasDonation.Status.PENDING):
            upper = donation.receipt_acronym.strip().upper()
            if donation.donation_type == AliasDonation.DonationType.PRODUCT:
                GPA.objects.get_or_create(
                    canonical_name=donation.decoded_name,
                    alias_text_upper=upper,
                    defaults={
                        'alias_text': donation.receipt_acronym,
                        'category': donation.category,
                        'source': 'donation',
                    },
                )
            else:
                StoreAlias.objects.update_or_create(
                    vendor_name_upper=upper,
                    defaults={
                        'vendor_name': donation.decoded_name,
                        'category': donation.category,
                        'source': 'donation',
                    },
                )
            donation.status = AliasDonation.Status.APPROVED
            donation.reviewed_by = request.user
            donation.reviewed_at = timezone.now()
            donation.save()
            approved += 1

        self.message_user(request, f'{approved} donation(s) approved.')

    @admin.action(description='Reject selected donations')
    def reject_selected(self, request, queryset):
        from django.utils import timezone

        rejected = queryset.filter(status=AliasDonation.Status.PENDING).update(
            status=AliasDonation.Status.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f'{rejected} donation(s) rejected.')


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['app_instance', 'donate_aliases', 'created_at']
    list_filter = ['donate_aliases']
    readonly_fields = ['created_at', 'updated_at']
