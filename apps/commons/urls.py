from django.urls import path
from .views import DeviceTokenView, ScheduleTodoView, DailyQuoteView, AnalyzeMoodView
print("Hello")

urlpatterns = [
    path('token/', DeviceTokenView.as_view(), name='register-token'),
    path('schedule/todo/', ScheduleTodoView.as_view(), name='schedule_todo'),
    path('daily-quote/', DailyQuoteView.as_view(), name='daily_quote'),
    path('analyze-mood/', AnalyzeMoodView.as_view(), name='analyze-mood')
]

