from django.db.models import Sum
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from workflow.models import PatientServiceLog
from patients.models import Patient

@login_required
def finance_queue_for_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    services = PatientServiceLog.objects.filter(
        patient=patient,
        billed=False
    ).select_related("service", "department")

    total = services.aggregate(total=Sum("total_price"))["total"] or 0

    if request.method == "POST":
        # mark as billed (after payment)
        services.update(billed=True)
        # generate receipt here or redirect to receipt view
        return render(request, "finance/receipt.html", {
            "patient": patient,
            "services": services,
            "total": total,
        })

    return render(request, "finance/summary.html", {
        "patient": patient,
        "services": services,
        "total": total,
    })
