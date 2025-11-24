from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class Hospital(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=20, unique=True)
    location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Department(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=True)
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        related_name="departments",
        null=True,
        blank=True,
    )

    def __str__(self):
        if self.hospital:
            return f"{self.name} - {self.hospital.code}"
        return self.name


class Role(models.Model):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name or self.code


class ServiceItem(models.Model):
    """
    Master list of billable / trackable hospital services.
    Referenced by workflow.PatientServiceLog and others.
    """
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="service_items",
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Default price used for billing if not overridden.",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class StaffProfile(models.Model):
    """
    One profile per user.
    Multi-tenant: user belongs to a hospital + department.
    Permissions: driven by many-to-many Role.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="staffprofile",
    )

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff",
    )

    roles = models.ManyToManyField(
        Role,
        blank=True,
        related_name="staff",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                name="unique_staffprofile_per_user",
            )
        ]

    def __str__(self):
        return self.user.username

    def has_role(self, *codes: str) -> bool:
        """
        Convenience: sp.has_role("FINANCE", "ADMIN")
        """
        norm = [c.upper() for c in codes]
        return self.roles.filter(code__in=norm).exists()
