
from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient
from django.conf import settings


class Prescription(models.Model):
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    drug = models.CharField(max_length=128)
    dose = models.CharField(max_length=64, blank=True)
    route = models.CharField(max_length=32, blank=True)
    freq = models.CharField(max_length=32, blank=True)
    start_at = models.DateTimeField(auto_now_add=True)
    end_at = models.DateTimeField(null=True, blank=True)
    prescriber = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=16, default="ACTIVE")

class PharmacyDispense(models.Model):
    id = models.AutoField(primary_key=True)
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="dispenses")
    quantity = models.IntegerField(default=1)
    dispensed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ts = models.DateTimeField(auto_now_add=True)

class LabOrder(models.Model):
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    test_code = models.CharField(max_length=64)
    ordered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=16, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

class LabResult(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.OneToOneField(LabOrder, on_delete=models.CASCADE, related_name="result")
    value_text = models.TextField()
    finalized_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    finalized_at = models.DateTimeField(auto_now_add=True)

class ImagingOrder(models.Model):
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    study = models.CharField(max_length=64)
    ordered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=16, default="PENDING")

class ImagingStudy(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.OneToOneField(ImagingOrder, on_delete=models.CASCADE, related_name="study_obj")
    report_text = models.TextField()
    signed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    signed_at = models.DateTimeField(auto_now_add=True)

class Invoice(models.Model):
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=16, default="UNPAID")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    id = models.AutoField(primary_key=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=32, default="CASH")
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ts = models.DateTimeField(auto_now_add=True)


class ServiceItem(models.Model):
    DEPARTMENT_CHOICES = [
        ("OPD", "Outpatient"),
        ("LAB", "Laboratory"),
        ("RAD", "Radiology"),
        ("PHARM", "Pharmacy"),
        ("FIN", "Finance"),
        ("OTHER", "Other"),
    ]

    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    department = models.CharField(max_length=16, choices=DEPARTMENT_CHOICES)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name} ({self.unit_price})"

