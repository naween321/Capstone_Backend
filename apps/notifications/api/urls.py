from django.urls import path

from apps.notifications.api.views.token import DailyQuoteView, DeviceTokenView
from apps.commons.views import AnalyzeMoodView

urlpatterns = [
    path('token/', DeviceTokenView.as_view(), name='device_token'),
    path('daily-quote/', DailyQuoteView.as_view(), name='daily_quote'),
    path('analyze-mood/', AnalyzeMoodView.as_view(), name='analyze-mood'),
]
