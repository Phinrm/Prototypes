from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from clinical.models import ServiceItem
from workflow.models import PatientServiceLog
from patients.models import Patient

@login_required
def dispense_medicine(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    drugs = ServiceItem.objects.filter(department="PHARM", is_active=True)

    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith("drug_") and value:
                service_id = key.split("_")[1]
                qty = int(value)
                service = get_object_or_404(ServiceItem, id=service_id)
                total = qty * service.unit_price

                PatientServiceLog.objects.create(
                    patient=patient,
                    service=service,
                    department=request.user.department,
                    quantity=qty,
                    unit_price=service.unit_price,
                    total_price=total,
                    created_by=request.user,
                )
        # optional: auto-refer to finance
        return redirect("finance_queue_for_patient", patient_id=patient.id)

    return render(request, "pharmacy/dispense.html", {"patient": patient, "drugs": drugs})
