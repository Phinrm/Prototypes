from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from .models import AuditLog
from .utils import compute_entry_hash
from .utils import generate_pdf_from_logs
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.conf import settings
import os

class VerifyHashChainView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        start_id = request.data.get("start_id")
        end_id = request.data.get("end_id")
        if not start_id or not end_id:
            return Response({"detail": "start_id and end_id are required"}, status=400)

        logs = list(AuditLog.objects.filter(id__gte=start_id, id__lte=end_id).order_by("id"))
        if not logs:
            return Response({"verified": False, "detail": "No logs in range"}, status=404)

        prev_hash = logs[0].prev_hash
        for log in logs:
            expected = compute_entry_hash(log, prev_hash)
            if expected != log.hash:
                return Response({
                    "verified": False,
                    "tampered_id": log.id,
                })
            prev_hash = log.hash

        return Response({"verified": True, "count": len(logs)})

class JacIngestStaffActivityView(APIView):
    permission_classes = [IsAdminUser]  # or token-based

    def post(self, request):
        # Expect Jac/agent to send structured activity logs
        logs = request.data.get("logs", [])
        # Save logs or merge with existing DAAS/audit logs
        # ...
        pdf_path = generate_pdf_from_logs(logs)
        return Response({"status": "ok", "pdf": pdf_path})
    

def is_auditor(user):
    staff = getattr(user, "staffprofile", None)
    role = getattr(staff, "role", None)
    return user.is_superuser or role == "AUDITOR"


@login_required
@user_passes_test(is_auditor)
def audit_console(request):
    """
    Lightweight security console for auditors:
    - Shows where the SIEM / hash-chained log file is.
    - Explains that DAAS and staff activity events are recorded there.
    """
    log_path = getattr(settings, "SIEM_EXPORT_PATH", None)
    log_exists = os.path.exists(log_path) if log_path else False

    context = {
        "log_path": log_path,
        "log_exists": log_exists,
    }
    return render(request, "audit/console.html", context)  


@login_required
@user_passes_test(is_auditor)
def export_audit_pdf(request):
    logs = AuditLog.objects.order_by("-timestamp")[:1000]
    pdf_bytes = generate_pdf_from_logs(logs)
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="audit_trail.pdf"'
    return resp