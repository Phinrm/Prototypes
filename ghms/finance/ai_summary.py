import os
import logging
from django.conf import settings

from workflow.models import PatientServiceLog

logger = logging.getLogger(__name__)


class LLMNotConfigured(Exception):
    """Raised when no valid LLM configuration is available."""
    pass


def _get_gemini_api_key() -> str:
    """
    Get Gemini API key from settings or environment.
    Raises LLMNotConfigured if missing.
    """
    key = getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
    if not key:
        raise LLMNotConfigured("GEMINI_API_KEY is not configured.")
    return key


def call_gemini(prompt: str) -> str:
    """
    Thin wrapper around Gemini.
    - Uses GEMINI_API_KEY
    - Raises LLMNotConfigured on any config/import/network failure
    """
    key = _get_gemini_api_key()

    try:
        import google.generativeai as genai
    except ImportError:
        raise LLMNotConfigured("google-generativeai package is not installed.")

    try:
        genai.configure(api_key=key)
        model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
        model = genai.GenerativeModel(model_name)
        resp = model.generate_content(prompt)

        # Try to extract text robustly
        text = getattr(resp, "text", "") or ""
        if not text and getattr(resp, "candidates", None):
            parts = resp.candidates[0].content.parts
            if parts:
                text = getattr(parts[0], "text", "") or ""

        return (text or "").strip()
    except Exception as exc:
        logger.warning("Gemini call failed: %s", exc, exc_info=True)
        # For our app, treat any runtime failure as "not configured" so we fall back safely
        raise LLMNotConfigured("Gemini runtime failure")


def summarize_patient_services(patient) -> str:
    """
    Build a structured summary of a patient's service history.
    - If Gemini is available, returns AI-generated narrative.
    - If not, returns a deterministic bullet list (no external calls).
    """
    logs = (
        PatientServiceLog.objects.filter(patient=patient)
        .select_related("service", "department")
        .order_by("created_at")
    )

    if not logs.exists():
        return "No clinical or billing data recorded for this patient yet."

    bullet_lines = []
    for s in logs:
        dept_name = s.department.name if getattr(s, "department", None) else "N/A"
        bullet_lines.append(
            f"- {s.created_at.date()} | {dept_name}: "
            f"{s.service.name} x{s.quantity} @ {s.unit_price} = {s.total_price}"
        )

    baseline = "\n".join(bullet_lines)

    prompt = (
        "You are an AI assistant for a public hospital EMR.\n"
        "Summarize the patient's journey based ONLY on the following services.\n"
        "Highlight key investigations, treatments, and pending financial/clinical actions.\n"
        "Be concise, structured, and NEVER invent information.\n\n"
        f"{baseline}\n"
    )

    try:
        ai_text = call_gemini(prompt)
        return ai_text or baseline
    except LLMNotConfigured:
        # Safe local fallback
        return baseline
