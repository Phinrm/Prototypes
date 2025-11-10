import os
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


class LLMNotConfigured(Exception):
    pass


def _check_config():
    if not GEMINI_API_KEY:
        raise LLMNotConfigured("GEMINI_API_KEY not set")


def call_gemini(prompt: str, temperature: float = 0.3) -> str:
    _check_config()

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}

    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 512,
        },
    }

    resp = requests.post(API_URL, headers=headers, params=params, json=data, timeout=15)
    resp.raise_for_status()
    body = resp.json()

    try:
        return body["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return ""
