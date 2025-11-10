
from rest_framework import viewsets, mixins, permissions
from patients.models import Patient
from workflow.models import Referral
from .serializers import *

class PatientViewset(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        dept = self.request.user.staffprofile.department
        allowed_upis = Referral.objects.filter(to_department=dept, status__in=["PENDING","IN_PROGRESS"]).values_list("patient__upi", flat=True)
        return Patient.objects.filter(upi__in=allowed_upis)

class ReferralViewset(viewsets.ModelViewSet):
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        dept = self.request.user.staffprofile.department
        return Referral.objects.filter(to_department=dept, status__in=["PENDING","IN_PROGRESS","COMPLETED"]).select_related("patient","to_department")
    def perform_create(self, serializer):
        dept = self.request.user.staffprofile.department
        serializer.save(from_department=dept)

class ScopedMixin:
    def filter_to_dept(self, qs, field="patient__upi"):
        dept = self.request.user.staffprofile.department
        allowed_upis = Referral.objects.filter(to_department=dept, status__in=["PENDING","IN_PROGRESS","COMPLETED"]).values_list("patient__upi", flat=True)
        return qs.filter(**{f"{field}__in": list(allowed_upis)})

class LabOrderViewset(viewsets.ModelViewSet, ScopedMixin):
    serializer_class = LabOrderSerializer
    def get_queryset(self): return self.filter_to_dept(LabOrder.objects.all())

class LabResultViewset(viewsets.ModelViewSet, ScopedMixin):
    serializer_class = LabResultSerializer
    def get_queryset(self): return self.filter_to_dept(LabResult.objects.select_related("order"), field="order__patient__upi")

class ImagingOrderViewset(viewsets.ModelViewSet, ScopedMixin):
    serializer_class = ImagingOrderSerializer
    def get_queryset(self): return self.filter_to_dept(ImagingOrder.objects.all())

class ImagingStudyViewset(viewsets.ModelViewSet, ScopedMixin):
    serializer_class = ImagingStudySerializer
    def get_queryset(self): return self.filter_to_dept(ImagingStudy.objects.select_related("order"), field="order__patient__upi")

class PrescriptionViewset(viewsets.ModelViewSet, ScopedMixin):
    serializer_class = PrescriptionSerializer
    def get_queryset(self): return self.filter_to_dept(Prescription.objects.all())

class PharmacyDispenseViewset(viewsets.ModelViewSet, ScopedMixin):
    serializer_class = PharmacyDispenseSerializer
    def get_queryset(self): return self.filter_to_dept(PharmacyDispense.objects.select_related("prescription"), field="prescription__patient__upi")

class InvoiceViewset(viewsets.ModelViewSet, ScopedMixin):
    serializer_class = InvoiceSerializer
    def get_queryset(self): return self.filter_to_dept(Invoice.objects.all())

class PaymentViewset(viewsets.ModelViewSet, ScopedMixin):
    serializer_class = PaymentSerializer
    def get_queryset(self): return self.filter_to_dept(Payment.objects.select_related("invoice"), field="invoice__patient__upi")
