
import json
from django.conf import settings

def export_to_siem(event: dict):
    path = getattr(settings, "SIEM_EXPORT_PATH", "siem_events.ndjson")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
