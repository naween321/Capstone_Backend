from django.urls import path
from .views import (
    DeviceTokenView,
    DailyQuoteView,
    AnalyzeMoodView,
    GratitudePreferenceView,
)

urlpatterns = [
    path('token/', DeviceTokenView.as_view(), name='register-token'),
    path('daily-quote/', DailyQuoteView.as_view(), name='daily_quote'),
    path('analyze-mood/', AnalyzeMoodView.as_view(), name='analyze-mood'),
    path('gratitude-preference/', GratitudePreferenceView.as_view(), name='gratitude-preference'),
]

