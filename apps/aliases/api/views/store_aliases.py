from rest_framework import generics

from apps.aliases.api.serializers import StoreAliasSerializer
from apps.aliases.models import StoreAlias
from apps.expenses.api.permissions import PrototypeAppKeyPermission


class StoreAliasListCreateView(generics.ListCreateAPIView):
    """GET / POST  /api/aliases/stores/"""
    serializer_class = StoreAliasSerializer
    permission_classes = [PrototypeAppKeyPermission]
    queryset = StoreAlias.objects.all()

    def perform_create(self, serializer):
        vendor = serializer.validated_data['vendor_name']
        upper = vendor.strip().upper()

        existing = StoreAlias.objects.filter(vendor_name_upper=upper).first()
        if existing:
            existing.category = serializer.validated_data['category']
            existing.vendor_name = vendor
            existing.save()
            serializer.instance = existing
        else:
            user = self.request.user if self.request.user.is_authenticated else None
            serializer.save(created_by=user, source='user')


class StoreAliasDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET / PATCH / DELETE  /api/aliases/stores/<pk>/"""
    serializer_class = StoreAliasSerializer
    permission_classes = [PrototypeAppKeyPermission]
    queryset = StoreAlias.objects.all()
