from datetime import timedelta

from django.utils import timezone
from django.db import transaction

from .models import DaasEvent, DaasShiftSummary
from ai.llm import call_gemini, LLMNotConfigured



SHIFT_LENGTH_HOURS = 8


def current_shift_window(ts=None):
    """
    Returns (shift_start, shift_end) for the given timestamp in 3 x 8-hour blocks.
    If ts is None, uses now().
    """
    if ts is None:
        ts = timezone.now()

    # Normalize to local-aware time
    ts = timezone.localtime(ts)

    shift_index = ts.hour // SHIFT_LENGTH_HOURS  # 0,1,2
    shift_start_hour = shift_index * SHIFT_LENGTH_HOURS

    shift_start = ts.replace(
        hour=shift_start_hour,
        minute=0,
        second=0,
        microsecond=0,
    )
    shift_end = shift_start + timedelta(hours=SHIFT_LENGTH_HOURS)
    return shift_start, shift_end


def score_event(event: DaasEvent) -> float:
    """
    Lightweight heuristic scorer for a single DAAS event.
    Produces a per-event contribution to an eventual 0–100 shift score.
    """
    meta = event.meta or {}

    keystrokes = float(meta.get("keystrokes", 0))
    mouse_moves = float(meta.get("mouse_moves", 0))
    duration = float(meta.get("duration_sec", 0))
    active_window = str(meta.get("active_window", "")).upper()

    score = 0.0

    # Reward interaction with GHMS / EHR
    if "GHMS" in active_window or "EHR" in active_window:
        score += 2.0

    # Normalize keystrokes / mouse / duration into bounded contributions
    score += min(keystrokes / 50.0, 3.0)      # typing
    score += min(mouse_moves / 80.0, 3.0)     # cursor activity
    score += min(duration / 60.0, 2.0)        # focused interval

    # Cap per-event score
    if score < 0:
        score = 0.0
    if score > 10.0:
        score = 10.0

    return score


def compute_shift_status(total_score: float) -> str:
    """
    Map cumulative numeric score to status bucket.
    """
    # Clamp to 0-100 range for interpretation
    normalized = max(0.0, min(total_score, 100.0))

    if normalized >= 75.0:
        return "VERIFIED"
    if normalized >= 40.0:
        return "FLAGGED"
    return "UNVERIFIED"


def compute_shift_verified(shift_summary: DaasShiftSummary) -> bool:
    """
    Convenience helper used by UI / other callers.
    True if the shift is considered verified.
    """
    return shift_summary.status == "VERIFIED"


@transaction.atomic
def process_event_and_update_shift(event: DaasEvent) -> None:
    """
    Called after each DAAS telemetry event is ingested.
    - Maps event to its 8-hour shift window.
    - Updates (or creates) DaasShiftSummary row for that user + shift.
    - Recomputes status based on cumulative score.
    """
    # Use the event's timestamp if present; fallback to created_at/now
    ts = getattr(event, "timestamp", None) or getattr(event, "created_at", None) or timezone.now()
    shift_start, shift_end = current_shift_window(ts)

    # Derive department from user if available
    user = event.user
    department = getattr(user, "department", None)

    summary, _ = DaasShiftSummary.objects.select_for_update().get_or_create(
        user=user,
        shift_start=shift_start,
        shift_end=shift_end,
        defaults={
            "department": department,
            "score": 0.0,
            "status": "UNVERIFIED",
        },
    )

    # Incremental score update
    increment = score_event(event)
    new_score = (summary.score or 0.0) + increment

    summary.score = new_score
    summary.status = compute_shift_status(new_score)
    summary.save(update_fields=["score", "status"])



def ai_score_shift(activity_events: list[dict]) -> tuple[float, str]:
    """
    activity_events: list of {timestamp, action, weight, meta}
    Returns (score_0_100, label)
    """

    if not activity_events:
        return 0.0, "Unverified"

    lines = []
    for e in activity_events[:200]:
        lines.append(f"- {e.get('timestamp')} :: {e.get('action')} :: weight={e.get('weight',1)}")

    prompt = (
        "You are evaluating a hospital staff member's shift activity for fraud and idleness.\n"
        "Given the events below, output ONLY a JSON object like "
        '{"score": 0-100, "label": "Verified" or "Unverified"}.\n'
        "Higher score = consistent, legitimate clinical work. Very low score = suspicious.\n\n"
        "Events:\n" + "\n".join(lines)
    )

    try:
        text = call_gemini(prompt)
    except LLMNotConfigured:
        # fallback to existing rule-based score if AI not configured
        return simple_rule_based_score(activity_events)

    import json
    try:
        data = json.loads(text)
        score = float(data.get("score", 0))
        label = data.get("label", "Unverified")
    except Exception:
        # if parsing fails, degrade gracefully
        return simple_rule_based_score(activity_events)

    score = max(0.0, min(100.0, score))
    return score, label