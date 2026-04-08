from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from groq import Groq
from drf_spectacular.utils import extend_schema

from .models import DeviceToken
from .serializers import DeviceTokenSerializer, ScheduleTodoSerializer, AnalyzeMoodSerializer, MoodReminderRuleSerializer
from .firebase import send_multicast_notification, send_scheduled_notification
from .scheduler import upsert_mood_reminder


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


class AnalyzeMoodView(APIView):

    @extend_schema(
        request=AnalyzeMoodSerializer,
        description="Analyze user mood and return a comforting message"
    )  # This extend schema is just for the Swagger view to display DTO
    def post(self, *args, **kwargs):
        ser = AnalyzeMoodSerializer(data=self.request.data)
        prompt_for = self.request.query_params.get('for')
        if ser.is_valid():
            client = Groq(api_key=settings.GROQ_API_KEY)
            mood = ser.validated_data.get('mood')
            description = ser.validated_data.get('description')
            persistence = ser.validated_data.get("persistence")
            energy = ser.validated_data.get('energy')
            if prompt_for == "main_page":
                prompt = f"""
                You are an insightful and supportive mental wellness assistant.

                User Mood History:
                {persistence}

                Task:
                Analyze the user's overall emotional patterns based on their mood history.

                Guidelines:
                - Identify trends (e.g., improving, declining, fluctuating).
                - Highlight any noticeable patterns (e.g., frequent stress, consistent happiness, mood swings).
                - Mention possible triggers if they can be inferred from patterns.
                - Keep the tone neutral, supportive, and non-judgmental.
                - Do NOT provide medical or clinical advice.
                - Keep the response concise (80–120 words).
                - Focus on insights, not just repeating the data.

                Output Format:
                - Overall Trend:
                - Key Observations:
                - Gentle Suggestion:
                """
            else:
                prompt = f"""
                You are a supportive and empathetic mental health assistant.
    
                User Information:
                - Current Mood: {mood}
                - Energy Level: {energy}
                - User Description: {description}
    
                Recent Mood History (last few entries):
                {persistence}
    
                Instructions:
                - Acknowledge the user's current feelings.
                - Consider patterns from their recent mood history.
                - Respond in a warm, caring, and encouraging tone.
                - Do NOT sound robotic or overly clinical.
                - Keep the response concise (50–60 words).
                - Offer gentle reassurance or a small helpful suggestion if appropriate.
    
                Response:
            """
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
            )
            return Response({
                "message": chat_completion.choices[0].message.content
            })
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


DAY_MAP = {
    "monday": "1", "tuesday": "2", "wednesday": "3",
    "thursday": "4", "friday": "5", "saturday": "6", "sunday": "0",
}


class MoodReminderRuleView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=MoodReminderRuleSerializer,
        description="Analyze user mood and return a comforting message"
    )
    def post(self, request):
        """
        Expected payload:
        {
            "time": "20:30",           // HH:MM in user's local time (handle TZ server-side as needed)
            "days": ["monday", "wednesday", "friday"]
        }
        """
        serializer = MoodReminderRuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        time_obj = serializer.validated_data["time"]
        days = serializer.validated_data["days"]
        device_id = serializer.validated_data["device_id"]

        days_of_week = ",".join(DAY_MAP[d] for d in days)
        if not days_of_week:
            return Response({"error": "No valid days provided."}, status=400)

        upsert_mood_reminder(
            device_id=device_id,
            hour=time_obj.hour,
            minute=time_obj.minute,
            days_of_week=days_of_week,
        )
        return Response({"message": "Reminder scheduled."}, status=status.HTTP_200_OK)
