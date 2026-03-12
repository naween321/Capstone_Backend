from django.urls import path, include


urlpatterns = [
    path('authentication/', include('apps.authentication.api.urls')),
    path('commons/', include('apps.commons.urls')),
    path('expenses/', include('apps.expenses.api.urls')),
    path('notifications/', include('apps.notifications.api.urls')),
]
