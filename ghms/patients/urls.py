
from django.urls import path
from . import views

urlpatterns = [
    path("search/", views.search_landing, name="patient_search_landing"),
    path("search/upi/", views.search_by_upi, name="search_by_upi"),
    path("search/national/", views.search_by_national, name="search_by_national"),
    path("search/phone/", views.search_by_phone, name="search_by_phone"),
    path("search/phone/verify/", views.verify_phone_otp, name="verify_phone_otp"),
]
