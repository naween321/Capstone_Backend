import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.aliases.api.permissions import AppInstancePermission
from apps.aliases.api.serializers import CategorizeAllRequestSerializer
from apps.aliases.models import (
    AliasDonation,
    GlobalProductAlias,
    StoreAlias,
    UserPreference,
)
from apps.expenses.api.permissions import PrototypeAppKeyPermission

logger = logging.getLogger(__name__)


class CategorizeAllView(APIView):
    """POST /api/aliases/categorize-all/

    Reads the instance's donate_aliases preference, optionally submits
    AliasDonation entries for the shared pipeline, and upserts a StoreAlias.

    Per-install alias corrections live exclusively in local SQLite on-device —
    no UserProductAlias table exists on the backend. The only server-side
    state this endpoint writes is donations (when opted in) and the store alias.
    """
    permission_classes = [PrototypeAppKeyPermission, AppInstancePermission]

    def post(self, request):
        ser = CategorizeAllRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        line_items = ser.validated_data['lineItems']
        vendor_name = ser.validated_data.get('vendorName', '')
        instance = request.app_instance

        donated = 0

        # Check if this instance has opted in to donate aliases.
        pref, _ = UserPreference.objects.get_or_create(app_instance=instance)
        should_donate = pref.donate_aliases

        for item in line_items:
            acronym = item['receiptAcronym']
            decoded = item['decodedName']
            category = item['category']
            upper = acronym.strip().upper()

            # ── Donate to shared pipeline ────────────────────────────
            if should_donate:
                # Skip if alias already exists globally (exact match).
                exists_global = GlobalProductAlias.objects.filter(
                    alias_text_upper=upper,
                ).exists()
                # Skip if already pending in the donation queue.
                exists_pending = AliasDonation.objects.filter(
                    receipt_acronym=upper,
                    decoded_name=decoded,
                    status=AliasDonation.Status.PENDING,
                ).exists()

                if not exists_global and not exists_pending:
                    AliasDonation.objects.create(
                        donation_type=AliasDonation.DonationType.PRODUCT,
                        donated_by=instance,
                        receipt_acronym=acronym,
                        decoded_name=decoded,
                        category=category,
                    )
                    donated += 1

        # ── Upsert StoreAlias ────────────────────────────────────────
        store_saved = False
        if vendor_name:
            vendor_upper = vendor_name.strip().upper()
            categories = [item['category'] for item in line_items]
            if categories:
                most_common = max(set(categories), key=categories.count)
                _, store_saved = StoreAlias.objects.update_or_create(
                    vendor_name_upper=vendor_upper,
                    defaults={
                        'vendor_name': vendor_name,
                        'category': most_common,
                        'source': 'user',
                        'created_by': instance,
                    },
                )

                # Donate store alias too if enabled.
                if should_donate and store_saved:
                    store_pending = AliasDonation.objects.filter(
                        donation_type=AliasDonation.DonationType.STORE,
                        receipt_acronym=vendor_upper,
                        status=AliasDonation.Status.PENDING,
                    ).exists()
                    if not store_pending:
                        AliasDonation.objects.create(
                            donation_type=AliasDonation.DonationType.STORE,
                            donated_by=instance,
                            receipt_acronym=vendor_name,
                            decoded_name=vendor_name,
                            category=most_common,
                        )

        return Response({
            'donated': donated,
            'storeSaved': bool(store_saved),
        }, status=status.HTTP_200_OK)
