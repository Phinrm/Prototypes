
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register("patients", PatientViewset, basename="api-patients")
router.register("referrals", ReferralViewset, basename="api-referrals")
router.register("lab/orders", LabOrderViewset, basename="api-lab-orders")
router.register("lab/results", LabResultViewset, basename="api-lab-results")
router.register("rad/orders", ImagingOrderViewset, basename="api-rad-orders")
router.register("rad/studies", ImagingStudyViewset, basename="api-rad-studies")
router.register("rx", PrescriptionViewset, basename="api-rx")
router.register("dispense", PharmacyDispenseViewset, basename="api-dispense")
router.register("invoice", InvoiceViewset, basename="api-invoice")
router.register("payment", PaymentViewset, basename="api-payment")

urlpatterns = [ path("", include(router.urls)) ]
