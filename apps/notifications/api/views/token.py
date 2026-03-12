import random

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import DeviceToken

DAILY_QUOTES = [
    "The secret of getting ahead is getting started.",
    "It does not matter how slowly you go as long as you do not stop.",
    "Our greatest weakness lies in giving up. The most certain way to succeed is always to try just one more time.",
    "You don't have to be great to start, but you have to start to be great.",
    "Believe you can and you're halfway there.",
    "Start where you are. Use what you have. Do what you can.",
    "Success is not final, failure is not fatal: it is the courage to continue that counts.",
    "The future belongs to those who believe in the beauty of their dreams.",
    "Don't watch the clock; do what it does. Keep going.",
    "Hardships often prepare ordinary people for an extraordinary destiny.",
]


class DeviceTokenView(APIView):
    def post(self, request):
        token = request.data.get('token')
        platform = request.data.get('platform', '')

        if not token:
            return Response({'error': 'token is required'}, status=400)

        device_token, created = DeviceToken.objects.update_or_create(
            token=token,
            defaults={'platform': platform},
        )

        status_code = 201 if created else 200
        return Response({'id': device_token.id, 'platform': device_token.platform}, status=status_code)


class DailyQuoteView(APIView):
    def get(self, request):
        return Response({'quote': random.choice(DAILY_QUOTES)})
