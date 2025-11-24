
from django.contrib import admin
from .models import Referral

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ("id", "from_department", "to_department", "patient", "created_at")
    list_filter = ("from_department", "to_department")