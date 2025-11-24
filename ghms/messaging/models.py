# messaging/models.py

from django.db import models
from django.contrib.auth.models import User
from core.models import Hospital

class Thread(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="threads")
    participants = models.ManyToManyField(User, related_name="message_threads")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        users = ", ".join(self.participants.values_list("username", flat=True))
        return f"Thread({self.hospital.code}): {users}"


class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(User, related_name="read_messages", blank=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.sender.username}: {self.body[:40]}"
