from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.aliases.api.serializers import (
    AliasLookupRequestSerializer,
    AliasLookupResultSerializer,
)
from apps.aliases.services.fuzzy_match import lookup_aliases_batch
from apps.expenses.api.permissions import PrototypeAppKeyPermission


class AliasLookupView(APIView):
    """POST /api/aliases/lookup/

    Accepts a list of receipt line items and returns suggested
    display names, categories, and fuzzy-match alternatives.

    Only global alias tiers are searched here. Per-install corrections
    live in local SQLite and are applied client-side before this call.
    """
    permission_classes = [PrototypeAppKeyPermission]

    def post(self, request):
        ser = AliasLookupRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        line_items = ser.validated_data['lineItems']
        vendor_name = ser.validated_data.get('vendorName', '')

        results = lookup_aliases_batch(line_items, vendor_name=vendor_name)

        out = AliasLookupResultSerializer(results, many=True)
        return Response({'results': out.data}, status=status.HTTP_200_OK)
