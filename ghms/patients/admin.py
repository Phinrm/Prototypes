
from django.contrib import admin
from .models import Patient
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display=("upi","full_name","national_id","phone")
    search_fields=("upi","full_name","national_id","phone")
