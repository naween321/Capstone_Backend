from django.urls import path

from apps.notifications.api.views.token import DailyQuoteView, DeviceTokenView
from apps.commons.views import ScheduleTodoView, AnalyzeMoodView, MoodReminderRuleView

urlpatterns = [
    path('token/', DeviceTokenView.as_view(), name='device_token'),
    path('daily-quote/', DailyQuoteView.as_view(), name='daily_quote'),
    path('schedule/todo/', ScheduleTodoView.as_view(), name='schedule_todo'),
    path('analyze-mood/', AnalyzeMoodView.as_view(), name='analyze-mood'),
    path('schedule/add-mood/', MoodReminderRuleView.as_view(), name='schedule_add_mood'),
]
