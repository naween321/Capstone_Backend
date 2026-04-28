"""Celery tasks for backend-pushed gratitude on-release prompts.

Two periodic tasks cooperate:

1. ``fetch_daily_gratitude_prompt`` runs once per day at a UTC hour when
   continental US users are asleep (default 09:00 UTC ≈ 4-5am ET / 1-2am PT).
   It calls Groq for a single prompt and stores it in ``GratitudePrompt`` keyed
   by today's date. Subsequent calls on the same date are no-ops, so the task
   is safe to retry. The cached row is also what the foreground
   ``/api/gratitude/prompt/`` endpoint serves to the app.

2. ``dispatch_gratitude_release`` runs hourly. For each IANA timezone present
   in the active on-release cohort, it checks whether the local hour is the
   release hour (default 18 = 6pm). When it is, it multicasts today's prompt
   to that cohort's FCM tokens with ``data.type=gratitude`` so the frontend
   tap routing lands on Add Gratitude.

Both tasks fail soft: if Groq is down at fetch time, ``dispatch`` will fall
back to the most recent stored prompt rather than skip the day's push.
"""

from datetime import date as date_cls

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone as dj_timezone

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # pragma: no cover - py<3.9
    from backports.zoneinfo import ZoneInfo, ZoneInfoNotFoundError  # type: ignore

from .firebase import send_gratitude_release
from .models import DeviceToken, GratitudePrompt

logger = get_task_logger(__name__)

GRATITUDE_RELEASE_LOCAL_HOUR = 18  # 6pm in each device's local timezone

GRATITUDE_PROMPT_INSTRUCTION = (
    "Generate a single gratitude journal prompt (one sentence, under 20 words). "
    "Vary the angle across calls: people and relationships, sensory moments, places, "
    "personal growth, small wins, challenges weathered, future hope, simple comforts, "
    "things often taken for granted. "
    "Vary the form: open questions, 'name three...', 'describe a moment when...', "
    "fill-in-the-blank ('I'm grateful for ___ because ___'), or a short directive. "
    "Vary the time horizon: today, this week, recently, this year, or ever. "
    "Do not number it. Do not wrap it in quotation marks. Do not add commentary, "
    "preamble, or attribution. Return only the prompt itself."
)

RECENT_PROMPT_LOOKBACK = 30


def _generate_prompt_from_groq() -> str:
    from groq import Groq

    recent = list(
        GratitudePrompt.objects
        .order_by('-date')
        .values_list('prompt', flat=True)[:RECENT_PROMPT_LOOKBACK]
    )
    user_content = GRATITUDE_PROMPT_INSTRUCTION
    if recent:
        avoid_block = "\n".join(f"- {p}" for p in recent if p)
        user_content = (
            f"{GRATITUDE_PROMPT_INSTRUCTION}\n\n"
            "Do NOT repeat, rephrase, or echo the structure of any of the recent "
            "prompts below. Pick a clearly different angle, form, and opening word.\n"
            f"{avoid_block}"
        )

    client = Groq(api_key=settings.GROQ_API_KEY)
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": user_content}],
        model="llama-3.3-70b-versatile",
        temperature=1.1,
        top_p=0.95,
    )
    text = (completion.choices[0].message.content or "").strip()
    # Strip stray wrapping quotes the model sometimes adds.
    if len(text) >= 2 and text[0] in {'"', "'"} and text[-1] == text[0]:
        text = text[1:-1].strip()
    return text


@shared_task(name="commons.tasks.fetch_daily_gratitude_prompt")
def fetch_daily_gratitude_prompt():
    """Cache today's gratitude prompt server-side. Idempotent per UTC date."""
    today = dj_timezone.now().date()
    existing = GratitudePrompt.objects.filter(date=today).first()
    if existing and existing.prompt:
        logger.info("Gratitude prompt for %s already cached, skipping Groq", today)
        return {"date": str(today), "prompt": existing.prompt, "fetched": False}

    try:
        prompt = _generate_prompt_from_groq()
    except Exception as exc:  # pragma: no cover - external API
        logger.exception("Groq fetch failed for %s: %s", today, exc)
        raise

    if not prompt:
        logger.warning("Groq returned empty prompt for %s", today)
        return {"date": str(today), "prompt": "", "fetched": False}

    GratitudePrompt.objects.update_or_create(
        date=today, defaults={"prompt": prompt}
    )
    logger.info("Cached gratitude prompt for %s: %s", today, prompt)
    return {"date": str(today), "prompt": prompt, "fetched": True}


def _todays_prompt() -> str | None:
    """Return today's cached prompt, falling back to the latest stored one."""
    today = dj_timezone.now().date()
    todays = GratitudePrompt.objects.filter(date=today).first()
    if todays and todays.prompt:
        return todays.prompt
    fallback = GratitudePrompt.objects.order_by('-date').first()
    return fallback.prompt if fallback else None


@shared_task(name="commons.tasks.dispatch_gratitude_release")
def dispatch_gratitude_release():
    """Hourly fan-out: push today's prompt to TZ cohorts whose local hour is 18."""
    prompt = _todays_prompt()
    if not prompt:
        logger.warning("No gratitude prompt cached; skipping dispatch")
        return {"dispatched_cohorts": 0, "reason": "no_prompt"}

    tz_names = (
        DeviceToken.objects
        .filter(is_active=True, gratitude_mode='on_release')
        .values_list('timezone', flat=True)
        .distinct()
    )

    now_utc = dj_timezone.now()
    cohorts_dispatched = 0
    total_success = 0
    total_failure = 0

    for tz_name in tz_names:
        if not tz_name:
            continue
        try:
            zone = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            logger.warning("Unknown IANA tz %r on DeviceToken; skipping", tz_name)
            continue

        local_hour = now_utc.astimezone(zone).hour
        if local_hour != GRATITUDE_RELEASE_LOCAL_HOUR:
            continue

        tokens = list(
            DeviceToken.objects
            .filter(is_active=True, gratitude_mode='on_release', timezone=tz_name)
            .values_list('token', flat=True)
        )
        if not tokens:
            continue

        result = send_gratitude_release(prompt=prompt, tokens=tokens)
        cohorts_dispatched += 1
        total_success += result.get("success_count", 0)
        total_failure += result.get("failure_count", 0)
        logger.info(
            "Gratitude release fan-out tz=%s tokens=%d success=%d failure=%d",
            tz_name, len(tokens), result.get("success_count", 0), result.get("failure_count", 0),
        )

    return {
        "dispatched_cohorts": cohorts_dispatched,
        "success_count": total_success,
        "failure_count": total_failure,
    }
