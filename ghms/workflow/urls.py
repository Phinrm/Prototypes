
from django.urls import path
from . import views
urlpatterns = [
    path("push/<str:upi>/", views.push_patient, name="push_patient"),
    path("accept/<int:ref_id>/", views.accept_referral, name="accept_referral"),
    path("complete/<int:ref_id>/", views.complete_referral, name="complete_referral"),
]
