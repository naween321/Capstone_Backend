from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.commons.models import DeviceToken  # adjust import if needed


class TestDeviceTokenView(APITestCase):

    def setUp(self):
        self.url = reverse("register-token")  # update if your URL name differs

        self.valid_payload = {
            "token": "sample_fcm_token_123",
            "platform": "android"
        }

    def test_register_device_token_success(self):
        """Test successful creation of a new device token"""
        response = self.client.post(self.url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DeviceToken.objects.count(), 1)

        token_obj = DeviceToken.objects.first()
        self.assertEqual(token_obj.token, self.valid_payload["token"])
        self.assertEqual(token_obj.platform, self.valid_payload["platform"])
        self.assertTrue(token_obj.is_active)

    def test_register_device_token_invalid_data(self):
        """Test validation error when token is missing"""
        invalid_payload = {
            "platform": "android"
        }

        response = self.client.post(self.url, invalid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DeviceToken.objects.count(), 0)

    def test_register_same_token_updates_instead_of_creating(self):
        """Same token should update existing record, not create a duplicate"""

        DeviceToken.objects.create(
            token="sample_fcm_token_123",
            platform="android",
            is_active=True
        )

        response = self.client.post(self.url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DeviceToken.objects.count(), 1)

        token_obj = DeviceToken.objects.first()
        self.assertEqual(token_obj.platform, "android")  # updated
        self.assertTrue(token_obj.is_active)  # reactivated

    def test_reactivate_existing_token(self):
        """Inactive token should become active again"""

        token_obj = DeviceToken.objects.create(
            token="sample_fcm_token_123",
            platform="android",
            is_active=True
        )

        response = self.client.post(self.url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        token_obj.refresh_from_db()
        self.assertTrue(token_obj.is_active)

    def test_unregister_device_token_success(self):
        """Test deactivating a device token"""

        token_obj = DeviceToken.objects.create(
            token="sample_fcm_token_123",
            platform="android",
            is_active=True
        )

        response = self.client.delete(
            self.url,
            {"token": token_obj.token},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token_obj.refresh_from_db()
        self.assertFalse(token_obj.is_active)

    def test_unregister_device_token_not_found(self):
        """Deleting a non-existing token should still return success"""

        response = self.client.delete(
            self.url,
            {"token": "non_existing_token"},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Token deactivated.")

    def test_delete_without_token(self):
        """Edge case: delete called without token"""

        response = self.client.delete(
            self.url,
            {},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Token deactivated.")