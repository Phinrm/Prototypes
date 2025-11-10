
import time
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Patient
from workflow.models import Referral

def _dept(user):
    sp = getattr(user, "staffprofile", None)
    return getattr(sp, "department", None)

@login_required
def search_landing(request):
    return render(request, "patients/search_landing.html")

@login_required
def search_by_upi(request):
    if request.method == "POST":
        q = request.POST.get("upi","").strip()
        return _resolve_and_redirect(request, q=q, fields=("upi",))
    return render(request, "patients/search_upi.html")

@login_required
def search_by_national(request):
    if request.method == "POST":
        q = request.POST.get("national_id","").strip()
        return _resolve_and_redirect(request, q=q, fields=("national_id",))
    return render(request, "patients/search_national.html")

@login_required
def search_by_phone(request):
    if request.method == "POST":
        phone = request.POST.get("phone","").strip()
        if not phone:
            messages.error(request, "Enter phone number.")
            return redirect("search_by_phone")
        patient = Patient.objects.filter(phone=phone).first()
        if not patient:
            messages.error(request, "No patient found with that phone.")
            return redirect("search_by_phone")
        from .sms import request_otp
        try:
            request_otp(phone)
        except Exception as e:
            messages.error(request, str(e))
            return redirect("search_by_phone")
        request.session["otp_phone"] = phone
        messages.info(request, f"OTP sent to {phone}.")
        return redirect("verify_phone_otp")
    return render(request, "patients/search_phone.html")

@login_required
def verify_phone_otp(request):
    if request.method == "POST":
        code = request.POST.get("otp","").strip()
        phone = request.session.get("otp_phone")
        if not phone:
            messages.error(request, "Start phone search again.")
            return redirect("search_by_phone")
        from .sms import verify_otp
        if not verify_otp(phone, code):
            messages.error(request, "Invalid or expired OTP.")
            return redirect("verify_phone_otp")
        return _resolve_and_redirect(request, q=phone, fields=("phone",))
    return render(request, "patients/verify_phone_otp.html")

def _resolve_and_redirect(request, q, fields=("upi","national_id","phone")):
    dept = _dept(request.user)
    patient = None
    for f in fields:
        kwargs = {f: q}
        patient = Patient.objects.filter(**kwargs).first()
        if patient: break
    if not patient:
        messages.error(request, "Patient not found.")
        return redirect("patient_search_landing")
    allowed = Referral.objects.filter(patient=patient, to_department=dept, status__in=["PENDING","IN_PROGRESS"]).exists()
    if not allowed:
        messages.error(request, "Patient not in your department worklist.")
        return redirect("patient_search_landing")
    return redirect("patient_detail", upi=patient.upi)
