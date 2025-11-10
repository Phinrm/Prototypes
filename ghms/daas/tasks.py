from celery import shared_task
from .logic import process_event_and_update_shift

@shared_task
def process_daas_event_task(event_id):
    from .models import DaasEvent
    event = DaasEvent.objects.get(id=event_id)
    process_event_and_update_shift(event)
