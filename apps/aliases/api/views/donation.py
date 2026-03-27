from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.aliases.api.serializers import (
    AliasDonationSerializer,
    DonationRejectSerializer,
)
from apps.aliases.models import AliasDonation, GlobalProductAlias, StoreAlias


class DonationListView(generics.ListAPIView):
    """GET /api/aliases/donations/?status=pending"""
    serializer_class = AliasDonationSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        qs = AliasDonation.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class DonationApproveView(APIView):
    """POST /api/aliases/donations/<pk>/approve/

    Promotes the donated alias into the shared GlobalProductAlias
    (or StoreAlias) table.
    """
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            donation = AliasDonation.objects.get(pk=pk)
        except AliasDonation.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if donation.status != AliasDonation.Status.PENDING:
            return Response(
                {'detail': f'Donation is already {donation.status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        upper = donation.receipt_acronym.strip().upper()

        if donation.donation_type == AliasDonation.DonationType.PRODUCT:
            _, created = GlobalProductAlias.objects.get_or_create(
                canonical_name=donation.decoded_name,
                alias_text_upper=upper,
                defaults={
                    'alias_text': donation.receipt_acronym,
                    'category': donation.category,
                    'source': 'donation',
                },
            )
            if not created:
                donation.status = AliasDonation.Status.DUPLICATE
                donation.reviewed_by = request.user
                donation.reviewed_at = timezone.now()
                donation.save()
                return Response({'detail': 'Alias already exists; marked duplicate.'})
        else:
            # Store donation
            StoreAlias.objects.update_or_create(
                vendor_name_upper=upper,
                defaults={
                    'vendor_name': donation.decoded_name,
                    'category': donation.category,
                    'source': 'donation',
                },
            )

        donation.status = AliasDonation.Status.APPROVED
        donation.reviewed_by = request.user
        donation.reviewed_at = timezone.now()
        donation.save()

        return Response({'detail': 'Donation approved and merged.'})


class DonationRejectView(APIView):
    """POST /api/aliases/donations/<pk>/reject/"""
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            donation = AliasDonation.objects.get(pk=pk)
        except AliasDonation.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if donation.status != AliasDonation.Status.PENDING:
            return Response(
                {'detail': f'Donation is already {donation.status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ser = DonationRejectSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        donation.status = AliasDonation.Status.REJECTED
        donation.rejection_reason = ser.validated_data.get('rejection_reason', '')
        donation.reviewed_by = request.user
        donation.reviewed_at = timezone.now()
        donation.save()

        return Response({'detail': 'Donation rejected.'})
