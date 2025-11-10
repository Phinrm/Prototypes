from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    timestamp = models.DateTimeField()
    action = models.CharField(max_length=255)

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )

    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    extra_data = models.JSONField(null=True, blank=True)

    prev_hash = models.CharField(max_length=128, blank=True)
    curr_hash = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ["-timestamp", "-id"]

    def __str__(self):
        who = self.actor.username if self.actor else "system"
        return f"[{self.timestamp}] {who} {self.action} {self.object_type}#{self.object_id}"
