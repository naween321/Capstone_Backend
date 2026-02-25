from django.urls import path, include


urlpatterns = [
    path('authentication/', include('apps.authentication.api.urls')),
]
