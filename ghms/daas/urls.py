from django.urls import path
from .views import (
    ingest,
    ShiftReportView,
    ShiftFeedbackView,
    DaasIngestView,
)

urlpatterns = [
    # Telemetry ingest from DAAS agents (original function-based endpoint)
    path("ingest/", ingest, name="daas_ingest"),

    # Optional v2 API-style ingest (if you choose to use it)
    path("ingest/v2/", DaasIngestView.as_view(), name="daas_ingest_v2"),

    # DAAS shift oversight page (used in the navbar as daas_shift_report)
    path("shifts/", ShiftReportView.as_view(), name="daas_shift_report"),

    # Feedback endpoint for auditors/admins to mark shifts as Verified/Invalid
    path("shifts/<int:pk>/feedback/", ShiftFeedbackView.as_view(), name="daas_shift_feedback"),
]
