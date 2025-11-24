from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

from patients.models import Patient


class Invoice(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_PARTIAL = "PARTIAL"
    STATUS_PAID = "PAID"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PARTIAL, "Partially Paid"),
        (STATUS_PAID, "Paid"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    total = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoices_created",
    )

    def __str__(self):
        return f"Invoice #{self.id} - {self.patient} - {self.total}"

    @property
    def balance(self) -> Decimal:
        return (self.total or Decimal("0")) - (self.amount_paid or Decimal("0"))

    def refresh_status(self, save=True):
        if self.status == self.STATUS_CANCELLED:
            return
        if self.amount_paid <= 0:
            self.status = self.STATUS_PENDING
        elif self.amount_paid < self.total:
            self.status = self.STATUS_PARTIAL
        else:
            self.status = self.STATUS_PAID
        if save:
            self.save(update_fields=["status"])


class Payment(models.Model):
    METHOD_CASH = "CASH"
    METHOD_MPESA = "MPESA"

    METHOD_CHOICES = [
        (METHOD_CASH, "Cash"),
        (METHOD_MPESA, "M-Pesa"),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=16, choices=METHOD_CHOICES)
    reference = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments_recorded",
    )

    def __str__(self):
        return f"{self.method} {self.amount} for Invoice #{self.invoice_id}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            agg = self.invoice.payments.aggregate(total=models.Sum("amount"))
            self.invoice.amount_paid = agg["total"] or Decimal("0")
            self.invoice.refresh_status(save=True)
