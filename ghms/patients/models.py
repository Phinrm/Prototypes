
from django.db import models

class Patient(models.Model):
    upi = models.CharField(max_length=32, primary_key=True, editable=False)
    national_id = models.CharField(max_length=32, unique=True)
    full_name = models.CharField(max_length=200)
    dob = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=16, blank=True)
    phone = models.CharField(max_length=24, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _generate_upi(self):
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

    def save(self, *args, **kwargs):
        if not self.upi:
            self.upi = self._generate_upi()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.upi})"