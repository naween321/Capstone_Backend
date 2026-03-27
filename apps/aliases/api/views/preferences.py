from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.aliases.api.permissions import AppInstancePermission
from apps.aliases.api.serializers import UserPreferenceSerializer
from apps.aliases.models import UserPreference
from apps.expenses.api.permissions import PrototypeAppKeyPermission


class UserPreferenceView(APIView):
    """GET / PATCH  /api/aliases/preferences/"""
    permission_classes = [PrototypeAppKeyPermission, AppInstancePermission]

    def get(self, request):
        pref, _ = UserPreference.objects.get_or_create(app_instance=request.app_instance)
        return Response(UserPreferenceSerializer(pref).data)

    def patch(self, request):
        pref, _ = UserPreference.objects.get_or_create(app_instance=request.app_instance)
        ser = UserPreferenceSerializer(pref, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)
