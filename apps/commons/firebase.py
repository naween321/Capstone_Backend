import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

from celery import shared_task
from celery.utils.log import get_task_logger
from .models import DeviceToken

_app = None
logger = get_task_logger(__name__)


def get_firebase_app():
    global _app
    if _app is None:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        _app = firebase_admin.initialize_app(cred)
    return _app


def send_push_notification(token: str, title: str, body: str, data: dict = None):
    """Send a push notification to a single device."""
    get_firebase_app()

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        token=token,
    )

    try:
        response = messaging.send(message)
        return {"success": True, "message_id": response}
    except messaging.UnregisteredError:
        return {"success": False, "error": "Token unregistered"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_multicast_notification(tokens: list, title: str, body: str, data: dict = None):
    """Send push notification to multiple devices."""
    get_firebase_app()

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        tokens=tokens,
    )

    response = messaging.send_each_for_multicast(message)
    return {
        "success_count": response.success_count,
        "failure_count": response.failure_count,
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_scheduled_notification(self, device_id: int, title: str, notification: str):
    """
    Scheduled task — fires at the exact eta provided by ScheduleTodoView.
    """
    try:
        device = DeviceToken.objects.get(id=device_id, is_active=True)
    except DeviceToken.DoesNotExist:
        logger.warning(f"DeviceToken id={device_id} not found or inactive. Skipping.")
        return {"success": False, "error": "device_not_found"}

    result = send_push_notification(
        token=device.token,
        title=title,
        body=notification,
    )

    # Deactivate stale token
    if not result["success"] and result.get("error") in ("unregistered", "invalid_token"):
        DeviceToken.objects.filter(id=device_id).update(is_active=False)
        logger.warning(f"Deactivated stale token for device id={device_id}")

    return result


@shared_task(bind=True, max_retries=3)
def send_mood_reminder(self, device_id: int):
    try:
        device = DeviceToken.objects.get(id=device_id, is_active=True)
    except DeviceToken.DoesNotExist:
        logger.warning(f"DeviceToken id={device_id} not found or inactive. Skipping.")
        return {"success": False, "error": "device_not_found"}
    try:

        send_push_notification(
            token=device.token,
            title="How are you feeling?",
            body="Take a moment to log your mood.",
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
