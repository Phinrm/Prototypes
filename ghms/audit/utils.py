import json
import hashlib
from django.utils import timezone
from .models import AuditLog
from django.conf import settings
import os
 

GENESIS_HASH = "GENESIS"

SIEM_PATH = getattr(
    settings,
    "SIEM_EXPORT_PATH",
    os.path.join(settings.BASE_DIR, "siem_events.ndjson"),
)

def _compute_hash(prev_hash: str, payload: dict) -> str:
    data = json.dumps(
        {"prev": prev_hash, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _get_last_hash():
    last = AuditLog.objects.order_by("-id").first()
    return last.curr_hash if last else GENESIS_HASH


def compute_entry_hash(entry, prev_hash: str) -> str:
    """
    Compute a SHA256 hash for an audit entry + prev_hash.

    Accepts either:
    - an AuditLog instance, or
    - a dict with the same keys we use in log().
    """
    if isinstance(entry, AuditLog):
        payload = {
            "ts": entry.timestamp.isoformat(),
            "action": entry.action,
            "object_type": entry.object_type or "",
            "object_id": entry.object_id or "",
            "actor_id": entry.actor_id,
            "ip": entry.ip_address or "",
            "extra": entry.extra_data or {},
        }
    else:
        # assume dict-like
        payload = {
            "ts": entry.get("ts") or entry.get("timestamp"),
            "action": entry.get("action", ""),
            "object_type": entry.get("object_type", ""),
            "object_id": str(entry.get("object_id", "")),
            "actor_id": entry.get("actor_id"),
            "ip": entry.get("ip", "") or entry.get("ip_address", ""),
            "extra": entry.get("extra") or entry.get("extra_data") or {},
        }

    payload["prev_hash"] = prev_hash
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def log(actor=None, action=None, object_type="", object_id="", meta=None):
    """
    Flexible audit logger.

    Usage patterns supported:

      log(request.user, "SHIFT_DEFINED",
          object_type="DaasShiftSummary", object_id="123", meta={...})

      log("USER_LOGIN", object_type="auth.User", object_id="1")

    It auto-detects whether AuditLog has fields like:
      - actor (FK)
      - user (FK)
      - details / extra / meta (for JSON/text)
    and only passes allowed fields.
    """

    # Backwards compatibility: allow log("ACTION_CODE", ...)
    if action is None and isinstance(actor, str):
        action = actor
        actor = None

    # Normalise meta
    if meta is None:
        meta = {}
    elif not isinstance(meta, dict):
        meta = {"data": str(meta)}

    # Introspect AuditLog fields so we don't pass invalid kwargs
    field_names = {f.name for f in AuditLog._meta.get_fields()}

    kwargs = {}

    # Timestamp
    if "timestamp" in field_names:
        kwargs["timestamp"] = timezone.now()

    # Action
    if "action" in field_names:
        kwargs["action"] = action or ""

    # Object type / id
    if "object_type" in field_names:
        kwargs["object_type"] = object_type or ""
    if "object_id" in field_names:
        kwargs["object_id"] = str(object_id or "")

    # Actor / user mapping
    actor_id = None
    if actor is not None and hasattr(actor, "pk"):
        actor_id = actor.pk

    if actor_id is not None:
        if "actor" in field_names:
            kwargs["actor_id"] = actor_id
        elif "user" in field_names:
            kwargs["user_id"] = actor_id

    # Meta / extra info
    if meta:
        meta_json = json.dumps(meta, default=str)

        if "meta" in field_names:
            # If your model actually has a JSONField/TextField called 'meta'
            kwargs["meta"] = meta
        elif "extra" in field_names:
            kwargs["extra"] = meta_json
        elif "details" in field_names:
            kwargs["details"] = meta_json
        # else: silently ignore, to avoid TypeError

    # Finally create the log row
    AuditLog.objects.create(**kwargs)

def hashchain_log(action: str, data: dict, actor=None, ip_address: str | None = None):
    """
    Backwards-compatible helper wrapping log().

    Expects `data` to contain any contextual fields you want stored in extra_data.
    """
    object_type = data.get("object_type", "")
    object_id = data.get("object_id")

    return log(
        action=action,
        object_type=object_type,
        object_id=object_id,
        actor=actor,
        ip_address=ip_address,
        extra_data=data,
    )


def verify_hash_chain():
    """
    Walk the ledger and verify that curr_hash matches the recomputed hash chain.

    Returns (ok: bool, broken_id: int | None)
    """
    prev = GENESIS_HASH
    for rec in AuditLog.objects.order_by("id"):
        expected = compute_entry_hash(rec, prev)
        if rec.curr_hash != expected:
            return False, rec.id
        prev = rec.curr_hash
    return True, None


def generate_pdf_from_logs(logs_queryset):
    """
    Minimal PDF export used by audit console.

    Returns raw PDF bytes.
    """
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, y, "Audit Log Export")
    y -= 20

    p.setFont("Helvetica", 8)
    for log in logs_queryset.order_by("-timestamp")[:5000]:
        actor = getattr(log.actor, "username", "system") if log.actor_id else "system"
        line = (
            f"{log.timestamp} | {actor} | {log.action} | "
            f"{log.object_type}#{log.object_id} | {log.ip_address or ''}"
        )
        p.drawString(40, y, line[:200])
        y -= 10
        if y < 40:
            p.showPage()
            y = height - 40
            p.setFont("Helvetica", 8)

    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
