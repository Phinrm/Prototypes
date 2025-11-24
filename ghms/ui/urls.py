
from django.urls import path
from . import views
from ui import views as ui_views

urlpatterns = [
    path("", views.department_home, name="department_home"),
    path("patient/<str:upi>/", views.patient_detail, name="patient_detail"),
    path("lab/<str:upi>/order/", views.lab_create_order_persist, name="lab_create_order"),
    path("lab/<str:upi>/finalize/", views.lab_finalize_result_persist, name="lab_finalize_result"),
    path("radiology/<str:upi>/order/", views.radiology_order_persist, name="radiology_order"),
    path("radiology/<str:upi>/report/", views.radiology_report_persist, name="radiology_report"),
    path("pharmacy/<str:upi>/dispense/", views.pharmacy_dispense_persist, name="pharmacy_dispense"),
    path("finance/<str:upi>/invoice/", views.finance_invoice_persist, name="finance_invoice"),
    path("register-patient/", ui_views.register_patient, name="register_patient"),
    path("patient/<str:upi>/complete/", ui_views.complete_department_process, name="complete_department_process"),
     path("register-patient/", ui_views.register_patient, name="register_patient"),
]
