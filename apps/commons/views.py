from django.conf import settings

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from groq import Groq
from drf_spectacular.utils import extend_schema

from .models import DeviceToken, GratitudePrompt
from .serializers import (
    DeviceTokenSerializer,
    AnalyzeMoodSerializer,
    GratitudePreferenceSerializer,
)
from .firebase import send_multicast_notification
from .tasks import fetch_daily_gratitude_prompt


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


class GratitudePreferenceView(APIView):
    """Persist a device's gratitude reminder mode + IANA timezone.

    The hourly dispatcher uses these fields to know which devices to push
    today's prompt to and at what local hour.
    """
    permission_classes = [AllowAny, ]

    def post(self, request):
        ser = GratitudePreferenceSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        token = ser.validated_data['token']
        try:
            device = DeviceToken.objects.get(token=token)
        except DeviceToken.DoesNotExist:
            return Response(
                {"detail": "Unknown device token."},
                status=status.HTTP_404_NOT_FOUND,
            )

        device.gratitude_mode = ser.validated_data['mode']
        tz = ser.validated_data.get('timezone')
        if tz:
            device.timezone = tz
        device.save(update_fields=['gratitude_mode', 'timezone', 'updated_at'])
        return Response(
            {
                "token": device.token[:20] + "...",
                "gratitude_mode": device.gratitude_mode,
                "timezone": device.timezone,
            },
            status=status.HTTP_200_OK,
        )


class GratitudePromptView(APIView):
    """Return today's cached gratitude prompt for the in-app fetch path.

    Matches the frontend's existing ``$baseUrl/api/gratitude/prompt/`` call.
    Triggers a synchronous Groq fetch as a fallback if today's row isn't
    cached yet (e.g., the daily celery task hasn't run yet on a fresh DB).
    """
    permission_classes = [AllowAny, ]

    def get(self, request):
        from django.utils import timezone as dj_timezone

        today = dj_timezone.now().date()
        row = GratitudePrompt.objects.filter(date=today).first()
        if row and row.prompt:
            return Response({"date": str(today), "prompt": row.prompt})

        # Fall back: synchronously fetch + cache so the user always gets a prompt.
        result = fetch_daily_gratitude_prompt()
        prompt = (result or {}).get("prompt") or ""
        if not prompt:
            latest = GratitudePrompt.objects.order_by('-date').first()
            prompt = latest.prompt if latest else ""
        return Response({"date": str(today), "prompt": prompt})


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
