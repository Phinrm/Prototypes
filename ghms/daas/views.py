import json
from typing import Any, Dict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import (
    JsonResponse,
    HttpResponseForbidden,
    HttpResponseBadRequest,
)
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from .models import DaasShiftSummary
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404

from .models import DaasShiftSummary
from audit.utils import hashchain_log
from django.contrib.auth.decorators import login_required, user_passes_test


from .models import DaasEvent, ActivityEvidence
from patients.models import Patient


User = get_user_model()


def _compute_ai_score(action: str, meta: Dict[str, Any]) -> (int, str):
    """
    Lightweight heuristic scoring that simulates an ML classifier over engagement signals.
    This is intentionally simple and dependency-free for hackathon/demo use,
    but the feature vector mirrors what a trained model would consume.
    """
    keystrokes = int(meta.get("keystrokes", 0))
    mouse_moves = int(meta.get("mouse_moves", meta.get("mouse", 0)))
    active_window = str(meta.get("active_window", "")).lower()
    cpu = float(meta.get("cpu_usage", 0.0))
    duration = float(meta.get("duration_sec", meta.get("duration", 0.0)))

    score = 0
    reasons = []

    # EHR window & clinical apps strongly indicate real work
    if action in ("ehr_active", "ehr_window") or "ehr" in active_window or "ghms" in active_window:
        score += 30
        reasons.append("Clinical system window active")

    # Dense keystrokes / mouse movements
    if keystrokes > 20 or mouse_moves > 30:
        score += 25
        reasons.append("High interactive input")

    # Long continuous focus
    if duration >= 30:
        score += 15
        reasons.append("Sustained activity interval")

    # System-level hints (optional)
    if cpu > 5:
        score += 5
        reasons.append("Foreground app usage detected")

    # Idle or spoof-like signals
    if action == "idle":
        score -= 25
        reasons.append("Idle event reported")

    # Very low interaction while marked active can be suspicious
    if action in ("ehr_active", "ehr_window") and keystrokes < 2 and mouse_moves < 2 and duration > 20:
        score -= 15
        reasons.append("Suspicious low input during claimed EHR use")

    # Clamp into [ -40, 100 ]
    score = max(-40, min(100, score))

    if not reasons:
        reasons.append("Low-signal telemetry")

    return score, "; ".join(reasons)


@csrf_exempt
def ingest(request):
    """
    Ingest telemetry from trusted DAAS agents.

    Expected JSON body:
    {
        "username": "opd_doc",
        "action": "ehr_active" | "ehr_window" | "idle",
        "upi": "12345678",
        "host": "HOST-01",
        "meta": {
            "keystrokes": 42,
            "mouse_moves": 60,
            "active_window": "GHMS-EHR",
            "duration_sec": 45
        }
    }
    """
    token = request.headers.get("X-DAAS-TOKEN")
    trusted = getattr(settings, "DAAS_TRUSTED_TOKENS", [])
    if token not in trusted:
        return HttpResponseForbidden("Invalid DAAS token")

    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    username = data.get("username")
    action = data.get("action")
    upi = data.get("upi") or ""
    host = data.get("host", "")
    meta = data.get("meta") or {}

    if not username or not action:
        return HttpResponseBadRequest("Missing required fields")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponseBadRequest("Unknown user")

    # Persist raw telemetry
    event = DaasEvent.objects.create(
        staff=user,
        host=host,
        action=action,
        upi=upi,
        meta=meta,
    )

    # AI-style scoring
    score, reason = _compute_ai_score(action, meta)

    patient = None
    if upi:
        # Either match on UPI-like field or ignore if not present
        patient = Patient.objects.filter(upi=upi).first() or Patient.objects.filter(pk=upi).first()

    dept = getattr(getattr(user, "staffprofile", None), "department", None)

    if score != 0:
        ActivityEvidence.objects.create(
            staff=user,
            patient=patient,
            department=dept,
            score=score,
            reason=reason,
        )

    return JsonResponse(
        {
            "ok": True,
            "event_id": event.id,
            "engagement_score": score,
            "reason": reason,
        }
    )

class ShiftReportView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = DaasShiftSummary
    template_name = "daas/shift_report.html"
    paginate_by = 50

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def get_queryset(self):
        qs = super().get_queryset().select_related("user", "department")
        status = self.request.GET.get("status")
        dept = self.request.GET.get("department")

        if status:
            qs = qs.filter(status=status)
        if dept:
            qs = qs.filter(department_id=dept)

        if not self.request.user.is_superuser:
            qs = qs.filter(department=getattr(self.request.user, "department", None))
        return qs
    

class ShiftFeedbackView(APIView):
    """
    Allows an auditor or admin to mark a shift as Verified/Invalid.
    This is used as feedback for the AI/DAAS engine and is written
    into the hash-chained audit log.

    No schema changes required; feedback is logged externally.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        shift = get_object_or_404(DaasShiftSummary, pk=pk)
        label = request.data.get("label")
        note = request.data.get("note", "")

        if label not in ["Verified", "Invalid"]:
            return Response({"detail": "Invalid label."}, status=400)

        # Log feedback into tamper-evident audit trail
        hashchain_log(
            "DAAS_SHIFT_FEEDBACK",
            {
                "shift_id": shift.id,
                "staff_id": shift.user_id,
                "label": label,
                "note": note,
            },
            actor=request.user,
        )

        # (Optional: hook into your AI training pipeline later)
        return Response({"detail": "Feedback recorded."}, status=200)
class DaasIngestView(APIView):
    permission_classes = [IsAuthenticated]  # and/or token-based

    def post(self, request):
        # parse payload (simplified — adapt to your schema)
        username = request.data.get("username") or request.user.username
        meta = request.data.get("meta", {})

        event = DaasEvent.objects.create(
            staff=request.user,
            action=request.data.get("action", "activity"),
            host=request.data.get("host", ""),
            upi=request.data.get("upi", ""),
            meta=meta,
        )

        # Synchronous processing for now
        #process_event_and_update_shift(event)

        return Response({"status": "ok"}, status=201)   
    
def is_auditor(user):
    # Superuser OR staffprofile.role == "AUDITOR"
    staff = getattr(user, "staffprofile", None)
    role = getattr(staff, "role", None)
    return user.is_superuser or role == "AUDITOR"


@login_required
@user_passes_test(is_auditor)
def shift_report(request):
    """
    Simple DAAS shift oversight view:
    Shows latest AI / rule-scored shifts for auditors & admins.
    """
    shifts = (
        DaasShiftSummary.objects
        .select_related("user")
        .order_by("-shift_start")[:200]
    )
    return render(request, "daas/shift_report.html", {"shifts": shifts})


@login_required
@user_passes_test(is_auditor)
def verify_hash_chain(request):
    """
    Hash-chain verification endpoint.

    Reads the SIEM/audit log at settings.SIEM_EXPORT_PATH and verifies that
    each entry's 'hash' matches sha256 of its contents and 'prev' links
    correctly to the previous hash.

    Returns JSON so auditors (or external SIEM) can call it.
    """
    log_path = getattr(settings, "SIEM_EXPORT_PATH", None)
    if not log_path or not os.path.exists(log_path):
        # If no log yet, treat as OK (nothing to tamper with)
        return JsonResponse(
            {"ok": True, "message": "No audit log found to verify."},
            status=200,
        )

    try:
        with open(log_path, "rb") as f:
            lines = [ln for ln in f.readlines() if ln.strip()]
    except Exception as exc:
        return JsonResponse(
            {"ok": False, "message": f"Unable to read audit log: {exc}"},
            status=500,
        )

    if not lines:
        return JsonResponse(
            {"ok": True, "message": "Audit log is empty but structurally valid."},
            status=200,
        )

    prev_hash = "GENESIS"
    index = 0

    for raw in lines:
        index += 1
        try:
            entry = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse(
                {"ok": False, "message": f"Invalid JSON at line {index}"},
                status=400,
            )

        stored_hash = entry.get("hash")
        claimed_prev = entry.get("prev")

        # Prepare data used for recomputing
        body = {
            "ts": entry.get("ts"),
            "type": entry.get("type"),
            "actor": entry.get("actor"),
            "data": entry.get("data"),
            "prev": entry.get("prev"),
        }
        recalculated = hashlib.sha256(
            json.dumps(body, sort_keys=True).encode("utf-8")
        ).hexdigest()

        if stored_hash != recalculated:
            return JsonResponse(
                {
                    "ok": False,
                    "message": "Hash mismatch (tampering detected).",
                    "line": index,
                },
                status=400,
            )

        if index == 1 and claimed_prev != "GENESIS":
            return JsonResponse(
                {
                    "ok": False,
                    "message": "First record prev != GENESIS (invalid chain start).",
                    "line": index,
                },
                status=400,
            )

        if index > 1 and claimed_prev != prev_hash:
            return JsonResponse(
                {
                    "ok": False,
                    "message": "Broken hash chain (prev does not match).",
                    "line": index,
                },
                status=400,
            )

        prev_hash = stored_hash

    return JsonResponse(
        {
            "ok": True,
            "message": "Hash chain verified. No tampering detected.",
            "entries": len(lines),
        },
        status=200,
    )