# messages/utils.py
from django.utils import timezone
from daas.models import DaasShiftSummary

def get_shift_status(user):
    shift = (
        DaasShiftSummary.objects
        .filter(user=user)
        .order_by("-shift_start")
        .first()
    )
    now = timezone.now()
    if not shift:
        return "off"

    if shift.shift_start <= now <= shift.shift_end:
        return "on"

    if now < shift.shift_start:
        return "scheduled"

    return "off"
