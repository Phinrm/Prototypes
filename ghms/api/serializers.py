
from rest_framework import serializers
from patients.models import Patient
from workflow.models import Referral
from core.models import Department
from clinical.models import LabOrder, LabResult, ImagingOrder, ImagingStudy, Prescription, PharmacyDispense, Invoice, Payment

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["upi","national_id","full_name","dob","sex","phone","address"]

class ReferralSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    patient_upi = serializers.CharField(write_only=True, required=True)
    to_department = serializers.SlugRelatedField(slug_field="code", queryset=Department.objects.all())
    class Meta:
        model = Referral
        fields = ["id","patient","patient_upi","from_department","to_department","status","created_at"]
    def create(self, validated_data):
        upi = validated_data.pop("patient_upi")
        from patients.models import Patient
        p = Patient.objects.get(pk=upi)
        validated_data["patient"] = p
        return super().create(validated_data)

class LabOrderSerializer(serializers.ModelSerializer):
    class Meta: model = LabOrder; fields = "__all__"

class LabResultSerializer(serializers.ModelSerializer):
    class Meta: model = LabResult; fields = "__all__"

class ImagingOrderSerializer(serializers.ModelSerializer):
    class Meta: model = ImagingOrder; fields = "__all__"

class ImagingStudySerializer(serializers.ModelSerializer):
    class Meta: model = ImagingStudy; fields = "__all__"

class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta: model = Prescription; fields = "__all__"

class PharmacyDispenseSerializer(serializers.ModelSerializer):
    class Meta: model = PharmacyDispense; fields = "__all__"

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta: model = Invoice; fields = "__all__"

class PaymentSerializer(serializers.ModelSerializer):
    class Meta: model = Payment; fields = "__all__"
