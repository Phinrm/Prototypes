
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from patients.models import Patient
from core.models import Department
from .models import Referral
from audit.utils import log

def _user_department(user):
    sp = getattr(user, "staffprofile", None)
    return getattr(sp, "department", None)

@login_required
def push_patient(request, upi):
    dept = _user_department(request.user)
    if not dept:
        messages.error(request, "No department assigned.")
        return redirect("dashboard")
    patient = get_object_or_404(Patient, pk=upi)
    if request.method == "POST":
        target_code = request.POST.get("target_department")
        target_dept = get_object_or_404(Department, code=target_code)
        Referral.objects.filter(patient=patient, to_department=dept, status__in=["PENDING","IN_PROGRESS"]).update(status="COMPLETED")
        Referral.objects.create(patient=patient, from_department=dept, to_department=target_dept, status="PENDING")
        log(request.user, "PUSH_PATIENT", "Patient", upi, request.META.get("REMOTE_ADDR",""))
        messages.success(request, f"Pushed {patient.full_name} to {target_dept.name}.")
        return redirect("department_home")
    targets = Department.objects.exclude(id=dept.id).order_by("name")
    return render(request, "workflow/push.html", {"patient": patient, "targets": targets})

@login_required
def accept_referral(request, ref_id):
    dept = _user_department(request.user)
    ref = get_object_or_404(Referral, id=ref_id, to_department=dept)
    ref.status = "IN_PROGRESS"; ref.save()
    log(request.user, "ACCEPT_REFERRAL", "Referral", str(ref.id), request.META.get("REMOTE_ADDR",""))
    messages.success(request, f"Accepted referral for {ref.patient.full_name}.")
    return redirect("department_home")

@login_required
def complete_referral(request, ref_id):
    dept = _user_department(request.user)
    ref = get_object_or_404(Referral, id=ref_id, to_department=dept)
    ref.status = "COMPLETED"; ref.save()
    log(request.user, "COMPLETE_REFERRAL", "Referral", str(ref.id), request.META.get("REMOTE_ADDR",""))
    messages.success(request, f"Completed referral for {ref.patient.full_name}.")
    return redirect("department_home")

@login_required
def refer_patient(request, patient_id, to_department_id):
    patient = get_object_or_404(Patient, id=patient_id)
    from_dept = request.user.department
    to_dept = get_object_or_404(Department, id=to_department_id)

    Referral.objects.create(
        patient=patient,
        from_department=from_dept,
        to_department=to_dept,
        created_by=request.user,
    )

    # nothing is lost: all previous PatientServiceLogs remain; billing later aggregates all
    return redirect("department_queue", department_id=to_dept.id)