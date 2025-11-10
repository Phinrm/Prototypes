
from django.contrib import admin
from django.urls import path, include
from ui import views as uiv
from daas.views import ShiftReportView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from ui import views as ui_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", uiv.login_view, name="login"),
    path("logout/", uiv.logout_view, name="logout"),
    path("", uiv.dashboard, name="dashboard"),
    path("department/", include("ui.urls")),
    path("patients/", include("patients.urls")),
    path("workflow/", include("workflow.urls")),
    path("api/", include("api.urls")),
    path("daas/", include("daas.urls")),
    path("daas/reports/", ShiftReportView.as_view(), name="daas_shift_report"),
    
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="api-docs"),

    
    path("find-patient/", uiv.find_patient, name="find_patient"),
    path("attended-today/", uiv.attended_today, name="attended_today"),
    path("my-profile/", uiv.my_profile, name="my_profile"),

    # ...
    path("export/worklist/csv/", uiv.export_worklist_csv, name="export_worklist_csv"),
    path("export/worklist/pdf/", uiv.export_worklist_pdf, name="export_worklist_pdf"),
    # ...
    path("set-shift/", uiv.set_shift, name="set_shift"),

    #audit
    path("audit/", include("audit.urls")),
    #messaging
    path("messages/", include("messaging.urls")),
    #register patient
    path("department/register-patient/", ui_views.register_patient, name="register_patient"),
    #refer patient
    path("patient/<str:upi>/refer/", ui_views.refer_patient, name="refer_patient"),




]


