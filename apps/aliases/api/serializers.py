from rest_framework import serializers

from apps.aliases.models import (
    VALID_CATEGORIES,
    AliasDonation,
    StoreAlias,
    UserPreference,
)


# ── Alias Lookup ─────────────────────────────────────────────────────

class LineItemInputSerializer(serializers.Serializer):
    receiptAcronym = serializers.CharField(max_length=255)
    price = serializers.FloatField(required=False, default=0.0)


class AliasLookupRequestSerializer(serializers.Serializer):
    lineItems = LineItemInputSerializer(many=True)
    vendorName = serializers.CharField(max_length=255, required=False, default='')


class AlternativeSerializer(serializers.Serializer):
    decodedName = serializers.CharField()
    category = serializers.CharField()
    similarity = serializers.FloatField()


class AliasLookupResultSerializer(serializers.Serializer):
    receiptAcronym = serializers.CharField()
    matchType = serializers.CharField(source='match_type', allow_null=True)
    decodedName = serializers.CharField(source='decoded_name', allow_null=True)
    category = serializers.CharField(allow_null=True)
    similarity = serializers.FloatField(allow_null=True)
    alternatives = AlternativeSerializer(many=True)



# ── Store Alias ──────────────────────────────────────────────────────

class StoreAliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreAlias
        fields = ['id', 'vendor_name', 'category', 'source', 'created_at', 'updated_at']
        read_only_fields = ['id', 'source', 'created_at', 'updated_at']

    def validate_category(self, value):
        upper = value.strip().upper()
        if upper not in VALID_CATEGORIES:
            raise serializers.ValidationError(f'Invalid category. Must be one of: {VALID_CATEGORIES}')
        return upper


# ── Categorize All ───────────────────────────────────────────────────

class CategorizeLineItemSerializer(serializers.Serializer):
    receiptAcronym = serializers.CharField(max_length=255)
    decodedName = serializers.CharField(max_length=255)
    category = serializers.CharField(max_length=50)

    def validate_category(self, value):
        upper = value.strip().upper()
        if upper not in VALID_CATEGORIES:
            raise serializers.ValidationError(f'Invalid category. Must be one of: {VALID_CATEGORIES}')
        return upper


class CategorizeAllRequestSerializer(serializers.Serializer):
    vendorName = serializers.CharField(max_length=255, required=False, default='')
    lineItems = CategorizeLineItemSerializer(many=True)


# ── Alias Donation ───────────────────────────────────────────────────

class AliasDonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AliasDonation
        fields = [
            'id', 'donation_type', 'receipt_acronym', 'decoded_name',
            'category', 'status', 'donated_by', 'reviewed_by',
            'reviewed_at', 'rejection_reason', 'donor_trust_score',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'donated_by', 'reviewed_by', 'reviewed_at',
            'donor_trust_score', 'created_at', 'updated_at',
        ]


class DonationRejectSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(max_length=1000, required=False, default='')


# ── User Preference ──────────────────────────────────────────────────

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ['donate_aliases']
