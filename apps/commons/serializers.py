from rest_framework import serializers
from .models import DeviceToken


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


class AnalyzeMoodSerializer(serializers.Serializer):
    mood = serializers.CharField()
    description = serializers.CharField()