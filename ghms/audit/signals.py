from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from .utils import log  # our normalized helper


@receiver(post_save, sender=User)
def audit_user_save(sender, instance, created, **kwargs):
    """
    Audit when users are created or updated.
    Runs without request, so actor is 'system' (None).
    """
    action = "USER_CREATED" if created else "USER_UPDATED"

    log(
        actor=None,  # no request context here
        action=action,
        object_type="auth.User",
        object_id=str(instance.pk),
        meta={
            "username": instance.username,
            # you CANNOT get IP here reliably; leave it out
        },
    )