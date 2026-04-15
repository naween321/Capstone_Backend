from django.urls import path, include

from apps.commons.views import GratitudePromptView


urlpatterns = [
    path('authentication/', include('apps.authentication.api.urls')),
    path('commons/', include('apps.commons.urls')),
    path('expenses/', include('apps.expenses.api.urls')),
    path('notifications/', include('apps.notifications.api.urls')),
    path('aliases/', include('apps.aliases.api.urls')),
    path('gratitude/prompt/', GratitudePromptView.as_view(), name='gratitude-prompt'),
]
