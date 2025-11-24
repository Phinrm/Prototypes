from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.http import HttpResponse

import csv
import datetime
import os

from django.db import transaction

from audit.utils import log as audit_log
from patients.models import Patient
from core.models import Department, StaffProfile, Role, ServiceItem
from workflow.models import Referral, PatientServiceLog
from daas.models import DaasShiftSummary
from finance.models import Invoice, Payment
from finance.ai_summary import summarize_patient_services

from clinical.models import (
    LabOrder,
    LabResult,
    ImagingOrder,
    ImagingStudy,
    Prescription,
    PharmacyDispense,
)

# Optional: AuditLog if present
try:
    from audit.models import AuditLog
except Exception:
    AuditLog = None


# ----------------- LLM wrapper ----------------- #

class LLMNotConfigured(Exception):
    """Raised when LLM (Gemini) is not configured properly."""
    pass


def call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY") or getattr(
        __import__("django.conf").conf.settings, "GEMINI_API_KEY", None
    )
    if not api_key:
        raise LLMNotConfigured("GEMINI_API_KEY not configured")

    try:
        import google.generativeai as genai
    except ImportError:
        raise LLMNotConfigured("google-generativeai not installed")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    resp = model.generate_content(prompt)
    text = getattr(resp, "text", None)
    if not text:
        raise LLMNotConfigured("No text returned from Gemini")
    return text


# ----------------- Helpers ----------------- #

def _get_role_codes(user):
    """
    Return a set of role codes for this user.
    Assumes StaffProfile.roles is a ManyToMany to Role(code),
    but degrades to empty set if not present.
    """
    sp = getattr(user, "staffprofile", None)
    if not sp or not hasattr(sp, "roles"):
        return set()
    return set(sp.roles.values_list("code", flat=True))


def _next_upi_preview():
    """
    Preview next UPI in format KEN-00001 (for display only).
    Actual UPI is generated in Patient model save().
    """
    last = (
        Patient.objects
        .filter(upi__startswith="KEN-")
        .order_by("-upi")
        .first()
    )
    if last:
        try:
            num = int(last.upi.split("-")[1])
        except Exception:
            num = 0
    else:
        num = 0
    return f"KEN-{num + 1:05d}"


# ----------------- Auth ----------------- #

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        audit_log(user, "LOGIN")
        return redirect("dashboard")

    return render(request, "login.html", {"form": form})


def logout_view(request):
    if request.user.is_authenticated:
        audit_log(request.user, "LOGOUT")
    logout(request)
    return redirect("login")


# ----------------- Dashboard ----------------- #

@login_required
def dashboard(request):
    user = request.user
    ctx = {}

    sp = getattr(user, "staffprofile", None)
    dept = getattr(sp, "department", None)
    role_codes = _get_role_codes(user)

    def can(*codes):
        codes = {c.upper() for c in codes}
        return bool(role_codes & codes)

    # Latest shift widget
    shift = (
        DaasShiftSummary.objects
        .filter(user=user)
        .order_by("-shift_start")
        .first()
    )
    if shift and shift.shift_end:
        now = timezone.now()
        total = (shift.shift_end - shift.shift_start).total_seconds()
        elapsed = (now - shift.shift_start).total_seconds()
        elapsed_clamped = max(0, min(elapsed, total)) if total > 0 else 0
        time_pct = round((elapsed_clamped / total) * 100, 1) if total > 0 else 0

        ctx["current_shift"] = shift
        ctx["shift_time_pct"] = time_pct
        ctx["shift_ai_score"] = getattr(shift, "score", None)
        ctx["shift_ai_label"] = getattr(shift, "status", "")
    else:
        ctx["current_shift"] = None

    # Capability flags for UI
    ctx.update({
        "department": dept,
        "role_codes": role_codes,

        "can_register_patient": can("RECEPTION", "ADMIN"),
        "can_view_clinical_queue": can("CLINICIAN", "NURSE", "RECEPTION", "ADMIN"),
        "can_order_lab": can("CLINICIAN", "OPD_DOCTOR", "DOCTOR"),
        "can_finalize_lab": can("LAB_TECH"),
        "can_order_imaging": can("CLINICIAN", "OPD_DOCTOR", "DOCTOR"),
        "can_sign_imaging": can("RADIOLOGIST"),
        "can_dispense": can("PHARMACIST"),
        "can_invoice": can("FINANCE"),
        "can_take_payment": can("FINANCE"),
        "can_audit": can("AUDITOR") or user.is_superuser,
        "can_manage_users": can("ADMIN") or user.is_superuser,
        "can_use_messages": True,
    })

    # --- Department worklist logic ---
    worklist = []
    if dept:
        patients_set = set()

        # 1) Active referrals into this department
        # (Assumes Referral has a 'status' field)
        active_refs = (
            Referral.objects
            .filter(to_department=dept, status__in=["PENDING", "IN_PROGRESS"])
            .select_related("patient")
            .order_by("created_at")
        )
        for r in active_refs:
            patients_set.add(r.patient)

        # 2) Registration-like departments:
        #    show today's registered patients with no referral yet
        is_registration = (
            (hasattr(sp, "role") and getattr(sp, "role", None) in ["RECEPTION"])
            or (dept.code and dept.code.upper() in ["REG", "RECEP", "REGISTRY"])
        )

        if is_registration:
            today = timezone.localdate()
            reg_service = ServiceItem.objects.filter(
                code="REGISTRATION",
                is_active=True,
            ).first()
            if reg_service:
                reg_logs = (
                    PatientServiceLog.objects
                    .filter(
                        department=dept,
                        created_at__date=today,
                        service=reg_service,
                    )
                    .select_related("patient")
                )
                for log in reg_logs:
                    has_ref = Referral.objects.filter(patient=log.patient).exists()
                    if not has_ref:
                        patients_set.add(log.patient)

        worklist = sorted(patients_set, key=lambda p: p.created_at, reverse=True)

    ctx["worklist"] = worklist

    return render(request, "ui/dashboard.html", ctx)


@login_required
def department_home(request):
    return redirect("dashboard")


# ----------------- Patient detail & referrals ----------------- #

@login_required
def patient_detail(request, upi):
    sp = getattr(request.user, "staffprofile", None)
    dept = getattr(sp, "department", None)
    patient = get_object_or_404(Patient, pk=upi)

    # Assumes Referral has 'status'
    ref = (
        Referral.objects
        .filter(
            patient=patient,
            to_department=dept,
            status__in=["PENDING", "IN_PROGRESS"],
        )
        .order_by("-created_at")
        .first()
    )

    if not ref:
        messages.error(request, "This patient is not assigned to your department.")
        return redirect("department_home")

    audit_log(
        request.user,
        "VIEW_PATIENT",
        object_type="Patient",
        object_id=str(upi),
    )

    all_departments = Department.objects.exclude(id=dept.id) if dept else Department.objects.all()

    return render(request, "patient_detail.html", {
        "patient": patient,
        "referral": ref,
        "department": dept,
        "all_departments": all_departments,
    })


@login_required
@require_POST
def refer_patient(request, upi):
    sp = getattr(request.user, "staffprofile", None)
    from_dept = getattr(sp, "department", None)
    patient = get_object_or_404(Patient, pk=upi)

    to_dept_id = request.POST.get("to_department")
    to_dept = get_object_or_404(Department, id=to_dept_id)

    Referral.objects.create(
        patient=patient,
        from_department=from_dept,
        to_department=to_dept,
        requested_by=request.user,
        status="PENDING",
    )

    messages.success(request, f"Patient referred to {to_dept.name}.")
    return redirect("patient_detail", upi=upi)


@login_required
@require_POST
def complete_department_process(request, upi):
    sp = getattr(request.user, "staffprofile", None)
    dept = getattr(sp, "department", None)
    patient = get_object_or_404(Patient, pk=upi)

    if not dept:
        messages.error(request, "No department assigned to your profile.")
        return redirect("patient_detail", upi=upi)

    # Guard: unpaid invoices
    has_unpaid = Invoice.objects.filter(patient=patient, status="UNPAID").exists()
    if has_unpaid:
        messages.error(request, "Cannot complete: patient has unpaid invoices.")
        return redirect("patient_detail", upi=upi)

    # Complete referrals into this department
    Referral.objects.filter(
        patient=patient,
        to_department=dept,
        status__in=["PENDING", "IN_PROGRESS"],
    ).update(status="COMPLETED")

    messages.success(request, "Process completed for this department.")
    return redirect("department_home")


# ----------------- Clinical flows (lab, imaging, pharmacy, finance) ----------------- #
# (Unchanged structurally; cleaned to use audit_log consistently.)

@login_required
@require_http_methods(["GET", "POST"])
def lab_create_order_persist(request, upi):
    sp = request.user.staffprofile
    dept = getattr(sp, "department", None)
    if not dept or dept.code != "OPD":
        messages.error(request, "Only OPD can create lab orders in this demo.")
        return redirect("department_home")

    patient = get_object_or_404(Patient, pk=upi)

    if request.method == "POST":
        test_code = request.POST.get("test_code", "").strip()
        if not test_code:
            messages.error(request, "Test code required.")
        else:
            lo = LabOrder.objects.create(
                patient=patient,
                test_code=test_code,
                ordered_by=request.user,
                status="PENDING",
            )
            lab = Department.objects.get(code="LAB")
            Referral.objects.create(
                patient=patient,
                from_department=dept,
                to_department=lab,
                requested_by=request.user,
                status="PENDING",
            )
            messages.success(request, f"Lab order created (#{lo.id}) and patient pushed to LAB.")
            audit_log(
                request.user,
                "CREATE_LAB_ORDER_DB",
                object_type="LabOrder",
                object_id=str(lo.id),
            )
            return redirect("patient_detail", upi=upi)

    return render(request, "departments/lab_create_order.html", {"upi": upi, "patient": patient})


@login_required
@require_http_methods(["GET", "POST"])
def lab_finalize_result_persist(request, upi):
    sp = request.user.staffprofile
    dept = getattr(sp, "department", None)
    if not dept or dept.code != "LAB":
        messages.error(request, "Only LAB can finalize results.")
        return redirect("department_home")

    patient = get_object_or_404(Patient, pk=upi)
    ref = Referral.objects.filter(
        patient=patient,
        to_department__code="LAB",
        status__in=["PENDING", "IN_PROGRESS"],
    ).first()
    if not ref:
        messages.error(request, "Patient not in LAB worklist.")
        return redirect("department_home")

    if request.method == "POST":
        res = request.POST.get("result", "").strip()
        order = (
            LabOrder.objects
            .filter(patient=patient, status__in=["PENDING", "IN_PROGRESS"])
            .order_by("-created_at")
            .first()
        )
        if not order:
            messages.error(request, "No active lab order for patient.")
        elif not res:
            messages.error(request, "Result text required.")
        else:
            order.status = "FINAL"
            order.save()
            LabResult.objects.create(
                order=order,
                value_text=res,
                finalized_by=request.user,
            )
            ref.status = "COMPLETED"
            ref.save()
            messages.success(request, f"Lab result saved for order #{order.id}.")
            audit_log(
                request.user,
                "FINALIZE_LAB_RESULT_DB",
                object_type="LabOrder",
                object_id=str(order.id),
            )
            return redirect("patient_detail", upi=upi)

    return render(request, "departments/lab_finalize_result.html", {"patient": patient})


@login_required
@require_http_methods(["GET", "POST"])
def radiology_order_persist(request, upi):
    sp = request.user.staffprofile
    dept = getattr(sp, "department", None)
    if not dept or dept.code != "OPD":
        messages.error(request, "Only OPD can create radiology orders in this demo.")
        return redirect("department_home")

    patient = get_object_or_404(Patient, pk=upi)

    if request.method == "POST":
        study = request.POST.get("study", "").strip()
        if study:
            io = ImagingOrder.objects.create(
                patient=patient,
                study=study,
                ordered_by=request.user,
                status="PENDING",
            )
            rad = Department.objects.get(code="RAD")
            Referral.objects.create(
                patient=patient,
                from_department=dept,
                to_department=rad,
                requested_by=request.user,
                status="PENDING",
            )
            messages.success(request, f"Radiology order created (#{io.id}) and patient pushed to Radiology.")
            audit_log(
                request.user,
                "CREATE_RAD_ORDER_DB",
                object_type="ImagingOrder",
                object_id=str(io.id),
            )
            return redirect("patient_detail", upi=upi)
        messages.error(request, "Study type required.")

    return render(request, "departments/radiology_order.html", {"patient": patient})


@login_required
@require_http_methods(["GET", "POST"])
def radiology_report_persist(request, upi):
    sp = request.user.staffprofile
    dept = getattr(sp, "department", None)
    if not dept or dept.code != "RAD":
        messages.error(request, "Only Radiology can finalize reports.")
        return redirect("department_home")

    # Example: if StaffProfile has helper has_role; otherwise use _get_role_codes
    if hasattr(sp, "has_role"):
        if not sp.has_role("RADIOLOGIST"):
            messages.error(request, "Only a Radiologist may sign reports.")
            return redirect("department_home")
    else:
        if "RADIOLOGIST" not in _get_role_codes(request.user):
            messages.error(request, "Only a Radiologist may sign reports.")
            return redirect("department_home")

    patient = get_object_or_404(Patient, pk=upi)
    ref = Referral.objects.filter(
        patient=patient,
        to_department__code="RAD",
        status__in=["PENDING", "IN_PROGRESS"],
    ).first()
    if not ref:
        messages.error(request, "Patient not in Radiology worklist.")
        return redirect("department_home")

    if request.method == "POST":
        rep = request.POST.get("report", "").strip()
        order = (
            ImagingOrder.objects
            .filter(patient=patient, status__in=["PENDING", "IN_PROGRESS"])
            .order_by("-id")
            .first()
        )
        if not order:
            messages.error(request, "No active imaging order.")
        elif not rep:
            messages.error(request, "Report text required.")
        else:
            order.status = "FINAL"
            order.save()
            ImagingStudy.objects.create(
                order=order,
                report_text=rep,
                signed_by=request.user,
            )
            ref.status = "COMPLETED"
            ref.save()
            messages.success(request, "Radiology report saved.")
            audit_log(
                request.user,
                "FINALIZE_RAD_REPORT_DB",
                object_type="ImagingOrder",
                object_id=str(order.id),
            )
            return redirect("patient_detail", upi=upi)

    return render(request, "departments/radiology_report.html", {"patient": patient})


@login_required
@require_http_methods(["GET", "POST"])
def pharmacy_dispense_persist(request, upi):
    sp = request.user.staffprofile
    dept = getattr(sp, "department", None)
    if not dept or dept.code != "PHARM":
        messages.error(request, "Only Pharmacy may dispense.")
        return redirect("department_home")

    patient = get_object_or_404(Patient, pk=upi)
    ref = Referral.objects.filter(
        patient=patient,
        to_department__code="PHARM",
        status__in=["PENDING", "IN_PROGRESS"],
    ).first()
    if not ref:
        messages.error(request, "Patient not in Pharmacy worklist.")
        return redirect("department_home")

    if request.method == "POST":
        drug = request.POST.get("drug", "").strip()
        qty = int(request.POST.get("qty", "1") or "1")
        rx = Prescription.objects.filter(
            patient=patient,
            drug=drug,
            status="ACTIVE",
        ).first()
        if not rx:
            rx = Prescription.objects.create(
                patient=patient,
                drug=drug,
                prescriber=None,
                status="ACTIVE",
            )
        PharmacyDispense.objects.create(
            prescription=rx,
            quantity=qty,
            dispensed_by=request.user,
        )
        ref.status = "COMPLETED"
        ref.save()
        messages.success(request, f"Dispensed {qty} x {drug}.")
        audit_log(
            request.user,
            "PHARM_DISPENSE_DB",
            object_type="Prescription",
            object_id=str(rx.id),
        )
        return redirect("patient_detail", upi=upi)

    return render(request, "departments/pharmacy_dispense.html", {"patient": patient})


@login_required
@require_http_methods(["GET", "POST"])
def finance_invoice_persist(request, upi):
    sp = request.user.staffprofile
    dept = getattr(sp, "department", None)
    if not dept or dept.code != "FIN":
        messages.error(request, "Only Finance may invoice.")
        return redirect("department_home")

    patient = get_object_or_404(Patient, pk=upi)

    if request.method == "POST":
        amount = request.POST.get("amount", "").strip()
        if not amount:
            messages.error(request, "Amount required.")
        else:
            inv = Invoice.objects.create(
                patient=patient,
                total=amount,
                status="UNPAID",
                created_by=request.user,
            )
            messages.success(request, f"Invoice #{inv.id} created KES {amount}.")
            audit_log(
                request.user,
                "FINANCE_INVOICE_DB",
                object_type="Invoice",
                object_id=str(inv.id),
            )
            return redirect("patient_detail", upi=upi)

    return render(request, "departments/finance_invoice.html", {"patient": patient})


# ----------------- LLM Patient Report ----------------- #

ALLOWED_REPORT_ROLES = {
    "OPD_DOCTOR",
    "CLINICIAN",
    "CONSULTANT",
    "NURSE",
    "LAB_TECH",
    "RADIOLOGIST",
    "PHARMACIST",
    "FINANCE",
}


@login_required
def patient_report(request, patient_id):
    user = request.user
    role_codes = _get_role_codes(user)

    if not (role_codes & ALLOWED_REPORT_ROLES) and not user.is_superuser:
        return render(request, "ui/not_allowed.html", status=403)

    # Patient.pk is UPI in your model
    patient = get_object_or_404(Patient, pk=patient_id)
    services = PatientServiceLog.objects.filter(
        patient=patient
    ).select_related("service", "department")

    lines = [
        f"- {s.created_at.date()} | {s.department.name}: "
        f"{s.service.name} x{s.quantity} @ {s.unit_price} = {s.total_price}"
        for s in services
    ]

    base_prompt = (
        "You are a clinical assistant in a public hospital.\n"
        "Generate a concise, structured patient encounter summary.\n"
        f"Patient ID: {patient.pk}\n"
        "Services history:\n" + "\n".join(lines) +
        "\nHighlight key investigations, treatments, and pending follow-ups.\n"
        "Use clear headings. Do NOT invent data."
    )

    try:
        auto_text = summarize_patient_services(base_prompt)
    except Exception:
        auto_text = "\n".join(lines) or "No services recorded yet."

    if request.method == "POST":
        final_text = request.POST.get("report_text", auto_text)
        audit_log(
            user,
            "PATIENT_REPORT_GENERATED",
            object_type="Patient",
            object_id=str(patient.pk),
        )
        return render(request, "ui/patient_report_final.html", {
            "patient": patient,
            "report": final_text,
        })

    return render(request, "ui/patient_report_edit.html", {
        "patient": patient,
        "auto_summary": auto_text,
    })


# ----------------- Utility views ----------------- #

@login_required
def find_patient(request):
    query = request.GET.get("q", "").strip()
    patients = []
    if query:
        patients = (
            Patient.objects.filter(upi__icontains=query)
            | Patient.objects.filter(full_name__icontains=query)
        )
    return render(request, "ui/find_patient.html", {
        "patients": patients,
        "query": query,
    })


@login_required
def attended_today(request):
    today = timezone.localdate()
    logs = (
        PatientServiceLog.objects
        .filter(created_at__date=today)
        .select_related("patient", "service", "department")
        .order_by("-created_at")
    )
    return render(request, "ui/attended_today.html", {"logs": logs})


@login_required
def my_profile(request):
    user = request.user
    sp = getattr(user, "staffprofile", None)

    roles = []
    role_codes = set()
    if sp and hasattr(sp, "roles"):
        roles = list(sp.roles.all())
        role_codes = {r.code for r in roles}

    is_admin_like = user.is_superuser or "ADMIN" in role_codes
    is_auditor_like = (
        "AUDITOR" in role_codes
        or "SECURITY_AUDITOR" in role_codes
    )

    latest_shift = (
        DaasShiftSummary.objects
        .filter(user=user)
        .order_by("-shift_start")
        .first()
    )

    ctx = {
        "user": user,
        "staffprofile": sp,
        "department": getattr(sp, "department", None) if sp else None,
        "hospital": getattr(sp, "hospital", None) if sp and hasattr(sp, "hospital") else None,
        "roles": roles,
        "role_codes": role_codes,
        "latest_shift": latest_shift,
        "is_admin": is_admin_like,
        "is_auditor": is_auditor_like,
    }

    if is_admin_like or is_auditor_like:
        ctx["recent_shifts"] = (
            DaasShiftSummary.objects
            .filter(user=user)
            .order_by("-shift_start")[:10]
        )
        if AuditLog:
            ctx["recent_audit_logs"] = (
                AuditLog.objects
                .filter(actor=user)
                .order_by("-timestamp")[:50]
            )

    return render(request, "ui/my_profile.html", ctx)


@login_required
def export_worklist_csv(request):
    sp = getattr(request.user, "staffprofile", None)
    dept = getattr(sp, "department", None) if sp else None
    if not dept:
        return HttpResponse("No department assigned.", status=400)

    rows = (
        PatientServiceLog.objects
        .filter(department=dept, billed=False)
        .select_related("patient", "service")
        .order_by("created_at")
    )

    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = f'attachment; filename="{dept.code}_worklist.csv"'
    writer = csv.writer(resp)
    writer.writerow(["UPI", "Patient", "Service", "Quantity", "Total", "Created At"])
    for r in rows:
        writer.writerow([
            getattr(r.patient, "upi", ""),
            getattr(r.patient, "full_name", str(r.patient)),
            r.service.name,
            r.quantity,
            r.total_price,
            r.created_at.strftime("%Y-%m-%d %H:%M"),
        ])
    return resp


@login_required
def export_worklist_pdf(request):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from io import BytesIO

    sp = getattr(request.user, "staffprofile", None)
    dept = getattr(sp, "department", None) if sp else None
    if not dept:
        return HttpResponse("No department assigned.", status=400)

    rows = (
        PatientServiceLog.objects
        .filter(department=dept, billed=False)
        .select_related("patient", "service")
        .order_by("created_at")
    )

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, y, f"GHMS v3 — {dept.name} Worklist")
    y -= 24
    p.setFont("Helvetica", 9)

    for r in rows:
        line = (
            f"{getattr(r.patient, 'upi', '')}  "
            f"{getattr(r.patient, 'full_name', str(r.patient))}  "
            f"{r.service.name}  x{r.quantity}  {r.total_price}"
        )
        p.drawString(40, y, line[:110])
        y -= 14
        if y < 60:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 9)

    if not rows:
        p.drawString(40, y, "No patients in your worklist.")

    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()

    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{dept.code}_worklist.pdf"'
    resp.write(pdf)
    return resp


@login_required
def set_shift(request):
    if request.method != "POST":
        return redirect("dashboard")

    start_str = request.POST.get("shift_start")
    end_str = request.POST.get("shift_end")

    if not start_str or not end_str:
        return redirect("dashboard")

    try:
        start_naive = datetime.datetime.fromisoformat(start_str)
        end_naive = datetime.datetime.fromisoformat(end_str)
    except ValueError:
        return redirect("dashboard")

    start = timezone.make_aware(start_naive)
    end = timezone.make_aware(end_naive)

    if end <= start:
        return redirect("dashboard")

    shift = DaasShiftSummary.objects.create(
        user=request.user,
        shift_start=start,
        shift_end=end,
        status="Planned",
        score=0.0,
    )

    audit_log(
        request.user,
        "SHIFT_DEFINED",
        object_type="DaasShiftSummary",
        object_id=str(shift.id),
    )

    return redirect("dashboard")


@login_required
def finance_take_payment(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == "POST":
        method = request.POST.get("method", "CASH")
        amount = invoice.total
        ref = request.POST.get("reference", "").strip()

        pay = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            method=method,
            reference=ref,
            status="SUCCESS" if method != "MPESA" else "PENDING",
        )

        if method != "MPESA":
            invoice.status = "PAID"
            invoice.save()

        audit_log(
            request.user,
            "PAYMENT_TAKEN",
            object_type="Payment",
            object_id=str(pay.id),
        )

        messages.success(request, f"Payment recorded via {method}.")
        return redirect("patient_detail", upi=invoice.patient.id)

    return render(request, "finance/take_payment.html", {"invoice": invoice})
@login_required
@require_http_methods(["GET", "POST"])
def register_patient(request):
    """
    Rules:
    - UPI is auto-generated in Patient model (KEN-xxxxx).
    - On the form: show UPI preview (disabled), but do NOT allow editing.
    - A patient cannot be registered twice in the same day.
    - Before creating a new patient, search by national_id.
    - Log a REGISTRATION service (ServiceItem.code = "REGISTRATION") once per day.
    - Registered patients with no referral should appear in Current Worklist.
    """
    sp = getattr(request.user, "staffprofile", None)
    dept = getattr(sp, "department", None)

    if not dept:
        messages.error(request, "Your account is not linked to any department.")
        return redirect("dashboard")

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        national_id = request.POST.get("national_id", "").strip()
        dob = request.POST.get("dob") or None
        sex = request.POST.get("sex", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()

        if not full_name or not national_id:
            messages.error(request, "Full name and National ID are required.")
            return redirect("register_patient")

        today = timezone.localdate()
        reg_service = ServiceItem.objects.filter(
            code="REGISTRATION",
            is_active=True,
        ).first()

        with transaction.atomic():
            # 1) Look for an existing patient by National ID
            patient = Patient.objects.filter(national_id=national_id).first()

            if patient:
                # 1a) Prevent double registration in the same day
                if reg_service and PatientServiceLog.objects.filter(
                    patient=patient,
                    service=reg_service,
                    created_at__date=today,
                ).exists():
                    messages.warning(
                        request,
                        f"Patient already registered today. UPI: {patient.upi}."
                    )
                    return redirect("patient_detail", upi=patient.upi)

                # 1b) Optionally refresh demographics
                if full_name:
                    patient.full_name = full_name
                if dob:
                    patient.dob = dob
                if sex:
                    patient.sex = sex
                if phone:
                    patient.phone = phone
                if address:
                    patient.address = address
                patient.save()

            else:
                # 2) New patient — UPI is auto-assigned in Patient.save()
                patient = Patient(
                    national_id=national_id,
                    full_name=full_name,
                    dob=dob,
                    sex=sex,
                    phone=phone,
                    address=address,
                )
                # IMPORTANT: Patient model must generate UPI if none is set
                patient.save()

            # 3) Log REGISTRATION service once per day
            if reg_service and not PatientServiceLog.objects.filter(
                patient=patient,
                service=reg_service,
                created_at__date=today,
            ).exists():
                PatientServiceLog.objects.create(
                    patient=patient,
                    department=dept,
                    service=reg_service,
                    quantity=1,
                    unit_price=reg_service.base_price,
                    total_price=reg_service.base_price,
                    created_by=request.user,
                )

            # 4) Audit
            audit_log(
                request.user,
                "PATIENT_REGISTERED",
                object_type="Patient",
                object_id=str(patient.upi),
                meta={"national_id": national_id},
            )

        messages.success(
            request,
            f"Patient {patient.full_name} registered with UPI {patient.upi}."
        )
        return redirect("patient_detail", upi=patient.upi)

    # GET: show registration form with a greyed-out preview UPI
    return render(request, "ui/register_patient.html", {
        "upi_preview": _next_upi_preview(),
    })

    #ctl z twizce to return 1800 pieces of code