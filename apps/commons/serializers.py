from rest_framework import serializers
from .models import DeviceToken

VALID_DAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'platform', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at', 'is_active']

    def create(self, validated_data):
        token, _ = DeviceToken.objects.update_or_create(
            token=validated_data['token'],
            defaults={**validated_data, 'is_active': True}
        )
        return token


class SendNotificationSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    body = serializers.CharField()
    data = serializers.DictField(child=serializers.CharField(), required=False)
    user_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )


class ScheduleTodoSerializer(serializers.Serializer):
    notification = serializers.CharField()
    date_time = serializers.DateTimeField()
    device_id = serializers.IntegerField()


class MoodHistorySerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    mood = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    description = serializers.CharField(required=False, allow_blank=True)
    energy = serializers.CharField()


class AnalyzeMoodSerializer(serializers.Serializer):
    mood = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    energy = serializers.CharField(required=False, allow_blank=True)
    tags = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    persistence = MoodHistorySerializer(many=True)


class MoodReminderRuleSerializer(serializers.Serializer):
    time = serializers.TimeField(format="%H:%M", input_formats=["%H:%M"])
    days = serializers.ListField(
        child=serializers.ChoiceField(choices=list(VALID_DAYS)),
        min_length=1,
        max_length=7,
    )
    device_id = serializers.IntegerField()

    def validate_days(self, value):
        normalized = [day.lower() for day in value]
        invalid = [day for day in normalized if day not in VALID_DAYS]
        if invalid:
            raise serializers.ValidationError(
                f"Invalid day(s): {', '.join(invalid)}. Must be full lowercase day names."
            )
        if len(normalized) != len(set(normalized)):
            raise serializers.ValidationError("Duplicate days are not allowed.")
        return normalized
