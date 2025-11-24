
from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "action",
        "actor",
        "object_type",
        "object_id",
        "ip_address",
        "prev_hash",
        "curr_hash",
    )

    list_filter = (
        "action",
        "object_type",
        "ip_address",
        "timestamp",
    )

    search_fields = (
        "action",
        "object_type",
        "object_id",
        "ip_address",
        "actor__username",
        "extra_data",
        "prev_hash",
        "curr_hash",
    )

    readonly_fields = (
        "timestamp",
        "action",
        "actor",
        "object_type",
        "object_id",
        "ip_address",
        "extra_data",
        "prev_hash",
        "curr_hash",
    )

    ordering = ("-timestamp", "-id")