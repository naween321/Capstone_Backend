import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

from celery.utils.log import get_task_logger

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

    # FCM caps multicast batches at 500 tokens.
    BATCH = 500
    success_count = 0
    failure_count = 0
    for i in range(0, len(tokens), BATCH):
        chunk = tokens[i:i + BATCH]
        if not chunk:
            continue
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            tokens=chunk,
        )
        response = messaging.send_each_for_multicast(message)
        success_count += response.success_count
        failure_count += response.failure_count

    return {
        "success_count": success_count,
        "failure_count": failure_count,
    }


def send_gratitude_release(prompt: str, tokens: list):
    """Multicast today's gratitude prompt to a cohort of on-release tokens."""
    if not tokens:
        return {"success_count": 0, "failure_count": 0}
    return send_multicast_notification(
        tokens=tokens,
        title="Today's gratitude prompt",
        body=prompt,
        data={"type": "gratitude", "prompt": prompt},
    )


