# messaging/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.inbox, name="msg_inbox"),
    path("compose/", views.message_compose, name="msg_compose"),
    path("thread/<int:thread_id>/", views.thread_detail, name="msg_thread"),
    path("start/<int:user_id>/", views.start_thread, name="msg_start"),
]
