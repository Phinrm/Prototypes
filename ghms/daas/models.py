
from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient
from core.models import Department
from django.conf import settings

class DaasEvent(models.Model):
    ts = models.DateTimeField(auto_now_add=True)
    staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    host = models.CharField(max_length=128, blank=True)
    action = models.CharField(max_length=64)  # ehr_active, ehr_window, idle
    upi = models.CharField(max_length=32, blank=True)
    meta = models.JSONField(default=dict)

class ActivityEvidence(models.Model):
    ts = models.DateTimeField(auto_now_add=True)
    staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    score = models.IntegerField(default=0)
    reason = models.TextField(blank=True)

class DaasShiftSummary(models.Model):
    STATUS_CHOICES = [
        ("VERIFIED", "Verified"),
        ("FLAGGED", "Flagged"),
        ("UNVERIFIED", "Unverified"),
    ]
    HUMAN_LABEL_CHOICES = [
        ("NONE", "None"),
        ("CONFIRMED", "Confirmed by Admin"),
        ("INVALID", "Marked Invalid"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department = models.ForeignKey("core.Department", on_delete=models.SET_NULL, null=True, blank=True)
    shift_start = models.DateTimeField()
    shift_end = models.DateTimeField()
    score = models.FloatField(default=0)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    human_label = models.CharField(max_length=16, choices=HUMAN_LABEL_CHOICES, default="NONE")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-shift_start",)

    def __str__(self):
        return f"{self.user} {self.shift_start} [{self.status}]"