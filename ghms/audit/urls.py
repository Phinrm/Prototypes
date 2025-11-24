from django.urls import path
from . import views

from .views import VerifyHashChainView


urlpatterns = [
    path("api/audit/verify-chain/", VerifyHashChainView.as_view(), name="audit-verify-chain"),
    path("console/", views.audit_console, name="audit_console"),
    path("export-pdf/", views.export_audit_pdf, name="audit_export_pdf"),


]