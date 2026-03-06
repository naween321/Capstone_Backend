from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from groq import Groq

from .models import DeviceToken
from .serializers import DeviceTokenSerializer, ScheduleTodoSerializer
from .firebase import send_multicast_notification, send_scheduled_notification


class DeviceTokenView(APIView):
    permission_classes = [AllowAny, ]

    def post(self, request):
        """Register or update a device FCM token."""
        serializer = DeviceTokenSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Unregister a device token."""
        token = request.data.get('token')
        DeviceToken.objects.filter(token=token).update(is_active=False)
        return Response({"detail": "Token deactivated."}, status=status.HTTP_200_OK)


@api_view(['POST'])
def send_to_self(request):
    """Let a user send a test notification to their own devices."""
    tokens = list(
        DeviceToken.objects.filter(is_active=True)
        .values_list('token', flat=True)
    )
    if not tokens:
        return Response({"detail": "No tokens registered."}, status=404)

    result = send_multicast_notification(
        tokens,
        title=request.data.get('title', 'Test Notification'),
        body=request.data.get('body', 'Hello from DRF!'),
    )
    return Response(result)


class ScheduleTodoView(APIView):
    permission_classes = [AllowAny, ]

    def post(self, *args, **kwargs):
        ser = ScheduleTodoSerializer(data=self.request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        data = ser.validated_data

        date_time = data["date_time"]
        if timezone.is_naive(date_time):
            date_time = timezone.make_aware(date_time)  # attaches Django's current TZ

        notify_at = date_time - timedelta(minutes=10)
        print(f"Scheduling notification at: {notify_at}")

        task = send_scheduled_notification.apply_async(
            kwargs={
                "device_id": data["device_id"],
                "title": "Todo Task Reminder",
                "notification": data["notification"]
            },
            eta=notify_at,
        )

        return Response(
            {
                "detail": "Notification scheduled.",
                "task_id": task.id,
                "todo_starts_at": data["date_time"],
                "notify_at": notify_at,
            },
            status=status.HTTP_201_CREATED,
        )


class DailyQuoteView(APIView):
    def get(self, *args, **kwargs):
        client = Groq(api_key=settings.GROQ_API_KEY)

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user",
                 "content": "Give new motivational quote everytime from 100 quotes. "
                            "Should be totally different. Don't give Author's name. Do not start with 'believe'"}
            ],
            model="llama-3.3-70b-versatile",  # or other available models
        )
        return Response({
            "quote": chat_completion.choices[0].message.content
        })
