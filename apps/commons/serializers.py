from rest_framework import serializers
from .models import DeviceToken


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = [
            'id', 'token', 'platform', 'is_active', 'created_at',
            'gratitude_mode', 'timezone',
        ]
        read_only_fields = ['id', 'created_at', 'is_active']
        extra_kwargs = {
            'gratitude_mode': {'required': False},
            'timezone': {'required': False},
        }

    def create(self, validated_data):
        token, _ = DeviceToken.objects.update_or_create(
            token=validated_data['token'],
            defaults={**validated_data, 'is_active': True}
        )
        return token


class GratitudePreferenceSerializer(serializers.Serializer):
    token = serializers.CharField()
    mode = serializers.ChoiceField(choices=['on_release', 'scheduled'])
    timezone = serializers.CharField(required=False, allow_blank=True)


class MoodHistorySerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    mood = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    energy = serializers.CharField(required=False, allow_blank=True)


class AnalyzeMoodSerializer(serializers.Serializer):
    mood = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    energy = serializers.CharField(required=False, allow_blank=True)
    tags = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    persistence = MoodHistorySerializer(many=True)
